"""TOR 카운트다운 타이머."""
import time


class Timer:
    """단순한 카운트다운 타이머."""

    def __init__(self, duration: float):
        """duration: 초 단위."""
        self.duration = duration
        self.start_time = None

    def start(self):
        self.start_time = time.time()

    def elapsed(self) -> float:
        """경과 시간 (초)."""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    def remaining(self) -> float:
        """남은 시간 (초). 0 이하면 종료."""
        return max(0.0, self.duration - self.elapsed())

    def is_done(self) -> bool:
        return self.remaining() <= 0

    def extend(self, extra: float):
        """시간 연장 (음성 유예용)."""
        self.duration += extra
