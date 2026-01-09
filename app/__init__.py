from __future__ import annotations

import logging
from logging.config import dictConfig

from flask import Flask, jsonify, request
from flask_cors import CORS

from app.routes import register_blueprints
from app.utils import config as config_module
from app.utils.auth import authenticate_service_user, generate_token
from app.utils.database import init_db


def create_app(config_class=config_module.Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    _setup_logging(app)
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    init_db(app, seed=app.config.get("AUTO_SEED_DATA", True))

    register_blueprints(app)
    _register_common_routes(app)

    return app


def _setup_logging(app: Flask) -> None:
    dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {
                    "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
                }
            },
            "handlers": {
                "wsgi": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://flask.logging.wsgi_errors_stream",
                    "formatter": "default",
                }
            },
            "root": {"level": "INFO", "handlers": ["wsgi"]},
        }
    )
    app.logger.setLevel(logging.INFO)


def _register_common_routes(app: Flask) -> None:
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"})

    @app.route("/api/auth/token", methods=["POST"])
    def get_token():
        payload = request.get_json(silent=True) or {}
        username = payload.get("username")
        password = payload.get("password")
        token = authenticate_service_user(username, password)
        if not token:
            return jsonify({"error": "Invalid credentials"}), 401
        return jsonify({"access_token": token})

    @app.route("/api/auth/refresh", methods=["POST"])
    def refresh_token():
        payload = request.get_json(silent=True) or {}
        subject = payload.get("subject")
        if not subject:
            return jsonify({"error": "subject is required"}), 400
        token = generate_token({"sub": subject, "role": "security_engineer"})
        return jsonify({"access_token": token})

