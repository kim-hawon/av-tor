from core.scenario import load
from core.states.phase2 import run

def main():
    scenarios, voice_cfg = load()

    for s in scenarios:
        print(f"{s['id']}. {s['label']}")

    while True:
        try:
            trigger = int(input("Trigger > "))
            matched = next((s for s in scenarios if s["id"] == trigger), None)
            if matched:
                break
        except ValueError:
            pass

    run(matched, voice_cfg)

if __name__ == "__main__":
    main()