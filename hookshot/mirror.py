"""Mirror mode: echo back request details as the response body."""

import json
from hookshot.models import WebhookRequest


class MirrorError(Exception):
    pass


class Mirror:
    """Reflects incoming request details back to the caller as JSON."""

    def __init__(self, include_body: bool = True, include_headers: bool = True):
        self.include_body = include_body
        self.include_headers = include_headers

    def reflect(self, request: WebhookRequest) -> dict:
        """Build a mirror response dict from a WebhookRequest."""
        if request is None:
            raise MirrorError("request must not be None")

        result = {
            "id": request.id,
            "method": request.method,
            "path": request.path,
            "received_at": request.received_at.isoformat(),
        }

        if request.query_string:
            result["query_string"] = request.query_string

        if self.include_headers:
            result["headers"] = dict(request.headers)

        if self.include_body:
            if request.is_json:
                try:
                    result["body"] = json.loads(request.body_text)
                except (ValueError, TypeError):
                    result["body"] = request.body_text
            else:
                result["body"] = request.body_text

        return result

    def to_json(self, request: WebhookRequest) -> str:
        """Return mirror response as a JSON string."""
        return json.dumps(self.reflect(request), indent=2)
