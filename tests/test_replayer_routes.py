import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from hookshot.replayer_routes import replayer_bp, init_replayer_routes
from hookshot.storage import RequestStore
from hookshot.models import WebhookRequest
from hookshot.replayer import ReplayResult, ReplayError


def make_request(request_id="req-1", method="POST", path="/hook"):
    return WebhookRequest(
        id=request_id,
        method=method,
        path=path,
        query_string="",
        headers={"content-type": "application/json"},
        body=b'{"x": 1}',
    )


@pytest.fixture()
def store():
    return RequestStore()


@pytest.fixture()
def client(store):
    app = Flask(__name__)
    app.register_blueprint(replayer_bp)
    init_replayer_routes(store, target_url="http://localhost:9000")
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_replay_request_not_found(client):
    resp = client.post("/requests/missing-id/replay")
    assert resp.status_code == 404
    assert "not found" in resp.get_json()["error"]


def test_replay_request_success(client, store):
    req = make_request()
    store.save(req)
    result = ReplayResult(
        request_id=req.id,
        status_code=200,
        response_body=b"ok",
        success=True,
    )
    with patch("hookshot.replayer_routes._get_replayer") as mock_get:
        mock_replayer = MagicMock()
        mock_replayer.replay.return_value = result
        mock_get.return_value = mock_replayer
        resp = client.post(f"/requests/{req.id}/replay")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["status_code"] == 200


def test_replay_request_forward_error(client, store):
    req = make_request()
    store.save(req)
    with patch("hookshot.replayer_routes._get_replayer") as mock_get:
        mock_replayer = MagicMock()
        mock_replayer.replay.side_effect = ReplayError("connection refused")
        mock_get.return_value = mock_replayer
        resp = client.post(f"/requests/{req.id}/replay")

    assert resp.status_code == 502
    assert "connection refused" in resp.get_json()["error"]


def test_replay_batch_missing_ids(client):
    resp = client.post("/requests/replay-batch", json={})
    assert resp.status_code == 400


def test_replay_batch_empty_ids(client):
    resp = client.post("/requests/replay-batch", json={"ids": []})
    assert resp.status_code == 400


def test_replay_batch_partial_results(client, store):
    req = make_request(request_id="r1")
    store.save(req)
    result = ReplayResult(request_id="r1", status_code=201, response_body=b"", success=True)
    with patch("hookshot.replayer_routes._get_replayer") as mock_get:
        mock_replayer = MagicMock()
        mock_replayer.replay.return_value = result
        mock_get.return_value = mock_replayer
        resp = client.post("/requests/replay-batch", json={"ids": ["r1", "r-missing"]})

    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 2
    ids = {d["id"] for d in data}
    assert "r1" in ids
    assert "r-missing" in ids
    missing = next(d for d in data if d["id"] == "r-missing")
    assert "error" in missing
