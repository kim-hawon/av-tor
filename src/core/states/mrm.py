"""MRM 상태: 최소위험기동(Minimal Risk Maneuver).

핸드오버 실패(타임아웃·리드백 실패 등) 시 진입.
감속·비상등·갓길 정차 등 차량을 안전 상태로 전이시킨다.

지금은 단일 파일. 내부가 0/1/2 단계 등으로 복잡해지면
states/mrm/__init__.py 패키지로 승격하는 것을 고려.
"""


def enter(ctx):
    """MRM 진입: 비상 HMI 표시, 감속 시퀀스 시작."""
    # TODO: 구현
    pass


def handle(ctx):
    """매 틱 처리. 다음 State를 반환하거나 변화 없으면 None.

    예: 정차 완료 -> State.IDLE (또는 종료 상태 유지)
    """
    # TODO: 구현
    return None


def exit(ctx):
    """상태 이탈 시 1회 실행."""
    # TODO: 구현
    pass
