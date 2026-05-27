"""I2C 캐릭터 LCD 드라이버.

20x4 (또는 16x2) I2C LCD 에 텍스트를 출력한다.
실제 하드웨어는 RPLCD(PCF8574 백팩)를 사용하고, 라이브러리/하드웨어가
없으면 콘솔에 LCD 모양 박스로 시뮬레이션한다.

레이아웃(WARN:400m 등 정확한 문구)은 hmi/screens.py 에 모아둔다.
여기서는 "줄을 그대로 띄운다"만 책임진다.

단독 테스트:
    python -m hmi.lcd          → 샘플 문구 표시
"""
try:
    from RPLCD.i2c import CharLCD  # type: ignore
    _HAS_RPLCD = True
except (ImportError, RuntimeError):
    CharLCD = None
    _HAS_RPLCD = False

from hmi import gpio_setup

_lcd = None          # 실제 CharLCD 객체 (real 모드)
_cols = 20
_rows = 4
_sim = True
_last_frame = None   # SIM 중복 출력 억제


def init(config=None):
    """LCD 초기화. SIM 모드면 콘솔 박스로 대체."""
    global _lcd, _cols, _rows, _sim, _last_frame
    _last_frame = None

    lcd_cfg = (config or {}).get("hmi", {}).get("lcd", {}) if config else {}
    _cols = lcd_cfg.get("cols", 20)
    _rows = lcd_cfg.get("rows", 4)

    # GPIO 가 SIM 이거나 RPLCD 가 없으면 LCD 도 SIM
    if gpio_setup.is_sim() or not _HAS_RPLCD:
        _sim = True
        print(f"[LCD] SIM 모드 ({_cols}x{_rows}) — 콘솔에 화면을 표시합니다")
        return

    try:
        _lcd = CharLCD(
            i2c_expander="PCF8574",
            address=lcd_cfg.get("i2c_address", 0x27),
            port=lcd_cfg.get("i2c_port", 1),
            cols=_cols, rows=_rows,
            auto_linebreaks=False,
        )
        _sim = False
        _lcd.clear()
        print(f"[LCD] 실제 I2C LCD 초기화 완료 ({_cols}x{_rows})")
    except Exception as e:  # noqa: BLE001 - 하드웨어 문제는 SIM 으로 폴백
        print(f"[LCD] 초기화 실패 → SIM 폴백: {e}")
        _sim = True


def show(*lines):
    """여러 줄을 LCD 에 출력. 각 줄은 cols 폭으로 잘리고/채워진다."""
    global _last_frame
    rows = [(_fit(lines[i]) if i < len(lines) else " " * _cols) for i in range(_rows)]

    if _sim:
        frame = tuple(rows[:max(1, len(lines))])
        if frame == _last_frame:
            return
        _last_frame = frame
        _print_box(rows[:max(1, len(lines))])
        return

    _lcd.clear()
    for r, text in enumerate(rows):
        if r >= _rows:
            break
        _lcd.cursor_pos = (r, 0)
        _lcd.write_string(text)


def clear():
    global _last_frame
    if _sim:
        if _last_frame is not None:
            print("[LCD][SIM] (clear)")
        _last_frame = None
        return
    if _lcd is not None:
        _lcd.clear()


def close():
    if not _sim and _lcd is not None:
        _lcd.close(clear=True)


def _fit(text: str) -> str:
    """cols 폭에 맞게 자르거나 공백으로 채운다."""
    text = str(text)
    return text[:_cols].ljust(_cols)


def _print_box(rows):
    top = "┌" + "─" * _cols + "┐"
    bottom = "└" + "─" * _cols + "┘"
    print("[LCD][SIM] " + top)
    for text in rows:
        print("           │" + text + "│")
    print("           " + bottom)


if __name__ == "__main__":
    gpio_setup.setup()
    init()
    print("[TEST] LCD 출력 테스트")
    show("WARN:400m  10s", "Eye:X Grip:X")
    import time
    time.sleep(1)
    show("HANDOVER OK", "MANUAL MODE")
    clear()
    close()
    print("[TEST] 종료")
