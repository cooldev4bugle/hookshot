import pytest
from hookshot.models import WebhookRequest
from hookshot.storage import RequestStore
from hookshot.deduplicator import Deduplicator, DeduplicateError


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def deduplicator(store):
    return Deduplicator(store)


def make_request(method="POST", path="/hook", body=b'{"event": "push"}', headers=None):
    return WebhookRequest(
        method=method,
        path=path,
        query_string="",
        headers=headers or {"content-type": "application/json"},
        body=body,
    )


def test_requires_positive_window(store):
    with pytest.raises(DeduplicateError):
        Deduplicator(store, window=0)


def test_is_duplicate_false_for_unique(store, deduplicator):
    req = make_request()
    store.save(req)
    req2 = make_request(body=b'{"event": "release"}')
    assert deduplicator.is_duplicate(req2) is False


def test_is_duplicate_true_for_same_body_and_path(store, deduplicator):
    req = make_request()
    store.save(req)
    req2 = make_request()  # same method/path/body, different id
    assert deduplicator.is_duplicate(req2) is True


def test_is_duplicate_ignores_self(store, deduplicator):
    req = make_request()
    store.save(req)
    # same request compared against itself should not flag as duplicate
    assert deduplicator.is_duplicate(req) is False


def test_is_duplicate_different_path_not_duplicate(store, deduplicator):
    req = make_request(path="/hook")
    store.save(req)
    req2 = make_request(path="/other")
    assert deduplicator.is_duplicate(req2) is False


def test_deduplicate_removes_duplicates():
    store = RequestStore()
    d = Deduplicator(store)
    r1 = make_request()
    r2 = make_request()  # duplicate of r1
    r3 = make_request(body=b'{"event": "release"}')
    result = d.deduplicate([r1, r2, r3])
    assert len(result) == 2
    assert result[0].id == r1.id
    assert result[1].id == r3.id


def test_deduplicate_empty_list():
    store = RequestStore()
    d = Deduplicator(store)
    assert d.deduplicate([]) == []


def test_find_duplicates(store, deduplicator):
    r1 = make_request()
    r2 = make_request()  # same fingerprint
    r3 = make_request(body=b'{"event": "other"}')
    store.save(r1)
    store.save(r2)
    store.save(r3)
    dups = deduplicator.find_duplicates(r1)
    assert len(dups) == 1
    assert dups[0].id == r2.id


def test_window_limits_search(store):
    d = Deduplicator(store, window=2)
    old = make_request(body=b'{"old": true}')
    store.save(old)
    # fill window with different requests
    store.save(make_request(body=b'{"a": 1}'))
    store.save(make_request(body=b'{"b": 2}'))
    # old request is outside the window of 2, should not be found
    probe = make_request(body=b'{"old": true}')
    assert d.is_duplicate(probe) is False
