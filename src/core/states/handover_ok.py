"""HANDOVER_OK: 제어권 전환 성공.

출력: 빨강 LED OFF, 초록 LED ON, 성공 효과음(띠로롱~), LCD "HANDOVER OK / MANUAL MODE".
"""
import time

from core.states import STATE_END
from hmi import led, lcd, screens, speaker
from iot import telegram_notify


def run(context):
    duration = context["config"]["timing"]["end_screen_duration"]

    led.red_off()
    led.green_on()
    lcd.show(*screens.handover_ok())
    # 성공 효과음(띠로롱~). 파일 없거나 SIM 이면 speaker 가 조용히 폴백.
    speaker.play("./audio/success.wav")
    print(f"[HANDOVER_OK] Takeover successful! → MANUAL MODE (displaying for {duration}s)")

    telegram_notify.notify_handover_ok(context["scenario"])

    time.sleep(duration)
    print("[HANDOVER_OK] Scenario complete")
    return STATE_END
