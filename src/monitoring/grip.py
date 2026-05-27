"""핸들 파지(그립) 터치 센서 입력.

가장 먼저 PHASE1 에 통합되는 입력. 임계값(디지털 HIGH/LOW)만 정하면
바로 "핸들 잡음/안 잡음" 판정이 된다.

동작 모드:
  - 실제 라파: GPIO 터치 핀을 읽어 판정 (grip_active_high 로 극성 조정)
  - SIM(맥/PC): config 의 dummy.grip_ok_after 초 후 자동으로 "잡음" 처리
    → PHASE1 흐름을 하드웨어 없이도 끝까지 검증 가능

단독 테스트(라파에서 센서 배선 후):
    python -m monitoring.grip      → 터치 센서 GPIO 값을 0.5s 마다 출력
"""
from hmi import gpio_setup

_active_high = True
_grip_ok_after = 4  # SIM 폴백용 (config.dummy.grip_ok_after)


def configure(config):
    """config 에서 극성/더미 임계 시간을 읽어온다."""
    global _active_high, _grip_ok_after
    _active_high = config.get("hmi", {}).get("grip_active_high", True)
    _grip_ok_after = config.get("dummy", {}).get("grip_ok_after", 4)


def read_raw() -> bool:
    """센서 핀의 원시 값(HIGH=True). SIM 모드면 항상 False."""
    return gpio_setup.read("grip_touch")


def is_gripped(elapsed: float = 0.0) -> bool:
    """핸들을 잡고 있으면 True.

    실제 모드: 핀 값을 active_high 극성에 맞춰 해석.
    SIM 모드: elapsed(경과초) 가 grip_ok_after 이상이면 잡은 것으로 간주.
    """
    if gpio_setup.is_sim():
        return elapsed >= _grip_ok_after
    pressed = read_raw()
    return pressed if _active_high else not pressed


if __name__ == "__main__":
    import time
    gpio_setup.setup()
    print("[TEST] 그립 터치 센서 값 출력 (Ctrl+C 로 종료)")
    if gpio_setup.is_sim():
        print("  (SIM 모드 — 실제 센서가 없어 항상 0 으로 표시됩니다)")
    try:
        while True:
            raw = read_raw()
            print(f"  grip_touch raw={int(raw)}  gripped={is_gripped()}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        gpio_setup.cleanup()
        print("\n[TEST] 종료")
