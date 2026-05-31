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
        self._preview_frame = None   # latest annotated frame; displayed by main thread
        self._frame_lock = threading.Lock()

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

        candidates = [self.camera_index] if self.camera_index is not None else [0, 1]
        found_index = None
        for idx in candidates:
            cap = cv2.VideoCapture(idx)
            opened = cap.isOpened()
            cap.release()
            if opened:
                found_index = idx
                break

        if found_index is None:
            print(
                f"[GAZE] Camera not found (tried {candidates}) — no camera gaze detection"
            )
            return False

        self.camera_index = found_index
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

    def is_gaze_ok(self, required_duration: float = 1.0) -> bool:
        """True if detection box has been green for >= required_duration seconds."""
        with self._lock:
            if self._green_since is None:
                return False
            return (time.monotonic() - self._green_since) >= required_duration

    # ------------------------------------------------------------------
    # Background thread
    # ------------------------------------------------------------------

    def _run(self):
        import cv2
        import dlib

        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor(_DLIB_MODEL)

        cap = cv2.VideoCapture(self.camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        while self._running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.05)
                continue

            h, w = frame.shape[:2]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector(gray, 1)

            green = False
            if faces:
                rect = faces[0]
                shape = predictor(gray, rect)
                lm = [(shape.part(i).x, shape.part(i).y) for i in range(68)]
                green = _frame_is_green(lm)

                if self.show_preview:
                    ear = (_ear(lm[36:42]) + _ear(lm[42:48])) / 2.0
                    ratio = _nose_ratio(lm)
                    x1 = max(0, rect.left())
                    y1 = max(0, rect.top())
                    x2 = min(w, rect.right())
                    y2 = min(h, rect.bottom())
                    box_color = (0, 200, 60) if green else (0, 0, 255)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                    for lx, ly in lm:
                        cv2.circle(frame, (lx, ly), 1, (0, 200, 255), -1)
                    cv2.putText(
                        frame,
                        f"EAR:{ear:.2f}  Nose:{ratio:.2f}",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (220, 220, 220),
                        2,
                    )
                    label = "Gaze OK" if green else "Gaze NG"
                    label_color = (0, 200, 60) if green else (0, 0, 255)
                    cv2.putText(
                        frame,
                        label,
                        (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        label_color,
                        2,
                    )
            else:
                if self.show_preview:
                    cv2.putText(
                        frame,
                        "No face detected",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (80, 80, 255),
                        2,
                    )

            with self._lock:
                if green:
                    if self._green_since is None:
                        self._green_since = time.monotonic()
                else:
                    self._green_since = None

            if self.show_preview:
                with self._frame_lock:
                    self._preview_frame = frame.copy()

        cap.release()
