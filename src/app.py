"""av-tor 상태기계 진입점 (통합 데모).

실행: 프로젝트 루트(av-tor)에서  `python src/app.py`  또는  `scripts/run.sh`
라즈베리파이면 실제 HMI 하드웨어(LED/부저/진동/LCD/스피커)로,
그 외 환경이면 콘솔 시뮬레이션으로 IDLE→PHASE1→PHASE2→(HANDOVER_OK|MRM)
흐름을 검증한다.

입력 형식:  <키워드> [수치]
    공사 구간:  const 400      (400m)
    우천 구간:  rain 20        (20mm/h)
    안개 구간:  fog 30         (가시거리 30m)
    결빙 구간:  icy -5         (-5℃)
  수치를 생략하면 시나리오 기본값을 사용한다(예: `const`).
  과거 호환으로 시나리오 번호(1~4)도 받는다. 종료는 q.

음성인식은 config 의 dummy.use_real_voice 로 더미/실제(STT) 전환.
음성 단독 테스트 진입점은 src/main.py 에 그대로 있음.
"""
from core.scenario import load_config
from core.state_machine import StateMachine
from monitoring import grip
import hmi


def print_banner(scenarios, use_real_voice, sim):
    print("=" * 52)
    print("  AV-TOR: 자율주행 제어권 전환 시스템 (데모)")
    print(f"  음성인식 모드: {'실제 STT' if use_real_voice else '더미'}")
    print(f"  HMI 모드: {'콘솔 시뮬레이션(SIM)' if sim else '실제 하드웨어'}")
    print("=" * 52)
    print("시나리오를 입력하세요  <키워드> [수치] :")
    for s in scenarios:
        unit = s.get("param", {}).get("unit", "")
        default = s.get("param", {}).get("default", "")
        print(f"  {s['key']:<6} [{default}{unit}]  {s['label']}  (번호 {s['id']})")
    print("  예) const 400 / rain 20 / fog 30 / icy -5      종료: q")
    print()


def parse_trigger(user_input, scenarios):
    """입력 문자열 → (scenario, param 값). 못 찾으면 (None, None)."""
    parts = user_input.split()
    if not parts:
        return None, None
    token = parts[0].lower()

    # 1) 시나리오 번호(1~4) — 과거 호환
    if token.isdigit():
        sc = next((s for s in scenarios if s["id"] == int(token)), None)
        return sc, None  # 기본값 사용

    # 2) 키워드(const/rain/fog/icy)
    sc = next((s for s in scenarios if s.get("key") == token), None)
    if sc is None:
        return None, None

    param = None
    if len(parts) > 1:
        try:
            param = int(parts[1])   # 음수(-5)도 처리됨
        except ValueError:
            print(f"[ERROR] 수치는 정수여야 합니다: '{parts[1]}' → 기본값 사용")
    return sc, param


def main():
    config = load_config()
    scenarios = config["scenarios"]
    use_real_voice = config.get("dummy", {}).get("use_real_voice", False)

    # HMI/센서 초기화 (라파=실제, 그 외=SIM 자동 폴백)
    hmi.setup_all(config)
    grip.configure(config)

    sm = StateMachine(config)
    print_banner(scenarios, use_real_voice, hmi.gpio_setup.is_sim())

    try:
        while True:
            try:
                user_input = input("Trigger > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n프로그램 종료")
                break

            if user_input.lower() == "q":
                print("프로그램 종료")
                break
            if not user_input:
                continue

            scenario, param = parse_trigger(user_input, scenarios)
            if scenario is None:
                print(f"[ERROR] 알 수 없는 입력: '{user_input}' "
                      f"(예: const 400 / 1 / q)")
                continue

            sm.run(scenario, param)
            print()  # 시나리오 종료 후 빈 줄
    finally:
        hmi.cleanup_all()


if __name__ == "__main__":
    main()
