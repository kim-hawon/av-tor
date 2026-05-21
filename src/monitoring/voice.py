import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json

answer_list = ["우회전 확인", "좌회전 확인", "확인"]
model = Model("vosk-model-small-ko-0.22")
rec = KaldiRecognizer(model, 16000)

vosk_voca = json.dumps(["우회전", "좌회전", "확인", "[Unk]"], ensure_ascii=False)
rec.SetWords(True)
rec.SetGrammar(vosk_voca)

while True:
    try:
        trigger = int(input("Sys: Trigger 입력 > "))
        if trigger < 0 or trigger >= len(answer_list):
            continue
        break
    
    except ValueError:
        continue
    
with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                        channels=1) as stream:
    print("Sys: 말해주세요.")
    while True:
        data, _ = stream.read(1000)
        if rec.AcceptWaveform(bytes(data)):
            partial = json.loads(rec.PartialResult())["partial"]
            print(partial)
            if answer_list[trigger] in partial:
                print("Sys: TOR 성공")
                break
