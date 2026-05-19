"""Request pinner — mark specific requests as pinned so they survive store eviction."""

from __future__ import annotations

from typing import Set

from hookshot.storage import RequestStore


class PinError(Exception):
    pass


class Pinner:
    """Tracks which request IDs are pinned.

    Pinned requests are excluded from bulk-clear operations and
    can be listed independently for quick reference.
    """

    def __init__(self, store: RequestStore) -> None:
        if store is None:
            raise PinError("store is required")
        self._store = store
        self._pinned: Set[str] = set()

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def pin(self, request_id: str) -> None:
        """Mark *request_id* as pinned.  Raises PinError if not found."""
        if self._store.get(request_id) is None:
            raise PinError(f"request '{request_id}' not found")
        self._pinned.add(request_id)

    def unpin(self, request_id: str) -> None:
        """Remove pin from *request_id*.  Raises PinError if not pinned."""
        if request_id not in self._pinned:
            raise PinError(f"request '{request_id}' is not pinned")
        self._pinned.discard(request_id)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def is_pinned(self, request_id: str) -> bool:
        return request_id in self._pinned

    def pinned_ids(self) -> list[str]:
        """Return a stable-sorted list of currently pinned IDs."""
        return sorted(self._pinned)

    def pinned_requests(self) -> list:
        """Return the full WebhookRequest objects for all pinned IDs."""
        results = []
        for rid in self.pinned_ids():
            req = self._store.get(rid)
            if req is not None:
                results.append(req)
        return results

    def clear_unpinned(self) -> int:
        """Delete every request that is *not* pinned.  Returns count removed."""
        all_requests = self._store.all()
        removed = 0
        for req in all_requests:
            if req.id not in self._pinned:
                self._store.delete(req.id)
                removed += 1
        return removed
