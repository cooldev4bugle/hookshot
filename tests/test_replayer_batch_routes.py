"""Tests for batch replay routes."""

import pytest
from unittest.mock import MagicMock
from flask import Flask

from hookshot.models import WebhookRequest
from hookshot.replayer import ReplayResult, ReplayError
from hookshot.storage import RequestStore
from hookshot.replayer_batch_routes import init_batch_replay_routes


def make_request(method="POST", path="/hook", body=b"{}") -> WebhookRequest:
    return WebhookRequest(
        method=method,
        path=path,
        query_string="",
        headers={"content-type": "application/json"},
        body=body,
    )


@pytest.fixture()
def store():
    s = RequestStore(max_size=100)
    return s


@pytest.fixture()
def client(store):
    app = Flask(__name__)
    app.config["TESTING"] = True
    mock_replayer = MagicMock()
    mock_replayer.replay.return_value = ReplayResult(success=True, status_code=200, body=b"ok")
    init_batch_replay_routes(app, store, mock_replayer)
    with app.test_client() as c:
        c._replayer = mock_replayer
        c._store = store
        yield c


def test_batch_replay_empty_store(client):
    resp = client.post("/replay/batch", json={})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 0
    assert data["succeeded"] == 0


def test_batch_replay_replays_all(client, store):
    store.save(make_request())
    store.save(make_request())
    resp = client.post("/replay/batch", json={})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 2
    assert data["succeeded"] == 2


def test_batch_replay_filters_by_method(client, store):
    store.save(make_request(method="POST"))
    store.save(make_request(method="GET"))
    resp = client.post("/replay/batch", json={"method": "GET"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 1


def test_batch_replay_filters_by_path_prefix(client, store):
    store.save(make_request(path="/hook/a"))
    store.save(make_request(path="/other"))
    resp = client.post("/replay/batch", json={"path_prefix": "/hook"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 1


def test_batch_replay_invalid_limit(client):
    resp = client.post("/replay/batch", json={"limit": 0})
    assert resp.status_code == 400


def test_batch_replay_limit_exceeded(client):
    resp = client.post("/replay/batch", json={"limit": 999})
    assert resp.status_code == 400


def test_dry_run_returns_ids(client, store):
    r1 = make_request()
    r2 = make_request()
    store.save(r1)
    store.save(r2)
    resp = client.post("/replay/batch/dry-run", json={})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 2
    assert r1.id in data["would_replay"]
    assert r2.id in data["would_replay"]


def test_dry_run_respects_filter(client, store):
    store.save(make_request(path="/alpha"))
    store.save(make_request(path="/beta"))
    resp = client.post("/replay/batch/dry-run", json={"path_prefix": "/alpha"})
    data = resp.get_json()
    assert data["count"] == 1
