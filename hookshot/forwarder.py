import httpx
from typing import Optional
from hookshot.models import WebhookRequest


class ForwardError(Exception):
    """Raised when a forwarding attempt fails."""
    pass


class Forwarder:
    """Forwards webhook requests to a local target URL."""

    def __init__(self, target_url: str, timeout: float = 10.0):
        if not target_url:
            raise ValueError("target_url must not be empty")
        self.target_url = target_url.rstrip("/")
        self.timeout = timeout

    def forward(self, request: WebhookRequest) -> httpx.Response:
        """
        Replay a WebhookRequest to the configured target URL.

        Returns the httpx.Response on success.
        Raises ForwardError if the HTTP request itself fails (network error, etc.).
        """
        headers = dict(request.headers or {})
        # Strip hop-by-hop / host headers that shouldn't be forwarded as-is
        for h in ("host", "content-length", "transfer-encoding"):
            headers.pop(h, None)
            headers.pop(h.title(), None)

        url = self._build_url(request.path, request.query_string)

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method=request.method,
                    url=url,
                    content=request.body,
                    headers=headers,
                )
            return response
        except httpx.HTTPError as exc:
            raise ForwardError(f"Failed to forward request: {exc}") from exc

    def _build_url(self, path: str, query_string: Optional[str]) -> str:
        url = f"{self.target_url}{path or '/'}"
        if query_string:
            url = f"{url}?{query_string}"
        return url
