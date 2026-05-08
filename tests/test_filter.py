"""Tests for hookshot.filter module."""

import pytest
from hookshot.filter import RequestFilter
from hookshot.models import WebhookRequest


def make_request(method="POST", path="/webhook", headers=None, body=b""):
    return WebhookRequest(
        method=method,
        path=path,
        query_string="",
        headers=headers or {"Content-Type": "application/json"},
        body=body,
    )


@pytest.fixture
def requests():
    return [
        make_request(method="POST", path="/webhook", headers={"Content-Type": "application/json", "X-Source": "github"}),
        make_request(method="GET", path="/ping", headers={"Content-Type": "text/plain"}),
        make_request(method="POST", path="/webhook/sub", headers={"Content-Type": "application/json"}),
        make_request(method="DELETE", path="/items/1", headers={"Content-Type": "application/json"}),
    ]


def test_filter_by_method(requests):
    result = RequestFilter(requests).by_method("POST").results()
    assert len(result) == 2
    assert all(r.method == "POST" for r in result)


def test_filter_by_method_case_insensitive(requests):
    result = RequestFilter(requests).by_method("get").results()
    assert len(result) == 1
    assert result[0].path == "/ping"


def test_filter_by_path_prefix(requests):
    result = RequestFilter(requests).by_path("/webhook").results()
    assert len(result) == 2


def test_filter_by_path_exact(requests):
    result = RequestFilter(requests).by_path("/ping").results()
    assert len(result) == 1


def test_filter_by_header_presence(requests):
    result = RequestFilter(requests).by_header("X-Source").results()
    assert len(result) == 1


def test_filter_by_header_with_value(requests):
    result = RequestFilter(requests).by_header("X-Source", "github").results()
    assert len(result) == 1


def test_filter_by_header_wrong_value(requests):
    result = RequestFilter(requests).by_header("X-Source", "gitlab").results()
    assert len(result) == 0


def test_filter_by_content_type(requests):
    result = RequestFilter(requests).by_content_type("application/json").results()
    assert len(result) == 3


def test_filter_limit(requests):
    result = RequestFilter(requests).limit(2).results()
    assert len(result) == 2
    assert result[-1].path == "/items/1"


def test_chained_filters(requests):
    result = (
        RequestFilter(requests)
        .by_method("POST")
        .by_path("/webhook")
        .results()
    )
    assert len(result) == 2


def test_len(requests):
    f = RequestFilter(requests).by_method("GET")
    assert len(f) == 1
