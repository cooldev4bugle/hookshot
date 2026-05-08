"""Filter and search webhook requests by various criteria."""

from typing import List, Optional
from hookshot.models import WebhookRequest


class RequestFilter:
    """Filter a list of WebhookRequests based on search criteria."""

    def __init__(self, requests: List[WebhookRequest]):
        self._requests = requests

    def by_method(self, method: str) -> "RequestFilter":
        """Keep only requests matching the given HTTP method."""
        method = method.upper()
        return RequestFilter(
            [r for r in self._requests if r.method.upper() == method]
        )

    def by_path(self, path: str) -> "RequestFilter":
        """Keep only requests whose path starts with the given prefix."""
        return RequestFilter(
            [r for r in self._requests if r.path.startswith(path)]
        )

    def by_header(self, name: str, value: Optional[str] = None) -> "RequestFilter":
        """Keep requests that have a specific header, optionally matching value."""
        name_lower = name.lower()
        filtered = []
        for r in self._requests:
            headers_lower = {k.lower(): v for k, v in r.headers.items()}
            if name_lower in headers_lower:
                if value is None or headers_lower[name_lower] == value:
                    filtered.append(r)
        return RequestFilter(filtered)

    def by_content_type(self, content_type: str) -> "RequestFilter":
        """Keep requests whose Content-Type contains the given string."""
        return RequestFilter(
            [r for r in self._requests if content_type.lower() in r.content_type.lower()]
        )

    def limit(self, n: int) -> "RequestFilter":
        """Keep only the most recent n requests."""
        return RequestFilter(self._requests[-n:])

    def results(self) -> List[WebhookRequest]:
        """Return the filtered list of requests."""
        return list(self._requests)

    def __len__(self) -> int:
        return len(self._requests)
