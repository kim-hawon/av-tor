"""PHASE1: TOR 경고 + 시선/그립 모니터링 (센서 영역).

더미1. : 실제 센서 대신 config의 dummy 값으로 시뮬레이션
  - gaze_ok_after 초 후 시선 OK
  - grip_ok_after 초 후 핸들 파지 OK
둘 다 충족하면 PHASE2, tor_budget 안에 못 채우면 MRM.
"""
import time
from core.timer import Timer
from core.states import STATE_PHASE2, STATE_MRM


def run(context):
    scenario = context["scenario"]
    config = context["config"]

    tor_budget = config["timing"]["tor_budget"]
    gaze_ok_after = config["dummy"]["gaze_ok_after"]
    grip_ok_after = config["dummy"]["grip_ok_after"]

    print(f"[PHASE1] TOR 경고 시작 ({scenario['label']})")
    print("[PHASE1] HMI 가정: LED 깜빡임, 부저 울림, 진동 ON, LCD 경고")

    timer = Timer(tor_budget)
    timer.start()

    gaze_ok = False
    grip_ok = False

    # 1초마다 상태 체크
    while not timer.is_done():
        remaining = int(timer.remaining())
        elapsed = int(timer.elapsed())

        # 더미: 일정 시간 후 자동으로 조건 충족
        if not gaze_ok and elapsed >= gaze_ok_after:
            gaze_ok = True
            print("[PHASE1] [더미] 시선 감지됨 (gaze=OK)")
        if not grip_ok and elapsed >= grip_ok_after:
            grip_ok = True
            print("[PHASE1] [더미] 핸들 파지 감지됨 (grip=OK)")

        gaze_str = "OK" if gaze_ok else " X"
        grip_str = "OK" if grip_ok else " X"
        print(f"[PHASE1] {remaining}s | gaze=[{gaze_str}] grip=[{grip_str}]")

        # 둘 다 충족 → PHASE2
        if gaze_ok and grip_ok:
            print("[PHASE1] 조건 충족 → PHASE2 진입")
            return STATE_PHASE2

        time.sleep(1)

    # 시간 초과 → MRM (부족한 조건 기록)
    if not gaze_ok:
        context["fail_reason"] = "전방 미주시"
    elif not grip_ok:
        context["fail_reason"] = "핸들 미파지"
    else:
        context["fail_reason"] = "알 수 없음"

    print(f"[PHASE1] 시간 초과 → MRM 진입 (사유: {context['fail_reason']})")
    return STATE_MRM
