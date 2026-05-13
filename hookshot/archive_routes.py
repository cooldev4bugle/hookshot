"""HTTP routes for triggering archive save/load operations."""

from flask import Blueprint, jsonify, request, current_app

from hookshot.archiver import Archiver, ArchiveError
from hookshot.storage import RequestStore

bp = Blueprint("archive", __name__)

_store: RequestStore = None  # type: ignore
_archiver: Archiver = None  # type: ignore


def init_archive_routes(store: RequestStore, archive_path: str) -> None:
    """Initialise module-level singletons (call once at app startup)."""
    global _store, _archiver
    _store = store
    _archiver = Archiver(store, archive_path)


@bp.route("/archive/save", methods=["POST"])
def save_archive():
    """Persist all in-memory requests to the archive file."""
    if _archiver is None:
        return jsonify({"error": "archiver not initialised"}), 503
    try:
        count = _archiver.save()
        return jsonify({"saved": count}), 200
    except ArchiveError as exc:
        return jsonify({"error": str(exc)}), 500


@bp.route("/archive/load", methods=["POST"])
def load_archive():
    """Load requests from the archive file into memory."""
    if _archiver is None:
        return jsonify({"error": "archiver not initialised"}), 503
    try:
        count = _archiver.load()
        return jsonify({"loaded": count}), 200
    except ArchiveError as exc:
        return jsonify({"error": str(exc)}), 500


@bp.route("/archive/clear", methods=["DELETE"])
def clear_archive():
    """Delete the archive file from disk."""
    if _archiver is None:
        return jsonify({"error": "archiver not initialised"}), 503
    try:
        _archiver.clear()
        return jsonify({"cleared": True}), 200
    except ArchiveError as exc:
        return jsonify({"error": str(exc)}), 500
