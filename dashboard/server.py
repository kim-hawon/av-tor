"""AV-TOR 제어권 전환 대시보드 서버.

실행: python -m dashboard.server
브라우저: http://localhost:5000
"""
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
from iot import telemetry

app = Flask(__name__, template_folder="templates")

# 텔레메트리 초기화
telemetry.init()


@app.route("/")
def index():
    """대시보드 메인 페이지."""
    return render_template("dashboard.html")


@app.route("/api/stats")
def api_stats():
    """시간대별 통계 API."""
    days = request.args.get("days", 7, type=int)
    stats = telemetry.get_stats(days)
    
    return jsonify({
        "days": days,
        "total": stats["total"],
        "success": stats["success"],
        "fail": stats["fail"],
        "success_rate": stats["success_rate"],
        "by_scenario": stats["by_scenario"],
        "fail_reasons": stats["fail_reasons"],
    })


@app.route("/api/events")
def api_events():
    """이벤트 목록 API."""
    days = request.args.get("days", 7, type=int)
    limit = request.args.get("limit", 100, type=int)
    
    events = telemetry.get_events(days)
    
    # TOR 세션 그룹화
    sessions = {}
    for event in events:
        session_id = event.get("session_id", "unknown")
        if session_id not in sessions:
            sessions[session_id] = {
                "session_id": session_id,
                "scenario": event.get("scenario_label"),
                "start_time": event.get("timestamp"),
                "events": [],
                "status": None,
            }
        sessions[session_id]["events"].append(event)
        
        # 마지막 이벤트 상태
        if event.get("event") == "tor_end":
            sessions[session_id]["status"] = event.get("status")
    
    # 시간순 정렬
    result = sorted(sessions.values(), key=lambda x: x["start_time"], reverse=True)
    return jsonify(result[:limit])


@app.route("/api/health")
def api_health():
    """헬스 체크."""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


if __name__ == "__main__":
    print("=" * 60)
    print("  AV-TOR DASHBOARD SERVER")
    print("=" * 60)
    print("\n🌐 Dashboard: http://localhost:5000")
    print("📊 API Stats: http://localhost:5000/api/stats?days=7")
    print("📋 API Events: http://localhost:5000/api/events?days=7")
    print("\nPress Ctrl+C to stop")
    print("=" * 60 + "\n")
    
    app.run(debug=True, host="0.0.0.0", port=5000)
