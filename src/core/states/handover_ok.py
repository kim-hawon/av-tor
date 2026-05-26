"""HANDOVER_OK 상태: 핸드오버 성공, 수동 운전으로 전환 완료."""


def enter(ctx):
    """핸드오버 성공 HMI 표시, 텔레메트리 기록."""
    # TODO: 구현
    pass


def handle(ctx):
    """매 틱 처리. 다음 State를 반환하거나 변화 없으면 None.

    예: 안정화 후 -> State.IDLE
    """
    # TODO: 구현
    return None


def exit(ctx):
    """상태 이탈 시 1회 실행."""
    # TODO: 구현
    pass
