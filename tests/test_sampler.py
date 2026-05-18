"""Tests for the request sampler module and its HTTP routes."""

import pytest
from flask import Flask
from hookshot.sampler import Sampler, SampleError
from hookshot.sampler_routes import init_sampler_routes, get_sampler
from hookshot.models import WebhookRequest


def make_request(**kwargs):
    defaults = dict(method="POST", path="/hook", headers={}, body=b"")
    defaults.update(kwargs)
    return WebhookRequest(**defaults)


# --- unit tests ---

def test_invalid_rate_raises():
    with pytest.raises(SampleError):
        Sampler(rate=1.5)


def test_invalid_rate_below_zero_raises():
    with pytest.raises(SampleError):
        Sampler(rate=-0.1)


def test_rate_zero_drops_all():
    s = Sampler(rate=0.0)
    reqs = [make_request() for _ in range(20)]
    assert s.filter(reqs) == []


def test_rate_one_keeps_all():
    s = Sampler(rate=1.0)
    reqs = [make_request() for _ in range(10)]
    assert len(s.filter(reqs)) == 10


def test_should_keep_none_raises():
    s = Sampler()
    with pytest.raises(SampleError):
        s.should_keep(None)


def test_stats_track_counts():
    s = Sampler(rate=1.0)
    reqs = [make_request() for _ in range(5)]
    s.filter(reqs)
    stats = s.stats()
    assert stats["seen"] == 5
    assert stats["kept"] == 5
    assert stats["dropped"] == 0


def test_reset_stats_clears_counts():
    s = Sampler(rate=1.0)
    s.should_keep(make_request())
    s.reset_stats()
    assert s.stats()["seen"] == 0


def test_set_rate_invalid_raises():
    s = Sampler()
    with pytest.raises(SampleError):
        s.set_rate(2.0)


# --- route tests ---

@pytest.fixture()
def client():
    app = Flask(__name__)
    sampler = Sampler(rate=1.0, seed=42)
    init_sampler_routes(app, sampler=sampler)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_get_config_returns_rate(client):
    resp = client.get("/sampler/config")
    assert resp.status_code == 200
    assert resp.get_json()["rate"] == 1.0


def test_set_config_updates_rate(client):
    resp = client.put("/sampler/config", json={"rate": 0.5})
    assert resp.status_code == 200
    assert resp.get_json()["rate"] == 0.5


def test_set_config_invalid_rate(client):
    resp = client.put("/sampler/config", json={"rate": 99})
    assert resp.status_code == 400


def test_set_config_missing_rate(client):
    resp = client.put("/sampler/config", json={})
    assert resp.status_code == 400


def test_get_stats(client):
    resp = client.get("/sampler/stats")
    data = resp.get_json()
    assert "seen" in data and "kept" in data


def test_reset_stats(client):
    resp = client.delete("/sampler/stats")
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True
