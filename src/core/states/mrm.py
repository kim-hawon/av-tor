"""MRM: 최소위험기동 (제어권 이양 실패 시).

핸드오버 실패(PHASE1 타임아웃 / PHASE2 인지 확인 실패) 시 진입.
지금은 단일 파일. 내부가 0/1/2 단계 등으로 복잡해지면
states/mrm/__init__.py 패키지로 승격하는 것을 고려.
"""
import time
from core.states import STATE_END


def run(context):
    config = context["config"]
    duration = config["timing"]["end_screen_duration"]
    reason = context.get("fail_reason", "알 수 없음")

    print("[MRM] HMI 가정: Red LED 지속, 스피커 '삐빅', LCD 'EMERGENCY STOP!'")
    print(f"[MRM] 비상 정차 (사유: {reason})")
    print("[MRM] 단계적 감속 시뮬레이션...")
    time.sleep(duration)
    print("[MRM] 정차 완료")
    return STATE_END
