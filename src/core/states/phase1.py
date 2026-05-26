"""PHASE1 상태: TOR 경고 + 1·2단계 모니터링.

- HMI 경고(LED/부저/진동/LCD) 출력
- 시선(gaze)·그립(grip) 모니터링으로 운전자 준비 상태 확인
"""


def enter(ctx):
    """경고 HMI 활성화, 1단계 타이머 시작."""
    # TODO: 구현
    pass


def handle(ctx):
    """매 틱 처리. 다음 State를 반환하거나 변화 없으면 None.

    예: 모니터링 통과 -> State.PHASE2
        타임아웃     -> State.MRM
    """
    # TODO: 구현
    return None


def exit(ctx):
    """경고 HMI 정리, 타이머 해제."""
    # TODO: 구현
    pass
