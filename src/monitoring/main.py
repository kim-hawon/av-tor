import sounddevice as sd
import soundfile as sf
from vosk import Model, KaldiRecognizer
import json

answer_list = ["drive in lane 1", "slow down to 64", "slow down to 40", "slow down to 40"]
audio_map = {
    1: "./audio/const.wav",
    2: "./audio/rain.wav",
    3: "./audio/fog.wav",
    4: "./audio/ice.wav",
}

model = Model("./models/vosk-en")
rec = KaldiRecognizer(model, 16000)

vosk_voca = json.dumps(["drive", "in", "lane", "1", "slow", "down", "to", "64", "40", "[unk]"], ensure_ascii=False)
rec.SetWords(True)
rec.SetGrammar(vosk_voca)

while True:
    print("1. 공사 구간")
    print("2. 우천 구간")
    print("3. 안개 구간")
    print("4. 결빙 구간")

    try:
        trigger = int(input("Trigger > "))
        if trigger < 1 or trigger >= 5:
            continue
        break
    
    except ValueError:
        continue

audio_data, samplerate = sf.read(audio_map[trigger])

with sd.RawInputStream(samplerate=16000, blocksize=4000, dtype='int16',
                        channels=1) as stream:
    sd.play(audio_data, samplerate)
    print("Sys: Say something...")
    while True:
        data, _ = stream.read(1000)
        if rec.AcceptWaveform(bytes(data)):
            result = json.loads(rec.Result())["text"]  # ← Result
            print(result)
            if answer_list[trigger - 1] in result:
                print("Sys: TOR success")
                break
        else:
            partial = json.loads(rec.PartialResult())["partial"]
            if partial:
                print(f"  ({partial})", end='\r')
