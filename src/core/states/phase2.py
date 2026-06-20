# """PHASE2 상태: 음성 안내(TTS) + STT 리드백 확인.

# - 시나리오별 audio/tts_*.wav 재생 (speaker)
# - Vosk STT로 운전자 복창(readback) 인식 및 검증
# """


# def enter(ctx):
#     """시나리오에 맞는 TTS 재생, STT 리스닝 시작."""
#     # TODO: 구현
#     pass


# def handle(ctx):
#     """매 틱 처리. 다음 State를 반환하거나 변화 없으면 None.

#     예: 리드백 성공 -> State.HANDOVER_OK
#         리드백 실패 -> tts_retry 재생 후 재시도
#         타임아웃    -> State.MRM
#     """
#     # TODO: 구현
#     return None


# def exit(ctx):
#     """STT 리스닝 종료."""
#     # TODO: 구현
#     pass

import time
from vosk import Model, KaldiRecognizer
import sounddevice as sd
import soundfile as sf
import json
from core.readback import verify
from hmi import lcd, screens


def _pick_input_samplerate() -> int:
    """입력 장치(마이크)가 실제 지원하는 샘플레이트를 고른다.

    Vosk 는 16kHz 를 요구하지만 라파 USB 마이크는 16kHz 를 지원 안 하는 경우가
    많다(보통 48000/44100). 장치 기본 레이트를 우선 쓰고, 못 구하면 48000 으로.
    """
    try:
        return int(sd.query_devices(kind="input")["default_samplerate"])
    except Exception:
        return 48000


def _clean(text: str) -> str:
    """인식 텍스트에서 [unk](미등록어 토큰)를 빼고 공백을 정리한다."""
    return " ".join(t for t in text.split() if t != "[unk]")


def _combined_text(chunks: list[str], partial: str | None = None) -> str:
    parts = [chunk for chunk in chunks if chunk]
    if partial:
        parts.append(partial)
    return " ".join(parts).strip()


class STTSession:
    def __init__(self, model, rec, stream, mic_sr):
        self.model = model
        self.rec = rec
        self.stream = stream
        self.mic_sr = mic_sr

    def close(self):
        if self.stream is None:
            return
        try:
            self.stream.stop()
        except Exception:
            pass
        try:
            self.stream.close()
        except Exception:
            pass
        self.stream = None


def prepare(voice_cfg: dict, warmup_blocks: int = 3, warmup_sleep: float = 0.05) -> STTSession:
    """PHASE1에서 미리 Vosk 모델과 마이크 스트림을 준비한다."""
    mic_sr = _pick_input_samplerate()
    model = Model(voice_cfg["model_path"])
    rec = KaldiRecognizer(model, float(mic_sr))
    rec.SetWords(True)
    rec.SetGrammar(json.dumps(voice_cfg["vocab"], ensure_ascii=False))

    stream = sd.RawInputStream(
        samplerate=mic_sr,
        blocksize=voice_cfg["blocksize"],
        dtype="int16",
        channels=1,
    )
    stream.start()
    for _ in range(warmup_blocks):
        stream.read(1000)
    time.sleep(warmup_sleep)

    return STTSession(model, rec, stream, mic_sr)


def cleanup_session(session: STTSession | None):
    if session is None:
        return
    session.close()


def run(scenario: dict, voice_cfg: dict, stt_session: STTSession | None = None,
        timeout: float = 12.0, extra: float = 3.0) -> bool:
    """시나리오 TTS 재생 후 운전자 리드백을 STT 로 검증.

    정답을 인식하면 True. 정답 인식 없이 timeout(초)이 지나면 False 를 반환해
    상위 상태기계가 MRM 으로 보내도록 한다(무한 대기 방지).

    timeout 종료 후 extra 초 만큼 추가 기회를 준다.
    실행 중 LCD에 남은 시간을 실시간으로 표시한다.
    """
    audio_data, sr = sf.read(scenario["audio"])

    if stt_session is None:
        stt_session = prepare(voice_cfg)
        cleanup_after = True
    else:
        cleanup_after = True

    rec = stt_session.rec
    mic_sr = stt_session.mic_sr
    stream = stt_session.stream
    print(f"[VOICE] Mic sample rate {mic_sr}Hz (recognizer at native rate, Vosk가 내부 변환)")

    # TTS 안내음은 마이크를 열기 "전에" 끝까지 재생한다.
    # (예전엔 RawInputStream 을 연 채로 TTS 를 재생 → 입력/출력 장치 경합 +
    #  재생 동안 마이크 버퍼가 넘쳐, 정작 리드백 구간에서 인식이 안 됐다.)
    sd.play(audio_data, sr)
    sd.wait()

    print(f"Sys: Say something... (listening up to {timeout:.0f}s + {extra:.0f}s grace)")

    stream = stt_session.stream

    # 초기 LCD 표시 (음성 안내 화면)
    action = scenario["lcd"]["phase2"]
    speak_sec = round(timeout)
    lcd.show(*screens.phase2(action, speak_sec, extra_remaining=0))

    # 마이크를 연 시점(=TTS 종료 직후)부터 리드백 대기 한 시간을 잰다.
    start = time.monotonic()
    deadline = start + timeout
    extra_deadline = deadline + extra
    last_lcd_update = start
    extra_notice_sent = False

    # 세션 동안 인식된 모든 최종 텍스트를 누적한다. "lane" 과 "one" 을 끊어
    # 말해 별도 발화로 잡혀도, 누적본("lane one")에서 키워드를 찾을 수 있다.
    # chunks: list[str] = []
    # transcript = ""

    try:
        while True:
            now = time.monotonic()
            elapsed = now - start
            if now <= deadline:
                remaining = max(0, deadline - now)
                extra_remaining = 0
            else:
                remaining = max(0, extra_deadline - now)
                extra_remaining = int(remaining)
                if not extra_notice_sent:
                    print("\nSys: Voice timeout reached, granting extra 3 seconds")
                    extra_notice_sent = True

            # LCD 시간 업데이트 (0.5초 주기로, 깜빡임 방지)
            if now - last_lcd_update >= 0.5:
                speak_remaining = int(remaining)
                lcd.show(*screens.phase2(action, speak_remaining, extra_remaining=extra_remaining))
                last_lcd_update = now

            if now > extra_deadline:
                # 남은 인식 버퍼를 비우고 누적본에 키워드가 있는지 마지막 확인
                final_text = _clean(json.loads(rec.FinalResult())["text"])
                transcript = f"{transcript} {final_text}".strip()
                if verify(scenario["answer"], transcript):
                    print(f"\nHeard: {transcript}")
                    print("Sys: TOR success")
                    return True
                print(f"\nHeard: '{transcript}' — Sys: Voice readback timeout")
                return False

            data, _ = stream.read(1000)
            if rec.AcceptWaveform(bytes(data)):
                # 한 발화 종료 → final result는 무시하고 partial 기반으로만 처리
                text = _clean(json.loads(rec.Result())["text"])
                if text:
                    print(f"Heard: {text}  (ignored for chunk logic)")
                # partial-only 모드이므로 here we do not update chunks/transcript
            else:
                # 발화 중 부분결과 — partial 텍스트만 실시간 비교
                partial = _clean(json.loads(rec.PartialResult()).get("partial", ""))
                if partial:
                    print(f"  ({partial})", end='\r')
                    if verify(scenario["answer"], partial):
                        print(f"\nHeard: {partial}")
                        print("Sys: TOR success")
                        return True
    finally:
        if cleanup_after:
            cleanup_session(stt_session)
