import json
import pytest
from datetime import datetime, timezone
from hookshot.mirror import Mirror, MirrorError
from hookshot.models import WebhookRequest


@pytest.fixture
def sample_request():
    return WebhookRequest(
        method="POST",
        path="/webhook",
        headers={"content-type": "application/json", "x-secret": "abc"},
        body=b'{"event": "push"}',
        query_string="ref=main",
    )


@pytest.fixture
def mirror():
    return Mirror()


def test_reflect_raises_on_none(mirror):
    with pytest.raises(MirrorError):
        mirror.reflect(None)


def test_reflect_includes_basic_fields(mirror, sample_request):
    result = mirror.reflect(sample_request)
    assert result["method"] == "POST"
    assert result["path"] == "/webhook"
    assert "id" in result
    assert "received_at" in result


def test_reflect_includes_query_string(mirror, sample_request):
    result = mirror.reflect(sample_request)
    assert result["query_string"] == "ref=main"


def test_reflect_omits_query_string_when_empty(mirror):
    req = WebhookRequest(method="GET", path="/ping", headers={}, body=b"")
    result = mirror.reflect(req)
    assert "query_string" not in result


def test_reflect_includes_headers_by_default(mirror, sample_request):
    result = mirror.reflect(sample_request)
    assert "headers" in result
    assert result["headers"]["content-type"] == "application/json"


def test_reflect_excludes_headers_when_disabled(sample_request):
    m = Mirror(include_headers=False)
    result = m.reflect(sample_request)
    assert "headers" not in result


def test_reflect_parses_json_body(mirror, sample_request):
    result = mirror.reflect(sample_request)
    assert result["body"] == {"event": "push"}


def test_reflect_returns_text_for_non_json_body():
    m = Mirror()
    req = WebhookRequest(
        method="POST",
        path="/hook",
        headers={"content-type": "text/plain"},
        body=b"hello world",
    )
    result = m.reflect(req)
    assert result["body"] == "hello world"


def test_reflect_excludes_body_when_disabled(sample_request):
    m = Mirror(include_body=False)
    result = m.reflect(sample_request)
    assert "body" not in result


def test_to_json_returns_valid_json(mirror, sample_request):
    output = mirror.to_json(sample_request)
    parsed = json.loads(output)
    assert parsed["method"] == "POST"
