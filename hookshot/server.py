"""Flask application factory and route definitions."""
from flask import Flask, request, jsonify, abort, Response
from hookshot.storage import RequestStore
from hookshot.models import WebhookRequest
from hookshot.replayer import Replayer, ReplayError
from hookshot.filter import RequestFilter
from hookshot.exporter import Exporter, ExportError


def create_app(store: RequestStore = None, target_url: str = None) -> Flask:
    app = Flask(__name__)
    app.config["store"] = store or RequestStore()
    app.config["target_url"] = target_url

    @app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT",
                                                    "PATCH", "DELETE", "OPTIONS"])
    @app.route("/<path:path>", methods=["GET", "POST", "PUT",
                                        "PATCH", "DELETE", "OPTIONS"])
    def catch_all(path):
        if request.path.startswith("/__hookshot"):
            abort(404)
        req = WebhookRequest(
            method=request.method,
            path="/" + path,
            query_string=request.query_string.decode("utf-8"),
            headers=dict(request.headers),
            body=request.get_data(),
        )
        app.config["store"].save(req)
        return jsonify({"id": req.id, "status": "received"}), 200

    @app.route("/__hookshot/requests", methods=["GET"])
    def list_requests():
        store = app.config["store"]
        reqs = store.all()
        f = RequestFilter(reqs)
        if method := request.args.get("method"):
            f = f.by_method(method)
        if path := request.args.get("path"):
            f = f.by_path(path)
        return jsonify([r.to_dict() for r in f.results()])

    @app.route("/__hookshot/requests/<req_id>", methods=["GET"])
    def get_request(req_id):
        req = app.config["store"].get(req_id)
        if req is None:
            abort(404)
        return jsonify(req.to_dict())

    @app.route("/__hookshot/requests/<req_id>/replay", methods=["POST"])
    def replay_request(req_id):
        req = app.config["store"].get(req_id)
        if req is None:
            abort(404)
        target = app.config.get("target_url")
        if not target:
            return jsonify({"error": "No target URL configured"}), 400
        replayer = Replayer(target_url=target)
        try:
            result = replayer.replay(req)
            return jsonify(result.to_dict())
        except ReplayError as e:
            return jsonify({"error": str(e)}), 502

    @app.route("/__hookshot/export", methods=["GET"])
    def export_requests():
        fmt = request.args.get("format", "json")
        reqs = app.config["store"].all()
        exporter = Exporter(reqs)
        try:
            content = exporter.export(fmt)
        except ExportError as e:
            return jsonify({"error": str(e)}), 400
        mime = "text/csv" if fmt == "csv" else "application/json"
        return Response(content, mimetype=mime)

    return app
