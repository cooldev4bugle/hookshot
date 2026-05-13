"""Simple webhook notification module — fires a callback URL when a request is received."""

import requests as http
from dataclasses import dataclass, field
from typing import Optional


class NotifyError(Exception):
    pass


@dataclass
class NotifyResult:
    success: bool
    status_code: Optional[int] = None
    error: Optional[str] = None

    def to_dict(self):
        return {
            "success": self.success,
            "status_code": self.status_code,
            "error": self.error,
        }


class Notifier:
    """Sends a JSON payload to a callback URL whenever a webhook is received."""

    def __init__(self, callback_url: str, timeout: int = 5):
        if not callback_url or not callback_url.startswith(("http://", "https://")):
            raise NotifyError("callback_url must be a valid http/https URL")
        self.callback_url = callback_url
        self.timeout = timeout

    def notify(self, webhook_request) -> NotifyResult:
        """POST a summary of the received webhook to the callback URL."""
        payload = {
            "event": "webhook.received",
            "request_id": webhook_request.id,
            "method": webhook_request.method,
            "path": webhook_request.path,
            "received_at": webhook_request.received_at.isoformat(),
        }
        try:
            resp = http.post(
                self.callback_url,
                json=payload,
                timeout=self.timeout,
            )
            return NotifyResult(success=resp.ok, status_code=resp.status_code)
        except http.exceptions.RequestException as exc:
            return NotifyResult(success=False, error=str(exc))
