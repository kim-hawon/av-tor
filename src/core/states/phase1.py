"""PHASE1: TOR 경고 + 시선/그립 모니터링.

출력: 빨강 LED 깜빡임 + 부저(잔여시간 비례) + 진동 ON + LCD 경고.
입력:
  - 그립(핸들 파지): monitoring/grip — 라파에선 터치센서, SIM 이면 dummy 시간.
  - 시선: 아직 판정 미구현 → dummy.gaze_ok_after 더미 사용.
둘 다 충족하면 PHASE2, tor_budget 안에 못 채우면 MRM.
콘솔 로그(`[PHASE1] ...`)는 디버깅용으로 계속 출력한다.
"""
import time

from core.timer import Timer
from core.states import STATE_PHASE2, STATE_MRM
from hmi import led, buzzer, vibration, lcd, screens
from monitoring import grip


def run(context):
    scenario = context["scenario"]
    config = context["config"]
    value = context.get("param", scenario.get("param", {}).get("default", 0))

    tor_budget = config["timing"]["tor_budget"]
    urgent = config["timing"]["warning_urgent"]
    critical = config["timing"]["warning_critical"]
    gaze_ok_after = config["dummy"]["gaze_ok_after"]

    # LCD 1행 경고문(예: "WARN:400m"). {v} 에 입력 수치를 치환.
    warn_prefix = scenario["lcd"]["phase1"].format(v=value)

    print(f"[PHASE1] TOR 경고 시작 ({scenario['label']}, {warn_prefix})")
    grip.configure(config)
    vibration.on()

    timer = Timer(tor_budget)
    timer.start()

    gaze_ok = False
    grip_ok = False

    while not timer.is_done():
        remaining = int(timer.remaining())
        elapsed = int(timer.elapsed())

        # 시선: 더미 / 그립: 센서(SIM 이면 시간 기반)
        if not gaze_ok and elapsed >= gaze_ok_after:
            gaze_ok = True
            print("[PHASE1] [더미] 시선 감지됨 (gaze=OK)")
        if not grip_ok and grip.is_gripped(elapsed):
            grip_ok = True
            print("[PHASE1] 핸들 파지 감지됨 (grip=OK)")

        # 콘솔 디버깅 로그
        gaze_str = "OK" if gaze_ok else " X"
        grip_str = "OK" if grip_ok else " X"
        print(f"[PHASE1] {remaining}s | gaze=[{gaze_str}] grip=[{grip_str}]")

        # HMI 출력
        lcd.show(*screens.phase1(warn_prefix, remaining, gaze_ok, grip_ok))
        led.red_toggle()                       # 1초 간격 깜빡임
        buzzer.urgency(remaining, urgent, critical)

        # 둘 다 충족 → PHASE2
        if gaze_ok and grip_ok:
            print("[PHASE1] 조건 충족 → PHASE2 진입")
            _warnings_off(red_off=True)
            return STATE_PHASE2

        time.sleep(1)

    # 시간 초과 → MRM (부족한 조건 기록: LCD 코드 + 콘솔 사유)
    if not gaze_ok:
        context["fail_code"] = "NoEye"
        context["fail_reason"] = "전방 미주시"
    elif not grip_ok:
        context["fail_code"] = "NoGrip"
        context["fail_reason"] = "핸들 미파지"
    else:
        context["fail_code"] = "Timeout"
        context["fail_reason"] = "알 수 없음"

    print(f"[PHASE1] 시간 초과 → MRM 진입 (사유: {context['fail_reason']})")
    _warnings_off(red_off=False)  # 빨강은 MRM 이 이어서 유지
    return STATE_MRM


def _warnings_off(red_off: bool):
    """PHASE1 경고 출력 정리. 부저/진동은 항상 끄고, 빨강 LED 는 선택."""
    buzzer.off()
    vibration.off()
    if red_off:
        led.red_off()
