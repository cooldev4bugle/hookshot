"""Tests for hookshot.compare_routes."""

import pytest
from flask import Flask
from hookshot.storage import RequestStore
from hookshot.models import WebhookRequest
from hookshot.compare_routes import init_compare_routes


def make_request(method="POST", path="/hook", body=b"{}"):
    return WebhookRequest(
        method=method,
        path=path,
        query_string="",
        headers={"content-type": "application/json"},
        body=body,
    )


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def client(store):
    app = Flask(__name__)
    app.config["TESTING"] = True
    init_compare_routes(app, store)
    return app.test_client(), store


def test_compare_missing_left_id(client):
    c, _ = client
    resp = c.post("/compare", json={"right_id": "abc"})
    assert resp.status_code == 400
    assert b"left_id" in resp.data


def test_compare_missing_right_id(client):
    c, _ = client
    resp = c.post("/compare", json={"left_id": "abc"})
    assert resp.status_code == 400
    assert b"right_id" in resp.data


def test_compare_unknown_ids_returns_404(client):
    c, _ = client
    resp = c.post("/compare", json={"left_id": "x", "right_id": "y"})
    assert resp.status_code == 404


def test_compare_identical_returns_200(client):
    c, store = client
    r1 = make_request()
    r2 = make_request()
    store.save(r1)
    store.save(r2)
    resp = c.post("/compare", json={"left_id": r1.id, "right_id": r2.id})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["identical"] is True


def test_compare_different_returns_diffs(client):
    c, store = client
    r1 = make_request(method="POST")
    r2 = make_request(method="GET")
    store.save(r1)
    store.save(r2)
    resp = c.post("/compare", json={"left_id": r1.id, "right_id": r2.id})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["identical"] is False
    assert any(d["key"] == "method" for d in data["diffs"])


def test_compare_via_get_query_params(client):
    c, store = client
    r1 = make_request(body=b"hello")
    r2 = make_request(body=b"world")
    store.save(r1)
    store.save(r2)
    resp = c.get(f"/compare?left_id={r1.id}&right_id={r2.id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert not data["identical"]
