from __future__ import annotations

import functools
import time
from collections import defaultdict, deque
from typing import Callable, Deque, Dict, Tuple

from flask import Request, current_app, jsonify, request


_REQUEST_LOG: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)


def rate_limit(fn: Callable) -> Callable:
    """Simple in-memory rate limiter keyed by IP + endpoint."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        limit = current_app.config["RATE_LIMIT_REQUESTS"]
        period = current_app.config["RATE_LIMIT_PERIOD_SECONDS"]

        key = _build_key(request)
        window = _REQUEST_LOG[key]
        now = time.time()

        while window and window[0] <= now - period:
            window.popleft()

        if len(window) >= limit:
            retry_after = period - (now - window[0])
            return (
                jsonify({"error": "Rate limit exceeded", "retry_after": retry_after}),
                429,
                {"Retry-After": f"{int(retry_after)}"},
            )

        window.append(now)
        return fn(*args, **kwargs)

    return wrapper


def _build_key(req: Request) -> Tuple[str, str]:
    ip = req.headers.get("X-Forwarded-For", req.remote_addr or "unknown")
    return ip, req.endpoint or "unknown"

