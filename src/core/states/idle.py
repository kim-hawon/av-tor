"""IDLE 상태: TOR 트리거 대기.

시나리오를 수신하면 출력을 깨끗이 초기화한 뒤 PHASE1 로 전이한다.
(직전 시나리오의 LED/LCD 잔상 제거 — 반복 실행 대비)
"""
from core.states import STATE_PHASE1
from hmi import led, buzzer, vibration, lcd, screens


def run(context):
    scenario = context["scenario"]

    # 클린 슬레이트
    led.all_off()
    buzzer.off()
    vibration.off()
    lcd.show(*screens.idle())

    print(f"[IDLE] Scenario received: {scenario['label']} (id={scenario['id']})")
    print("[IDLE] → Transitioning to PHASE1")
    return STATE_PHASE1
