"""텔레그램 봇 - 메시지 받기 및 대시보드 조회 기능.

설계:
  - 텔레그램 봇이 사용자 메시지를 받는다 (long polling)
  - 특정 명령어(/dashboard, 대시보드 등)에 반응
  - 현재 통계를 텍스트 + 이미지로 텔레그램에 전송
  - 백그라운드 스레드에서 메시지 수신 대기

실행: python -m iot.telegram_bot
"""
import os
import re
import threading
import time
from datetime import datetime

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    requests = None
    _HAS_REQUESTS = False

_config = {
    "bot_token": "",
    "chat_id": "",
}

_running = False
_last_update_id = 0


def configure(bot_token: str, chat_id: str):
    """봇 토큰과 채팅 ID 설정."""
    _config["bot_token"] = bot_token
    _config["chat_id"] = str(chat_id)
    print(f"[TELEGRAM_BOT] Configured: token={'✓' if bot_token else '✗'}, "
          f"chat_id={chat_id}")


def _get_api_url(method: str) -> str:
    """Telegram API URL 생성."""
    return f"https://api.telegram.org/bot{_config['bot_token']}/{method}"


def _send_message(chat_id: str, text: str, parse_mode: str = "Markdown") -> bool:
    """메시지 전송."""
    if not _HAS_REQUESTS or not _config["bot_token"]:
        return False
    
    try:
        url = _get_api_url("sendMessage")
        payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
        resp = requests.post(url, json=payload, timeout=5)
        if resp.status_code != 200 and parse_mode:
            # Markdown 파싱 실패 가능 → 평문으로 재전송
            payload.pop("parse_mode", None)
            resp = requests.post(url, json=payload, timeout=5)
        return resp.status_code == 200
    except Exception as e:
        print(f"[TELEGRAM_BOT] Send error: {e}")
        return False


def _send_photo(chat_id: str, photo_path: str, caption: str = "") -> bool:
    """사진 전송."""
    if not _HAS_REQUESTS or not _config["bot_token"]:
        return False
    
    try:
        url = _get_api_url("sendPhoto")
        with open(photo_path, "rb") as f:
            files = {"photo": f}
            resp = requests.post(
                url,
                data={
                    "chat_id": chat_id,
                    "caption": caption,
                    "parse_mode": "Markdown",
                },
                files=files,
                timeout=10
            )
        return resp.status_code == 200
    except Exception as e:
        print(f"[TELEGRAM_BOT] Photo send error: {e}")
        return False


def _get_updates(timeout: int = 30) -> list:
    """새로운 메시지 조회 (long polling)."""
    global _last_update_id
    
    if not _HAS_REQUESTS or not _config["bot_token"]:
        return []
    
    try:
        url = _get_api_url("getUpdates")
        resp = requests.get(
            url,
            params={
                "offset": _last_update_id + 1,
                "timeout": timeout,
                "allowed_updates": ["message"],
            },
            timeout=timeout + 5
        )
        
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        if not data.get("ok"):
            return []
        
        updates = data.get("result", [])
        
        # 마지막 update_id 업데이트
        if updates:
            _last_update_id = max(u["update_id"] for u in updates)
        
        return updates
    except Exception as e:
        print(f"[TELEGRAM_BOT] Get updates error: {e}")
        return []


