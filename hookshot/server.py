"""Flask application for the hookshot webhook relay server."""

from flask import Flask, request, jsonify, abort
from hookshot.models import WebhookRequest
from hookshot.storage import RequestStore
from hookshot.replayer import Replayer, ReplayError
from hookshot.filter import RequestFilter


def create_app(store: RequestStore, target_url: str = None) -> Flask:
    app = Flask(__name__)
    app.config["store"] = store
    app.config["target_url"] = target_url

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

    @app.route("/_hookshot/requests", methods=["GET"])
    def list_requests():
        method = request.args.get("method")
        path_prefix = request.args.get("path")
        content_type = request.args.get("content_type")
        limit = request.args.get("limit", type=int)

        f = RequestFilter(store.all())
        if method:
            f = f.by_method(method)
        if path_prefix:
            f = f.by_path(path_prefix)
        if content_type:
            f = f.by_content_type(content_type)
        if limit:
            f = f.limit(limit)

        return jsonify([r.to_dict() for r in f.results()])

    @app.route("/_hookshot/requests/<request_id>", methods=["GET"])
    def get_request(request_id):
        req = store.get(request_id)
        if req is None:
            abort(404)
        return jsonify(req.to_dict())

    @app.route("/_hookshot/requests/<request_id>/replay", methods=["POST"])
    def replay_request(request_id):
        req = store.get(request_id)
        if req is None:
            abort(404)
        url = app.config.get("target_url")
        if not url:
            return jsonify({"error": "No target URL configured"}), 400
        try:
            replayer = Replayer(target_url=url)
            result = replayer.replay(req)
            return jsonify(result.to_dict())
        except ReplayError as e:
            return jsonify({"error": str(e)}), 502

    return app
