#!/usr/bin/env python3
"""대시보드 테스트용 샘플 데이터 생성."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from datetime import datetime, timedelta
from iot import telemetry
import json
import random

# 텔레메트리 초기화
telemetry.init()

scenarios = [
    {"id": 1, "label": "Construction Zone"},
    {"id": 2, "label": "Rain"},
    {"id": 3, "label": "Fog"},
    {"id": 4, "label": "Icy Road"},
]

fail_reasons = [
    "NoGrip",
    "NoEye", 
    "Timeout",
    "NoVoice"
]

print("=" * 60)
print("  DASHBOARD TEST DATA GENERATOR")
print("=" * 60)

# 지난 7일간의 샘플 데이터 생성
print("\n생성 중... (약 7일간 50개 시도)")

for day in range(7):
    scenario = random.choice(scenarios)
    
    # 하루에 7~8개 TOR 시도
    attempts = random.randint(7, 8)
    
    for attempt in range(attempts):
        # 시간대 랜덤
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        
        timestamp = datetime.now() - timedelta(days=day, hours=hour, minutes=minute, seconds=second)
        session_id = f"test_{day}_{attempt}"
        
        # TOR 시작
        success = random.random() > 0.25  # 75% 성공률
        fail_reason = random.choice(fail_reasons) if not success else None
        
        print(f"  [{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {scenario['label']:20} → {'✓ 성공' if success else '✗ ' + (fail_reason or 'Unknown')}")

print("\n✅ 샘플 데이터 생성 완료!")
print("\n다음 명령으로 대시보드를 실행하세요:")
print("  python -m dashboard.server")
print("\n그리고 브라우저에서 열기:")
print("  http://localhost:5000")
print("\n" + "=" * 60)
