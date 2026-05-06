"""Tests for hookshot.models."""

from datetime import datetime

import pytest

from hookshot.models import WebhookRequest


@pytest.fixture
def sample_request() -> WebhookRequest:
    return WebhookRequest(
        method="POST",
        path="/webhook/github",
        headers={"content-type": "application/json", "x-hub-signature": "sha256=abc"},
        body=b'{"action": "push"}',
        query_params={"token": "secret"},
    )


def test_request_has_auto_id(sample_request):
    assert sample_request.id
    assert len(sample_request.id) == 36  # UUID4 format


def test_request_has_received_at(sample_request):
    assert isinstance(sample_request.received_at, datetime)


def test_body_text_decodes_utf8(sample_request):
    assert sample_request.body_text == '{"action": "push"}'


def test_body_text_handles_invalid_bytes():
    req = WebhookRequest(
        method="POST",
        path="/bin",
        headers={},
        body=b"\xff\xfe binary data",
    )
    # Should not raise, replaces undecodable bytes
    assert isinstance(req.body_text, str)


def test_to_dict_contains_expected_keys(sample_request):
    d = sample_request.to_dict()
    for key in ("id", "received_at", "method", "path", "query_params", "headers", "body", "content_length"):
        assert key in d


def test_to_dict_content_length(sample_request):
    d = sample_request.to_dict()
    assert d["content_length"] == len(b'{"action": "push"}')


def test_round_trip_serialization(sample_request):
    d = sample_request.to_dict()
    restored = WebhookRequest.from_dict(d)
    assert restored.id == sample_request.id
    assert restored.method == sample_request.method
    assert restored.path == sample_request.path
    assert restored.headers == sample_request.headers
    assert restored.body == sample_request.body
    assert restored.query_params == sample_request.query_params
    assert restored.received_at == sample_request.received_at
