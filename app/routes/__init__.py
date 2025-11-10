from flask import Flask

from .analytics_routes import analytics_bp
from .player_routes import players_bp
from .security_routes import security_bp
from .ui_routes import ui_bp


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(ui_bp)
    app.register_blueprint(security_bp, url_prefix="/api/security")
    app.register_blueprint(players_bp, url_prefix="/api/players")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")

