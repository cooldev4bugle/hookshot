"""Tests for hookshot.notifier."""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from hookshot.notifier import Notifier, NotifyError, NotifyResult
from hookshot.models import WebhookRequest


@pytest.fixture
def sample_request():
    return WebhookRequest(
        method="POST",
        path="/hook",
        query_string="",
        headers={"content-type": "application/json"},
        body=b'{"event": "ping"}',
    )


@pytest.fixture
def notifier():
    return Notifier(callback_url="http://localhost:9999/notify")


def test_notifier_requires_valid_url():
    with pytest.raises(NotifyError):
        Notifier(callback_url="")


def test_notifier_rejects_non_http_url():
    with pytest.raises(NotifyError):
        Notifier(callback_url="ftp://example.com/notify")


def test_notify_success(notifier, sample_request):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.status_code = 200

    with patch("hookshot.notifier.http.post", return_value=mock_resp) as mock_post:
        result = notifier.notify(sample_request)

    assert result.success is True
    assert result.status_code == 200
    assert result.error is None

    call_kwargs = mock_post.call_args
    assert call_kwargs[0][0] == "http://localhost:9999/notify"
    payload = call_kwargs[1]["json"]
    assert payload["event"] == "webhook.received"
    assert payload["request_id"] == sample_request.id
    assert payload["method"] == "POST"


def test_notify_non_2xx_is_not_success(notifier, sample_request):
    mock_resp = MagicMock()
    mock_resp.ok = False
    mock_resp.status_code = 503

    with patch("hookshot.notifier.http.post", return_value=mock_resp):
        result = notifier.notify(sample_request)

    assert result.success is False
    assert result.status_code == 503


def test_notify_connection_error(notifier, sample_request):
    import requests.exceptions

    with patch(
        "hookshot.notifier.http.post",
        side_effect=requests.exceptions.ConnectionError("refused"),
    ):
        result = notifier.notify(sample_request)

    assert result.success is False
    assert "refused" in result.error


def test_notify_result_to_dict(notifier, sample_request):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.status_code = 200

    with patch("hookshot.notifier.http.post", return_value=mock_resp):
        result = notifier.notify(sample_request)

    d = result.to_dict()
    assert d["success"] is True
    assert d["status_code"] == 200
    assert d["error"] is None
