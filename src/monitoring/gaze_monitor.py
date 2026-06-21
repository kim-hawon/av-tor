"""Real-time gaze monitoring using dlib face landmarks.

Runs in a background thread so phase1's countdown loop is not blocked.
Detection logic mirrors realtime_drowsiness.py:
  - EAR (Eye Aspect Ratio) > 0.2  → eyes open
  - nose center ratio 0.4–0.6     → looking forward
  Both conditions met → detection box is "green" (gaze OK).

Usage:
    monitor = GazeMonitor()
    if monitor.start():          # True = camera + model found
        ...
        if monitor.is_gaze_ok(): # green for >= 1 s
            gaze_ok = True
        monitor.stop()
    else:
        # fall back to time-based dummy logic
"""

import os
import threading
import time

import numpy as np

EAR_THRESHOLD = 0.2
NOSE_RATIO_MIN = 0.4
NOSE_RATIO_MAX = 0.6

# shape_predictor sits next to realtime_drowsiness.py at the workspace root
# This file lives at  src/monitoring/gaze_monitor.py  → 2 levels up = root
_DLIB_MODEL = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
        "models",
        "68_face",
        "shape_predictor_68_face_landmarks.dat",
    )
)


def _dist(a, b):
    return np.linalg.norm(np.array(a, dtype=float) - np.array(b, dtype=float))


def _ear(eye):
    return (_dist(eye[1], eye[5]) + _dist(eye[2], eye[4])) / (
        2.0 * _dist(eye[0], eye[3])
    )


def _nose_ratio(lm):
    left_cx = sum(lm[i][0] for i in range(36, 42)) / 6.0
    right_cx = sum(lm[i][0] for i in range(42, 48)) / 6.0
    if right_cx == left_cx:
        return 0.5
    return (lm[30][0] - left_cx) / (right_cx - left_cx)


def _frame_is_green(lm) -> bool:
    ear = (_ear(lm[36:42]) + _ear(lm[42:48])) / 2.0
    ratio = _nose_ratio(lm)
    return ear > EAR_THRESHOLD and NOSE_RATIO_MIN <= ratio <= NOSE_RATIO_MAX


