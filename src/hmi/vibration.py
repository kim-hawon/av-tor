"""진동 모터 제어.

PHASE1 경고 동안 ON, 그 외 OFF. 모터는 트랜지스터/모터드라이버를 경유해
GPIO 로 스위칭하는 것을 가정(GPIO 직결 금지).

단독 테스트:
    python -m hmi.vibration    → 0.5s ON / 0.5s OFF 반복
"""
import time
from hmi import gpio_setup

_active_high = True
_on = False


def configure(config):
    global _active_high
    _active_high = config.get("hmi", {}).get("vibration_active_high", True)


def on():
    global _on
    if _on:
        return
    _on = True
    gpio_setup.write("vibration", _active_high)
    if gpio_setup.is_sim():
        print("[VIB][SIM] 📳 진동 ON")


def off():
    global _on
    if not _on:
        return
    _on = False
    gpio_setup.write("vibration", not _active_high)
    if gpio_setup.is_sim():
        print("[VIB][SIM] 📴 진동 OFF")


def pulse(duration: float = 0.5):
    """duration 초 동안 진동 후 끈다."""
    on()
    time.sleep(duration)
    off()


if __name__ == "__main__":
    gpio_setup.setup()
    print("[TEST] 진동 모터 ON/OFF 테스트 (Ctrl+C 로 종료)")
    try:
        while True:
            on(); time.sleep(0.5)
            off(); time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        off()
        gpio_setup.cleanup()
        print("\n[TEST] 종료")
