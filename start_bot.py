#!/usr/bin/env python3
"""AV-TOR 텔레그램 봇 실행 스크립트.

텔레그램에서 대시보드 조회 등의 명령어를 처리합니다.

실행: python start_bot.py
"""
import os
import sys
import time

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from iot import telegram_bot, telemetry

# 텔레메트리 초기화
telemetry.init()

# 봇 설정
tg_token = os.environ.get("TG_BOT_TOKEN")
tg_chat = os.environ.get("TG_CHAT_ID")

if not tg_token or not tg_chat:
    print("=" * 60)
    print("  ERROR: Telegram credentials not configured")
    print("=" * 60)
    print("\n텔레그램 봇을 실행하려면 다음이 필요합니다:")
    print("  1. .env 파일에 TG_BOT_TOKEN 설정")
    print("  2. .env 파일에 TG_CHAT_ID 설정")
    print("\n.env.example 을 참고하세요.")
    sys.exit(1)

print("=" * 60)
print("  AV-TOR TELEGRAM BOT")
print("=" * 60)
print(f"\n✅ Bot Token: ****{tg_token[-10:]}")
print(f"✅ Chat ID: {tg_chat}")
print("\n📱 Available Commands:")
print("  /dashboard - 최근 7일 통계")
print("  /dashboard_1d - 어제 통계")
print("  /dashboard_31d - 지난 31일 통계")
print("  /help - 도움말")
print("  /start - 시작")
print("\n또는 자연어로:")
print("  '대시보드', '어제', '지난달' 등")
print("\n" + "=" * 60)
print("🤖 Bot starting... (Press Ctrl+C to stop)")
print("=" * 60 + "\n")

telegram_bot.configure(tg_token, tg_chat)

try:
    telegram_bot.start()
    # 메인 스레드 유지
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\n⏹️ Bot stopping...")
    telegram_bot.stop()
    print("✅ Bot stopped")
