from __future__ import annotations

import functools
from datetime import datetime, timedelta
from typing import Callable, Dict, Optional, Tuple

import jwt
from flask import Response, current_app, jsonify, request


class AuthenticationError(Exception):
    """Raised when JWT validation fails."""


def generate_token(payload: Dict) -> str:
    expiry: timedelta = current_app.config["JWT_EXPIRATION_DELTA"]
    payload = {
        **payload,
        "exp": datetime.utcnow() + expiry,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )


def decode_token(token: str) -> Dict:
    try:
        return jwt.decode(
            token,
            current_app.config["JWT_SECRET_KEY"],
            algorithms=[current_app.config["JWT_ALGORITHM"]],
        )
    except jwt.PyJWTError as exc:
        raise AuthenticationError(str(exc)) from exc


def require_jwt(fn: Callable) -> Callable:
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split(" ", 1)[1].strip()
        try:
            request.jwt_payload = decode_token(token)
        except AuthenticationError as exc:
            return jsonify({"error": "Invalid token", "detail": str(exc)}), 401

        return fn(*args, **kwargs)

    return wrapper


def authenticate_service_user(username: str, password: str) -> Optional[str]:
    """Simple service credential check, to be replaced with IAM integration."""
    configured_user, configured_password = _credentials_from_config()
    if username == configured_user and password == configured_password:
        return generate_token({"sub": username, "role": "security_engineer"})
    return None


def _credentials_from_config() -> Tuple[str, str]:
    user = current_app.config.get("SERVICE_USERNAME", "security_console")
    password = current_app.config.get("SERVICE_PASSWORD", "letmein123")
    return user, password

