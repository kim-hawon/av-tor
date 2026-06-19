# 텔레그램 봇 가이드

## 개요

AV-TOR 텔레그램 봇을 통해 다음을 할 수 있습니다:

- 📊 **대시보드 통계 조회** - 시간대별 TOR 시도 통계 확인
- 📈 **성공률 분석** - 시나리오별 성공/실패 데이터
- ⚠️ **실패 원인 분석** - 실패한 TOR의 원인 파악

## 시작하기

### 1️⃣ 설정 확인

`.env` 파일에 다음이 설정되어 있는지 확인하세요:

```
TG_BOT_TOKEN=8712922597:AAGqMS-L70sriTmdQwMmoxMFnwyYCzYpduY
TG_CHAT_ID=8794149474
```

### 2️⃣ 봇 시작 (2가지 방법)

**방법 1: 독립 실행** (추천)

```bash
cd c:\Users\LG\Desktop\avtor
python start_bot.py
```

**방법 2: 메인 앱과 함께**

```bash
python src/app.py
```

그 후 별도 터미널에서 TOR 시나리오를 실행합니다.

### 3️⃣ 텔레그램에서 명령어 입력

봇(`@av_tor_monitor_bot`)에 다음 명령어를 입력합니다:

```
/dashboard
```

또는 자연어로:

```
대시보드
```

## 명령어 목록

| 명령어 | 설명 |
|--------|------|
| `/dashboard` | 최근 7일 통계 |
| `/dashboard_1d` | 어제(24시간) 통계 |
| `/dashboard_31d` | 지난 31일 통계 |
| `/help` | 도움말 표시 |
| `/start` | 시작 메시지 |

**자연어 인식** (대소문자 무관):

| 입력 | 기능 |
|------|------|
| 대시보드 | 7일 통계 |
| 어제 | 24시간 통계 |
| 지난달 | 31일 통계 |
| 도움말 | 명령어 표시 |
| 시작 | 시작 메시지 |

## 응답 예시

```
📊 AV-TOR 대시보드 통계

전체 시도: 50 건
성공: 40 건 ✅
실패: 10 건 ❌
성공률: 80.0%

실패 원인:
  • NoGrip: 6건
  • Timeout: 3건
  • NoVoice: 1건

시나리오별 통계:
  • Construction Zone: 10/12 (83%)
  • Rain: 8/10 (80%)
  • Fog: 12/15 (80%)
  • Icy Road: 10/13 (77%)

최근 7일 통계
```

## 트러블슈팅

### "봇이 응답하지 않음"

1. **봇 프로세스 확인**
   ```bash
   # 윈도우
   tasklist | findstr python
   ```

2. **텔레그램 봇이 실행 중인지 확인**
   - 터미널에서 "Bot starting..." 메시지 확인
   - 포트 충돌 없음을 확인

3. **토큰/채팅 ID 재확인**
   ```bash
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('TOKEN:', os.environ.get('TG_BOT_TOKEN')); print('CHAT_ID:', os.environ.get('TG_CHAT_ID'))"
   ```

### "메시지가 와도 응답 없음"

1. **봇에 메시지 권한 확인** - `/start` 먼저 입력
2. **네트워크 연결 확인** - 인터넷 연결 확인
3. **로그 확인** - 터미널의 `[TELEGRAM_BOT]` 로그 메시지 확인

### "대시보드 데이터가 없음"

1. **먼저 TOR 시나리오 실행**
   ```bash
   python src/app.py
   # const / rain 등 시나리오 입력
   ```

2. **데이터 저장 확인**
   ```
   data/telemetry/tor_YYYY-MM-DD.jsonl
   ```
   파일이 생성되었는지 확인

## 고급 사용

### 봇 프로세스 백그라운드 실행 (Windows)

**Batch 스크립트 생성:**

```batch
@echo off
title AV-TOR Telegram Bot
:loop
python start_bot.py
timeout /t 5
goto loop
```

`start_bot.bat` 로 저장 후 더블클릭으로 실행

### Linux/Mac

```bash
nohup python start_bot.py &
```

## 기술 상세

### 메시지 수신 방식

- **Long Polling**: Telegram Bot API의 `getUpdates` 메서드 사용
- **스레드 기반**: 메인 프로세스 차단 없음
- **비동기**: TOR 시나리오 실행 중에도 메시지 수신 가능

### 지연 시간

- 메시지 수신 지연: 0~30초 (long polling timeout)
- 응답 생성 시간: 0~2초 (데이터 조회)
- 전송 시간: 1~2초

### 데이터 프라이버시

- 모든 데이터는 로컬에 저장됨
- 텔레그램으로는 통계 텍스트만 전송
- 원본 이벤트 데이터는 전송 안 함

## 피드백 & 개선

추가 기능 제안:

- [ ] 그래프/이미지 전송 (ChartJS 렌더링)
- [ ] 실시간 알림 (특정 실패 발생 시)
- [ ] 시나리오별 상세 분석
- [ ] 비교 분석 (어제 vs 오늘)
- [ ] CSV 내보내기

---

**문의사항이 있으면 이슈를 등록하세요!** 🚀
