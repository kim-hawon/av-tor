"""상태 기계 디스패처.

5개 상태(IDLE, PHASE1, PHASE2, HANDOVER_OK, MRM)를 등록하고 전이를 처리한다.
PHASE2는 음성인식 모듈(core/states/phase2.py)을 어댑터로 감싸 호출한다.
"""
from core.states import (
    idle, phase1, handover_ok, mrm,
    STATE_IDLE, STATE_PHASE1, STATE_PHASE2,
    STATE_HANDOVER_OK, STATE_MRM, STATE_END,
)


class StateMachine:
    """상태 기계 메인 클래스."""

    def __init__(self, config):
        self.config = config
        # 상태 이름 → 핸들러 매핑. PHASE2는 팀원 STT 어댑터.
        self.handlers = {
            STATE_IDLE: idle.run,
            STATE_PHASE1: phase1.run,
            STATE_PHASE2: self._run_phase2,
            STATE_HANDOVER_OK: handover_ok.run,
            STATE_MRM: mrm.run,
        }

    def _run_phase2(self, context):
        """음성 인식 phase2.run(scenario, voice_cfg) -> bool 을 상태 전이로 매핑.

        dummy.use_real_voice 가 False면 마이크/모델 없이 voice_ok 값으로
        흐름만 통과시킨다(센서 개발/테스트용). True면 실제 Vosk STT를 호출
        phase2 모듈은 더미 모드에서 import되지 않도록 지연 import
        """
        cfg = context["config"]
        dummy = cfg.get("dummy", {})
        scenario = context["scenario"]

        print("[PHASE2] HMI 가정: 경고 OFF, LCD 동작 지시로 전환")

        if dummy.get("use_real_voice", False):
            from core.states.phase2 import run as phase2_run  # 지연 import
            print(f"[PHASE2] 실제 STT 시작 (정답: '{scenario['answer']}')")
            ok = phase2_run(scenario, cfg["voice"])
        else:
            ok = bool(dummy.get("voice_ok", True))
            result = "성공" if ok else "실패"
            print(f"[PHASE2] [더미] 음성인식 {result} (정답: '{scenario['answer']}')")

        if ok:
            print("[PHASE2] 복창 검증 통과 → HANDOVER_OK")
            return STATE_HANDOVER_OK

        context["fail_reason"] = "인지 확인 실패"
        print("[PHASE2] 복창 검증 실패 → MRM")
        return STATE_MRM

    def run(self, scenario):
        """하나의 시나리오를 처음부터 끝까지 실행.

        IDLE → PHASE1 → PHASE2 → (HANDOVER_OK | MRM) → END
        """
        context = {
            "scenario": scenario,
            "config": self.config,
            "fail_reason": None,  # MRM 진입 시 사유
        }

        current_state = STATE_IDLE
        while current_state != STATE_END:
            handler = self.handlers.get(current_state)
            if handler is None:
                print(f"[ERROR] 알 수 없는 상태: {current_state}")
                break
            current_state = handler(context)
