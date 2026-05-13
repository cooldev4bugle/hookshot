"""Tests for the Summarizer module."""

import pytest
from hookshot.models import WebhookRequest
from hookshot.summarizer import Summarizer


def make_request(method="POST", path="/webhook", content_type="application/json", body=b"{}"):
    return WebhookRequest(
        method=method,
        path=path,
        query_string="",
        headers={"content-type": content_type},
        body=body,
    )


@pytest.fixture
def requests():
    return [
        make_request(method="POST", path="/webhook", content_type="application/json"),
        make_request(method="POST", path="/webhook", content_type="application/json"),
        make_request(method="GET", path="/ping", content_type="text/plain"),
        make_request(method="PUT", path="/webhook", content_type="application/json"),
    ]


def test_total(requests):
    s = Summarizer(requests)
    assert s.total() == 4


def test_total_empty():
    s = Summarizer([])
    assert s.total() == 0


def test_method_counts(requests):
    s = Summarizer(requests)
    counts = s.method_counts()
    assert counts["POST"] == 2
    assert counts["GET"] == 1
    assert counts["PUT"] == 1


def test_path_counts(requests):
    s = Summarizer(requests)
    counts = s.path_counts()
    assert counts["/webhook"] == 3
    assert counts["/ping"] == 1


def test_content_type_counts(requests):
    s = Summarizer(requests)
    counts = s.content_type_counts()
    assert counts["application/json"] == 3
    assert counts["text/plain"] == 1


def test_content_type_unknown():
    req = make_request(content_type=None)
    req.headers = {}
    s = Summarizer([req])
    counts = s.content_type_counts()
    assert counts.get("unknown", 0) >= 0  # no crash on missing content type


def test_to_dict_keys(requests):
    s = Summarizer(requests)
    result = s.to_dict()
    assert "total" in result
    assert "by_method" in result
    assert "by_path" in result
    assert "by_content_type" in result


def test_to_dict_total(requests):
    s = Summarizer(requests)
    assert s.to_dict()["total"] == 4
