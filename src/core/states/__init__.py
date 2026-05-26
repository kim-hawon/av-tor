"""상태(state)별 핸들러 모듈.

state_machine.py가 현재 State에 맞는 모듈의 handle()을 호출하고,
반환된 다음 State로 전이한다.

상태: idle, phase1, phase2, handover_ok, mrm (모두 동등 레벨)
"""
