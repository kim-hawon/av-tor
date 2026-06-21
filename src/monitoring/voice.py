"""마이크 음성 입력.

이 단계 목표는 "마이크 신호가 들어온다"까지. 판정/STT 는 다음 단계.
마이크로 .wav 를 녹음하고 재생해 입출력 경로를 검증한다.

단독 테스트(라파에서 마이크 연결 후):
    python -m monitoring.voice     → 4초 녹음 → captures/voice_*.wav 저장 → 재생
"""
import os
import time

try:
    import sounddevice as sd  # type: ignore
    import numpy as np       # type: ignore
    import wave
    _HAS_SD = True
except (ImportError, OSError):
    sd = None
    np = None
    wave = None
    _HAS_SD = False


def record(out_path: str, seconds: float = 4.0, samplerate: int = 16000) -> str:
    """마이크에서 seconds 초 녹음해 out_path(.wav) 로 저장하고 경로 반환.

    sounddevice 가 없으면(맥/PC 라이브러리 미설치) 콘솔 시뮬레이션만 한다.
    """
    if not _HAS_SD:
        print(f"[VOICE][SIM] 🎤 {seconds:.0f}s recording (simulated) → {out_path}")
        return out_path

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    print(f"[VOICE] 🎤 Recording started ({seconds:.0f}s)...")
    frames = int(seconds * samplerate)
    audio = sd.rec(frames, samplerate=samplerate, channels=1, dtype="int16")
    sd.wait()
    # write WAV using wave module
    try:
        with wave.open(out_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # int16
            wf.setframerate(samplerate)
            wf.writeframes(audio.tobytes())
    except Exception:
        # fallback: write raw bytes
        with open(out_path, "wb") as fh:
            fh.write(audio.tobytes())
    print(f"[VOICE] Saved: {out_path}")
    return out_path


if __name__ == "__main__":
    out_dir = "./data/captures"
    out = os.path.join(out_dir, f"voice_{int(time.time())}.wav")
    print("[TEST] Microphone raw recording test")
    record(out, seconds=4.0)
    # 녹음 검증: 재생
    from hmi import speaker
    speaker.play(out)
    print("[TEST] Done")


# ─────────────────────────────────────────────────────────────
# 참고: 다음 단계(STT) 용 Vosk 리스너. 지금은 사용하지 않음.
# ─────────────────────────────────────────────────────────────
# from vosk import Model, KaldiRecognizer
# import json
#
# class VoiceMonitor:
#     def __init__(self, model_path: str, vocab: list):
#         self.model = Model(model_path)
#         self.rec = KaldiRecognizer(self.model, 16000)
#         self.rec.SetWords(True)
#         self.rec.SetGrammar(json.dumps(vocab, ensure_ascii=False))
#
#     def listen_once(self, blocksize=4000) -> str:
#         with sd.RawInputStream(samplerate=16000, blocksize=blocksize,
#                                dtype='int16', channels=1) as stream:
#             while True:
#                 data, _ = stream.read(1000)
#                 if self.rec.AcceptWaveform(bytes(data)):
#                     return json.loads(self.rec.Result())["text"]
#                 else:
#                     partial = json.loads(self.rec.PartialResult())["partial"]
#                     if partial:
#                         print(f"  ({partial})", end='\r')
