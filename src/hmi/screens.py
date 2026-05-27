"""LCD 화면 레이아웃 모음.

사용자가 확정한 문구/정렬을 한곳에 모아 lcd.show(*lines) 에 넘길
(line1, line2) 튜플을 만든다. 각 함수는 (1행, 2행) 문자열을 반환.

PHASE1 예시:
    "WARN:400m  10s"   /  "Eye:X Grip:X"
    "RAIN 20mmh 10s"   /  "Eye:X Grip:X"
    "FOG vis30m 10s"   /  "Eye:X Grip:X"
    "ICY -5C    10s"   /  "Eye:X Grip:X"
PHASE2:  "Lane 1 GO" / "Speak: 07s"   등
PHASE3:  "HANDOVER OK"/"MANUAL MODE",  "EMERGENCY!"/"Reason:NoGrip"
"""


def phase1(warn_prefix: str, remaining: int, eye_ok: bool, grip_ok: bool):
    """1행: 경고문 + 잔여초(우측), 2행: 시선/그립 상태(O/X).

    warn_prefix 는 이미 {v} 가 치환된 문자열(예: "WARN:400m").
    prefix 를 10칸으로 맞추고 잔여초를 우측 정렬해 사용자가 준 예시를 재현.
    """
    line1 = f"{warn_prefix:<10}{int(remaining):>3}s"
    eye = "O" if eye_ok else "X"
    grip = "O" if grip_ok else "X"
    line2 = f"Eye:{eye} Grip:{grip}"
    return line1, line2


def phase2(action: str, speak_remaining: int):
    """1행: 동작 지시(TTS 내용), 2행: 음성 안내 잔여초."""
    line1 = action
    line2 = f"Speak: {int(speak_remaining):02d}s"
    return line1, line2


def handover_ok():
    return "HANDOVER OK", "MANUAL MODE"


def mrm(reason_code: str):
    """비상 정차 화면. reason_code 예: NoGrip / NoEye / NoVoice / Timeout."""
    return "EMERGENCY!", f"Reason:{reason_code}"


def idle():
    return "AV-TOR READY", "Waiting TOR..."
