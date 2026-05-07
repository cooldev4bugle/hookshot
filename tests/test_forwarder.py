import pytest
import httpx
from unittest.mock import patch, MagicMock

from hookshot.forwarder import Forwarder, ForwardError
from hookshot.models import WebhookRequest


@pytest.fixture
def sample_request():
    return WebhookRequest(
        method="POST",
        path="/webhook",
        query_string="token=abc",
        headers={"Content-Type": "application/json", "Host": "example.com"},
        body=b'{"event": "push"}',
    )


@pytest.fixture
def forwarder():
    return Forwarder(target_url="http://localhost:3000")


def test_forwarder_requires_target_url():
    with pytest.raises(ValueError):
        Forwarder(target_url="")


def test_build_url_with_query_string(forwarder):
    url = forwarder._build_url("/hook", "foo=bar")
    assert url == "http://localhost:3000/hook?foo=bar"


def test_build_url_without_query_string(forwarder):
    url = forwarder._build_url("/hook", None)
    assert url == "http://localhost:3000/hook"


def test_build_url_defaults_path(forwarder):
    url = forwarder._build_url("", None)
    assert url == "http://localhost:3000/"


def test_forward_strips_host_header(forwarder, sample_request):
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200

    with patch("httpx.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value.__enter__.return_value
        mock_client.request.return_value = mock_response

        forwarder.forward(sample_request)

        _, kwargs = mock_client.request.call_args
        assert "Host" not in kwargs["headers"]
        assert "host" not in kwargs["headers"]


def test_forward_returns_response(forwarder, sample_request):
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 204

    with patch("httpx.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value.__enter__.return_value
        mock_client.request.return_value = mock_response

        response = forwarder.forward(sample_request)

        assert response.status_code == 204


def test_forward_raises_forward_error_on_network_failure(forwarder, sample_request):
    with patch("httpx.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value.__enter__.return_value
        mock_client.request.side_effect = httpx.ConnectError("refused")

        with pytest.raises(ForwardError, match="Failed to forward request"):
            forwarder.forward(sample_request)
