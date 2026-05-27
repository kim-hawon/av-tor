# 하드웨어 (HMI / 센서)

라즈베리파이4 기준. 라파가 아니거나 라이브러리가 없으면 모든 모듈이
자동으로 **콘솔 시뮬레이션(SIM)** 으로 폴백한다(맥/PC 에서 로직 검증 가능).
라파에서도 배선 전 로직만 보고 싶으면 `config.yaml` 의 `hmi.force_sim: true`.

## 핀 맵 (BCM 번호, config.yaml `hmi.pins`)

| 이름           | BCM | 방향   | 부품                     | 비고 |
|----------------|-----|--------|--------------------------|------|
| `led_red`      | 17  | OUT    | 빨강 LED (+ 저항 330Ω)   | 경고/위험 |
| `led_green`    | 27  | OUT    | 초록 LED (+ 저항 330Ω)   | 정상/수동전환 |
| `buzzer`       | 22  | OUT    | 능동 부저                | active-high |
| `vibration`    | 23  | OUT    | 진동 모터 (드라이버 경유)| GPIO 직결 금지 |
| `grip_touch`   | 24  | IN     | 터치 센서                | 감지=HIGH (pull-down) |
| (I2C) SDA      | 2   | —      | 20x4 LCD (PCF8574)       | I2C 고정 핀 |
| (I2C) SCL      | 3   | —      | 20x4 LCD (PCF8574)       | I2C 고정 핀 |
| 마이크         | USB | —      | USB 마이크               | voice raw |
| 카메라         | USB/CSI | —  | 웹캠/파이카메라          | gaze 캡쳐 |
| 스피커         | 3.5mm/USB | — | 스피커                  | TTS/효과음 |

LCD I2C 주소는 보통 `0x27` 또는 `0x3F` (config `hmi.lcd.i2c_address`).
확인: `sudo i2cdetect -y 1`. 진동/모터는 반드시 트랜지스터+플라이백
다이오드(또는 모터 드라이버) 경유로 연결한다.

## 배선 주의
- LED: GPIO → 저항 → LED(+) → LED(-) → GND.
- 부저: 능동 부저는 HIGH 만으로 소리남. 수동 부저면 PWM 필요(buzzer.py 수정).
- 터치 센서: VCC/GND/SIG. SIG → BCM24. 센서 극성에 따라 config
  `hmi.grip_active_high` 조정(감지 시 LOW 인 모듈이면 false).
- 공통 GND 를 라파와 반드시 공유.

## 라이브러리 설치 (라파에서만)
```bash
sudo apt install -y python3-rpi.gpio i2c-tools
pip install RPLCD smbus2 sounddevice soundfile numpy opencv-python
# I2C 활성화: raspi-config → Interface Options → I2C → Enable
```

## 모듈 단독 검증 (av-tor/src 디렉터리에서 실행)

2주차(출력):
```bash
cd src
python -m hmi.led          # Day1 Red/Green 점멸
python -m hmi.buzzer       # Day2 부저 패턴(여유→긴급→위급)
python -m hmi.vibration    # Day3 진동 ON/OFF
python -m hmi.lcd          # Day4 LCD 문자 표시
python -m hmi.speaker ../audio/const.wav   # Day5 .wav 재생
```

3주차(입력):
```bash
cd src
python -m monitoring.grip  # Day1~2 터치 센서 GPIO 값 출력
python -m monitoring.voice # Day4~5 마이크 4초 녹음 → 재생
python -m monitoring.gaze  # Day6~7 카메라 프레임 1장 캡쳐(.jpg)
```

통합 데모(루트에서):
```bash
python src/app.py          # 또는 scripts/run.sh
# Trigger > const 400   →  빨강 LED 점멸 + 부저 + 진동 + LCD "WARN:400m"
```
