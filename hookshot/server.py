import uuid
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from hookshot.models import WebhookRequest
from hookshot.storage import RequestStore
from hookshot.forwarder import Forwarder, ForwardError


def create_app(target_url=None, store=None):
    app = Flask(__name__)
    app.config["TARGET_URL"] = target_url

    if store is None:
        store = RequestStore()
    app.extensions["store"] = store

    forwarder = Forwarder(target_url) if target_url else None

    @app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    @app.route("/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    def catch_all(path):
        incoming = WebhookRequest(
            method=request.method,
            path="/" + path if path else "/",
            headers=dict(request.headers),
            body=request.get_data(),
            query_string=request.query_string.decode("utf-8"),
        )
        store.save(incoming)

        forward_status = None
        forward_error = None
        if forwarder:
            try:
                resp = forwarder.forward(incoming)
                forward_status = resp.status_code
            except ForwardError as e:
                forward_error = str(e)

        result = {"id": incoming.id, "status": "received"}
        if forward_status is not None:
            result["forwarded_status"] = forward_status
        if forward_error is not None:
            result["forward_error"] = forward_error
        return jsonify(result), 200

    @app.route("/_hookshot/requests", methods=["GET"])
    def list_requests():
        return jsonify([r.to_dict() for r in store.all()])

    @app.route("/_hookshot/requests/<request_id>", methods=["GET"])
    def get_request(request_id):
        req = store.get(request_id)
        if req is None:
            return jsonify({"error": "not found"}), 404
        return jsonify(req.to_dict())

    return app
