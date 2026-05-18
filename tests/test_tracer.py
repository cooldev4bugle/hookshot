"""Tests for hookshot.tracer."""

import pytest
from hookshot.tracer import Tracer, TraceError


@pytest.fixture
def tracer():
    return Tracer()


def test_start_trace_creates_entry(tracer):
    entry = tracer.start_trace("req-1", {})
    assert entry.request_id == "req-1"
    assert entry.trace_id
    assert entry.parent_trace_id is None
    assert entry.hops == []


def test_start_trace_inherits_parent(tracer):
    headers = {"x-hookshot-trace-id": "parent-abc"}
    entry = tracer.start_trace("req-2", headers)
    assert entry.parent_trace_id == "parent-abc"


def test_start_trace_missing_request_id_raises(tracer):
    with pytest.raises(TraceError):
        tracer.start_trace("", {})


def test_record_hop_appends_url(tracer):
    entry = tracer.start_trace("req-3", {})
    tracer.record_hop(entry.trace_id, "http://localhost:9000/hook")
    tracer.record_hop(entry.trace_id, "http://example.com/hook")
    assert len(entry.hops) == 2
    assert entry.hops[0] == "http://localhost:9000/hook"


def test_record_hop_unknown_trace_raises(tracer):
    with pytest.raises(TraceError, match="Unknown trace_id"):
        tracer.record_hop("no-such-id", "http://example.com")


def test_get_returns_entry(tracer):
    entry = tracer.start_trace("req-4", {})
    found = tracer.get(entry.trace_id)
    assert found is entry


def test_get_missing_returns_none(tracer):
    assert tracer.get("ghost") is None


def test_all_returns_all_entries(tracer):
    tracer.start_trace("req-5", {})
    tracer.start_trace("req-6", {})
    assert len(tracer.all()) == 2


def test_inject_header_returns_dict(tracer):
    entry = tracer.start_trace("req-7", {})
    headers = tracer.inject_header(entry.trace_id)
    assert headers == {"x-hookshot-trace-id": entry.trace_id}


def test_to_dict(tracer):
    entry = tracer.start_trace("req-8", {"x-hookshot-trace-id": "p-id"})
    tracer.record_hop(entry.trace_id, "http://a.com")
    d = entry.to_dict()
    assert d["request_id"] == "req-8"
    assert d["parent_trace_id"] == "p-id"
    assert d["hops"] == ["http://a.com"]


def test_clear_removes_all(tracer):
    tracer.start_trace("req-9", {})
    tracer.clear()
    assert tracer.all() == []
