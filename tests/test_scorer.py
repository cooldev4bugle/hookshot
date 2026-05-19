"""Tests for hookshot.scorer."""

import pytest
from flask import Flask

from hookshot.models import WebhookRequest
from hookshot.scorer import Scorer, ScoreError, ScoreResult
from hookshot.storage import RequestStore
from hookshot.scorer_routes import init_scorer_routes


def make_request(
    method="POST",
    path="/hook",
    headers=None,
    body=b'{"event": "ping"}',
    query_string="",
):
    return WebhookRequest(
        method=method,
        path=path,
        headers=headers or {"Content-Type": "application/json", "User-Agent": "tester/1"},
        body=body,
        query_string=query_string,
    )


@pytest.fixture
def scorer():
    return Scorer()


def test_score_none_raises(scorer):
    with pytest.raises(ScoreError):
        scorer.score(None)


def test_perfect_score(scorer):
    req = make_request()
    result = scorer.score(req)
    # JSON bonus pushes it to 105 but capped at 100
    assert result.score == 100.0
    assert result.grade == "A"


def test_missing_content_type_penalised(scorer):
    req = make_request(headers={"User-Agent": "bot"})
    result = scorer.score(req)
    assert result.score <= 80
    labels = [b.label for b in result.breakdowns]
    assert "content_type" in labels


def test_missing_user_agent_penalised(scorer):
    req = make_request(headers={"Content-Type": "application/json"})
    result = scorer.score(req)
    labels = [b.label for b in result.breakdowns]
    assert "user_agent" in labels


def test_large_body_penalised(scorer):
    big_body = b"x" * (600 * 1024)
    req = make_request(body=big_body, headers={"Content-Type": "text/plain", "User-Agent": "x"})
    result = scorer.score(req)
    labels = [b.label for b in result.breakdowns]
    assert "body_size" in labels


def test_json_body_rewarded(scorer):
    req = make_request()
    result = scorer.score(req)
    labels = [b.label for b in result.breakdowns]
    assert "json_body" in labels
    assert any(b.delta > 0 for b in result.breakdowns if b.label == "json_body")


def test_score_to_dict(scorer):
    req = make_request()
    d = scorer.score(req).to_dict()
    assert "request_id" in d
    assert "score" in d
    assert "grade" in d
    assert "breakdowns" in d


# --- route tests ---

@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def client(store):
    app = Flask(__name__)
    app.config["TESTING"] = True
    init_scorer_routes(app, store)
    with app.test_client() as c:
        yield c, store


def test_score_not_found(client):
    c, _ = client
    resp = c.get("/requests/missing/score")
    assert resp.status_code == 404


def test_score_single_request(client):
    c, store = client
    req = make_request()
    store.save(req)
    resp = c.get(f"/requests/{req.id}/score")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["request_id"] == req.id
    assert "grade" in data


def test_score_all_returns_list(client):
    c, store = client
    store.save(make_request())
    store.save(make_request())
    resp = c.get("/requests/scores")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 2
