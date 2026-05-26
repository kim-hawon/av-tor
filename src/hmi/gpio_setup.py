"""GPIO 핀 매핑 및 초기화.

하드웨어 전용이므로 utils가 아닌 hmi/ 아래에 둔다.
시스템 시작 시 1회 호출한다 (hmi/__init__.py 또는 main.py).
"""


def setup():
    """GPIO 모드 설정 및 모든 출력 핀 초기화.

    예: GPIO.setmode(GPIO.BCM); 각 핀 setup ...
    """
    # TODO: 구현
    pass
