from pathlib import Path
from datetime import timedelta
import os


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = BASE_DIR / "instance" / "game_security.db"


class Config:
    """Application configuration values."""

    SECRET_KEY = os.getenv("FLASK_SECRET", "change-me-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-signing-key")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{DATABASE_PATH.as_posix()}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PROPAGATE_EXCEPTIONS = True
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_DELTA = timedelta(hours=12)

    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_PERIOD_SECONDS = int(os.getenv("RATE_LIMIT_PERIOD_SECONDS", "60"))

    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    AUTO_SEED_DATA = os.getenv("AUTO_SEED_DATA", "true").lower() == "true"


def ensure_instance_dir() -> None:
    """Create the SQLite instance directory when missing."""
    instance_dir = DATABASE_PATH.parent
    instance_dir.mkdir(parents=True, exist_ok=True)

