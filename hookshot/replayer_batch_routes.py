"""Batch replay routes with filtering and result aggregation."""

from flask import Blueprint, jsonify, request

from hookshot.filter import RequestFilter
from hookshot.replayer import Replayer, ReplayError
from hookshot.storage import RequestStore

_store: RequestStore | None = None
_replayer: Replayer | None = None

batch_bp = Blueprint("batch_replay", __name__)


def init_batch_replay_routes(app, store: RequestStore, replayer: Replayer) -> None:
    global _store, _replayer
    _store = store
    _replayer = replayer
    app.register_blueprint(batch_bp)


@batch_bp.route("/replay/batch", methods=["POST"])
def replay_batch_filtered():
    """Replay multiple requests with optional method/path filters."""
    data = request.get_json(silent=True) or {}

    method = data.get("method")
    path_prefix = data.get("path_prefix")
    limit = data.get("limit", 50)

    if not isinstance(limit, int) or limit < 1 or limit > 200:
        return jsonify({"error": "limit must be an integer between 1 and 200"}), 400

    all_requests = _store.all()
    f = RequestFilter(all_requests)

    if method:
        f = f.by_method(method)
    if path_prefix:
        f = f.by_path(path_prefix)

    candidates = f.results()[:limit]

    results = []
    for req in candidates:
        try:
            result = _replayer.replay(req)
            results.append({"id": req.id, "success": result.success, "status_code": result.status_code})
        except ReplayError as exc:
            results.append({"id": req.id, "success": False, "error": str(exc)})

    total = len(results)
    succeeded = sum(1 for r in results if r["success"])
    failed = total - succeeded

    return jsonify({
        "total": total,
        "succeeded": succeeded,
        "failed": failed,
        "results": results,
    }), 200


@batch_bp.route("/replay/batch/dry-run", methods=["POST"])
def dry_run_batch():
    """Return which requests would be replayed without actually replaying them."""
    data = request.get_json(silent=True) or {}

    method = data.get("method")
    path_prefix = data.get("path_prefix")
    limit = data.get("limit", 50)

    if not isinstance(limit, int) or limit < 1 or limit > 200:
        return jsonify({"error": "limit must be an integer between 1 and 200"}), 400

    all_requests = _store.all()
    f = RequestFilter(all_requests)

    if method:
        f = f.by_method(method)
    if path_prefix:
        f = f.by_path(path_prefix)

    candidates = f.results()[:limit]

    return jsonify({
        "would_replay": [req.id for req in candidates],
        "count": len(candidates),
    }), 200
