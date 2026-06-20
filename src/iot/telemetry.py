"""TOR 시도 이벤트 텔레메트리 저장 및 조회."""
import os
import json
from datetime import datetime, timedelta
from pathlib import Path


_TELEMETRY_DIR = "./data/telemetry"
_LOG_FILE = None

# 대시보드에 0건이어도 "항상" 표시할 표준 목록 (config.yaml 시나리오 / 실패 코드와 일치).
# 시나리오를 안 돌렸거나 특정 실패가 0건이어도 4개/4종을 모두 노출한다.
ALL_SCENARIOS = ["Construction Zone", "Rain", "Fog", "Icy Road"]
ALL_FAIL_LABELS = {
    "NoEye": "전방 미주시(NoEye)",
    "NoGrip": "핸들 미파지(NoGrip)",
    "NoVoice": "음성확인 실패(NoVoice)",
    "Timeout": "시간 초과(Timeout)",
}


def init(config=None):
    """텔레메트리 디렉토리 초기화."""
    global _LOG_FILE
    telemetry_dir = (config or {}).get("capture", {}).get("out_dir", "./data/captures")
    telemetry_dir = os.path.join(os.path.dirname(telemetry_dir), "telemetry")
    
    Path(telemetry_dir).mkdir(parents=True, exist_ok=True)
    
    # 오늘 날짜로 로그 파일 생성
    today = datetime.now().strftime("%Y-%m-%d")
    _LOG_FILE = os.path.join(telemetry_dir, f"tor_{today}.jsonl")
    print(f"[TELEMETRY] Initialized: {_LOG_FILE}")

    # 30일보다 오래된 기록은 정리(디스크 무한 증가 방지, 대시보드 최대 조회와 일치)
    _cleanup_old(telemetry_dir, keep_days=30)


def _cleanup_old(telemetry_dir: str, keep_days: int = 30):
    """keep_days 보다 오래된 tor_YYYY-MM-DD.jsonl 파일을 삭제한다.

    하루당 파일 1개라, 항상 최근 keep_days 일치(≈ keep_days 개 파일)만 남는다.
    파일명이 날짜 형식이 아니면 건드리지 않는다.
    """
    cutoff = datetime.now().date() - timedelta(days=keep_days)
    for log_file in Path(telemetry_dir).glob("tor_*.jsonl"):
        try:
            date_str = log_file.stem.replace("tor_", "")   # "YYYY-MM-DD"
            file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            continue  # 예상치 못한 파일명은 건너뜀
        if file_date < cutoff:
            try:
                log_file.unlink()
                print(f"[TELEMETRY] Removed old log (>{keep_days}d): {log_file.name}")
            except OSError as e:
                print(f"[TELEMETRY] Could not remove {log_file.name}: {e}")


def log_event(event_type: str, scenario: dict, status: str, **kwargs):
    """TOR 이벤트 기록 (JSONL 형식).
    
    event_type: 'tor_start', 'phase1_complete', 'phase2_success', 'phase2_fail', 'tor_end'
    status: 'success', 'fail', 'timeout', 'nogaze', 'nogrip', 'novoice'
    """
    if _LOG_FILE is None:
        init()
    
    record = {
        "timestamp": datetime.now().isoformat(),
        "event": event_type,
        "scenario_id": scenario.get("id"),
        "scenario_label": scenario.get("label"),
        "status": status,
        **kwargs
    }
    
    try:
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[TELEMETRY] Write error: {e}")


def get_events(days: int = 1) -> list:
    """최근 N일간의 모든 이벤트 조회.
    
    days: 1 (어제), 7 (지난 7일), 31 (지난 31일), 0 (전체)
    """
    if _LOG_FILE is None:
        init()
    
    telemetry_dir = os.path.dirname(_LOG_FILE)
    events = []
    
    # 조회 기간 계산
    if days > 0:
        cutoff_date = datetime.now() - timedelta(days=days)
    else:
        cutoff_date = None
    
    # 모든 텔레메트리 파일 읽기
    for log_file in sorted(Path(telemetry_dir).glob("tor_*.jsonl")):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    ts = datetime.fromisoformat(record["timestamp"])
                    
                    if cutoff_date is None or ts >= cutoff_date:
                        events.append(record)
        except Exception as e:
            print(f"[TELEMETRY] Read error {log_file}: {e}")
    
    return sorted(events, key=lambda x: x["timestamp"])


def get_stats(days: int = 1) -> dict:
    """시간대별 통계 계산.
    
    Returns:
        {
            'total': 총 시도 횟수,
            'success': 성공,
            'fail': 실패,
            'success_rate': 성공률(%),
            'by_scenario': {scenario_label: {total, success, fail}},
            'fail_reasons': {reason: count},
        }
    """
    events = get_events(days)
    
    stats = {
        "total": 0,
        "success": 0,
        "fail": 0,
        "success_rate": 0.0,
        # 0건이어도 4개 시나리오 / 4종 실패원인을 항상 노출 (대시보드용)
        "by_scenario": {
            label: {"total": 0, "success": 0, "fail": 0} for label in ALL_SCENARIOS
        },
        "fail_reasons": {flabel: 0 for flabel in ALL_FAIL_LABELS.values()},
    }
    
    # TOR 시작(phase1 들어가기) 기준으로 카운트
    tor_starts = [e for e in events if e.get("event") == "tor_start"]
    
    if not tor_starts:
        return stats
    
    stats["total"] = len(tor_starts)
    
    for event in tor_starts:
        label = event.get("scenario_label", "Unknown")
        
        # 같은 TOR 세션의 결과 찾기
        session_id = event.get("session_id")
        if not session_id:
            continue
        
        result = next(
            (e for e in events 
             if e.get("session_id") == session_id and e.get("event") == "tor_end"),
            None
        )
        
        if result:
            status = result.get("status", "unknown")
            if status == "success":
                stats["success"] += 1
            else:
                stats["fail"] += 1
                # 안정적인 fail_code(NoEye/NoGrip/NoVoice/Timeout)로 집계해 친절한 라벨로
                code = result.get("fail_code") or "Timeout"
                flabel = ALL_FAIL_LABELS.get(code, code)
                stats["fail_reasons"][flabel] = stats["fail_reasons"].get(flabel, 0) + 1
        
        # 시나리오별 통계
        if label not in stats["by_scenario"]:
            stats["by_scenario"][label] = {"total": 0, "success": 0, "fail": 0}
        
        stats["by_scenario"][label]["total"] += 1
        if result and result.get("status") == "success":
            stats["by_scenario"][label]["success"] += 1
        else:
            stats["by_scenario"][label]["fail"] += 1
    
    # 성공률 계산
    if stats["total"] > 0:
        stats["success_rate"] = round(100 * stats["success"] / stats["total"], 1)
    
    return stats


if __name__ == "__main__":
    import sys
    
    init()
    
    if len(sys.argv) > 1:
        days = int(sys.argv[1])
    else:
        days = 7
    
    print(f"\n[TELEMETRY] Events (last {days} days):")
    events = get_events(days)
    for e in events:
        print(f"  {e['timestamp']} | {e['event']:20} | {e.get('scenario_label', '?'):15} | {e.get('status')}")
    
    print(f"\n[TELEMETRY] Statistics (last {days} days):")
    stats = get_stats(days)
    print(f"  Total: {stats['total']}, Success: {stats['success']}, Fail: {stats['fail']}")
    print(f"  Success Rate: {stats['success_rate']}%")
    print(f"  Fail Reasons: {stats['fail_reasons']}")
    print(f"  By Scenario: {stats['by_scenario']}")
