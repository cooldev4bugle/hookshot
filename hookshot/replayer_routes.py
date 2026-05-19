from flask import Blueprint, jsonify, request as flask_request
from hookshot.replayer import Replayer, ReplayError
from hookshot.storage import RequestStore

_store: RequestStore | None = None
_replayer: Replayer | None = None

replayer_bp = Blueprint("replayer", __name__)


def init_replayer_routes(store: RequestStore, target_url: str) -> None:
    global _store, _replayer
    _store = store
    _replayer = Replayer(target_url=target_url)


def _get_store() -> RequestStore:
    if _store is None:
        raise RuntimeError("RequestStore not initialised")
    return _store


def _get_replayer() -> Replayer:
    if _replayer is None:
        raise RuntimeError("Replayer not initialised")
    return _replayer


@replayer_bp.route("/requests/<request_id>/replay", methods=["POST"])
def replay_request(request_id: str):
    store = _get_store()
    req = store.get(request_id)
    if req is None:
        return jsonify({"error": f"Request '{request_id}' not found"}), 404

    replayer = _get_replayer()
    try:
        result = replayer.replay(req)
    except ReplayError as exc:
        return jsonify({"error": str(exc)}), 502

    return jsonify(result.to_dict()), 200


@replayer_bp.route("/requests/replay-batch", methods=["POST"])
def replay_batch():
    body = flask_request.get_json(silent=True) or {}
    ids = body.get("ids", [])
    if not isinstance(ids, list) or not ids:
        return jsonify({"error": "'ids' must be a non-empty list"}), 400

    store = _get_store()
    replayer = _get_replayer()
    results = []
    for rid in ids:
        req = store.get(rid)
        if req is None:
            results.append({"id": rid, "error": "not found"})
            continue
        try:
            result = replayer.replay(req)
            entry = result.to_dict()
            entry["id"] = rid
            results.append(entry)
        except ReplayError as exc:
            results.append({"id": rid, "error": str(exc)})

    return jsonify(results), 200
