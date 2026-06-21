"""PHASE1: TOR 경고 + 시선/그립 모니터링.

출력: 빨강 LED 깜빡임 + 부저(잔여시간 비례) + 진동 ON + LCD 경고.
입력:
  - 그립(핸들 파지): monitoring/grip — 라파에선 터치센서, SIM/센서미연결이면 dummy 시간.
  - 시선: 아직 판정 미구현 → dummy.gaze_ok_after 더미 사용.
둘 다 충족하면 PHASE2, tor_budget 안에 못 채우면 MRM.

타이밍:
  카운트다운은 절대시각(monotonic) 기준으로 1초마다 정확히 한 틱씩 진행한다.
  매 틱마다 LED+부저를 동기 펄스로 울리며, 잔여시간이 짧을수록 더 빠르게 깜빡/삐삐.
"""

import time

from core.states import STATE_PHASE2, STATE_MRM
from hmi import led, buzzer, vibration, lcd, screens
from iot import telemetry
from monitoring import grip


def _alarm_pulse(remaining: int, urgent: int, critical: int):
    """잔여(초)에 따라 LED+부저를 동기로 펄스. 1틱 안에서 끝나도록 짧게.

    remaining > urgent           → 1회 (느림)
    urgent ≥ remaining > critical → 2회 (빠름)
    remaining ≤ critical         → 4회 (가장 빠름)
    """
    if remaining > urgent:
        beats, on_t, off_t = 1, 0.10, 0.0
    elif remaining > critical:
        beats, on_t, off_t = 2, 0.08, 0.12
    else:
        beats, on_t, off_t = 4, 0.05, 0.07

    for i in range(beats):
        led.red_on()
        buzzer.on()
        time.sleep(on_t)
        led.red_off()
        buzzer.off()
        if i < beats - 1:
            time.sleep(off_t)


