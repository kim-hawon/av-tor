"""HANDOVER_OK: 제어권 전환 성공.

출력: 빨강 LED OFF, 초록 LED ON, LCD "HANDOVER OK / MANUAL MODE".
(성공 효과음 wav 가 준비되면 speaker.play 로 추가 가능 - 띠로롱~)
"""
import time

from core.states import STATE_END
from hmi import led, lcd, screens


def run(context):
    duration = context["config"]["timing"]["end_screen_duration"]

    led.red_off()
    led.green_on()
    lcd.show(*screens.handover_ok())
    print(f"[HANDOVER_OK] Takeover successful! → MANUAL MODE (displaying for {duration}s)")

    time.sleep(duration)
    print("[HANDOVER_OK] Scenario complete")
    return STATE_END