class GazeMonitor:
    """Background capture thread that tracks how long the detection box stays green."""

    def __init__(self, camera_index: int = None, show_preview: bool = False):
        self.camera_index = camera_index
        self.show_preview = show_preview
        self.available = False
        self._lock = threading.Lock()
        self._green_since = None  # monotonic timestamp when green streak started
        self._running = False
        self._thread = None
        self._cap = None             # start()에서 연 카메라 핸들 — 스레드가 그대로 재사용
        self._preview_frame = None   # latest annotated frame; displayed by main thread
        self._frame_lock = threading.Lock()
        # Logging
        self._log_path = None
        self._log_fh = None
        self._log_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> bool:
        """Open camera and load dlib model. Returns True on success."""
        try:
            import cv2
            import dlib  # noqa: F401
        except ImportError:
            print("[GAZE] cv2/dlib not available — no camera gaze detection")
            return False

        if not os.path.isfile(_DLIB_MODEL):
            print(f"[GAZE] dlib model not found: {_DLIB_MODEL}")
            return False

        import cv2

        # 라파 USB 카메라는 open/read 가 근본적으로 간헐 실패한다(isOpened 가 False 였다가
        # 잠시 뒤 True, open 직후 첫 프레임은 비어 옴 등). 그래서 끈질기게 재시도한다:
        #   - 여러 "라운드"로 후보 인덱스를 반복 시도하고
        #   - open 된 핸들은 첫 프레임이 들어올 때까지 여러 번 read 로 워밍업하고
        #   - 진짜 프레임이 들어오는 노드만 채택(가짜 캡처 노드 거름).
        # 핵심: 한 번 잡은 핸들은 release 하지 않고 스레드가 그대로 재사용한다
        #       (열었다 닫고 바로 다시 여는 것이 간헐 실패를 키운다).
        candidates = [self.camera_index] if self.camera_index is not None else [0, 1, 2]
        ROUNDS = 5            # 전체 후보 목록을 최대 5라운드 반복
        WARMUP_READS = 10     # open 직후 첫 프레임 대기(각 0.1s)
        cap = None
        for round_no in range(1, ROUNDS + 1):
            for idx in candidates:
                c = cv2.VideoCapture(idx, cv2.CAP_V4L2)
                if not c.isOpened():
                    c.release()
                    continue
                c.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
                c.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
                got = False
                for _ in range(WARMUP_READS):
                    ok, frame = c.read()
                    if ok and frame is not None:
                        got = True
                        break
                    time.sleep(0.1)  # 첫 프레임 워밍업 대기
                if got:
                    cap = c
                    self.camera_index = idx
                    break
                c.release()
            if cap is not None:
                break
            print(f"[GAZE] camera open round {round_no}/{ROUNDS} failed — retrying...")
            time.sleep(0.5)  # 라운드 간 백오프

        if cap is None:
            print(
                f"[GAZE] Camera not found/readable (tried {candidates}, {ROUNDS} rounds) "
                f"— no camera gaze detection"
            )
            return False

        self._cap = cap
        self.available = True
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        preview_note = " (preview window ON)" if self.show_preview else ""
        print(
            f"[GAZE] Camera {self.camera_index} detected — real-time gaze monitoring active{preview_note}"
        )
        return True

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def get_preview_frame(self):
        """Return the latest annotated frame for display in the main thread."""
        with self._frame_lock:
            return self._preview_frame

    def start_logging(self, path: str):
        """Start appending per-frame metrics to CSV `path`.

        CSV columns: epoch_ts, monotonic_ts, frame_index, face, ear, nose_ratio, gaze_ok
        """
        with self._log_lock:
            # open in append mode; write header if new
            new_file = not os.path.exists(path)
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            self._log_fh = open(path, "a", buffering=1)
            if new_file:
                self._log_fh.write("epoch_ts,monotonic_ts,frame_index,face,ear,nose_ratio,gaze_ok\n")
            self._log_path = path

    def stop_logging(self):
        with self._log_lock:
            if self._log_fh:
                try:
                    self._log_fh.close()
                except Exception:
                    pass
            self._log_fh = None
            self._log_path = None

    def is_gaze_ok(self, required_duration: float = 1.0) -> bool:
        """True if detection box has been green for >= required_duration seconds."""
        with self._lock:
            if self._green_since is None:
                return False
            return (time.monotonic() - self._green_since) >= required_duration

    def reset(self):
        """현재 green 연속 구간을 초기화한다.

        프로그램 시작 시 한 번 start() 한 모니터를 여러 TOR 세션이 공유할 때,
        새 세션마다 호출해 '직전 응시 상태'가 넘어오지 않고 다시 1초 응시를
        요구하도록 만든다(카메라/스레드는 그대로 유지).
        """
        with self._lock:
            self._green_since = None

    # ------------------------------------------------------------------
    # Background thread
    # ------------------------------------------------------------------

    def _run(self):
        import cv2
        import dlib

        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor(_DLIB_MODEL)

        # start()에서 이미 열어 검증한 핸들을 그대로 사용(재open 금지 — 간헐 실패 방지).
        cap = self._cap
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)   # Pi: 320x240이 4배 빠름
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

        # dlib 검출은 2프레임마다 한 번 — 마지막 결과를 캐시해서 재사용
        _DETECT_EVERY = 2
        frame_count = 0
        last_rect = None
        last_lm = None
        green = False

        while self._running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.05)
                continue

            h, w = frame.shape[:2]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if frame_count % _DETECT_EVERY == 0:
                # 업샘플링 0: 이미지 원본 크기로만 검출 (Pi에서 2-4배 빠름)
                faces = detector(gray, 0)
                if faces:
                    last_rect = faces[0]
                    shape = predictor(gray, last_rect)
                    last_lm = [(shape.part(i).x, shape.part(i).y) for i in range(68)]
                    green = _frame_is_green(last_lm)
                else:
                    last_rect = None
                    last_lm = None
                    green = False
            frame_count += 1

            if self.show_preview:
                if last_lm is not None:
                    ear = (_ear(last_lm[36:42]) + _ear(last_lm[42:48])) / 2.0
                    ratio = _nose_ratio(last_lm)
                    x1 = max(0, last_rect.left())
                    y1 = max(0, last_rect.top())
                    x2 = min(w, last_rect.right())
                    y2 = min(h, last_rect.bottom())
                    box_color = (0, 200, 60) if green else (0, 0, 255)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                    cv2.putText(
                        frame,
                        f"EAR:{ear:.2f}  Nose:{ratio:.2f}",
                        (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (220, 220, 220),
                        1,
                    )
                    label = "Gaze OK" if green else "Gaze NG"
                    label_color = (0, 200, 60) if green else (0, 0, 255)
                    cv2.putText(
                        frame,
                        label,
                        (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        label_color,
                        2,
                    )
                else:
                    cv2.putText(
                        frame,
                        "No face",
                        (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (80, 80, 255),
                        1,
                    )
                with self._frame_lock:
                    self._preview_frame = frame  # cap.read()가 매번 새 배열을 반환하므로 copy 불필요

            with self._lock:
                if green:
                    if self._green_since is None:
                        self._green_since = time.monotonic()
                else:
                    self._green_since = None

            # Per-frame logging if enabled
            if self._log_fh is not None:
                try:
                    epoch_ts = time.time()
                    mono_ts = time.monotonic()
                    face = 1 if last_lm is not None else 0
                    if last_lm is not None:
                        ear = (_ear(last_lm[36:42]) + _ear(last_lm[42:48])) / 2.0
                        ratio = _nose_ratio(last_lm)
                        gaze_ok = 1 if (_ear(last_lm[36:42]) + _ear(last_lm[42:48])) / 2.0 > EAR_THRESHOLD and NOSE_RATIO_MIN <= ratio <= NOSE_RATIO_MAX else 0
                    else:
                        ear = 0.0
                        ratio = 0.0
                        gaze_ok = 0
                    with self._log_lock:
                        if self._log_fh:
                            self._log_fh.write(f"{epoch_ts:.3f},{mono_ts:.3f},{frame_count},{face},{ear:.3f},{ratio:.3f},{gaze_ok}\n")
                except Exception:
                    # don't let logging errors stop the monitor
                    pass

        cap.release()
