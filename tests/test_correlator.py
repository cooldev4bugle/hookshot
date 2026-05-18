"""Tests for hookshot.correlator."""

import pytest

from hookshot.correlator import Correlator, CorrelateError
from hookshot.models import WebhookRequest
from hookshot.storage import RequestStore


@pytest.fixture
def store():
    return RequestStore(max_size=50)


def make_request(store: RequestStore, cid: str | None = None, path: str = "/hook") -> WebhookRequest:
    headers = {"content-type": "application/json"}
    if cid:
        headers["x-correlation-id"] = cid
    req = WebhookRequest(
        method="POST",
        path=path,
        query_string="",
        headers=headers,
        body=b"{}",
    )
    store.save(req)
    return req


def test_invalid_header_raises(store):
    with pytest.raises(CorrelateError):
        Correlator(store, header="")


def test_group_empty_store(store):
    c = Correlator(store)
    assert c.group() == {}


def test_group_single_cid(store):
    make_request(store, cid="abc-123")
    make_request(store, cid="abc-123")
    c = Correlator(store)
    groups = c.group()
    assert "abc-123" in groups
    assert len(groups["abc-123"]) == 2


def test_group_multiple_cids(store):
    make_request(store, cid="aaa")
    make_request(store, cid="bbb")
    make_request(store, cid="aaa")
    c = Correlator(store)
    groups = c.group()
    assert len(groups["aaa"]) == 2
    assert len(groups["bbb"]) == 1


def test_requests_without_cid_are_excluded(store):
    make_request(store, cid=None)
    make_request(store, cid="xyz")
    c = Correlator(store)
    groups = c.group()
    assert list(groups.keys()) == ["xyz"]


def test_get_group_returns_matching(store):
    make_request(store, cid="tok-1")
    make_request(store, cid="tok-2")
    c = Correlator(store)
    result = c.get_group("tok-1")
    assert len(result) == 1
    assert result[0].headers["x-correlation-id"] == "tok-1"


def test_get_group_empty_id_raises(store):
    c = Correlator(store)
    with pytest.raises(CorrelateError):
        c.get_group("")


def test_correlation_ids_sorted(store):
    make_request(store, cid="zzz")
    make_request(store, cid="aaa")
    make_request(store, cid="mmm")
    c = Correlator(store)
    assert c.correlation_ids() == ["aaa", "mmm", "zzz"]


def test_custom_header(store):
    req = WebhookRequest(
        method="GET",
        path="/ping",
        query_string="",
        headers={"X-Request-Group": "grp-99"},
        body=b"",
    )
    store.save(req)
    c = Correlator(store, header="X-Request-Group")
    groups = c.group()
    assert "grp-99" in groups
