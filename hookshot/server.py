"""Flask application for the hookshot webhook relay server."""

from flask import Flask, request, jsonify, abort
from hookshot.storage import RequestStore
from hookshot.models import WebhookRequest
from hookshot.replayer import Replayer, ReplayError
from hookshot.tagger import Tagger, TagError


def create_app(target_url=None, max_size=200):
    app = Flask(__name__)
    store = RequestStore(max_size=max_size)
    tagger = Tagger(store)
    replayer = Replayer(target_url=target_url)

    @app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    @app.route("/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    def catch_all(path):
        req = WebhookRequest(
            method=request.method,
            path="/" + path,
            query_string=request.query_string.decode("utf-8"),
            headers=dict(request.headers),
            body=request.get_data(),
        )
        store.save(req)
        return jsonify({"id": req.id, "status": "received"}), 200

    @app.route("/hookshot/requests", methods=["GET"])
    def list_requests():
        return jsonify([r.to_dict() for r in store.all()]), 200

    @app.route("/hookshot/requests/<request_id>", methods=["GET"])
    def get_request(request_id):
        req = store.get(request_id)
        if req is None:
            abort(404)
        return jsonify(req.to_dict()), 200

    @app.route("/hookshot/requests/<request_id>/replay", methods=["POST"])
    def replay_request(request_id):
        req = store.get(request_id)
        if req is None:
            abort(404)
        try:
            result = replayer.replay(req)
            return jsonify(result.to_dict()), 200
        except ReplayError as e:
            return jsonify({"error": str(e)}), 400

    @app.route("/hookshot/requests/<request_id>/tags", methods=["GET"])
    def get_tags(request_id):
        if store.get(request_id) is None:
            abort(404)
        return jsonify({"tags": tagger.get_tags(request_id)}), 200

    @app.route("/hookshot/requests/<request_id>/tags", methods=["POST"])
    def add_tag(request_id):
        data = request.get_json(silent=True) or {}
        tag = data.get("tag", "")
        try:
            tags = tagger.add_tag(request_id, tag)
            return jsonify({"tags": tags}), 200
        except TagError as e:
            return jsonify({"error": str(e)}), 400

    @app.route("/hookshot/requests/<request_id>/tags/<tag>", methods=["DELETE"])
    def remove_tag(request_id, tag):
        if store.get(request_id) is None:
            abort(404)
        tags = tagger.remove_tag(request_id, tag)
        return jsonify({"tags": tags}), 200

    return app
