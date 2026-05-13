"""Flask routes for the scheduler feature."""

from flask import Blueprint, jsonify, request, current_app
from hookshot.scheduler import ScheduleError

scheduler_bp = Blueprint("scheduler", __name__)


def _scheduler():
    return current_app.config["scheduler"]


def _replayer():
    return current_app.config["replayer"]


def _store():
    return current_app.config["store"]


@scheduler_bp.post("/schedule")
def create_schedule():
    data = request.get_json(force=True, silent=True) or {}
    request_id = data.get("request_id")
    interval = data.get("interval")

    if not request_id:
        return jsonify({"error": "request_id is required"}), 400
    if interval is None:
        return jsonify({"error": "interval is required"}), 400

    stored = _store().get(request_id)
    if stored is None:
        return jsonify({"error": f"request {request_id!r} not found"}), 404

    replayer = _replayer()

    def do_replay(rid):
        req = _store().get(rid)
        if req is None:
            raise RuntimeError(f"request {rid!r} disappeared from store")
        replayer.replay(req)

    try:
        job = _scheduler().schedule(request_id, float(interval), do_replay)
    except ScheduleError as exc:
        return jsonify({"error": str(exc)}), 409
    except (TypeError, ValueError):
        return jsonify({"error": "interval must be a positive number"}), 400

    return jsonify(job.to_dict()), 201


@scheduler_bp.delete("/schedule/<request_id>")
def cancel_schedule(request_id: str):
    try:
        _scheduler().cancel(request_id)
    except ScheduleError as exc:
        return jsonify({"error": str(exc)}), 404
    return jsonify({"cancelled": request_id}), 200


@scheduler_bp.get("/schedule")
def list_schedules():
    return jsonify(_scheduler().list_jobs()), 200
