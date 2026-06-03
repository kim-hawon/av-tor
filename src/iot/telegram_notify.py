"""텔레그램 알림 모듈.

제어권 전환 성공(HANDOVER_OK) / 실패(MRM) 시점에 호출되어
텔레그램 봇 API(sendMessage)로 메시지를 보낸다.

설계 원칙:
  - 네트워크 지연/실패가 차량 로직(상태기계)을 막지 않도록 별도 스레드로 전송.
  - 토큰/chat_id 는 환경변수(TG_BOT_TOKEN, TG_CHAT_ID) 우선, 없으면 config.yaml.
  - enabled=false 거나 token/chat_id 비어 있으면 조용히 no-op.
"""
import os
import threading
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None

_API_URL = "https://api.telegram.org/bot{token}/sendMessage"

_config = {
    "enabled": False,
    "bot_token": "",
    "chat_id": "",
    "timeout": 3,
}


def configure(cfg):
    """app 시작 시 1회 호출. config['telegram'] 섹션을 받아 모듈 상태에 저장."""
    tg = (cfg or {}).get("telegram", {}) or {}
    _config["enabled"] = bool(tg.get("enabled", False))
    _config["bot_token"] = os.environ.get("TG_BOT_TOKEN") or tg.get("bot_token", "")
    _config["chat_id"] = os.environ.get("TG_CHAT_ID") or str(tg.get("chat_id", ""))
    _config["timeout"] = float(tg.get("timeout", 3))

    if _config["enabled"] and (not _config["bot_token"] or not _config["chat_id"]):
        print("[TELEGRAM] enabled=true but bot_token/chat_id missing → notifications off")
        _config["enabled"] = False


def _send_async(text):
    if not _config["enabled"] or requests is None:
        return

    def _worker():
        url = _API_URL.format(token=_config["bot_token"])
        payload = {
            "chat_id": _config["chat_id"],
            "text": text,
            "parse_mode": "Markdown",
        }
        try:
            requests.post(url, json=payload, timeout=_config["timeout"])
        except Exception as e:
            print(f"[TELEGRAM] send failed: {e}")

    threading.Thread(target=_worker, daemon=True).start()


def _ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def notify_handover_ok(scenario):
    """제어권 전환 성공 알림."""
    label = scenario.get("label", "?")
    text = (
        "*[AV-TOR] 제어권 전환 성공*\n"
        f"- 시나리오: {label}\n"
        f"- 시각: {_ts()}\n"
        "- 상태: MANUAL MODE"
    )
    _send_async(text)


def notify_mrm(scenario, reason, reason_code):
    """제어권 전환 실패 → MRM 진입 알림."""
    label = scenario.get("label", "?")
    text = (
        "*[AV-TOR] 제어권 전환 실패 (MRM)*\n"
        f"- 시나리오: {label}\n"
        f"- 사유: {reason} ({reason_code})\n"
        f"- 시각: {_ts()}\n"
        "- 상태: EMERGENCY STOP"
    )
    _send_async(text)
