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

def run(scenario: dict, voice_cfg: dict, timeout: float = 12.0) -> bool:
    """시나리오 TTS 재생 후 운전자 리드백을 STT 로 검증.

    정답을 인식하면 True. 정답 인식 없이 timeout(초)이 지나면 False 를 반환해
    상위 상태기계가 MRM 으로 보내도록 한다(무한 대기 방지).
    """
    audio_data, sr = sf.read(scenario["audio"])

    rec = KaldiRecognizer(Model(voice_cfg["model_path"]), 16000)
    rec.SetWords(True)
    rec.SetGrammar(json.dumps(voice_cfg["vocab"], ensure_ascii=False))

    print(f"Sys: Say something... (listening up to {timeout:.0f}s)")

    with sd.RawInputStream(samplerate=16000, blocksize=voice_cfg["blocksize"],
                           dtype='int16', channels=1) as stream:
        sd.play(audio_data, sr)
        sd.wait()
        # TTS 안내가 끝난 시점부터 리드백 대기 한도를 잰다.
        deadline = time.monotonic() + timeout
        while True:
            if time.monotonic() >= deadline:
                # 마지막으로 누적된 부분 인식 결과도 한 번 확인
                final_text = json.loads(rec.FinalResult())["text"]
                if final_text and verify(scenario["answer"], final_text):
                    print(final_text)
                    print("Sys: TOR success")
                    return True
                print("\nSys: Voice readback timeout")
                return False

            data, _ = stream.read(1000)
            if rec.AcceptWaveform(bytes(data)):
                text = json.loads(rec.Result())["text"]
                print(text)
                if verify(scenario["answer"], text):
                    print("Sys: TOR success")
                    return True
            else:
                partial = json.loads(rec.PartialResult())["partial"]
                if partial:
                    print(f"  ({partial})", end='\r')