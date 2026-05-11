"""Tests for the Flask server routes."""
import json
import pytest
from hookshot.storage import RequestStore
from hookshot.server import create_app


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def client(store):
    app = create_app(store=store, target_url=None)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_post_to_root_returns_200(client):
    resp = client.post("/", json={"hello": "world"})
    assert resp.status_code == 200


def test_request_is_stored(client, store):
    client.post("/webhook", json={"x": 1})
    assert len(store.all()) == 1


def test_list_requests_empty(client):
    resp = client.get("/__hookshot/requests")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_list_requests_after_post(client):
    client.post("/hook", json={"a": "b"})
    resp = client.get("/__hookshot/requests")
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["path"] == "/hook"


def test_get_request_by_id(client, store):
    client.post("/hook", json={})
    req = store.all()[0]
    resp = client.get(f"/__hookshot/requests/{req.id}")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == req.id


def test_get_missing_request_returns_404(client):
    resp = client.get("/__hookshot/requests/nonexistent")
    assert resp.status_code == 404


def test_export_json(client):
    client.post("/hook", json={"event": "test"})
    resp = client.get("/__hookshot/export?format=json")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) == 1


def test_export_csv(client):
    client.post("/hook", json={"event": "test"})
    resp = client.get("/__hookshot/export?format=csv")
    assert resp.status_code == 200
    assert b"id,received_at" in resp.data


def test_export_unsupported_format(client):
    resp = client.get("/__hookshot/export?format=xml")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_filter_by_method(client):
    client.post("/hook", json={})
    client.get("/ping")
    resp = client.get("/__hookshot/requests?method=GET")
    data = resp.get_json()
    assert all(r["method"] == "GET" for r in data)
