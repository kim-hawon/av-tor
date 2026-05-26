"""리드백(복창) 검증 로직.

monitoring/voice.py가 인식한 STT 결과(raw)를 받아,
현재 시나리오의 정답 토큰과 일치하는지 판정한다.
(monitoring = raw 입력, core = 판정/상태기계 로직)
"""


def verify(recognized_text, scenario):
    """인식 텍스트가 시나리오 정답 토큰과 일치하면 True.

    예: scenario.answer == "우회전 확인" 이고
        recognized_text 안에 해당 토큰이 포함되면 성공.
    """
    # TODO: 구현
    raise NotImplementedError
