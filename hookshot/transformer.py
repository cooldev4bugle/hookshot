"""Request body and header transformation utilities."""

import json
from typing import Any, Dict, Optional


class TransformError(Exception):
    pass


class Transformer:
    """Apply transformations to a webhook request before forwarding."""

    def __init__(self):
        self._header_overrides: Dict[str, str] = {}
        self._header_removals: set = set()
        self._body_template: Optional[str] = None

    def set_header(self, name: str, value: str) -> "Transformer":
        if not name or not isinstance(name, str):
            raise TransformError("Header name must be a non-empty string")
        self._header_overrides[name.lower()] = value
        return self

    def remove_header(self, name: str) -> "Transformer":
        if not name or not isinstance(name, str):
            raise TransformError("Header name must be a non-empty string")
        self._header_removals.add(name.lower())
        return self

    def set_body_template(self, template: str) -> "Transformer":
        """Set a JSON template string with {field} placeholders."""
        if not isinstance(template, str):
            raise TransformError("Template must be a string")
        self._body_template = template
        return self

    def apply_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Return a new headers dict with overrides and removals applied."""
        result = {}
        for k, v in headers.items():
            if k.lower() in self._header_removals:
                continue
            result[k] = v
        for k, v in self._header_overrides.items():
            result[k] = v
        return result

    def apply_body(self, body: bytes, context: Optional[Dict[str, Any]] = None) -> bytes:
        """Apply body template substitution if configured."""
        if self._body_template is None:
            return body
        ctx = context or {}
        try:
            rendered = self._body_template.format(**ctx)
            return rendered.encode("utf-8")
        except KeyError as e:
            raise TransformError(f"Missing template variable: {e}") from e
        except Exception as e:
            raise TransformError(f"Template rendering failed: {e}") from e

    def to_dict(self) -> Dict[str, Any]:
        return {
            "header_overrides": self._header_overrides,
            "header_removals": list(self._header_removals),
            "body_template": self._body_template,
        }
