import json
import pytest
from unittest.mock import patch, MagicMock
from hookshot.server import create_app
from hookshot.storage import RequestStore
from hookshot.forwarder import ForwardError


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def client(store):
    app = create_app(store=store)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_post_to_root_returns_200(client):
    resp = client.post("/", data=b'{"event": "ping"}', content_type="application/json")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "received"
    assert "id" in data


def test_request_is_stored(client, store):
    client.post("/webhook", data=b"hello", content_type="text/plain")
    requests = store.all()
    assert len(requests) == 1
    assert requests[0].path == "/webhook"


def test_list_requests_empty(client):
    resp = client.get("/_hookshot/requests")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_list_requests_after_post(client):
    client.post("/hook", data=b"data")
    resp = client.get("/_hookshot/requests")
    items = resp.get_json()
    assert len(items) == 1
    assert items[0]["path"] == "/hook"


def test_get_request_by_id(client, store):
    client.post("/ping", data=b"body")
    req = store.all()[0]
    resp = client.get(f"/_hookshot/requests/{req.id}")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == req.id


def test_get_missing_request_returns_404(client):
    resp = client.get("/_hookshot/requests/nonexistent")
    assert resp.status_code == 404


def test_various_http_methods(client):
    for method in ["get", "put", "patch", "delete"]:
        resp = getattr(client, method)("/test")
        assert resp.status_code == 200


def test_forward_error_included_in_response(store):
    app = create_app(target_url="http://localhost:9999", store=store)
    app.config["TESTING"] = True
    with app.test_client() as c:
        with patch("hookshot.server.Forwarder.forward", side_effect=ForwardError("connection refused")):
            resp = c.post("/hook", data=b"test")
            data = resp.get_json()
            assert "forward_error" in data
