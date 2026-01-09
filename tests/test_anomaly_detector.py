from datetime import datetime, timedelta

from app.models.game_session import GameSession
from app.services.anomaly_detector import AnomalyDetector


def build_session(**kwargs):
    defaults = {
        "player_id": 1,
        "duration_minutes": 30,
        "actions_per_minute": 150,
        "headshot_rate": 0.4,
        "reaction_time_ms": 180,
        "recorded_at": datetime.utcnow(),
    }
    defaults.update(kwargs)
    return GameSession(**defaults)


def test_detector_flags_reaction_time_streak():
    detector = AnomalyDetector(reaction_time_threshold_ms=120)
    base_time = datetime.utcnow()
    sessions = [
        build_session(reaction_time_ms=95, recorded_at=base_time - timedelta(minutes=30)),
        build_session(reaction_time_ms=90, recorded_at=base_time - timedelta(minutes=20)),
        build_session(reaction_time_ms=85, recorded_at=base_time - timedelta(minutes=10)),
    ]

    findings = detector.detect(sessions)
    categories = [finding.category for finding in findings]
    assert "reaction_time" in categories


def test_detector_identifies_bot_like_behavior():
    detector = AnomalyDetector()
    base_time = datetime.utcnow()
    sessions = [
        build_session(
            actions_per_minute=210, recorded_at=base_time - timedelta(minutes=idx * 5)
        )
        for idx in range(4)
    ]

    findings = detector.detect(sessions)
    assert any(f.category == "bot_like" for f in findings)

