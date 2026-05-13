"""Redact sensitive header and body fields from webhook requests."""

import json
import re
from typing import List, Optional

DEFAULT_HEADERS = {"authorization", "x-api-key", "x-secret", "cookie", "set-cookie"}
DEFAULT_BODY_KEYS = {"password", "secret", "token", "api_key", "apikey", "access_token"}
REDACTED = "[REDACTED]"


class RedactError(Exception):
    pass


class Redactor:
    def __init__(
        self,
        sensitive_headers: Optional[List[str]] = None,
        sensitive_body_keys: Optional[List[str]] = None,
    ):
        self.sensitive_headers = {
            h.lower() for h in (sensitive_headers or DEFAULT_HEADERS)
        }
        self.sensitive_body_keys = {
            k.lower() for k in (sensitive_body_keys or DEFAULT_BODY_KEYS)
        }

    def redact_headers(self, headers: dict) -> dict:
        """Return a copy of headers with sensitive values replaced."""
        return {
            k: (REDACTED if k.lower() in self.sensitive_headers else v)
            for k, v in headers.items()
        }

    def redact_body(self, body: bytes, content_type: str = "") -> bytes:
        """Return body with sensitive JSON fields redacted, if applicable."""
        if "application/json" not in content_type:
            return body
        try:
            data = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return body
        redacted = self._redact_dict(data)
        return json.dumps(redacted).encode()

    def _redact_dict(self, obj):
        if isinstance(obj, dict):
            return {
                k: (REDACTED if k.lower() in self.sensitive_body_keys else self._redact_dict(v))
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [self._redact_dict(item) for item in obj]
        return obj

    def redact_request(self, request) -> dict:
        """Return a redacted dict representation of a WebhookRequest."""
        d = request.to_dict()
        d["headers"] = self.redact_headers(d.get("headers", {}))
        ct = request.content_type or ""
        redacted_body = self.redact_body(request.body or b"", ct)
        try:
            d["body"] = redacted_body.decode("utf-8", errors="replace")
        except Exception:
            d["body"] = REDACTED
        return d
