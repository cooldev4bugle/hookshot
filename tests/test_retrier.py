import pytest
from unittest.mock import MagicMock, patch
from hookshot.retrier import Retrier, RetryError, RetryResult
from hookshot.replayer import Replayer, ReplayResult, ReplayError
from hookshot.models import WebhookRequest


@pytest.fixture
def sample_request():
    return WebhookRequest(
        method="POST",
        path="/hook",
        query_string="",
        headers={"content-type": "application/json"},
        body=b'{"x": 1}',
    )


@pytest.fixture
def replayer():
    return MagicMock(spec=Replayer)


def test_invalid_max_attempts_raises(replayer):
    with pytest.raises(RetryError):
        Retrier(replayer=replayer, max_attempts=0)


def test_negative_backoff_raises(replayer):
    with pytest.raises(RetryError):
        Retrier(replayer=replayer, backoff=-1.0)


def test_succeeds_on_first_attempt(replayer, sample_request):
    replayer.replay.return_value = ReplayResult(status_code=200, success=True, body=b"ok")
    retrier = Retrier(replayer=replayer, max_attempts=3, backoff=0)
    result = retrier.retry(sample_request, _sleep=lambda s: None)

    assert result.succeeded is True
    assert result.attempts == 1
    assert replayer.replay.call_count == 1


def test_retries_on_non_2xx(replayer, sample_request):
    replayer.replay.return_value = ReplayResult(status_code=503, success=False, body=b"err")
    retrier = Retrier(replayer=replayer, max_attempts=3, backoff=0)
    result = retrier.retry(sample_request, _sleep=lambda s: None)

    assert result.succeeded is False
    assert result.attempts == 3
    assert len(result.errors) == 3


def test_succeeds_on_second_attempt(replayer, sample_request):
    replayer.replay.side_effect = [
        ReplayResult(status_code=500, success=False, body=b"fail"),
        ReplayResult(status_code=200, success=True, body=b"ok"),
    ]
    retrier = Retrier(replayer=replayer, max_attempts=3, backoff=0)
    result = retrier.retry(sample_request, _sleep=lambda s: None)

    assert result.succeeded is True
    assert result.attempts == 2
    assert len(result.errors) == 1


def test_handles_replay_error(replayer, sample_request):
    replayer.replay.side_effect = ReplayError("connection refused")
    retrier = Retrier(replayer=replayer, max_attempts=2, backoff=0)
    result = retrier.retry(sample_request, _sleep=lambda s: None)

    assert result.succeeded is False
    assert result.attempts == 2
    assert "connection refused" in result.errors[0]


def test_to_dict_shape(replayer, sample_request):
    replayer.replay.return_value = ReplayResult(status_code=200, success=True, body=b"ok")
    retrier = Retrier(replayer=replayer, max_attempts=1, backoff=0)
    result = retrier.retry(sample_request, _sleep=lambda s: None)
    d = result.to_dict()

    assert set(d.keys()) == {"request_id", "attempts", "succeeded", "last_status", "errors"}
    assert d["succeeded"] is True
    assert d["last_status"] == 200


def test_sleep_called_between_attempts(replayer, sample_request):
    replayer.replay.return_value = ReplayResult(status_code=500, success=False, body=b"")
    sleep_calls = []
    retrier = Retrier(replayer=replayer, max_attempts=3, backoff=2.0)
    retrier.retry(sample_request, _sleep=lambda s: sleep_calls.append(s))

    assert sleep_calls == [2.0, 4.0]
