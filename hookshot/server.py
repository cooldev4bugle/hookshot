from flask import Flask, request, jsonify, abort
from hookshot.storage import RequestStore
from hookshot.models import WebhookRequest
from hookshot.forwarder import Forwarder, ForwardError
from hookshot.replayer import Replayer, ReplayError


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

        if target_url:
            try:
                forwarder = Forwarder(target_url=target_url)
                forwarder.forward(req)
            except ForwardError:
                pass

        return jsonify({"id": req.id, "status": "received"}), 200

    @app.route("/_hookshot/requests", methods=["GET"])
    def list_requests():
        return jsonify([r.to_dict() for r in store.all()])

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
            return jsonify(result.to_dict()), 200
        except ReplayError as e:
            return jsonify({"error": str(e)}), 502

    return app
