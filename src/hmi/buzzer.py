"""능동 부저 제어.

잔여 시간에 따라 경고 강도를 높인다(여유→1회, 긴급→2회, 위급→연속).
능동 부저(HIGH 만 줘도 소리남)를 가정. 수동 부저(PWM 필요)면
on()/off() 사이를 PWM 으로 바꾸면 된다.

단독 테스트:
    python -m hmi.buzzer       → 여유→긴급→위급 패턴 순차 재생
"""
import time
from hmi import gpio_setup

# config 의 hmi.buzzer_active_high. setup_from_config()로 갱신, 기본 True.
_active_high = True


def configure(config):
    """config 에서 active_high 설정을 읽어온다(선택)."""
    global _active_high
    _active_high = config.get("hmi", {}).get("buzzer_active_high", True)


def on():
    gpio_setup.write("buzzer", _active_high)


def off():
    gpio_setup.write("buzzer", not _active_high)


def beep(on_time: float = 0.1, off_time: float = 0.1, count: int = 1):
    """count 회 짧게 운다. SIM 이면 콘솔에 표시."""
    if gpio_setup.is_sim():
        print(f"[BUZZER][SIM] 🔊 beep x{count} ({'♪ ' * count})".rstrip())
        return
    for _ in range(count):
        on()
        time.sleep(on_time)
        off()
        if off_time:
            time.sleep(off_time)


def urgency(remaining: float, urgent: float = 5, critical: float = 3):
    """잔여 시간(초)에 맞는 경고 부저를 1틱 분량만 운다.

    remaining > urgent     → 1회 (여유)
    urgent ≥ remaining > critical → 2회 (긴급)
    remaining ≤ critical   → 연속음 0.4s (위급)
    PHASE1 루프가 1초마다 호출하는 것을 가정(블로킹 0.5s 이내).
    """
    if remaining > urgent:
        beep(on_time=0.08, off_time=0.0, count=1)
    elif remaining > critical:
        beep(on_time=0.08, off_time=0.08, count=2)
    else:
        if gpio_setup.is_sim():
            print("[BUZZER][SIM] 🔊🔊 Critical! Continuous tone ━━━")
            return
        on()
        time.sleep(0.4)
        off()


if __name__ == "__main__":
    gpio_setup.setup()
    print("[TEST] Buzzer pattern test")
    try:
        for rem in (8, 4, 2):
            print(f"  remaining={rem}s")
            urgency(rem)
            time.sleep(1)
    finally:
        off()
        gpio_setup.cleanup()
        print("[TEST] Done")
