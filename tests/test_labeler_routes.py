"""Tests for hookshot.labeler_routes."""

import pytest
from flask import Flask
from hookshot.storage import RequestStore
from hookshot.models import WebhookRequest
from hookshot.labeler_routes import init_labeler_routes, get_labeler


def make_request(method="POST", path="/hook"):
    return WebhookRequest(
        method=method,
        path=path,
        query_string="",
        headers={"content-type": "application/json"},
        body=b"{}",
    )


@pytest.fixture(autouse=True)
def reset_labeler():
    get_labeler().clear()
    yield
    get_labeler().clear()


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def client(store):
    app = Flask(__name__)
    app.config["TESTING"] = True
    init_labeler_routes(app, store)
    return app.test_client()


def test_list_rules_empty(client):
    resp = client.get("/labeler/rules")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_add_rule_returns_201(client):
    resp = client.post("/labeler/rules", json={"label": "my-label", "method": "POST"})
    assert resp.status_code == 201
    assert resp.get_json()["label"] == "my-label"


def test_add_rule_empty_label_returns_400(client):
    resp = client.post("/labeler/rules", json={"label": ""})
    assert resp.status_code == 400


def test_delete_rule(client):
    client.post("/labeler/rules", json={"label": "temp"})
    resp = client.delete("/labeler/rules/temp")
    assert resp.status_code == 204


def test_delete_unknown_rule_returns_404(client):
    resp = client.delete("/labeler/rules/ghost")
    assert resp.status_code == 404


def test_label_request_not_found(client):
    resp = client.get("/labeler/label/does-not-exist")
    assert resp.status_code == 404


def test_label_request_returns_labels(client, store):
    req = make_request(method="POST", path="/hook")
    store.save(req)
    client.post("/labeler/rules", json={"label": "post-hook", "method": "POST", "path_prefix": "/hook"})
    resp = client.get(f"/labeler/label/{req.id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "post-hook" in data["labels"]


def test_clear_rules(client):
    client.post("/labeler/rules", json={"label": "a"})
    client.post("/labeler/rules", json={"label": "b"})
    resp = client.delete("/labeler/rules")
    assert resp.status_code == 204
    rules = client.get("/labeler/rules").get_json()
    assert rules == []
