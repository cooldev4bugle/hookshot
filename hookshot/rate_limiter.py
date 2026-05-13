"""Simple in-memory rate limiter for webhook ingestion."""

import time
from collections import deque
from typing import Dict


class RateLimitError(Exception):
    pass


class RateLimiter:
    """Sliding window rate limiter keyed by client IP.

    Args:
        max_requests: Maximum number of requests allowed in the window.
        window_seconds: Length of the sliding window in seconds.
    """

    def __init__(self, max_requests: int = 100, window_seconds: float = 60.0):
        if max_requests < 1:
            raise RateLimitError("max_requests must be at least 1")
        if window_seconds <= 0:
            raise RateLimitError("window_seconds must be positive")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: Dict[str, deque] = {}

    def _now(self) -> float:
        return time.monotonic()

    def _prune(self, key: str, now: float) -> None:
        """Remove timestamps outside the current window."""
        bucket = self._buckets.get(key)
        if bucket is None:
            return
        cutoff = now - self.window_seconds
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()

    def is_allowed(self, key: str) -> bool:
        """Return True if the request is within the rate limit."""
        now = self._now()
        self._prune(key, now)
        bucket = self._buckets.setdefault(key, deque())
        if len(bucket) >= self.max_requests:
            return False
        bucket.append(now)
        return True

    def remaining(self, key: str) -> int:
        """Return how many requests are still allowed in the current window."""
        now = self._now()
        self._prune(key, now)
        bucket = self._buckets.get(key, deque())
        return max(0, self.max_requests - len(bucket))

    def reset(self, key: str) -> None:
        """Clear rate limit state for a given key."""
        self._buckets.pop(key, None)
