"""Tests for hookshot.profiler."""

import time
import pytest
from hookshot.profiler import Profiler, ProfileEntry, ProfileError
from hookshot.models import WebhookRequest


def make_request(**kwargs):
    defaults = dict(
        method="POST",
        path="/hook",
        query_string="",
        headers={"content-type": "application/json"},
        body=b'{"x": 1}',
    )
    defaults.update(kwargs)
    return WebhookRequest(**defaults)


@pytest.fixture
def profiler():
    return Profiler(max_entries=10)


def test_invalid_max_entries_raises():
    with pytest.raises(ProfileError):
        Profiler(max_entries=0)


def test_record_returns_entry(profiler):
    req = make_request()
    entry = profiler.record(req)
    assert isinstance(entry, ProfileEntry)
    assert entry.request_id == req.id
    assert entry.method == "POST"
    assert entry.path == "/hook"


def test_body_size_is_correct(profiler):
    body = b"hello world"
    req = make_request(body=body)
    entry = profiler.record(req)
    assert entry.body_size == len(body)


def test_header_count(profiler):
    req = make_request(headers={"content-type": "application/json", "x-id": "abc"})
    entry = profiler.record(req)
    assert entry.header_count == 2


def test_latency_ms_is_non_negative(profiler):
    req = make_request()
    entry = profiler.record(req)
    assert entry.latency_ms >= 0


def test_get_returns_entry(profiler):
    req = make_request()
    profiler.record(req)
    found = profiler.get(req.id)
    assert found is not None
    assert found.request_id == req.id


def test_get_missing_returns_none(profiler):
    assert profiler.get("nonexistent") is None


def test_all_returns_all_entries(profiler):
    for _ in range(3):
        profiler.record(make_request())
    assert len(profiler.all()) == 3


def test_max_entries_evicts_oldest(profiler):
    p = Profiler(max_entries=3)
    reqs = [make_request() for _ in range(4)]
    for r in reqs:
        p.record(r)
    entries = p.all()
    assert len(entries) == 3
    ids = [e.request_id for e in entries]
    assert reqs[0].id not in ids


def test_summary_empty(profiler):
    s = profiler.summary()
    assert s["count"] == 0
    assert s["avg_latency_ms"] == 0.0


def test_summary_with_entries(profiler):
    for _ in range(5):
        profiler.record(make_request(body=b"12345"))
    s = profiler.summary()
    assert s["count"] == 5
    assert s["avg_body_size"] == 5.0


def test_clear_removes_all(profiler):
    profiler.record(make_request())
    profiler.clear()
    assert profiler.all() == []


def test_to_dict_has_expected_keys(profiler):
    req = make_request()
    entry = profiler.record(req)
    d = entry.to_dict()
    for key in ("request_id", "method", "path", "body_size", "header_count", "latency_ms"):
        assert key in d
