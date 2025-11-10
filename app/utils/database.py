import random
from datetime import datetime, timedelta
from typing import Optional

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from .config import ensure_instance_dir

db = SQLAlchemy()


def init_db(app: Flask, *, seed: bool = True) -> None:
    """Initialise the database and optionally load sample data."""
    ensure_instance_dir()
    db.init_app(app)

    with app.app_context():
        from app.models.player import Player
        from app.models.game_session import GameSession
        from app.models.security_event import SecurityEvent

        db.create_all()

        if seed:
            seed_sample_data(Player, GameSession, SecurityEvent)
            db.session.commit()


def seed_sample_data(Player, GameSession, SecurityEvent) -> None:
    """Populate the database with deterministic but varied demo data."""
    if Player.query.first():
        return

    rng = random.Random(42)
    now = datetime.utcnow()

    players = []
    for idx in range(1, 51):
        risk_score = min(100, max(0, int(rng.gauss(35 + idx % 7 * 5, 15))))
        player = Player(
            username=f"player_{idx:03d}",
            risk_score=risk_score,
            created_at=now - timedelta(days=rng.randint(10, 365)),
        )
        players.append(player)

    db.session.add_all(players)
    db.session.flush()

    sessions = []
    events = []

    for _ in range(1050):
        player = rng.choice(players)
        base_duration = rng.randint(5, 120)
        actions_per_minute = rng.randint(30, 180)
        headshot_rate = round(min(1.0, max(0.05, rng.gauss(0.35, 0.15))), 2)

        if player.risk_score > 70 and rng.random() < 0.4:
            actions_per_minute = rng.randint(200, 320)
            headshot_rate = round(rng.uniform(0.85, 0.98), 2)
        elif player.risk_score < 20 and rng.random() < 0.1:
            headshot_rate = round(rng.uniform(0.5, 0.7), 2)

        reaction_time_ms = rng.randint(80, 400)

        session = GameSession(
            player_id=player.id,
            duration_minutes=base_duration,
            actions_per_minute=actions_per_minute,
            headshot_rate=headshot_rate,
            reaction_time_ms=reaction_time_ms,
            recorded_at=now - timedelta(hours=rng.randint(1, 500)),
        )
        sessions.append(session)

        if headshot_rate > 0.9 or actions_per_minute > 220 or reaction_time_ms < 110:
            severity = rng.choice(["medium", "high"])
            event = SecurityEvent(
                player_id=player.id,
                event_type=rng.choice(
                    ["aimbot_suspected", "macro_usage", "rapid_skill_increase"]
                ),
                severity=severity,
                detected_at=session.recorded_at + timedelta(minutes=5),
                notes="Generated from sample session data",
            )
            events.append(event)

    db.session.add_all(sessions)
    db.session.add_all(events)


def get_player_by_id(player_id: int) -> Optional["Player"]:
    from app.models.player import Player

    return Player.query.get(player_id)

