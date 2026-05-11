"""Tests for the Exporter module."""
import json
import pytest
from datetime import datetime, timezone
from hookshot.exporter import Exporter, ExportError
from hookshot.models import WebhookRequest


@pytest.fixture
def sample_requests():
    def make(method="POST", path="/hook", body=b'{"event": "push"}',
             headers=None, query_string=""):
        return WebhookRequest(
            method=method,
            path=path,
            query_string=query_string,
            headers=headers or {"Content-Type": "application/json"},
            body=body,
        )
    return [
        make(method="POST", path="/hook", query_string="token=abc"),
        make(method="GET", path="/ping", body=b"",
             headers={"Accept": "text/plain"}),
    ]


@pytest.fixture
def exporter(sample_requests):
    return Exporter(sample_requests)


def test_export_json_returns_list(exporter):
    result = exporter.to_json()
    data = json.loads(result)
    assert isinstance(data, list)
    assert len(data) == 2


def test_export_json_contains_fields(exporter):
    data = json.loads(exporter.to_json())
    assert "method" in data[0]
    assert "path" in data[0]
    assert "id" in data[0]


def test_export_csv_has_header(exporter):
    result = exporter.to_csv()
    lines = result.strip().splitlines()
    assert lines[0].startswith("id,received_at")


def test_export_csv_row_count(exporter):
    result = exporter.to_csv()
    lines = result.strip().splitlines()
    assert len(lines) == 3  # header + 2 rows


def test_export_har_structure(exporter):
    result = exporter.to_har()
    har = json.loads(result)
    assert "log" in har
    assert "entries" in har["log"]
    assert len(har["log"]["entries"]) == 2


def test_export_har_entry_has_request(exporter):
    har = json.loads(exporter.to_har())
    entry = har["log"]["entries"][0]
    assert "request" in entry
    assert entry["request"]["method"] == "POST"


def test_export_dispatches_format(exporter):
    result = exporter.export("json")
    assert json.loads(result)


def test_export_unsupported_format_raises(exporter):
    with pytest.raises(ExportError, match="Unsupported format"):
        exporter.export("xml")


def test_export_empty_list():
    exp = Exporter([])
    assert json.loads(exp.to_json()) == []
    assert exp.to_csv().strip().startswith("id,")
