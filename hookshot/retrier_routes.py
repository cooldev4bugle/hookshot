from flask import Blueprint, jsonify, request as flask_request
from hookshot.retrier import Retrier, RetryError
from hookshot.replayer import Replayer
from hookshot.storage import RequestStore

_store: RequestStore | None = None
_retrier: Retrier | None = None


def init_retrier_routes(store: RequestStore, target_url: str,
                        max_attempts: int = 3, backoff: float = 1.0) -> Blueprint:
    global _store, _retrier
    _store = store
    replayer = Replayer(target_url=target_url)
    _retrier = Retrier(replayer=replayer, max_attempts=max_attempts, backoff=backoff)

    bp = Blueprint("retrier", __name__)

    @bp.route("/requests/<request_id>/retry", methods=["POST"])
    def retry_request(request_id):
        req = _store.get(request_id)
        if req is None:
            return jsonify({"error": "request not found"}), 404

        body = flask_request.get_json(silent=True) or {}
        attempts = int(body.get("max_attempts", _retrier.max_attempts))
        backoff = float(body.get("backoff", _retrier.backoff))

        try:
            local_retrier = Retrier(
                replayer=replayer, max_attempts=attempts, backoff=backoff
            )
        except RetryError as exc:
            return jsonify({"error": str(exc)}), 400

        result = local_retrier.retry(req)
        status = 200 if result.succeeded else 502
        return jsonify(result.to_dict()), status

    @bp.route("/retrier/config", methods=["GET"])
    def get_config():
        return jsonify({
            "max_attempts": _retrier.max_attempts,
            "backoff": _retrier.backoff,
        })

    return bp
