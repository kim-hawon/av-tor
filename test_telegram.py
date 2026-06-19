#!/usr/bin/env python3
"""텔레그램 설정 및 연결 테스트."""
import os
import sys

# .env 파일 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

print("=" * 60)
print("  AV-TOR TELEGRAM DIAGNOSTIC TEST")
print("=" * 60)

# 1. requests 라이브러리 확인
print("\n[1] Checking requests library...")
try:
    import requests
    print("    ✓ requests installed")
except ImportError:
    print("    ✗ requests NOT installed")
    print("    → Run: pip install requests")
    sys.exit(1)

# 2. 환경변수 확인
print("\n[2] Checking environment variables...")
tg_token = os.environ.get("TG_BOT_TOKEN", "").strip()
tg_chat = os.environ.get("TG_CHAT_ID", "").strip()

if tg_token:
    print(f"    ✓ TG_BOT_TOKEN found (length: {len(tg_token)})")
else:
    print("    ✗ TG_BOT_TOKEN not set")

if tg_chat:
    print(f"    ✓ TG_CHAT_ID found: {tg_chat}")
else:
    print("    ✗ TG_CHAT_ID not set")

# 3. 설정 파일 확인
print("\n[3] Checking config.yaml...")
try:
    import yaml
    with open("./config/config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    tg_cfg = config.get("telegram", {})
    print(f"    enabled: {tg_cfg.get('enabled', 'N/A')}")
    print(f"    bot_token (yaml): {'✓' if tg_cfg.get('bot_token') else '✗ (empty)'}")
    print(f"    chat_id (yaml): {tg_cfg.get('chat_id', 'N/A')}")
except Exception as e:
    print(f"    ✗ Error reading config: {e}")
    sys.exit(1)

# 4. 최종 검증
print("\n[4] Final check...")
final_token = tg_token or tg_cfg.get("bot_token", "").strip()
final_chat = tg_chat or str(tg_cfg.get("chat_id", "")).strip()

if not final_token:
    print("    ✗ NO bot_token available (env or config)")
elif not final_chat:
    print("    ✗ NO chat_id available (env or config)")
else:
    print("    ✓ All settings found!")
    
    # 5. API 테스트
    print("\n[5] Testing Telegram API...")
    url = f"https://api.telegram.org/bot{final_token}/getMe"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("ok"):
                bot_name = data.get("result", {}).get("username", "?")
                print(f"    ✓ Token valid! Bot: @{bot_name}")
                
                # 메시지 전송 테스트
                print("\n[6] Sending test message...")
                msg_url = f"https://api.telegram.org/bot{final_token}/sendMessage"
                payload = {
                    "chat_id": final_chat,
                    "text": "*[AV-TOR] Telegram Connection Test*\n✓ Configuration successful",
                    "parse_mode": "Markdown"
                }
                msg_resp = requests.post(msg_url, json=payload, timeout=5)
                if msg_resp.status_code == 200:
                    print("    ✓ Message sent successfully!")
                else:
                    print(f"    ✗ Send failed: {msg_resp.status_code}")
                    print(f"    {msg_resp.text}")
            else:
                print(f"    ✗ Token invalid: {data}")
        else:
            print(f"    ✗ API error: {resp.status_code}")
    except Exception as e:
        print(f"    ✗ Connection error: {e}")

print("\n" + "=" * 60)
print("  TEST COMPLETE")
print("=" * 60)
