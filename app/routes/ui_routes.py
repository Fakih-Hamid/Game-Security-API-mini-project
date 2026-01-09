from flask import Blueprint, render_template
from sqlalchemy import func

from app.models.player import Player
from app.models.security_event import SecurityEvent
from app.utils.database import db

ui_bp = Blueprint("ui", __name__)


@ui_bp.route("/")
def landing():
    total_players = Player.query.count()
    high_risk_players = Player.query.filter(Player.risk_score >= 75).count()
    total_events = SecurityEvent.query.count()

    suspicious_players = (
        Player.query.filter(Player.risk_score >= 70)
        .order_by(Player.risk_score.desc())
        .limit(5)
        .all()
    )

    recent_events = (
        SecurityEvent.query.order_by(SecurityEvent.detected_at.desc()).limit(5).all()
    )

    avg_risk = db.session.query(func.avg(Player.risk_score)).scalar() or 0

    return render_template(
        "dashboard.html",
        totals={
            "players": total_players,
            "high_risk_players": high_risk_players,
            "security_events": total_events,
            "avg_risk": round(avg_risk, 1),
        },
        suspicious_players=suspicious_players,
        recent_events=recent_events,
    )

