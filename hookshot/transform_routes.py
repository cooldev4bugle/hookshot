"""Flask routes exposing transformer configuration per-session."""

from flask import Blueprint, jsonify, request

from hookshot.transformer import Transformer, TransformError

bp = Blueprint("transform", __name__)

# Single shared transformer instance (could be swapped for per-session later)
_transformer = Transformer()


def get_transformer() -> Transformer:
    return _transformer


@bp.route("/transform/headers", methods=["POST"])
def set_header():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "")
    value = data.get("value", "")
    try:
        _transformer.set_header(name, value)
    except TransformError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"status": "ok", "header": name, "value": value}), 200


@bp.route("/transform/headers/<name>", methods=["DELETE"])
def remove_header(name: str):
    try:
        _transformer.remove_header(name)
    except TransformError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"status": "ok", "removed": name}), 200


@bp.route("/transform/body", methods=["POST"])
def set_body_template():
    data = request.get_json(silent=True) or {}
    template = data.get("template")
    if template is None:
        return jsonify({"error": "'template' field required"}), 400
    try:
        _transformer.set_body_template(template)
    except TransformError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"status": "ok"}), 200


@bp.route("/transform", methods=["GET"])
def get_config():
    return jsonify(_transformer.to_dict()), 200


@bp.route("/transform/reset", methods=["POST"])
def reset():
    global _transformer
    _transformer = Transformer()
    return jsonify({"status": "reset"}), 200
