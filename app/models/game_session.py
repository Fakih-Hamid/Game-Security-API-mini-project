from datetime import datetime

from app.utils.database import db


class GameSession(db.Model):
    __tablename__ = "game_sessions"

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    actions_per_minute = db.Column(db.Integer, nullable=False)
    headshot_rate = db.Column(db.Float, nullable=False)
    reaction_time_ms = db.Column(db.Integer, nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "player_id": self.player_id,
            "duration_minutes": self.duration_minutes,
            "actions_per_minute": self.actions_per_minute,
            "headshot_rate": self.headshot_rate,
            "reaction_time_ms": self.reaction_time_ms,
            "recorded_at": self.recorded_at.isoformat(),
        }

