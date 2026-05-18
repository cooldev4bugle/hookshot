"""HTTP routes for request comparison."""

from flask import Blueprint, jsonify, request
from hookshot.comparator import Comparator, CompareError
from hookshot.storage import RequestStore

_bp = Blueprint("compare", __name__)
_store: RequestStore = None


def init_compare_routes(app, store: RequestStore):
    global _store
    _store = store
    app.register_blueprint(_bp)


def _get_comparator():
    return Comparator(_store)


@_bp.route("/compare", methods=["POST"])
def compare_requests():
    data = request.get_json(silent=True) or {}
    left_id = data.get("left_id")
    right_id = data.get("right_id")

    if not left_id:
        return jsonify({"error": "left_id is required"}), 400
    if not right_id:
        return jsonify({"error": "right_id is required"}), 400

    try:
        result = _get_comparator().compare(left_id, right_id)
        return jsonify(result.to_dict()), 200
    except CompareError as exc:
        return jsonify({"error": str(exc)}), 404


@_bp.route("/compare", methods=["GET"])
def compare_via_query():
    left_id = request.args.get("left_id")
    right_id = request.args.get("right_id")

    if not left_id:
        return jsonify({"error": "left_id is required"}), 400
    if not right_id:
        return jsonify({"error": "right_id is required"}), 400

    try:
        result = _get_comparator().compare(left_id, right_id)
        return jsonify(result.to_dict()), 200
    except CompareError as exc:
        return jsonify({"error": str(exc)}), 404