def _format_stats(stats: dict) -> str:
    """통계를 텍스트로 포맷."""
    lines = [
        "*📊 AV-TOR 대시보드 통계*",
        f"",
        f"*전체 시도:* {stats['total']} 건",
        f"*성공:* {stats['success']} 건 ✅",
        f"*실패:* {stats['fail']} 건 ❌",
        f"*성공률:* {stats['success_rate']:.1f}%",
        f"",
        f"*실패 원인:*"
    ]
    
    if stats["fail_reasons"]:
        for reason, count in sorted(stats["fail_reasons"].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  • {reason}: {count}건")
    else:
        lines.append("  (없음)")
    
    if stats["by_scenario"]:
        lines.append(f"")
        lines.append(f"*시나리오별 통계:*")
        for scenario, data in stats["by_scenario"].items():
            success_rate = (data["success"] / data["total"] * 100) if data["total"] > 0 else 0
            lines.append(f"  • {scenario}: {data['success']}/{data['total']} ({success_rate:.0f}%)")
    
    return "\n".join(lines)


def _handle_dashboard_request(chat_id: str, days: int = 7):
    """대시보드 조회 요청 처리."""
    try:
        from iot import telemetry
        
        # 통계 조회
        stats = telemetry.get_stats(days)
        
        # 포맷 및 전송
        text = _format_stats(stats)
        text += f"\n\n_최근 {days}일 통계_"
        
        success = _send_message(chat_id, text)
        
        if success:
            print(f"[TELEGRAM_BOT] Dashboard sent to {chat_id}")
        else:
            print(f"[TELEGRAM_BOT] Failed to send dashboard")
    except Exception as e:
        print(f"[TELEGRAM_BOT] Dashboard error: {e}")
        _send_message(chat_id, f"⚠️ 대시보드 조회 실패: {e}")


def _process_message(message: dict):
    """메시지 처리."""
    try:
        chat_id = str(message["chat"]["id"])
        text = message.get("text", "").lower().strip()

        print(f"[TELEGRAM_BOT] Message from {chat_id}: {text}")

        # 대시보드: /dashboard=1일, /dashboard3=3일, /dashboard7=7일, /dashboard30=30일
        #   (숫자를 안 붙이면 1일. '대시보드'/'dashboard' 도 1일.)
        if text.startswith("/dashboard") or text in ["대시보드", "dashboard"]:
            m = re.search(r"(\d+)", text)
            days = int(m.group(1)) if m else 1
            days = max(1, min(days, 30))  # 1~30일만 (보관 한도와 일치)
            _send_message(chat_id, f"📊 최근 {days}일 통계를 조회하는 중...")
            _handle_dashboard_request(chat_id, days=days)

        elif text in ["/help", "도움말", "help"]:
            help_text = (
                "*🤖 AV-TOR 봇 명령어*\n"
                "\n"
                "*대시보드 조회 (기간별):*\n"
                "  /dashboard - 최근 1일 통계\n"
                "  /dashboard3 - 최근 3일\n"
                "  /dashboard7 - 최근 7일\n"
                "  /dashboard30 - 최근 30일\n"
                "\n"
                "/help - 이 도움말"
            )
            _send_message(chat_id, help_text)
        
        elif text in ["/start", "시작"]:
            welcome = (
                "*🚗 AV-TOR 제어권 전환 시스템*\n"
                "\n"
                "안녕하세요! 🤖\n"
                "/help 를 입력하면 사용 가능한 명령어를 볼 수 있습니다."
            )
            _send_message(chat_id, welcome)
    
    except Exception as e:
        print(f"[TELEGRAM_BOT] Message processing error: {e}")


def start():
    """봇 시작 (백그라운드 스레드)."""
    global _running
    
    if not _config["bot_token"]:
        print("[TELEGRAM_BOT] Bot token not configured")
        return
    
    _running = True
    print("[TELEGRAM_BOT] Bot starting... (Ctrl+C to stop)")
    
    def _polling_loop():
        while _running:
            try:
                updates = _get_updates(timeout=30)
                for update in updates:
                    if "message" in update:
                        _process_message(update["message"])
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[TELEGRAM_BOT] Polling error: {e}")
                time.sleep(5)
    
    thread = threading.Thread(target=_polling_loop, daemon=True)
    thread.start()
    return thread


def stop():
    """봇 중지."""
    global _running
    _running = False
    print("[TELEGRAM_BOT] Bot stopped")


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    token = os.environ.get("TG_BOT_TOKEN")
    chat_id = os.environ.get("TG_CHAT_ID")
    
    if not token or not chat_id:
        print("[ERROR] TG_BOT_TOKEN and TG_CHAT_ID must be set")
        exit(1)
    
    configure(token, chat_id)
    
    try:
        start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping bot...")
        stop()
