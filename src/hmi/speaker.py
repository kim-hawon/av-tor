"""스피커 .wav 재생.

PHASE2 의 TTS 안내음, HANDOVER_OK/MRM 의 효과음을 재생한다.
sounddevice + soundfile 를 쓰되, 둘 다 없으면 시스템 aplay 로,
그것도 없으면 콘솔 시뮬레이션으로 폴백한다(맥/PC 개발 환경 대응).

단독 테스트:
    python -m hmi.speaker ./audio/const.wav
"""
import os
import shutil
import subprocess
import wave

import numpy as np  # type: ignore

try:
    import sounddevice as sd  # type: ignore
    _HAS_SD = True
except (ImportError, OSError):
    sd = None
    _HAS_SD = False


def configure_devices(config) -> None:
    """config.audio 의 입력/출력 장치를 sounddevice 기본 장치로 고정한다.

    라파에 USB 오디오가 여러 개(스피커/마이크 + HDMI + 3.5mm 잭)면 sounddevice
    기본 장치가 엉뚱하게 잡혀(예: TTS가 HDMI/잭으로) 소리가 안 나거나 마이크가
    안 잡힌다. 여기서 이름 부분일치(또는 정수 인덱스)로 장치를 골라 고정하면
    speaker.play / phase2 마이크 입력 / voice.record 가 전부 같은 장치를 쓴다.

    config 예:
        audio:
          input_device: "USB-Audio"   # 마이크
          output_device: "USB PnP"    # 스피커
    못 찾으면 경고만 하고 시스템 기본값을 유지한다.
    """
    if not _HAS_SD:
        return
    audio_cfg = (config or {}).get("audio", {}) or {}
    want_in = audio_cfg.get("input_device")
    want_out = audio_cfg.get("output_device")
    if want_in in (None, "") and want_out in (None, ""):
        return

    devices = sd.query_devices()

    def _resolve(want, kind):  # kind: "in" | "out"
        if want in (None, ""):
            return None
        if isinstance(want, int):
            return want
        ch_key = "max_input_channels" if kind == "in" else "max_output_channels"
        for i, d in enumerate(devices):
            if want.lower() in d["name"].lower() and d[ch_key] > 0:
                return i
        print(f"[AUDIO] ⚠ {kind} device '{want}' not found — keeping system default")
        return None

    cur = sd.default.device  # [input_index, output_index]
    in_idx = _resolve(want_in, "in")
    out_idx = _resolve(want_out, "out")
    sd.default.device = (
        in_idx if in_idx is not None else cur[0],
        out_idx if out_idx is not None else cur[1],
    )

    sel_in, sel_out = sd.default.device
    in_name = devices[sel_in]["name"] if isinstance(sel_in, int) and sel_in >= 0 else "system default"
    out_name = devices[sel_out]["name"] if isinstance(sel_out, int) and sel_out >= 0 else "system default"
    print(f"[AUDIO] Default devices → in: {in_name} | out: {out_name}")


def play(path: str, block: bool = True) -> float:
    """wav 파일을 재생하고 길이(초)를 반환. 파일이 없으면 0 을 반환.

    block=True 면 재생이 끝날 때까지 대기.
    SIM(라이브러리/도구 없음) 모드면 콘솔에만 표시하고 추정 길이 0 반환.
    """
    name = os.path.basename(path)
    if not os.path.exists(path):
        print(f"[SPK] ⚠ File not found: {path}")
        return 0.0

    if _HAS_SD:
        with wave.open(path, "rb") as wf:
            sr = wf.getframerate()
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            raw = wf.readframes(wf.getnframes())
        dtype = np.int16 if sampwidth == 2 else np.uint8
        data = np.frombuffer(raw, dtype=dtype)
        if n_channels > 1:
            data = data.reshape(-1, n_channels)
        duration = len(data) / float(sr)
        print(f"[SPK] ▶ Playing: {name} ({duration:.1f}s)")
        sd.play(data, sr)
        if block:
            sd.wait()
        return duration

    if shutil.which("aplay"):
        print(f"[SPK] ▶ aplay playing: {name}")
        run = subprocess.run if block else subprocess.Popen
        run(["aplay", "-q", path])
        return 0.0

    print(f"[SPK][SIM] 🔈 Playing: {name}")
    return 0.0


def duration(path: str) -> float:
    """wav 길이(초). 알 수 없으면 0."""
    if os.path.exists(path):
        with wave.open(path, "rb") as wf:
            return wf.getnframes() / float(wf.getframerate())
    return 0.0


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "./audio/const.wav"
    print(f"[TEST] Speaker playback test: {target}")
    play(target)
    print("[TEST] Done")
