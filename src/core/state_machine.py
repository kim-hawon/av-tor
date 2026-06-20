"""상태 기계 디스패처.

5개 상태(IDLE, PHASE1, PHASE2, HANDOVER_OK, MRM)를 등록하고 전이를 처리한다.
PHASE2는 음성인식 모듈(core/states/phase2.py)을 어댑터로 감싸 호출한다.
"""
from core.states import (
    idle, phase1, handover_ok, mrm,
    STATE_IDLE, STATE_PHASE1, STATE_PHASE2,
    STATE_HANDOVER_OK, STATE_MRM, STATE_END,
)
from hmi import lcd, speaker, screens
from iot import telemetry
import uuid


class StateMachine:
    """상태 기계 메인 클래스."""

    def __init__(self, config, gaze_monitor=None, use_real_gaze=False):
        self.config = config
        # 프로그램 시작 시 1회 초기화된 시선 모니터를 모든 세션이 공유한다.
        self.gaze_monitor = gaze_monitor
        self.use_real_gaze = use_real_gaze
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

        우선순위:
          1) dummy.voice_ok = true → 항상 성공 처리 (음성 인식 미구현 흐름 통과용)
          2) dummy.use_real_voice = true → 실제 Vosk STT 호출 (마이크/모델/wav 필요)
          3) 그 외 → 실패 처리 (MRM 로 이동)
        phase2 모듈은 더미 모드에서 import되지 않도록 지연 import.
        """
        cfg = context["config"]
        dummy = cfg.get("dummy", {})
        scenario = context["scenario"]

        # 경고 OFF(PHASE1 에서 처리됨)
        # phase2.run() 내부에서 LCD 시간 실시간 업데이트하므로 여기서는 표시 안 함
        speak_sec = round(speaker.duration(scenario["audio"])) or 7
        action = scenario["lcd"]["phase2"]  # 예: "Lane 1 GO"
        print(f"[PHASE2] Action: {action} (TTS guidance {speak_sec}s)")

        voice_ok_flag = bool(dummy.get("voice_ok", True))
        if voice_ok_flag:
            speaker.play(scenario["audio"])              # TTS 안내음 재생
            ok = True
            print(f"[PHASE2] [DUMMY] voice_ok=true → voice recognition success "
                  f"(expected: '{scenario['answer']}')")
        elif dummy.get("use_real_voice", False):
            from core.states.phase2 import run as phase2_run  # 지연 import
            # PHASE1에서 남은 카운트다운 초를 이어받아 계속 카운트다운하고,
            # 그 시간이 끝나면 voice_extra(기본 3초)를 추가로 더 준다.
            # (carryover 정보가 없으면 voice_listen 기본값으로 폴백)
            voice_extra = float(cfg.get("timing", {}).get("voice_extra", 3))
            carried = context.get("phase1_remaining")
            if carried is not None:
                listen_timeout = float(carried) + voice_extra
                print(f"[PHASE2] Carrying over {carried}s from PHASE1 "
                      f"+ {voice_extra:.0f}s extra → listen {listen_timeout:.0f}s")
            else:
                listen_timeout = float(cfg.get("timing", {}).get("voice_listen", 12))
            print(f"[PHASE2] Starting real STT (expected: '{scenario['answer']}', "
                  f"timeout {listen_timeout:.0f}s)")
            ok = phase2_run(scenario, cfg["voice"], timeout=listen_timeout)
        else:
            speaker.play(scenario["audio"])
            ok = False
            print(f"[PHASE2] [DUMMY] voice_ok=false, use_real_voice=false → fail")

        if ok:
            print("[PHASE2] Voice verification passed → HANDOVER_OK")
            return STATE_HANDOVER_OK

        context["fail_reason"] = "Cognitive check failed"
        context["fail_code"] = "NoVoice"
        print("[PHASE2] Voice verification failed → MRM")
        return STATE_MRM

    def run(self, scenario, param=None):
        """하나의 시나리오를 처음부터 끝까지 실행.

        IDLE → PHASE1 → PHASE2 → (HANDOVER_OK | MRM) → END
        param: 입력 수치(예: const 400 의 400). None 이면 시나리오 기본값.
        """
        if param is None:
            param = scenario.get("param", {}).get("default", 0)

        # 이 TOR 세션의 고유 ID
        session_id = str(uuid.uuid4())[:8]

        context = {
            "scenario": scenario,
            "config": self.config,
            "param": param,       # LCD 경고문에 표시할 수치
            "session_id": session_id,
            "fail_reason": None,  # MRM 진입 시 사유(한글)
            "fail_code": None,    # MRM LCD 표시용 코드(NoGrip 등)
            "gaze_monitor": self.gaze_monitor,    # 시작 시 1회 초기화된 공유 모니터
            "use_real_gaze": self.use_real_gaze,  # 카메라 사용 가능 여부
        }

        # TOR 시작 기록
        telemetry.log_event(
            "tor_start",
            scenario,
            "started",
            session_id=session_id,
            param=param
        )
        print(f"[TOR] Session {session_id} started")

        current_state = STATE_IDLE
        while current_state != STATE_END:
            handler = self.handlers.get(current_state)
            if handler is None:
                print(f"[ERROR] Unknown state: {current_state}")
                break
            current_state = handler(context)

        # TOR 종료 기록
        final_status = "success" if context.get("fail_code") is None else "fail"
        telemetry.log_event(
            "tor_end",
            scenario,
            final_status,
            session_id=session_id,
            fail_code=context.get("fail_code"),
            fail_reason=context.get("fail_reason")
        )
        print(f"[TOR] Session {session_id} ended: {final_status}")
