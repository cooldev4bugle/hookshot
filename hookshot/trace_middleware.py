"""WSGI middleware that auto-starts a trace for every incoming request
and injects the trace ID into the Flask request context."""

from __future__ import annotations

from typing import Callable

from flask import Flask, g, request as flask_request

from hookshot.tracer import Tracer


def attach_tracer(app: Flask, tracer: Tracer) -> None:
    """Register before/teardown hooks on *app* to manage trace lifecycle."""

    @app.before_request
    def _start_trace() -> None:
        incoming_headers = {k.lower(): v for k, v in flask_request.headers.items()}
        # request_id may be set earlier by another middleware; fall back to path
        request_id = getattr(g, "request_id", None) or flask_request.path
        entry = tracer.start_trace(request_id, incoming_headers)
        g.trace_entry = entry

    @app.after_request
    def _inject_trace_header(response):
        entry = getattr(g, "trace_entry", None)
        if entry is not None:
            response.headers["x-hookshot-trace-id"] = entry.trace_id
        return response


def build_trace_headers(tracer: Tracer, trace_id: str) -> dict:
    """Convenience wrapper: return headers to forward with an outbound request."""
    return tracer.inject_header(trace_id)
