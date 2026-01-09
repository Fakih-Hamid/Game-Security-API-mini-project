from datetime import datetime

from app.utils.database import db


class Player(db.Model):
    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    risk_score = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    sessions = db.relationship(
        "GameSession", backref="player", lazy=True, cascade="all, delete-orphan"
    )
    security_events = db.relationship(
        "SecurityEvent", backref="player", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "risk_score": self.risk_score,
            "created_at": self.created_at.isoformat(),
        }

