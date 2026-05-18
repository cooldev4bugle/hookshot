"""Tests for hookshot.comparator."""

import pytest
from hookshot.comparator import Comparator, CompareError
from hookshot.models import WebhookRequest
from hookshot.storage import RequestStore


@pytest.fixture
def store():
    return RequestStore()


def make_request(method="POST", path="/hook", query_string="",
                 headers=None, body=b"{}"):
    return WebhookRequest(
        method=method,
        path=path,
        query_string=query_string,
        headers=headers or {"content-type": "application/json"},
        body=body,
    )


@pytest.fixture
def comparator(store):
    return Comparator(store)


def test_comparator_requires_store():
    with pytest.raises(CompareError, match="store is required"):
        Comparator(None)


def test_compare_identical_requests(store, comparator):
    r1 = make_request()
    r2 = make_request()
    store.save(r1)
    store.save(r2)
    result = comparator.compare(r1.id, r2.id)
    assert result.identical is True
    assert result.diffs == []


def test_compare_different_method(store, comparator):
    r1 = make_request(method="POST")
    r2 = make_request(method="GET")
    store.save(r1)
    store.save(r2)
    result = comparator.compare(r1.id, r2.id)
    assert not result.identical
    keys = [d.key for d in result.diffs]
    assert "method" in keys


def test_compare_different_body(store, comparator):
    r1 = make_request(body=b'{"a": 1}')
    r2 = make_request(body=b'{"a": 2}')
    store.save(r1)
    store.save(r2)
    result = comparator.compare(r1.id, r2.id)
    assert not result.identical
    assert any(d.key == "body" for d in result.diffs)


def test_compare_missing_left_raises(store, comparator):
    r = make_request()
    store.save(r)
    with pytest.raises(CompareError, match="request not found"):
        comparator.compare("nonexistent", r.id)


def test_compare_missing_right_raises(store, comparator):
    r = make_request()
    store.save(r)
    with pytest.raises(CompareError, match="request not found"):
        comparator.compare(r.id, "nonexistent")


def test_to_dict_structure(store, comparator):
    r1 = make_request(method="POST")
    r2 = make_request(method="PUT")
    store.save(r1)
    store.save(r2)
    result = comparator.compare(r1.id, r2.id)
    d = result.to_dict()
    assert d["left_id"] == r1.id
    assert d["right_id"] == r2.id
    assert d["identical"] is False
    assert isinstance(d["diffs"], list)
    assert d["diffs"][0]["key"] == "method"
