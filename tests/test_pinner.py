"""Tests for hookshot.pinner."""

import pytest

from hookshot.models import WebhookRequest
from hookshot.storage import RequestStore
from hookshot.pinner import Pinner, PinError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def store():
    return RequestStore(max_size=50)


@pytest.fixture()
def pinner(store):
    return Pinner(store)


def make_request(method="POST", path="/hook", body=b""):
    return WebhookRequest(
        method=method,
        path=path,
        query_string="",
        headers={"content-type": "application/json"},
        body=body,
    )


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_pinner_requires_store():
    with pytest.raises(PinError):
        Pinner(None)


# ---------------------------------------------------------------------------
# pin / unpin
# ---------------------------------------------------------------------------

def test_pin_unknown_request_raises(pinner):
    with pytest.raises(PinError, match="not found"):
        pinner.pin("nonexistent-id")


def test_pin_marks_request(store, pinner):
    req = make_request()
    store.save(req)
    pinner.pin(req.id)
    assert pinner.is_pinned(req.id)


def test_unpin_removes_pin(store, pinner):
    req = make_request()
    store.save(req)
    pinner.pin(req.id)
    pinner.unpin(req.id)
    assert not pinner.is_pinned(req.id)


def test_unpin_not_pinned_raises(store, pinner):
    req = make_request()
    store.save(req)
    with pytest.raises(PinError, match="not pinned"):
        pinner.unpin(req.id)


# ---------------------------------------------------------------------------
# pinned_ids / pinned_requests
# ---------------------------------------------------------------------------

def test_pinned_ids_empty_initially(pinner):
    assert pinner.pinned_ids() == []


def test_pinned_requests_returns_objects(store, pinner):
    req = make_request()
    store.save(req)
    pinner.pin(req.id)
    results = pinner.pinned_requests()
    assert len(results) == 1
    assert results[0].id == req.id


# ---------------------------------------------------------------------------
# clear_unpinned
# ---------------------------------------------------------------------------

def test_clear_unpinned_removes_only_unpinned(store, pinner):
    pinned = make_request(path="/pinned")
    unpinned = make_request(path="/unpinned")
    store.save(pinned)
    store.save(unpinned)
    pinner.pin(pinned.id)

    removed = pinner.clear_unpinned()

    assert removed == 1
    assert store.get(pinned.id) is not None
    assert store.get(unpinned.id) is None


def test_clear_unpinned_returns_zero_when_all_pinned(store, pinner):
    req = make_request()
    store.save(req)
    pinner.pin(req.id)
    assert pinner.clear_unpinned() == 0
