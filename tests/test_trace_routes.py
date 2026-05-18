"""Tests for hookshot.trace_routes."""

import pytest
from flask import Flask

from hookshot.tracer import Tracer
from hookshot.trace_routes import init_trace_routes


@pytest.fixture
def tracer():
    return Tracer()


@pytest.fixture
def client(tracer):
    app = Flask(__name__)
    app.config["TESTING"] = True
    init_trace_routes(app, tracer)
    with app.test_client() as c:
        yield c, tracer


def test_list_traces_empty(client):
    c, _ = client
    resp = c.get("/traces")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_list_traces_returns_entries(client):
    c, tracer = client
    tracer.start_trace("r1", {})
    tracer.start_trace("r2", {})
    resp = c.get("/traces")
    data = resp.get_json()
    assert len(data) == 2


def test_get_trace_found(client):
    c, tracer = client
    entry = tracer.start_trace("r3", {})
    resp = c.get(f"/traces/{entry.trace_id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["trace_id"] == entry.trace_id
    assert data["request_id"] == "r3"


def test_get_trace_not_found(client):
    c, _ = client
    resp = c.get("/traces/no-such-id")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "not found"


def test_clear_traces(client):
    c, tracer = client
    tracer.start_trace("r4", {})
    resp = c.delete("/traces")
    assert resp.status_code == 200
    assert resp.get_json()["cleared"] is True
    assert tracer.all() == []


def test_trace_hops_visible(client):
    c, tracer = client
    entry = tracer.start_trace("r5", {})
    tracer.record_hop(entry.trace_id, "http://target.local/hook")
    resp = c.get(f"/traces/{entry.trace_id}")
    data = resp.get_json()
    assert data["hops"] == ["http://target.local/hook"]
