"""시선(카메라) 입력 (프레임 캡쳐만).

이 단계 목표는 "카메라 프레임이 들어온다"까지. 시선 방향 판정은 다음 단계.
프레임 1장을 .jpg 로 저장해 카메라 경로를 검증한다.

PHASE1 통합은 아직(시선 판정 미구현) — 현재 PHASE1 의 시선 OK 는
dummy.gaze_ok_after 더미를 그대로 쓴다. 본 모듈의 capture() 는
PHASE1 시작 시 1장 저장하는 용도로만 선택적으로 호출한다.

단독 테스트(라파에서 카메라 연결 후):
    python -m monitoring.gaze      → 한 프레임을 captures/gaze_*.jpg 로 저장
"""
import os
import time

try:
    import cv2  # type: ignore
    _HAS_CV2 = True
except (ImportError, OSError):
    cv2 = None
    _HAS_CV2 = False


def capture(out_path: str, camera_index: int = 0) -> str:
    """카메라에서 한 프레임을 잡아 out_path(.jpg) 로 저장하고 경로 반환.

    cv2 가 없거나 카메라가 없으면 콘솔 시뮬레이션만 한다(저장 안 함).
    """
    if not _HAS_CV2:
        print(f"[GAZE][SIM] 📷 Frame capture (simulated) → {out_path}")
        return out_path

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    cap = cv2.VideoCapture(camera_index)
    try:
        ok, frame = cap.read()
        if not ok:
            print("[GAZE] ⚠ Failed to read camera frame")
            return ""
        cv2.imwrite(out_path, frame)
        print(f"[GAZE] Saved: {out_path}")
        return out_path
    finally:
        cap.release()


if __name__ == "__main__":
    out_dir = "./data/captures"
    out = os.path.join(out_dir, f"gaze_{int(time.time())}.jpg")
    print("[TEST] Camera frame capture test")
    capture(out)
    print("[TEST] Done")
