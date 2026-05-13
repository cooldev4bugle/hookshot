"""Tests for scheduler HTTP routes."""

import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from hookshot.scheduler_routes import scheduler_bp
from hookshot.scheduler import Scheduler, ScheduleError
from hookshot.models import WebhookRequest


def make_request(rid="req-abc"):
    return WebhookRequest(
        id=rid,
        method="POST",
        path="/hook",
        query_string="",
        headers={"content-type": "application/json"},
        body=b'{"x": 1}',
    )


@pytest.fixture
def app():
    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True

    mock_store = MagicMock()
    mock_replayer = MagicMock()
    mock_scheduler = MagicMock(spec=Scheduler)

    flask_app.config["store"] = mock_store
    flask_app.config["replayer"] = mock_replayer
    flask_app.config["scheduler"] = mock_scheduler

    flask_app.register_blueprint(scheduler_bp)
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


def test_create_schedule_missing_request_id(client):
    resp = client.post("/schedule", json={"interval": 5})
    assert resp.status_code == 400
    assert "request_id" in resp.get_json()["error"]


def test_create_schedule_missing_interval(client):
    resp = client.post("/schedule", json={"request_id": "req-1"})
    assert resp.status_code == 400
    assert "interval" in resp.get_json()["error"]


def test_create_schedule_unknown_request(client, app):
    app.config["store"].get.return_value = None
    resp = client.post("/schedule", json={"request_id": "ghost", "interval": 5})
    assert resp.status_code == 404


def test_create_schedule_success(client, app):
    req = make_request()
    app.config["store"].get.return_value = req
    fake_job = MagicMock()
    fake_job.to_dict.return_value = {"request_id": req.id, "interval": 5, "run_count": 0, "running": True, "last_error": None}
    app.config["scheduler"].schedule.return_value = fake_job

    resp = client.post("/schedule", json={"request_id": req.id, "interval": 5})
    assert resp.status_code == 201
    assert resp.get_json()["running"] is True


def test_create_schedule_conflict(client, app):
    app.config["store"].get.return_value = make_request()
    app.config["scheduler"].schedule.side_effect = ScheduleError("already scheduled")

    resp = client.post("/schedule", json={"request_id": "req-abc", "interval": 5})
    assert resp.status_code == 409


def test_cancel_schedule_success(client, app):
    resp = client.delete("/schedule/req-abc")
    assert resp.status_code == 200
    assert resp.get_json()["cancelled"] == "req-abc"


def test_cancel_schedule_not_found(client, app):
    app.config["scheduler"].cancel.side_effect = ScheduleError("no job found")
    resp = client.delete("/schedule/ghost")
    assert resp.status_code == 404


def test_list_schedules(client, app):
    app.config["scheduler"].list_jobs.return_value = [{"request_id": "r1", "interval": 10}]
    resp = client.get("/schedule")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 1
