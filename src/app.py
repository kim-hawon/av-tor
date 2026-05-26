"""av-tor 상태기계 진입점 (1주차 통합 데모).

실행: 프로젝트 루트(av-tor)에서  `python src/app.py`  또는  `scripts/run.sh`
하드웨어 없이 콘솔 로그로 IDLE→PHASE1→PHASE2→(HANDOVER_OK|MRM) 흐름을 검증.
음성인식은 config의 dummy.use_real_voice 로 더미/실제(STT) 전환.

참고: 음성 단독 테스트 진입점은 src/main.py 에 그대로 있음.
"""
from core.scenario import load_config
from core.state_machine import StateMachine


def print_banner(scenarios, use_real_voice):
    print("=" * 52)
    print("  AV-TOR: 자율주행 제어권 전환 시스템 (데모)")
    voice_mode = "실제 STT" if use_real_voice else "더미"
    print(f"  음성인식 모드: {voice_mode}")
    print("=" * 52)
    print("시나리오를 번호로 선택하세요:")
    for s in scenarios:
        print(f"  {s['id']}. {s['label']}")
    print("  q. 종료")
    print()


def main():
    config = load_config()
    scenarios = config["scenarios"]
    use_real_voice = config.get("dummy", {}).get("use_real_voice", False)

    sm = StateMachine(config)
    print_banner(scenarios, use_real_voice)

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

        try:
            trigger = int(user_input)
        except ValueError:
            print("[ERROR] 시나리오 번호(숫자) 또는 q 를 입력하세요.")
            continue

        matched = next((s for s in scenarios if s["id"] == trigger), None)
        if matched is None:
            print(f"[ERROR] 없는 시나리오 번호: {trigger}")
            continue

        sm.run(matched)
        print()  # 시나리오 종료 후 빈 줄


if __name__ == "__main__":
    main()
