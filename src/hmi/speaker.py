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

try:
    import sounddevice as sd  # type: ignore
    import soundfile as sf    # type: ignore
    _HAS_SD = True
except (ImportError, OSError):
    sd = None
    sf = None
    _HAS_SD = False


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
        data, sr = sf.read(path)
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
    if _HAS_SD and os.path.exists(path):
        info = sf.info(path)
        return info.frames / float(info.samplerate)
    return 0.0


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "./audio/const.wav"
    print(f"[TEST] Speaker playback test: {target}")
    play(target)
    print("[TEST] Done")
