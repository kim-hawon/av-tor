import yaml

def load(config_path="./config/config.yaml"):
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg["scenarios"], cfg["voice"]