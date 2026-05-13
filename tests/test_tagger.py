"""Tests for the Tagger module."""

import pytest
from hookshot.tagger import Tagger, TagError
from hookshot.models import WebhookRequest
from hookshot.storage import RequestStore


@pytest.fixture
def store():
    return RequestStore(max_size=100)


@pytest.fixture
def make_request(store):
    def _make(path="/hook", method="POST"):
        req = WebhookRequest(
            method=method,
            path=path,
            query_string="",
            headers={"content-type": "application/json"},
            body=b'{"x": 1}',
        )
        store.save(req)
        return req
    return _make


@pytest.fixture
def tagger(store):
    return Tagger(store)


def test_tagger_requires_store():
    with pytest.raises(TagError):
        Tagger(None)


def test_add_tag_returns_sorted_list(tagger, make_request):
    req = make_request()
    tags = tagger.add_tag(req.id, "payment")
    assert tags == ["payment"]


def test_add_multiple_tags(tagger, make_request):
    req = make_request()
    tagger.add_tag(req.id, "zebra")
    tags = tagger.add_tag(req.id, "alpha")
    assert tags == ["alpha", "zebra"]


def test_tag_is_lowercased(tagger, make_request):
    req = make_request()
    tags = tagger.add_tag(req.id, "  PAYMENT  ")
    assert tags == ["payment"]


def test_add_tag_empty_raises(tagger, make_request):
    req = make_request()
    with pytest.raises(TagError, match="empty"):
        tagger.add_tag(req.id, "   ")


def test_add_tag_too_long_raises(tagger, make_request):
    req = make_request()
    with pytest.raises(TagError, match="max length"):
        tagger.add_tag(req.id, "x" * 33)


def test_add_tag_missing_request_raises(tagger):
    with pytest.raises(TagError, match="not found"):
        tagger.add_tag("nonexistent-id", "test")


def test_remove_tag(tagger, make_request):
    req = make_request()
    tagger.add_tag(req.id, "beta")
    tags = tagger.remove_tag(req.id, "beta")
    assert "beta" not in tags


def test_remove_nonexistent_tag_is_noop(tagger, make_request):
    req = make_request()
    tags = tagger.remove_tag(req.id, "ghost")
    assert tags == []


def test_get_tags(tagger, make_request):
    req = make_request()
    tagger.add_tag(req.id, "stripe")
    assert tagger.get_tags(req.id) == ["stripe"]


def test_find_by_tag(tagger, make_request):
    req1 = make_request(path="/a")
    req2 = make_request(path="/b")
    tagger.add_tag(req1.id, "important")
    tagger.add_tag(req2.id, "other")
    results = tagger.find_by_tag("important")
    assert len(results) == 1
    assert results[0].id == req1.id


def test_clear_tags(tagger, make_request):
    req = make_request()
    tagger.add_tag(req.id, "temp")
    tagger.clear_tags(req.id)
    assert tagger.get_tags(req.id) == []


def test_max_tags_per_request(tagger, make_request):
    req = make_request()
    for i in range(10):
        tagger.add_tag(req.id, f"tag{i}")
    with pytest.raises(TagError, match="10 tags"):
        tagger.add_tag(req.id, "overflow")
