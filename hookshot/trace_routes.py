"""Flask routes exposing tracer state for the inspection UI."""

from flask import Blueprint, jsonify, current_app

from hookshot.tracer import Tracer

_tracer: Tracer = Tracer()

trace_bp = Blueprint("traces", __name__)


def get_tracer() -> Tracer:
    return _tracer


def init_trace_routes(app, tracer: Tracer | None = None) -> None:
    global _tracer
    if tracer is not None:
        _tracer = tracer
    app.register_blueprint(trace_bp)


@trace_bp.route("/traces", methods=["GET"])
def list_traces():
    """Return all recorded traces."""
    return jsonify([e.to_dict() for e in _tracer.all()])


@trace_bp.route("/traces/<trace_id>", methods=["GET"])
def get_trace(trace_id: str):
    """Return a single trace by ID."""
    entry = _tracer.get(trace_id)
    if entry is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(entry.to_dict())


@trace_bp.route("/traces", methods=["DELETE"])
def clear_traces():
    """Clear all traces (useful for testing)."""
    _tracer.clear()
    return jsonify({"cleared": True})
