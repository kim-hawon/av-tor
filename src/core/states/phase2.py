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
import numpy as np
import json
from core.readback import verify


def _pick_input_samplerate() -> int:
    """입력 장치(마이크)가 실제 지원하는 샘플레이트를 고른다.

    Vosk 는 16kHz 를 요구하지만 라파 USB 마이크는 16kHz 를 지원 안 하는 경우가
    많다(보통 48000/44100). 장치 기본 레이트를 우선 쓰고, 못 구하면 48000 으로.
    """
    try:
        return int(sd.query_devices(kind="input")["default_samplerate"])
    except Exception:
        return 48000


def _resample_to_16k(pcm_bytes, src_sr: int) -> bytes:
    """int16 mono PCM 을 src_sr → 16000Hz 로 선형보간 리샘플 (Vosk 입력용)."""
    if src_sr == 16000:
        return bytes(pcm_bytes)
    audio = np.frombuffer(bytes(pcm_bytes), dtype=np.int16)
    if audio.size == 0:
        return b""
    n_dst = int(round(audio.size * 16000 / src_sr))
    if n_dst <= 0:
        return b""
    x_src = np.arange(audio.size)
    x_dst = np.linspace(0, audio.size - 1, n_dst)
    return np.interp(x_dst, x_src, audio.astype(np.float64)).astype(np.int16).tobytes()


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

    # 마이크 네이티브 레이트로 열고, 읽은 청크를 16kHz 로 변환해 Vosk 에 먹인다.
    mic_sr = _pick_input_samplerate()
    if mic_sr != 16000:
        print(f"[VOICE] Mic sample rate {mic_sr}Hz → resampling to 16000Hz")
    with sd.RawInputStream(samplerate=mic_sr, blocksize=voice_cfg["blocksize"],
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
            if rec.AcceptWaveform(_resample_to_16k(data, mic_sr)):
                text = json.loads(rec.Result())["text"]
                print(text)
                if verify(scenario["answer"], text):
                    print("Sys: TOR success")
                    return True
            else:
                partial = json.loads(rec.PartialResult())["partial"]
                if partial:
                    print(f"  ({partial})", end='\r')