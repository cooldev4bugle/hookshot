"""Request correlator — group requests by a shared correlation ID header."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional

from hookshot.models import WebhookRequest
from hookshot.storage import RequestStore


class CorrelateError(Exception):
    pass


class Correlator:
    """Groups stored requests by a correlation header value."""

    DEFAULT_HEADER = "x-correlation-id"

    def __init__(self, store: RequestStore, header: str = DEFAULT_HEADER) -> None:
        if not header or not isinstance(header, str):
            raise CorrelateError("header name must be a non-empty string")
        self._store = store
        self._header = header.lower()

    def group(self) -> Dict[str, List[WebhookRequest]]:
        """Return a dict mapping correlation ID -> list of requests."""
        groups: Dict[str, List[WebhookRequest]] = defaultdict(list)
        for req in self._store.all():
            cid = self._get_cid(req)
            if cid:
                groups[cid].append(req)
        return dict(groups)

    def get_group(self, correlation_id: str) -> List[WebhookRequest]:
        """Return all requests that share the given correlation ID."""
        if not correlation_id:
            raise CorrelateError("correlation_id must be a non-empty string")
        return [
            req
            for req in self._store.all()
            if self._get_cid(req) == correlation_id
        ]

    def correlation_ids(self) -> List[str]:
        """Return a sorted list of distinct correlation IDs seen so far."""
        ids = set()
        for req in self._store.all():
            cid = self._get_cid(req)
            if cid:
                ids.add(cid)
        return sorted(ids)

    def _get_cid(self, req: WebhookRequest) -> Optional[str]:
        headers = {k.lower(): v for k, v in (req.headers or {}).items()}
        return headers.get(self._header)
