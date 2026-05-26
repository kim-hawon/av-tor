"""IDLE 상태: TOR 트리거 대기.

선택된 시나리오를 수신하면 곧바로 PHASE1로 전이한다.
"""
from core.states import STATE_PHASE1


def run(context):
    scenario = context["scenario"]
    print(f"[IDLE] 시나리오 수신: {scenario['label']} (id={scenario['id']})")
    print("[IDLE] → PHASE1 전이")
    return STATE_PHASE1
