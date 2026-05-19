"""Flask routes for the request scorer."""

from __future__ import annotations

from flask import Blueprint, jsonify, current_app

from hookshot.scorer import Scorer

_scorer = Scorer()
_bp = Blueprint("scorer", __name__)


def get_scorer() -> Scorer:
    return _scorer


def init_scorer_routes(app, store) -> None:
    """Register scorer routes on *app*, binding to *store*."""

    @_bp.route("/requests/<request_id>/score", methods=["GET"])
    def score_request(request_id: str):
        req = store.get(request_id)
        if req is None:
            return jsonify({"error": "not found"}), 404
        result = get_scorer().score(req)
        return jsonify(result.to_dict()), 200

    @_bp.route("/requests/scores", methods=["GET"])
    def score_all():
        scorer = get_scorer()
        results = [scorer.score(r).to_dict() for r in store.all()]
        return jsonify(results), 200

    app.register_blueprint(_bp)
