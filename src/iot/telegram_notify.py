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
    _HAS_REQUESTS = True
except ImportError:
    requests = None
    _HAS_REQUESTS = False

# 모듈 로드 시 경고
if not _HAS_REQUESTS:
    print("[TELEGRAM] Warning: requests library not installed.")
    print("           Install with: pip install requests")

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
    _config["chat_id"] = os.environ.get("TG_CHAT_ID") or str(tg.get("chat_id", "")).strip()
    _config["timeout"] = float(tg.get("timeout", 3))

    # 설정 상태 출력
    print(f"[TELEGRAM] enabled={_config['enabled']}, requests={_HAS_REQUESTS}")
    if _config["enabled"]:
        if not _HAS_REQUESTS:
            print("[TELEGRAM] ERROR: requests library not installed → notifications disabled")
            _config["enabled"] = False
        elif not _config["bot_token"]:
            print("[TELEGRAM] ERROR: bot_token not set (env TG_BOT_TOKEN or config.yaml) → disabled")
            _config["enabled"] = False
        elif not _config["chat_id"]:
            print("[TELEGRAM] ERROR: chat_id not set (env TG_CHAT_ID or config.yaml) → disabled")
            _config["enabled"] = False
        else:
            print(f"[TELEGRAM] Configured: chat_id={_config['chat_id'][:10]}... (masked token)")
            print("[TELEGRAM] Ready to send notifications")


def _send_async(text):
    if not _config["enabled"]:
        return
    
    if not _HAS_REQUESTS:
        print("[TELEGRAM] Cannot send: requests not installed")
        return

    def _worker():
        url = _API_URL.format(token=_config["bot_token"])
        payload = {
            "chat_id": _config["chat_id"],
            "text": text,
            "parse_mode": "Markdown",
        }
        try:
            resp = requests.post(url, json=payload, timeout=_config["timeout"])
            if resp.status_code == 200:
                print("[TELEGRAM] Message sent successfully")
            else:
                print(f"[TELEGRAM] API error: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"[TELEGRAM] Send failed: {type(e).__name__}: {e}")

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


def test_send():
    """테스트 메시지 전송 (디버깅용)."""
    if not _config["enabled"]:
        print("[TELEGRAM] Cannot test: notifications disabled")
        print(f"  enabled={_config['enabled']}, has_requests={_HAS_REQUESTS}")
        print(f"  token={'✓' if _config['bot_token'] else '✗'}, chat_id={'✓' if _config['chat_id'] else '✗'}")
        return
    
    print("[TELEGRAM] Sending test message...")
    text = f"*[AV-TOR] Test Message*\n- Time: {_ts()}\n- Status: Connection OK"
    _send_async(text)
    print("[TELEGRAM] Test message queued (check in 1-2 seconds)")
