# AV-TOR 대시보드 사용 가이드

## 개요

AV-TOR 제어권 전환 시스템의 모든 활동을 모니터링하는 웹 기반 대시보드입니다.

**기능:**
- 📊 제어권 전환 성공/실패 통계
- 📈 시간대별 분석 (1일, 7일, 31일)
- ⚠️ 실패 원인 분석
- 📋 최근 TOR 시도 목록
- 🎯 시나리오별 성공률

## 설치

### 1. Flask 설치

```bash
pip install flask
```

또는

```bash
C:/Users/LG/AppData/Local/Programs/Python/Python310/python.exe -m pip install flask
```

### 2. 대시보드 실행

프로젝트 루트에서:

```bash
python -m dashboard.server
```

또는

```bash
C:/Users/LG/AppData/Local/Programs/Python/Python310/python.exe -m dashboard.server
```

### 3. 브라우저에서 접속

```
http://localhost:5000
```

## API 엔드포인트

### 통계 조회

```
GET /api/stats?days=7
```

**파라미터:**
- `days`: 1 (24시간), 7 (지난 7일), 31 (지난 31일), 0 (전체)

**응답 예시:**
```json
{
  "days": 7,
  "total": 15,
  "success": 12,
  "fail": 3,
  "success_rate": 80.0,
  "by_scenario": {
    "Construction Zone": {"total": 5, "success": 4, "fail": 1},
    "Rain": {"total": 10, "success": 8, "fail": 2}
  },
  "fail_reasons": {
    "NoGrip": 2,
    "Timeout": 1
  }
}
```

### 이벤트 조회

```
GET /api/events?days=7&limit=50
```

**파라미터:**
- `days`: 조회 기간
- `limit`: 최대 반환 개수

## 데이터 저장 위치

TOR 시도 데이터는 다음 위치에 JSONL 형식으로 저장됩니다:

```
data/telemetry/tor_YYYY-MM-DD.jsonl
```

매일 새 파일이 생성됩니다.

## 실시간 업데이트

대시보드는 자동으로 최신 데이터를 로드합니다. 시간 필터를 선택하면 그 기간의 통계가 업데이트됩니다.

## 트러블슈팅

### "Flask를 찾을 수 없음" 오류

```bash
pip install flask
```

### 포트 5000이 이미 사용 중

다른 포트로 실행:

```python
# dashboard/server.py의 마지막 줄 수정
app.run(debug=True, host="0.0.0.0", port=5001)  # 포트 변경
```

### 데이터가 표시되지 않음

1. `python src/app.py`를 실행해 TOR 시나리오를 진행
2. `data/telemetry/` 폴더에 파일이 생성되는지 확인
3. 브라우저 개발자 도구에서 `/api/stats` 응답 확인

## 개발 노트

- 백엔드: Flask (Python)
- 프론트엔드: 순수 JavaScript (jQuery 없음)
- 차트: Chart.js
- 데이터 저장: JSON Lines (.jsonl)

## 기능 확장

대시보드에 기능을 추가하려면:

1. `server.py`에 새 API 엔드포인트 추가
2. `templates/dashboard.html`에서 JavaScript로 호출
3. 필요시 `telemetry.py`에 쿼리 함수 추가

예시:

```python
# server.py
@app.route("/api/custom")
def api_custom():
    # 커스텀 로직
    return jsonify({"data": "..."})
```

```javascript
// dashboard.html
fetch('/api/custom')
    .then(r => r.json())
    .then(data => console.log(data));
```
