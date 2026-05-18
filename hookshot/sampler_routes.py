"""HTTP routes for inspecting and configuring the request sampler."""

from flask import Blueprint, jsonify, request
from hookshot.sampler import Sampler, SampleError

_sampler = Sampler(rate=1.0)

sampler_bp = Blueprint("sampler", __name__)


def get_sampler() -> Sampler:
    return _sampler


def init_sampler_routes(app, sampler: Sampler = None):
    global _sampler
    if sampler is not None:
        _sampler = sampler
    app.register_blueprint(sampler_bp, url_prefix="/sampler")


@sampler_bp.route("/config", methods=["GET"])
def get_config():
    return jsonify({"rate": _sampler.rate})


@sampler_bp.route("/config", methods=["PUT"])
def set_config():
    data = request.get_json(silent=True) or {}
    rate = data.get("rate")
    if rate is None:
        return jsonify({"error": "rate is required"}), 400
    try:
        _sampler.set_rate(float(rate))
    except (SampleError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"rate": _sampler.rate})


@sampler_bp.route("/stats", methods=["GET"])
def get_stats():
    return jsonify(_sampler.stats())


@sampler_bp.route("/stats", methods=["DELETE"])
def reset_stats():
    _sampler.reset_stats()
    return jsonify({"ok": True})
