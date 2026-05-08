import pytest
from unittest.mock import MagicMock, patch
from hookshot.replayer import Replayer, ReplayError, ReplayResult
from hookshot.models import WebhookRequest
from hookshot.forwarder import ForwardError


@pytest.fixture
def sample_request():
    return WebhookRequest(
        method="POST",
        path="/webhook",
        query_string="source=github",
        headers={"Content-Type": "application/json"},
        body=b'{"event": "push"}',
    )


@pytest.fixture
def replayer():
    return Replayer(target_url="http://localhost:9000")


def test_replayer_requires_target_url():
    with pytest.raises(ReplayError, match="target_url is required"):
        Replayer(target_url="")


def test_replay_success(replayer, sample_request):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "OK"

    with patch.object(replayer._forwarder, "forward", return_value=mock_response):
        result = replayer.replay(sample_request)

    assert result.success is True
    assert result.status_code == 200
    assert result.response_body == "OK"
    assert result.request_id == sample_request.id


def test_replay_non_2xx_is_not_success(replayer, sample_request):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    with patch.object(replayer._forwarder, "forward", return_value=mock_response):
        result = replayer.replay(sample_request)

    assert result.success is False
    assert result.status_code == 500


def test_replay_raises_on_forward_error(replayer, sample_request):
    with patch.object(replayer._forwarder, "forward", side_effect=ForwardError("connection refused")):
        with pytest.raises(ReplayError, match="Replay failed"):
            replayer.replay(sample_request)


def test_replay_result_to_dict(sample_request):
    result = ReplayResult(
        request_id=sample_request.id,
        status_code=201,
        response_body="created",
        success=True,
    )
    d = result.to_dict()
    assert d["status_code"] == 201
    assert d["success"] is True
    assert d["response_body"] == "created"
    assert "request_id" in d
