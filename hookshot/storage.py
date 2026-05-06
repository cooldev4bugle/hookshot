"""In-memory storage for captured webhook requests."""

from collections import OrderedDict
from typing import List, Optional

from hookshot.models import WebhookRequest


class RequestStore:
    """Stores and retrieves webhook requests in memory."""

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._requests: OrderedDict[str, WebhookRequest] = OrderedDict()

    def save(self, request: WebhookRequest) -> WebhookRequest:
        """Save a request, evicting the oldest if over capacity."""
        if request.id in self._requests:
            self._requests.move_to_end(request.id)
        else:
            if len(self._requests) >= self.max_size:
                self._requests.popitem(last=False)
            self._requests[request.id] = request
        return request

    def get(self, request_id: str) -> Optional[WebhookRequest]:
        """Retrieve a request by ID, or None if not found."""
        return self._requests.get(request_id)

    def all(self) -> List[WebhookRequest]:
        """Return all stored requests, newest last."""
        return list(self._requests.values())

    def delete(self, request_id: str) -> bool:
        """Delete a request by ID. Returns True if it existed."""
        if request_id in self._requests:
            del self._requests[request_id]
            return True
        return False

    def clear(self) -> int:
        """Clear all stored requests. Returns the count removed."""
        count = len(self._requests)
        self._requests.clear()
        return count

    def __len__(self) -> int:
        return len(self._requests)
