"""Flask middleware helper that enforces rate limiting on incoming requests."""

from functools import wraps
from flask import request, jsonify
from hookshot.rate_limiter import RateLimiter

# Module-level default limiter; can be replaced in tests or via configure().
_limiter: RateLimiter = RateLimiter(max_requests=100, window_seconds=60.0)


def configure(max_requests: int = 100, window_seconds: float = 60.0) -> None:
    """Replace the module-level limiter with new settings."""
    global _limiter
    _limiter = RateLimiter(max_requests=max_requests, window_seconds=window_seconds)


def _client_key() -> str:
    """Return a string key identifying the current request's origin."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or "unknown"


def rate_limited(f):
    """Decorator that applies rate limiting to a Flask route handler.

    Returns HTTP 429 with a JSON error body when the limit is exceeded.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        key = _client_key()
        if not _limiter.is_allowed(key):
            remaining = _limiter.remaining(key)
            response = jsonify({
                "error": "rate limit exceeded",
                "remaining": remaining,
            })
            response.status_code = 429
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Limit"] = str(_limiter.max_requests)
            return response
        resp = f(*args, **kwargs)
        # Attach informational headers to successful responses.
        remaining = _limiter.remaining(key)
        if hasattr(resp, "headers"):
            resp.headers["X-RateLimit-Remaining"] = str(remaining)
            resp.headers["X-RateLimit-Limit"] = str(_limiter.max_requests)
        return resp
    return wrapper
