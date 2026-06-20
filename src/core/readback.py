"""리드백(복창) 검증 로직.

monitoring/voice.py가 인식한 STT 결과(raw)를 받아,
현재 시나리오의 정답 토큰과 일치하는지 판정한다.
(monitoring = raw 입력, core = 판정/상태기계 로직)
"""


def verify(answer: str, text: str) -> bool:
    """인식 텍스트가 시나리오 정답 토큰과 일치하면 True.

    예: scenario.answer == "lane one" 이고 인식 결과가 "lane one check" 처럼
        정답 토큰을 포함하면 성공. 대소문자/앞뒤 공백 차이는 무시한다.
    """
    if not answer or not text:
        return False
    norm_answer = " ".join(answer.lower().split())
    norm_text = " ".join(text.lower().split())
    return norm_answer in norm_text

