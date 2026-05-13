"""Request throttler: delays forwarding based on configurable rules."""

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


class ThrottleError(Exception):
    pass


@dataclass
class ThrottleResult:
    delayed: bool
    delay_ms: int
    path: str

    def to_dict(self) -> dict:
        return {
            "delayed": self.delayed,
            "delay_ms": self.delay_ms,
            "path": self.path,
        }


class Throttler:
    """Applies per-path or global delay to incoming requests."""

    def __init__(self, default_delay_ms: int = 0):
        if default_delay_ms < 0:
            raise ThrottleError("default_delay_ms must be non-negative")
        self._default_delay_ms = default_delay_ms
        self._path_delays: Dict[str, int] = {}

    def set_path_delay(self, path_prefix: str, delay_ms: int) -> None:
        if delay_ms < 0:
            raise ThrottleError("delay_ms must be non-negative")
        if not path_prefix.startswith("/"):
            raise ThrottleError("path_prefix must start with '/'")
        self._path_delays[path_prefix] = delay_ms

    def remove_path_delay(self, path_prefix: str) -> None:
        if path_prefix not in self._path_delays:
            raise ThrottleError(f"No delay configured for path: {path_prefix}")
        del self._path_delays[path_prefix]

    def _resolve_delay(self, path: str) -> int:
        for prefix, delay in self._path_delays.items():
            if path.startswith(prefix):
                return delay
        return self._default_delay_ms

    def throttle(self, path: str, *, _sleep=time.sleep) -> ThrottleResult:
        delay_ms = self._resolve_delay(path)
        if delay_ms > 0:
            _sleep(delay_ms / 1000.0)
            return ThrottleResult(delayed=True, delay_ms=delay_ms, path=path)
        return ThrottleResult(delayed=False, delay_ms=0, path=path)

    def config(self) -> dict:
        return {
            "default_delay_ms": self._default_delay_ms,
            "path_delays": dict(self._path_delays),
        }
