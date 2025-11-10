from datetime import datetime

from app.utils.database import db


class SecurityEvent(db.Model):
    __tablename__ = "security_events"

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    event_type = db.Column(db.String(120), nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    detected_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "player_id": self.player_id,
            "event_type": self.event_type,
            "severity": self.severity,
            "detected_at": self.detected_at.isoformat(),
            "notes": self.notes,
        }

