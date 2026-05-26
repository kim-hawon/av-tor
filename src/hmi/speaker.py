import sounddevice as sd
import soundfile as sf

def play(path: str):
    data, sr = sf.read(path)
    sd.play(data, sr)
    sd.wait()