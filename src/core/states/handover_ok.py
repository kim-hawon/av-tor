"""HANDOVER_OK: 제어권 전환 성공."""
import time
from core.states import STATE_END


def run(context):
    duration = context["config"]["timing"]["end_screen_duration"]

    print("[HANDOVER_OK] HMI 가정: Red LED OFF, Green LED ON, "
          "스피커 '또로롱', LCD 'MANUAL MODE ACTIVE'")
    print(f"[HANDOVER_OK] 제어권 전환 성공! ({duration}초 표시)")
    time.sleep(duration)
    print("[HANDOVER_OK] 시나리오 종료")
    return STATE_END
