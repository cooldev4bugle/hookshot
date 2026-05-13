import pytest
from flask import Flask
from hookshot.transform_routes import bp, reset


@pytest.fixture(autouse=True)
def reset_transformer(client):
    """Reset transformer state before each test."""
    client.post("/transform/reset")
    yield


@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(bp)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_get_config_default(client):
    resp = client.get("/transform")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["header_overrides"] == {}
    assert data["header_removals"] == []
    assert data["body_template"] is None


def test_set_header(client):
    resp = client.post("/transform/headers", json={"name": "X-Env", "value": "staging"})
    assert resp.status_code == 200
    cfg = client.get("/transform").get_json()
    assert cfg["header_overrides"]["x-env"] == "staging"


def test_set_header_missing_name_returns_400(client):
    resp = client.post("/transform/headers", json={"name": "", "value": "v"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_remove_header(client):
    client.post("/transform/headers", json={"name": "Cookie", "value": "x"})
    resp = client.delete("/transform/headers/Cookie")
    assert resp.status_code == 200
    cfg = client.get("/transform").get_json()
    assert "cookie" in cfg["header_removals"]


def test_set_body_template(client):
    resp = client.post("/transform/body", json={"template": '{"k": "{v}"}'})
    assert resp.status_code == 200
    cfg = client.get("/transform").get_json()
    assert cfg["body_template"] == '{"k": "{v}"}'


def test_set_body_template_missing_field(client):
    resp = client.post("/transform/body", json={})
    assert resp.status_code == 400


def test_reset_clears_state(client):
    client.post("/transform/headers", json={"name": "X-A", "value": "1"})
    client.post("/transform/reset")
    cfg = client.get("/transform").get_json()
    assert cfg["header_overrides"] == {}
