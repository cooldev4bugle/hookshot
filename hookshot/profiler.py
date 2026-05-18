"""Request profiler: tracks timing and size metrics for incoming requests."""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class ProfileError(Exception):
    pass


@dataclass
class ProfileEntry:
    request_id: str
    method: str
    path: str
    body_size: int
    header_count: int
    received_at: float
    processed_at: float

    @property
    def latency_ms(self) -> float:
        return round((self.processed_at - self.received_at) * 1000, 3)

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "method": self.method,
            "path": self.path,
            "body_size": self.body_size,
            "header_count": self.header_count,
            "latency_ms": self.latency_ms,
            "received_at": self.received_at,
            "processed_at": self.processed_at,
        }


class Profiler:
    def __init__(self, max_entries: int = 500):
        if max_entries < 1:
            raise ProfileError("max_entries must be at least 1")
        self._max_entries = max_entries
        self._entries: List[ProfileEntry] = []

    def record(self, request) -> ProfileEntry:
        """Profile a WebhookRequest and store the entry."""
        body = request.body or b""
        entry = ProfileEntry(
            request_id=request.id,
            method=request.method,
            path=request.path,
            body_size=len(body),
            header_count=len(request.headers),
            received_at=request.received_at,
            processed_at=time.time(),
        )
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries.pop(0)
        return entry

    def get(self, request_id: str) -> Optional[ProfileEntry]:
        for e in self._entries:
            if e.request_id == request_id:
                return e
        return None

    def all(self) -> List[ProfileEntry]:
        return list(self._entries)

    def summary(self) -> Dict:
        if not self._entries:
            return {"count": 0, "avg_latency_ms": 0.0, "avg_body_size": 0.0}
        latencies = [e.latency_ms for e in self._entries]
        sizes = [e.body_size for e in self._entries]
        return {
            "count": len(self._entries),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 3),
            "avg_body_size": round(sum(sizes) / len(sizes), 2),
        }

    def clear(self) -> None:
        self._entries.clear()
