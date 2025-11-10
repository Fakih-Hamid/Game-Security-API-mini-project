from flask import Blueprint, jsonify, request
from sqlalchemy import func

from app.models.player import Player
from app.models.game_session import GameSession
from app.models.security_event import SecurityEvent
from app.services.anomaly_detector import AnomalyDetector
from app.services.log_analyzer import LogAnalyzer
from app.services.threat_scorer import ThreatScorer
from app.utils.auth import require_jwt
from app.utils.database import db
from app.utils.rate_limiter import rate_limit

security_bp = Blueprint("security", __name__)
log_analyzer = LogAnalyzer()
anomaly_detector = AnomalyDetector()
threat_scorer = ThreatScorer()


@security_bp.route("/scan-log", methods=["POST"])
@require_jwt
@rate_limit
def scan_log():
    payload = request.get_json(silent=True) or {}
    entries = payload.get("entries", [])
    if not isinstance(entries, list):
        return jsonify({"error": "entries must be a list"}), 400

    result = log_analyzer.scan(entries)
    return jsonify(
        {
            "suspicious_players": result.suspicious_players,
            "anomaly_counts": result.anomaly_counts,
            "insights": result.insights,
        }
    )


@security_bp.route("/player-risk/<int:player_id>", methods=["GET"])
@require_jwt
@rate_limit
def player_risk(player_id: int):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": f"Player {player_id} not found"}), 404

    sessions = GameSession.query.filter_by(player_id=player.id).all()
    anomalies = anomaly_detector.detect(sessions)
    events = SecurityEvent.query.filter_by(player_id=player.id).all()

    score = threat_scorer.score_player(
        baseline=player.risk_score, sessions=sessions, anomalies=anomalies, events=events
    )

    return jsonify(
        {
            "player": player.to_dict(),
            "risk_score": score,
            "anomalies": [finding.__dict__ for finding in anomalies],
            "event_count": len(events),
        }
    )


@security_bp.route("/report", methods=["POST"])
@require_jwt
@rate_limit
def create_report():
    payload = request.get_json(silent=True) or {}
    player_id = payload.get("player_id")
    if not player_id:
        return jsonify({"error": "player_id is required"}), 400

    reason = payload.get("reason", "manual_report")
    severity = payload.get("severity", "medium")
    notes = payload.get("notes", "")

    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": f"Player {player_id} not found"}), 404

    event = SecurityEvent(
        player_id=player.id,
        event_type=reason,
        severity=severity,
        notes=notes[:500],
    )
    db.session.add(event)
    db.session.commit()

    return jsonify({"message": "Report recorded", "event": event.to_dict()}), 201


@security_bp.route("/dashboard", methods=["GET"])
@require_jwt
@rate_limit
def dashboard():
    total_players = Player.query.count()
    high_risk_players = Player.query.filter(Player.risk_score >= 75).count()
    total_events = SecurityEvent.query.count()
    recent_events = (
        SecurityEvent.query.order_by(SecurityEvent.detected_at.desc()).limit(5).all()
    )

    avg_apm = db.session.query(func.avg(GameSession.actions_per_minute)).scalar() or 0
    avg_headshot = db.session.query(func.avg(GameSession.headshot_rate)).scalar() or 0

    return jsonify(
        {
            "totals": {
                "players": total_players,
                "high_risk_players": high_risk_players,
                "security_events": total_events,
            },
            "recent_events": [event.to_dict() for event in recent_events],
            "metrics": {
                "avg_actions_per_minute": round(avg_apm, 2),
                "avg_headshot_rate": round(avg_headshot, 3),
            },
        }
    )

