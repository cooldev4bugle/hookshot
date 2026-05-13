"""Tests for hookshot.redactor."""

import json
import pytest
from hookshot.redactor import Redactor, REDACTED
from hookshot.models import WebhookRequest


@pytest.fixture
def redactor():
    return Redactor()


def make_request(headers=None, body=b"", content_type="text/plain", path="/hook", method="POST"):
    return WebhookRequest(
        method=method,
        path=path,
        query_string="",
        headers=headers or {},
        body=body,
        content_type=content_type,
    )


def test_redact_authorization_header(redactor):
    headers = {"Authorization": "Bearer secret123", "Content-Type": "application/json"}
    result = redactor.redact_headers(headers)
    assert result["Authorization"] == REDACTED
    assert result["Content-Type"] == "application/json"


def test_redact_headers_case_insensitive(redactor):
    headers = {"X-API-KEY": "abc", "x-api-key": "def"}
    result = redactor.redact_headers(headers)
    assert all(v == REDACTED for v in result.values())


def test_non_sensitive_headers_unchanged(redactor):
    headers = {"X-Custom-Header": "visible", "Accept": "*/*"}
    result = redactor.redact_headers(headers)
    assert result == headers


def test_redact_json_body_password(redactor):
    body = json.dumps({"username": "alice", "password": "hunter2"}).encode()
    result = redactor.redact_body(body, "application/json")
    data = json.loads(result)
    assert data["password"] == REDACTED
    assert data["username"] == "alice"


def test_redact_nested_json_body(redactor):
    body = json.dumps({"auth": {"token": "abc", "user": "bob"}}).encode()
    result = redactor.redact_body(body, "application/json")
    data = json.loads(result)
    assert data["auth"]["token"] == REDACTED
    assert data["auth"]["user"] == "bob"


def test_non_json_body_unchanged(redactor):
    body = b"plain text body"
    result = redactor.redact_body(body, "text/plain")
    assert result == body


def test_invalid_json_body_unchanged(redactor):
    body = b"{not valid json"
    result = redactor.redact_body(body, "application/json")
    assert result == body


def test_redact_request_full(redactor):
    body = json.dumps({"api_key": "secret", "event": "push"}).encode()
    req = make_request(
        headers={"Authorization": "token xyz", "X-Event": "push"},
        body=body,
        content_type="application/json",
    )
    result = redactor.redact_request(req)
    assert result["headers"]["Authorization"] == REDACTED
    assert result["headers"]["X-Event"] == "push"
    body_data = json.loads(result["body"])
    assert body_data["api_key"] == REDACTED
    assert body_data["event"] == "push"


def test_custom_sensitive_keys():
    redactor = Redactor(sensitive_body_keys=["my_secret"])
    body = json.dumps({"my_secret": "val", "password": "visible"}).encode()
    result = json.loads(redactor.redact_body(body, "application/json"))
    assert result["my_secret"] == REDACTED
    assert result["password"] == "visible"
