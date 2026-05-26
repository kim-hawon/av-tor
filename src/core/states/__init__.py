"""상태(state) 패키지.

각 상태 모듈은 run(context) -> 다음 상태 문자열 인터페이스를 따른다.
(PHASE2만 예외: 팀원의 phase2.run(scenario, voice_cfg) -> bool 을
 state_machine이 어댑터로 감싸 호출한다.)
"""

# 상태 이름 상수 (state_machine과 각 상태가 공유)
STATE_IDLE = "IDLE"
STATE_PHASE1 = "PHASE1"
STATE_PHASE2 = "PHASE2"
STATE_HANDOVER_OK = "HANDOVER_OK"
STATE_MRM = "MRM"
STATE_END = "END"  # 종료 신호
