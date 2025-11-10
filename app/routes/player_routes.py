from flask import Blueprint, jsonify, request

from app.models.game_session import GameSession
from app.models.player import Player
from app.models.security_event import SecurityEvent
from app.services.anomaly_detector import AnomalyDetector
from app.utils.auth import require_jwt
from app.utils.database import db
from app.utils.rate_limiter import rate_limit

players_bp = Blueprint("players", __name__)
anomaly_detector = AnomalyDetector()


@players_bp.route("/<int:player_id>/behavior", methods=["GET"])
@require_jwt
@rate_limit
def player_behavior(player_id: int):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": f"Player {player_id} not found"}), 404

    sessions = (
        GameSession.query.filter_by(player_id=player.id)
        .order_by(GameSession.recorded_at.desc())
        .limit(30)
        .all()
    )
    events = (
        SecurityEvent.query.filter_by(player_id=player.id)
        .order_by(SecurityEvent.detected_at.desc())
        .limit(10)
        .all()
    )

    anomalies = anomaly_detector.detect(sessions)

    if sessions:
        avg_duration = sum(s.duration_minutes for s in sessions) / len(sessions)
        avg_apm = sum(s.actions_per_minute for s in sessions) / len(sessions)
        avg_headshot = sum(s.headshot_rate for s in sessions) / len(sessions)
    else:
        avg_duration = avg_apm = avg_headshot = 0

    return jsonify(
        {
            "player": player.to_dict(),
            "aggregates": {
                "avg_duration_minutes": round(avg_duration, 2),
                "avg_actions_per_minute": round(avg_apm, 2),
                "avg_headshot_rate": round(avg_headshot, 3),
            },
            "recent_sessions": [session.to_dict() for session in sessions[:5]],
            "recent_events": [event.to_dict() for event in events],
            "anomalies": [finding.__dict__ for finding in anomalies],
        }
    )


@players_bp.route("/<int:player_id>/session", methods=["POST"])
@require_jwt
@rate_limit
def create_session(player_id: int):
    payload = request.get_json(silent=True) or {}
    required_fields = {"duration_minutes", "actions_per_minute", "headshot_rate"}
    missing = required_fields - payload.keys()
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(sorted(missing))}"}), 400

    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": f"Player {player_id} not found"}), 404

    try:
        session = GameSession(
            player_id=player.id,
            duration_minutes=int(payload["duration_minutes"]),
            actions_per_minute=int(payload["actions_per_minute"]),
            headshot_rate=float(payload["headshot_rate"]),
            reaction_time_ms=int(payload.get("reaction_time_ms", 200)),
        )
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid type provided for session metrics"}), 400

    if not 0 <= session.headshot_rate <= 1:
        return jsonify({"error": "headshot_rate must be between 0 and 1"}), 400

    db.session.add(session)
    db.session.commit()

    return jsonify({"message": "Session recorded", "session": session.to_dict()}), 201


@players_bp.route("/suspicious", methods=["GET"])
@require_jwt
@rate_limit
def suspicious_players():
    threshold = int(request.args.get("risk_threshold", 70))
    players = (
        Player.query.filter(Player.risk_score >= threshold)
        .order_by(Player.risk_score.desc())
        .limit(25)
        .all()
    )

    payload = []
    for player in players:
        recent_event = (
            SecurityEvent.query.filter_by(player_id=player.id)
            .order_by(SecurityEvent.detected_at.desc())
            .first()
        )
        payload.append(
            {
                **player.to_dict(),
                "recent_event": recent_event.to_dict() if recent_event else None,
            }
        )

    return jsonify({"players": payload, "count": len(payload)})

