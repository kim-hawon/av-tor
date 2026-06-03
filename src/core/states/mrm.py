"""MRM: 최소위험기동 (제어권 이양 실패 시).

핸드오버 실패(PHASE1 타임아웃 / PHASE2 인지 확인 실패) 시 진입.
출력: 빨강 LED 지속 ON, 초록 OFF, 부저 경보, LCD "EMERGENCY! / Reason:XXX".

지금은 단일 파일. 내부가 0/1/2 단계 등으로 복잡해지면
states/mrm/__init__.py 패키지로 승격하는 것을 고려.
"""
import time

from core.states import STATE_END
from hmi import led, buzzer, lcd, screens
from iot import telegram_notify


def run(context):
    config = context["config"]
    duration = config["timing"]["end_screen_duration"]
    reason = context.get("fail_reason", "Unknown")
    reason_code = context.get("fail_code", "Unknown")

    led.green_off()
    led.red_on()                       # 비상 — 빨강 지속
    lcd.show(*screens.mrm(reason_code))
    buzzer.beep(on_time=0.2, off_time=0.15, count=3)

    print(f"[MRM] Emergency stop (reason: {reason} / {reason_code})")
    telegram_notify.notify_mrm(context["scenario"], reason, reason_code)
    print("[MRM] Gradual deceleration simulation...")
    time.sleep(duration)
    buzzer.off()
    print("[MRM] Vehicle stopped")
    return STATE_END
