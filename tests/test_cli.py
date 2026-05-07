import pytest
from unittest.mock import patch, MagicMock
from hookshot.cli import parse_args, main


def test_default_args():
    args = parse_args([])
    assert args.port == 5000
    assert args.host == "127.0.0.1"
    assert args.target is None
    assert args.debug is False


def test_custom_port():
    args = parse_args(["--port", "8080"])
    assert args.port == 8080


def test_custom_host():
    args = parse_args(["--host", "0.0.0.0"])
    assert args.host == "0.0.0.0"


def test_target_url():
    args = parse_args(["--target", "http://localhost:3000"])
    assert args.target == "http://localhost:3000"


def test_debug_flag():
    args = parse_args(["--debug"])
    assert args.debug is True


def test_main_starts_server(capsys):
    mock_app = MagicMock()
    with patch("hookshot.cli.create_app", return_value=mock_app) as mock_create:
        main(["--port", "5001", "--host", "127.0.0.1"])
        mock_create.assert_called_once_with(target_url=None)
        mock_app.run.assert_called_once_with(host="127.0.0.1", port=5001, debug=False)


def test_main_prints_target_info(capsys):
    mock_app = MagicMock()
    with patch("hookshot.cli.create_app", return_value=mock_app):
        main(["--target", "http://example.com"])
    captured = capsys.readouterr()
    assert "forwarding to" in captured.out
    assert "http://example.com" in captured.out
