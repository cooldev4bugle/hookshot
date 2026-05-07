"""Core data models for storing and inspecting webhook requests."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class WebhookRequest:
    """Represents a captured incoming webhook request."""

    method: str
    path: str
    headers: dict[str, str]
    body: bytes
    query_params: dict[str, str] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    received_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def body_text(self) -> str:
        """Decode body as UTF-8 text, replacing undecodable bytes."""
        return self.body.decode("utf-8", errors="replace")

    @property
    def content_type(self) -> str | None:
        """Return the Content-Type header value, case-insensitively, or None if absent."""
        for key, value in self.headers.items():
            if key.lower() == "content-type":
                return value
        return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the request to a JSON-friendly dictionary."""
        return {
            "id": self.id,
            "received_at": self.received_at.isoformat(),
            "method": self.method,
            "path": self.path,
            "query_params": self.query_params,
            "headers": self.headers,
            "body": self.body_text,
            "content_length": len(self.body),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WebhookRequest":
        """Reconstruct a WebhookRequest from a serialized dictionary."""
        return cls(
            id=data["id"],
            received_at=datetime.fromisoformat(data["received_at"]),
            method=data["method"],
            path=data["path"],
            query_params=data.get("query_params", {}),
            headers=data["headers"],
            body=data["body"].encode("utf-8"),
        )
