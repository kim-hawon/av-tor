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

from vosk import Model, KaldiRecognizer
import sounddevice as sd
import soundfile as sf
import json
from core.readback import verify

def run(scenario: dict, voice_cfg: dict) -> bool:
    audio_data, sr = sf.read(scenario["audio"])

    rec = KaldiRecognizer(Model(voice_cfg["model_path"]), 16000)
    rec.SetWords(True)
    rec.SetGrammar(json.dumps(voice_cfg["vocab"], ensure_ascii=False))

    print("Sys: Say something...")

    with sd.RawInputStream(samplerate=16000, blocksize=voice_cfg["blocksize"],
                           dtype='int16', channels=1) as stream:
        sd.play(audio_data, sr)
        sd.wait()
        while True:
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