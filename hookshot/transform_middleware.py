"""WSGI-level middleware that applies transformer to outgoing forwarded requests.

This module provides a helper used by the Forwarder to optionally run
a Transformer over headers and body before the HTTP call is made.
"""

from typing import Dict, Optional, Tuple

from hookshot.transformer import Transformer
from hookshot.models import WebhookRequest


def apply_transform(
    transformer: Optional[Transformer],
    request: WebhookRequest,
    context: Optional[Dict] = None,
) -> Tuple[bytes, Dict[str, str]]:
    """Return (body, headers) after applying transformer, or originals if None."""
    raw_headers = dict(request.headers) if request.headers else {}
    raw_body = request.body if request.body else b""

    if transformer is None:
        return raw_body, raw_headers

    transformed_headers = transformer.apply_headers(raw_headers)
    transformed_body = transformer.apply_body(raw_body, context=context)
    return transformed_body, transformed_headers


def build_forward_kwargs(
    transformer: Optional[Transformer],
    request: WebhookRequest,
    context: Optional[Dict] = None,
) -> Dict:
    """Build kwargs dict suitable for passing to requests.request()."""
    body, headers = apply_transform(transformer, request, context)
    return {
        "method": request.method,
        "headers": headers,
        "data": body,
        "params": request.query_string or "",
        "allow_redirects": True,
        "timeout": 10,
    }
