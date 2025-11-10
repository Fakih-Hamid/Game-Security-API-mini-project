import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.models.game_session import GameSession
from app.models.player import Player
from app.models.security_event import SecurityEvent
from app.utils import config as config_module
from app.utils.auth import generate_token
from app.utils.database import db


class TestConfig(config_module.Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    RATE_LIMIT_REQUESTS = 1000
    AUTO_SEED_DATA = False


@pytest.fixture()
def app():
    app = create_app(TestConfig)

    with app.app_context():
        player = Player(username="test_player", risk_score=65)
        safe_player = Player(username="legit_player", risk_score=15)
        db.session.add_all([player, safe_player])
        db.session.flush()

        session = GameSession(
            player_id=player.id,
            duration_minutes=45,
            actions_per_minute=240,
            headshot_rate=0.92,
            reaction_time_ms=85,
        )
        db.session.add(session)

        event = SecurityEvent(
            player_id=player.id,
            event_type="aimbot_suspected",
            severity="high",
            notes="Test fixture event",
        )
        db.session.add(event)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_headers(app):
    with app.app_context():
        token = generate_token({"sub": "test_service", "role": "analyst"})
    return {"Authorization": f"Bearer {token}"}

