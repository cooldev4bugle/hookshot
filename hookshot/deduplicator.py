import hashlib
import json
from typing import List, Optional

from hookshot.models import WebhookRequest
from hookshot.storage import RequestStore


class DeduplicateError(Exception):
    pass


class Deduplicator:
    """Detects and optionally drops duplicate webhook requests based on body + path hash."""

    def __init__(self, store: RequestStore, window: int = 100):
        if window < 1:
            raise DeduplicateError("window must be at least 1")
        self._store = store
        self._window = window

    def _fingerprint(self, request: WebhookRequest) -> str:
        """Compute a hash fingerprint from method, path, and body."""
        payload = json.dumps({
            "method": request.method.upper(),
            "path": request.path,
            "body": request.body.hex() if request.body else "",
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def is_duplicate(self, request: WebhookRequest) -> bool:
        """Return True if a recent request with the same fingerprint exists."""
        target = self._fingerprint(request)
        recent = self._store.all()[-self._window:]
        for existing in recent:
            if existing.id == request.id:
                continue
            if self._fingerprint(existing) == target:
                return True
        return False

    def deduplicate(self, requests: List[WebhookRequest]) -> List[WebhookRequest]:
        """Return list with consecutive duplicates removed (keeps first occurrence)."""
        seen = set()
        result = []
        for req in requests:
            fp = self._fingerprint(req)
            if fp not in seen:
                seen.add(fp)
                result.append(req)
        return result

    def find_duplicates(self, request: WebhookRequest) -> List[WebhookRequest]:
        """Return all stored requests that are duplicates of the given request."""
        target = self._fingerprint(request)
        return [
            r for r in self._store.all()
            if r.id != request.id and self._fingerprint(r) == target
        ]
