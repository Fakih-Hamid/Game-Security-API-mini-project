from flask import Blueprint, jsonify, request
from sqlalchemy import func

from app.models.game_session import GameSession
from app.models.player import Player
from app.models.security_event import SecurityEvent
from app.services.anomaly_detector import AnomalyDetector
from app.utils.auth import require_jwt
from app.utils.database import db
from app.utils.rate_limiter import rate_limit

analytics_bp = Blueprint("analytics", __name__)
anomaly_detector = AnomalyDetector()


@analytics_bp.route("/cheat-patterns", methods=["GET"])
@require_jwt
@rate_limit
def cheat_patterns():
    pattern_counts = (
        SecurityEvent.query.with_entities(SecurityEvent.event_type, func.count())
        .group_by(SecurityEvent.event_type)
        .order_by(func.count().desc())
        .all()
    )

    payload = [
        {"pattern": event_type, "occurrences": count} for event_type, count in pattern_counts
    ]
    return jsonify({"patterns": payload})


@analytics_bp.route("/detect-anomalies", methods=["POST"])
@require_jwt
@rate_limit
def detect_anomalies():
    payload = request.get_json(silent=True) or {}
    player_id = payload.get("player_id")
    if not player_id:
        return jsonify({"error": "player_id is required"}), 400

    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": f"Player {player_id} not found"}), 404

    sessions = (
        GameSession.query.filter_by(player_id=player.id)
        .order_by(GameSession.recorded_at.desc())
        .limit(50)
        .all()
    )

    findings = anomaly_detector.detect(sessions)
    return jsonify({"anomalies": [finding.__dict__ for finding in findings]})


@analytics_bp.route("/stats", methods=["GET"])
@require_jwt
@rate_limit
def analytics_stats():
    total_sessions = GameSession.query.count()
    total_events = SecurityEvent.query.count()
    avg_risk = db_avg = (
        Player.query.with_entities(func.avg(Player.risk_score)).scalar() or 0
    )

    latest_sessions = (
        GameSession.query.order_by(GameSession.recorded_at.desc()).limit(5).all()
    )

    return jsonify(
        {
            "totals": {
                "sessions": total_sessions,
                "security_events": total_events,
                "avg_risk": round(db_avg, 2),
            },
            "latest_sessions": [session.to_dict() for session in latest_sessions],
        }
    )