def run(context):
    scenario = context["scenario"]
    config = context["config"]
    value = context.get("param", scenario.get("param", {}).get("default", 0))

    tor_budget = int(config["timing"]["tor_budget"])
    urgent = int(config["timing"]["warning_urgent"])
    critical = int(config["timing"]["warning_critical"])
    gaze_ok_after = config["dummy"]["gaze_ok_after"]

    # LCD 1행 경고문(예: "WARN:400m"). {v} 에 입력 수치를 치환.
    warn_prefix = scenario["lcd"]["phase1"].format(v=value)

    print(f"[PHASE1] TOR warning started ({scenario['label']}, {warn_prefix})")
    grip.configure(config)
    stt_session = None
    if config.get("dummy", {}).get("use_real_voice", False):
        from core.states.phase2 import prepare as prepare_stt
        stt_session = prepare_stt(config["voice"])
    vibration.on()

    # 입력 즉시 카운트다운 화면을 띄운다 — 카메라는 프로그램 시작 시 이미
    # 초기화돼 있으므로(아래 공유 모니터) "로딩" 공백 없이 바로 보인다.
    lcd.show(*screens.phase1(warn_prefix, tor_budget, False, False))

    # 시선 모니터는 app.py에서 프로그램 시작 시 1회 초기화해 context로 넘어온다.
    # 매 세션 카메라를 새로 열지 않으므로 PHASE1 진입이 즉시 이뤄진다.
    # 카메라가 없으면 use_real_gaze=False → 더미(gaze_ok_after) 사용.
    gaze_monitor = context.get("gaze_monitor")
    use_real_gaze = context.get("use_real_gaze", False) and gaze_monitor is not None
    if use_real_gaze:
        gaze_monitor.reset()  # 이번 세션은 새로 1초 응시를 요구(직전 상태 무시)
        gaze_csv = telemetry.gaze_log_path(context["session_id"])
        gaze_monitor.start_logging(gaze_csv)
        print(f"[PHASE1] Gaze metrics logging → {gaze_csv}")
    else:
        print(f"[PHASE1] No camera — dummy gaze active (ok after {gaze_ok_after}s)")

    # cv2 window must be driven from the main thread (Windows HighGUI constraint).
    show_preview = use_real_gaze and gaze_monitor.show_preview
    if show_preview:
        import cv2

    gaze_ok = False
    grip_ok = False
    start = time.monotonic()

    try:
        # tick = 표시될 잔여초. tor_budget 부터 1 까지 1초 간격으로 정확히 한 번씩.
        for tick in range(tor_budget, 0, -1):
            remaining = tick
            elapsed = tor_budget - tick

            # Gaze: real camera (green box >= 1 s) or time-based dummy
            if not gaze_ok:
                if use_real_gaze:
                    if gaze_monitor.is_gaze_ok(required_duration=1.0):
                        gaze_ok = True
                        if show_preview:
                            cv2.destroyAllWindows()
                            cv2.waitKey(1)
                            show_preview = False
                        # 공유 모니터는 멈추지 않는다(다음 세션 재사용)
                        print("[PHASE1] Gaze OK (green detection for 1s)")
                else:
                    if elapsed >= gaze_ok_after:
                        gaze_ok = True
                        print("[PHASE1] [DUMMY] Gaze detected (gaze=OK)")

            if not grip_ok and grip.is_gripped(elapsed):
                grip_ok = True
                print("[PHASE1] Handle grip detected (grip=OK)")

            # 콘솔 디버깅 로그
            gaze_str = "OK" if gaze_ok else " X"
            grip_str = "OK" if grip_ok else " X"
            print(f"[PHASE1] {remaining}s | gaze=[{gaze_str}] grip=[{grip_str}]")

            # HMI 출력 (4줄 화면)
            lcd.show(*screens.phase1(warn_prefix, remaining, gaze_ok, grip_ok))

            # 둘 다 충족 → PHASE2 (잠금/펄스 없이 즉시 이탈)
            if gaze_ok and grip_ok:
                # 남은 카운트다운 초를 PHASE2로 넘긴다 → 거기서 이어서 카운트다운(+3초 유예)
                context["phase1_remaining"] = remaining
                context["stt_session"] = stt_session
                print(f"[PHASE1] Conditions met → entering PHASE2 "
                      f"(remaining {remaining}s carried over)")
                _warnings_off(red_off=True)
                return STATE_PHASE2

            # 1 틱 분량의 LED+부저 동기 펄스 (잔여가 짧을수록 더 빠르게)
            _alarm_pulse(remaining, urgent, critical)

            # 절대시각 기준으로 다음 틱(elapsed+1초)까지 대기 → 드리프트 방지
            # show_preview 모드에서는 대기 중 cv2 이벤트 루프를 펌핑해 창을 갱신한다.
            next_deadline = start + (elapsed + 1)
            if show_preview:
                while True:
                    remaining_sleep = next_deadline - time.monotonic()
                    if remaining_sleep <= 0:
                        break
                    frame = gaze_monitor.get_preview_frame()
                    if frame is not None:
                        cv2.imshow("Gaze Monitor", frame)
                    cv2.waitKey(max(1, min(30, int(remaining_sleep * 1000))))
            else:
                sleep_for = next_deadline - time.monotonic()
                if sleep_for > 0:
                    time.sleep(sleep_for)

        # 시간 초과 → MRM (부족한 조건 기록: LCD 코드 + 콘솔 사유)
        if not gaze_ok:
            context["fail_code"] = "NoEye"
            context["fail_reason"] = "Not looking forward"
        elif not grip_ok:
            context["fail_code"] = "NoGrip"
            context["fail_reason"] = "Handle not gripped"
        else:
            context["fail_code"] = "Timeout"
            context["fail_reason"] = "Unknown"

        print(f"[PHASE1] Timeout → entering MRM (reason: {context['fail_reason']})")
        _warnings_off(red_off=False)  # 빨강은 MRM 이 이어서 유지
        return STATE_MRM

    finally:
        if use_real_gaze:
            gaze_monitor.stop_logging()
        if stt_session is not None and context.get("phase1_remaining") is None:
            from core.states.phase2 import cleanup_session as cleanup_stt_session
            cleanup_stt_session(stt_session)
        if show_preview:
            cv2.destroyAllWindows()
            cv2.waitKey(1)
        # 공유 GazeMonitor는 여기서 멈추지 않는다 — 프로그램 종료 시 app.py가 정리.


def _warnings_off(red_off: bool):
    """PHASE1 경고 출력 정리. 부저/진동은 항상 끄고, 빨강 LED 는 선택."""
    buzzer.off()
    vibration.off()
    if red_off:
        led.red_off()
