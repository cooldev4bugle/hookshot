"""HTTP routes for managing labeling rules and labeling stored requests."""

from flask import Blueprint, jsonify, request, current_app
from hookshot.labeler import Labeler, LabelError

_labeler: Labeler = Labeler()


def get_labeler() -> Labeler:
    return _labeler


def init_labeler_routes(app, store) -> Blueprint:
    bp = Blueprint("labeler", __name__)

    @bp.get("/labeler/rules")
    def list_rules():
        return jsonify(_labeler.rules())

    @bp.post("/labeler/rules")
    def add_rule():
        data = request.get_json(force=True, silent=True) or {}
        label = data.get("label", "")
        method = data.get("method")
        path_prefix = data.get("path_prefix")
        header_key = data.get("header_key")
        description = data.get("description", "")

        def predicate(req):
            if method and req.method.upper() != method.upper():
                return False
            if path_prefix and not req.path.startswith(path_prefix):
                return False
            if header_key and header_key.lower() not in req.headers:
                return False
            return True

        try:
            _labeler.add_rule(label, predicate, description)
        except LabelError as exc:
            return jsonify({"error": str(exc)}), 400

        return jsonify({"label": label, "description": description}), 201

    @bp.delete("/labeler/rules/<label>")
    def delete_rule(label):
        try:
            _labeler.remove_rule(label)
        except LabelError as exc:
            return jsonify({"error": str(exc)}), 404
        return "", 204

    @bp.get("/labeler/label/<request_id>")
    def label_request(request_id):
        req = store.get(request_id)
        if req is None:
            return jsonify({"error": "Request not found"}), 404
        labels = _labeler.label(req)
        return jsonify({"id": request_id, "labels": labels})

    @bp.delete("/labeler/rules")
    def clear_rules():
        _labeler.clear()
        return "", 204

    app.register_blueprint(bp)
    return bp
