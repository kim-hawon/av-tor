from vosk import Model, KaldiRecognizer
import sounddevice as sd
import json

class VoiceMonitor:
    def __init__(self, model_path: str, vocab: list):
        self.model = Model(model_path)
        self.rec = KaldiRecognizer(self.model, 16000)
        self.rec.SetWords(True)
        self.rec.SetGrammar(json.dumps(vocab, ensure_ascii=False))

    def listen_once(self, blocksize=4000) -> str:
        with sd.RawInputStream(samplerate=16000, blocksize=blocksize,
                               dtype='int16', channels=1) as stream:
            while True:
                data, _ = stream.read(1000)
                if self.rec.AcceptWaveform(bytes(data)):
                    return json.loads(self.rec.Result())["text"]
                else:
                    partial = json.loads(self.rec.PartialResult())["partial"]
                    if partial:
                        print(f"  ({partial})", end='\r')