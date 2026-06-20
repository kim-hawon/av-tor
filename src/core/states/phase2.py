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


def run(scenario: dict, voice_cfg: dict, timeout: float = 12.0, extra: float = 3.0) -> bool:
    """시나리오 TTS 재생 후 운전자 리드백을 STT 로 검증.

    정답을 인식하면 True. 정답 인식 없이 timeout(초)이 지나면 False 를 반환해
    상위 상태기계가 MRM 으로 보내도록 한다(무한 대기 방지).

    timeout 종료 후 extra 초 만큼 추가 기회를 준다.
    실행 중 LCD에 남은 시간을 실시간으로 표시한다.
    """
    audio_data, sr = sf.read(scenario["audio"])

    # 마이크 네이티브 레이트로 캡처하고, 인식기도 "그 레이트로" 생성한다.
    # (예전엔 16kHz 인식기 + 수동 선형보간 리샘플 → 'lane' 같은 단어가 뭉개져
    #  'one' 만 잡혔다. Vosk 가 내부에서 고품질 리샘플하므로, 네이티브 레이트를
    #  그대로 먹이는 게 가장 정확하다.)
    mic_sr = _pick_input_samplerate()
    print(f"[VOICE] Mic sample rate {mic_sr}Hz (recognizer at native rate, Vosk가 내부 변환)")

    # 문법(SetGrammar)으로 인식 단어를 vocab 으로 제한한다. 작은 vosk-en 모델은
    # 자유 인식 시 "lane one" 을 "i'm live on a" 처럼 엉뚱하게 듣는다. 단어를
    # vocab(lane/one/...)으로 묶으면 그 단어만 후보라 정확히 잡힌다.
    # "lane" 과 "one" 이 별도 발화로 쪼개지는 문제는 아래 transcript 누적이 해결한다.
    rec = KaldiRecognizer(Model(voice_cfg["model_path"]), float(mic_sr))
    rec.SetWords(True)
    rec.SetGrammar(json.dumps(voice_cfg["vocab"], ensure_ascii=False))

    # TTS 안내음은 마이크를 열기 "전에" 끝까지 재생한다.
    # (예전엔 RawInputStream 을 연 채로 TTS 를 재생 → 입력/출력 장치 경합 +
    #  재생 동안 마이크 버퍼가 넘쳐, 정작 리드백 구간에서 인식이 안 됐다.)
    sd.play(audio_data, sr)
    sd.wait()

    print(f"Sys: Say something... (listening up to {timeout:.0f}s + {extra:.0f}s grace)")

    with sd.RawInputStream(samplerate=mic_sr, blocksize=voice_cfg["blocksize"],
                           dtype='int16', channels=1) as stream:
        # 초기 LCD 표시 (음성 안내 화면)
        action = scenario["lcd"]["phase2"]
        speak_sec = round(timeout)
        lcd.show(*screens.phase2(action, speak_sec, extra_remaining=0))

        # 마이크를 연 시점(=TTS 종료 직후)부터 리드백 대기 한도를 잰다.
        start = time.monotonic()
        deadline = start + timeout
        extra_deadline = deadline + extra
        last_lcd_update = start
        extra_notice_sent = False

        # 세션 동안 인식된 모든 최종 텍스트를 누적한다. "lane" 과 "one" 을 끊어
        # 말해 별도 발화로 잡혀도, 누적본("lane one")에서 키워드를 찾을 수 있다.
        transcript = ""

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
                final_text = json.loads(rec.FinalResult())["text"]
                transcript = f"{transcript} {final_text}".strip()
                if verify(scenario["answer"], transcript):
                    print(f"\nHeard: {transcript}")
                    print("Sys: TOR success")
                    return True
                print(f"\nHeard: '{transcript}' — Sys: Voice readback timeout")
                return False

            data, _ = stream.read(1000)
            if rec.AcceptWaveform(bytes(data)):
                # 한 발화 종료 → 최종 텍스트를 누적본에 더하고 키워드 검사
                text = json.loads(rec.Result())["text"]
                if text:
                    transcript = f"{transcript} {text}".strip()
                    print(f"Heard: {text}  (so far: {transcript})")
                if verify(scenario["answer"], transcript):
                    print("Sys: TOR success")
                    return True
            else:
                # 발화 중 부분결과 — 누적본 + 현재 부분에도 키워드가 보이면 즉시 성공
                partial = json.loads(rec.PartialResult())["partial"]
                if partial:
                    print(f"  ({partial})", end='\r')
                    if verify(scenario["answer"], f"{transcript} {partial}".strip()):
                        print(f"\nHeard: {transcript} {partial}".strip())
                        print("Sys: TOR success")
                        return True