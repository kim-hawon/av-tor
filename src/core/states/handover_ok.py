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
    print(f"[HANDOVER_OK] 제어권 전환 성공! → MANUAL MODE ({duration}초 표시)")

    time.sleep(duration)
    print("[HANDOVER_OK] 시나리오 종료")
    return STATE_END
