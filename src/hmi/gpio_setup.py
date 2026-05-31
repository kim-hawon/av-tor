"""GPIO 핀 매핑 및 초기화 (RPi.GPIO 기반).

모든 hmi 모듈(led/buzzer/vibration)과 monitoring/grip 이 이 파일을 통해
핀을 읽고 쓴다. 하드웨어 분기(실제 GPIO vs 콘솔 시뮬레이션)를 여기에
한 번만 두어, 각 장치 모듈은 의미(빨강 LED ON 등)만 다루도록 한다.

동작 모드:
  - 라즈베리파이에서 RPi.GPIO 가 import 되면  → 실제 GPIO 제어
  - 그 외(맥/PC) 또는 config 의 hmi.force_sim=true → 콘솔 시뮬레이션(SIM)
시스템 시작 시 setup(config) 1회, 종료 시 cleanup() 1회 호출한다.
"""

# RPi.GPIO 는 라즈베리파이에서만 설치/동작한다. 없으면 SIM 모드.
try:
    import RPi.GPIO as GPIO  # type: ignore
    _HAS_GPIO = True
except (ImportError, RuntimeError):
    GPIO = None
    _HAS_GPIO = False

# config 가 없을 때(모듈 단독 테스트 등) 쓰는 기본 BCM 핀 번호
DEFAULT_PINS = {
    "led_red": 17,
    "led_green": 27,
    "buzzer": 22,
    "vibration": 23,
    "grip_touch": 24,
}
_OUTPUT_PINS = ("led_red", "led_green", "buzzer", "vibration")
_INPUT_PINS = ("grip_touch",)

# 모듈 전역 상태
_pins = dict(DEFAULT_PINS)
_sim = True            # 실제 setup() 전까지는 SIM 으로 간주
_ready = False
_grip_active_high = True


def is_sim() -> bool:
    """현재 SIM(콘솔 시뮬레이션) 모드면 True."""
    return _sim


def is_ready() -> bool:
    """setup() 이 호출되었으면 True."""
    return _ready


def pin(name: str) -> int:
    """이름(led_red 등)에 해당하는 BCM 핀 번호."""
    return _pins.get(name, DEFAULT_PINS.get(name, -1))


def setup(config=None):
    """GPIO 모드 설정 및 모든 핀 초기화. 시작 시 1회 호출.

    config["hmi"] 의 pins / force_sim / *_active_high 를 읽는다.
    config 가 None 이면 기본값으로 동작(모듈 단독 테스트용).
    """
    global _pins, _sim, _ready, _grip_active_high

    hmi_cfg = (config or {}).get("hmi", {}) if config else {}
    _pins = {**DEFAULT_PINS, **hmi_cfg.get("pins", {})}
    _grip_active_high = hmi_cfg.get("grip_active_high", True)
    force_sim = hmi_cfg.get("force_sim", False)

    _sim = force_sim or not _HAS_GPIO

    if _sim:
        reason = "force_sim=true" if force_sim else "No RPi.GPIO (not a Raspberry Pi)"
        print(f"[GPIO] SIM mode ({reason}) — displaying hardware state in console")
        _ready = True
        return

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for name in _OUTPUT_PINS:
        GPIO.setup(_pins[name], GPIO.OUT, initial=GPIO.LOW)
    pud = GPIO.PUD_DOWN if _grip_active_high else GPIO.PUD_UP
    for name in _INPUT_PINS:
        GPIO.setup(_pins[name], GPIO.IN, pull_up_down=pud)
    _ready = True
    print(f"[GPIO] Real GPIO initialized (BCM): {_pins}")


def write(name: str, high: bool):
    """출력 핀을 HIGH/LOW 로 설정. SIM 모드면 무동작.

    active_high 같은 의미 변환은 호출하는 장치 모듈이 처리한다(여기선 핀 레벨만).
    """
    if _sim or GPIO is None:
        return
    GPIO.output(_pins[name], GPIO.HIGH if high else GPIO.LOW)


def read(name: str) -> bool:
    """입력 핀이 HIGH 면 True. SIM 모드면 False(센서 미연결로 간주)."""
    if _sim or GPIO is None:
        return False
    return bool(GPIO.input(_pins[name]))


def cleanup():
    """GPIO 정리. 종료 시 1회 호출."""
    global _ready
    if not _sim and GPIO is not None:
        GPIO.cleanup()
    _ready = False
