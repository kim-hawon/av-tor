"""HMI(휴먼-머신 인터페이스) 패키지.

출력 하드웨어 묶음: led / buzzer / vibration / lcd / speaker (+ screens 레이아웃).
모든 모듈은 라즈베리파이에서 실제 하드웨어를, 그 외 환경에서 콘솔
시뮬레이션을 자동 사용한다(gpio_setup.is_sim() 기준).

app.py 시작 시 setup_all(config), 종료 시 cleanup_all() 한 번씩 호출.

참고: 서브모듈을 패키지 최상위에서 eager import 하지 않는다.
`python -m hmi.led` 같은 단독 실행 시 RuntimeWarning 을 피하기 위함.
필요한 곳에서 `from hmi import led` 처럼 직접 import 하면 된다.
"""

__all__ = ["setup_all", "cleanup_all"]


def setup_all(config):
    """GPIO/LCD 초기화 + 장치별 설정 적용. 시작 시 1회."""
    from hmi import gpio_setup, buzzer, vibration, lcd
    gpio_setup.setup(config)
    buzzer.configure(config)
    vibration.configure(config)
    lcd.init(config)


def cleanup_all():
    """모든 출력 OFF 후 GPIO/LCD 정리. 종료 시 1회."""
    from hmi import gpio_setup, led, buzzer, vibration, lcd
    try:
        led.all_off()
        buzzer.off()
        vibration.off()
        lcd.clear()
        lcd.close()
    finally:
        gpio_setup.cleanup()
