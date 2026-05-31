"""Red/Green LED 제어.

빨강 = 경고/위험(PHASE1, MRM), 초록 = 정상/수동전환 성공(HANDOVER_OK).
LED 는 active-high 로 가정(핀 HIGH = 점등).

단독 테스트:  (av-tor/src 에서)
    python -m hmi.led          → 빨강/초록 교대 점멸
"""
from hmi import gpio_setup

# 현재 점등 상태(중복 로그 억제 및 blink 토글에 사용)
_state = {"led_red": False, "led_green": False}


def _set(name: str, on: bool):
    if _state[name] == on:
        return
    _state[name] = on
    gpio_setup.write(name, on)  # LED active-high
    if gpio_setup.is_sim():
        icon = {"led_red": "🔴", "led_green": "🟢"}[name]
        color = "RED" if name == "led_red" else "GREEN"
        print(f"[LED][SIM] {icon} {color} {'ON' if on else 'OFF'}")


def red_on():
    _set("led_red", True)


def red_off():
    _set("led_red", False)


def green_on():
    _set("led_green", True)


def green_off():
    _set("led_green", False)


def red_toggle():
    """현재 상태를 반전(PHASE1 의 1초 간격 깜빡임용)."""
    _set("led_red", not _state["led_red"])


def all_off():
    red_off()
    green_off()


def red_blink(times: int = 3, interval: float = 0.3):
    """빨강 LED 를 times 회 깜빡임(간단한 동기식)."""
    import time
    for _ in range(times):
        red_on()
        time.sleep(interval)
        red_off()
        time.sleep(interval)


if __name__ == "__main__":
    import time
    gpio_setup.setup()  # config 없이 기본 핀으로
    print("[TEST] Red/Green LED blink test (Press Ctrl+C to exit)")
    try:
        while True:
            red_on(); green_off(); time.sleep(0.5)
            red_off(); green_on(); time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        all_off()
        gpio_setup.cleanup()
        print("\n[TEST] Done")
