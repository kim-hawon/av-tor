"""IDLE 상태: 자율주행 정상 주행, TOR 트리거 대기."""


def enter(ctx):
    """상태 진입 시 1회 실행 (예: HMI 평상시 표시)."""
    # TODO: 구현
    pass


def handle(ctx):
    """매 틱 처리. 다음 State를 반환하거나 변화 없으면 None.

    예: TOR 트리거 감지 시 -> State.PHASE1
    """
    # TODO: 구현
    return None


def exit(ctx):
    """상태 이탈 시 1회 실행."""
    # TODO: 구현
    pass
