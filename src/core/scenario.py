"""시나리오 설정 로드.

config.yaml의 scenarios/voice 섹션을 읽는다.
scenario는 dict 형태({id, label, audio, answer})로 다룬다
(팀원의 phase2.py가 scenario["audio"], scenario["answer"]를 사용).
"""
import yaml


def load_config(config_path="./config/config.yaml"):
    """config.yaml 전체를 dict로 로드."""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load(config_path="./config/config.yaml"):
    """(scenarios, voice) 반환 — 음성 모듈 호환용."""
    cfg = load_config(config_path)
    return cfg["scenarios"], cfg["voice"]
