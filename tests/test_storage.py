"""Tests for in-memory request storage."""

import pytest

from hookshot.models import WebhookRequest
from hookshot.storage import RequestStore


@pytest.fixture
def store():
    return RequestStore(max_size=3)


def make_request(path="/webhook"):
    return WebhookRequest(
        method="POST",
        path=path,
        headers={"content-type": "application/json"},
        body=b'{"ok": true}',
    )


def test_save_and_retrieve(store):
    req = make_request()
    store.save(req)
    found = store.get(req.id)
    assert found is req


def test_get_missing_returns_none(store):
    assert store.get("nonexistent-id") is None


def test_all_returns_saved_requests(store):
    r1 = store.save(make_request("/a"))
    r2 = store.save(make_request("/b"))
    all_reqs = store.all()
    assert r1 in all_reqs
    assert r2 in all_reqs


def test_evicts_oldest_when_over_capacity(store):
    r1 = store.save(make_request("/1"))
    r2 = store.save(make_request("/2"))
    r3 = store.save(make_request("/3"))
    r4 = store.save(make_request("/4"))  # should evict r1
    assert store.get(r1.id) is None
    assert store.get(r4.id) is r4
    assert len(store) == 3


def test_delete_existing_request(store):
    req = store.save(make_request())
    result = store.delete(req.id)
    assert result is True
    assert store.get(req.id) is None


def test_delete_nonexistent_returns_false(store):
    assert store.delete("ghost-id") is False


def test_clear_removes_all(store):
    store.save(make_request("/a"))
    store.save(make_request("/b"))
    removed = store.clear()
    assert removed == 2
    assert len(store) == 0


def test_len_reflects_count(store):
    assert len(store) == 0
    store.save(make_request())
    assert len(store) == 1
