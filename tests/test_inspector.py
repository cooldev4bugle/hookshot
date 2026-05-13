import json
import pytest
from hookshot.inspector import Inspector, InspectionResult
from hookshot.models import WebhookRequest


def make_request(**kwargs):
    defaults = dict(
        method="POST",
        path="/hook",
        query_string="",
        headers={"content-type": "application/json", "user-agent": "test/1.0"},
        body=json.dumps({"event": "push"}).encode(),
    )
    defaults.update(kwargs)
    return WebhookRequest(**defaults)


@pytest.fixture
def inspector():
    return Inspector()


def test_inspect_returns_result(inspector):
    req = make_request()
    result = inspector.inspect(req)
    assert isinstance(result, InspectionResult)
    assert result.request_id == req.id


def test_clean_request_has_no_insights(inspector):
    req = make_request()
    result = inspector.inspect(req)
    assert result.insights == []
    assert not result.has_warnings
    assert not result.has_errors


def test_missing_content_type_warns(inspector):
    req = make_request(headers={"user-agent": "test/1.0"})
    result = inspector.inspect(req)
    codes = [i.code for i in result.insights]
    assert "missing_content_type" in codes
    assert result.has_warnings


def test_empty_body_info(inspector):
    req = make_request(body=b"", headers={"content-type": "application/json", "user-agent": "x"})
    result = inspector.inspect(req)
    codes = [i.code for i in result.insights]
    assert "empty_body" in codes


def test_large_body_warns(inspector):
    big = b"x" * (1_048_576 + 1)
    req = make_request(body=big)
    result = inspector.inspect(req)
    codes = [i.code for i in result.insights]
    assert "large_body" in codes
    assert result.has_warnings


def test_invalid_json_body_errors(inspector):
    req = make_request(body=b"{not valid json", headers={"content-type": "application/json", "user-agent": "x"})
    result = inspector.inspect(req)
    codes = [i.code for i in result.insights]
    assert "invalid_json" in codes
    assert result.has_errors


def test_missing_user_agent_info(inspector):
    req = make_request(headers={"content-type": "application/json"})
    result = inspector.inspect(req)
    codes = [i.code for i in result.insights]
    assert "missing_user_agent" in codes


def test_to_dict_shape(inspector):
    req = make_request(headers={"content-type": "application/json"})
    result = inspector.inspect(req)
    d = result.to_dict()
    assert "request_id" in d
    assert "insights" in d
    assert "has_warnings" in d
    assert "has_errors" in d
    assert isinstance(d["insights"], list)


def test_insight_to_dict(inspector):
    req = make_request(headers={})
    result = inspector.inspect(req)
    for insight in result.insights:
        d = insight.to_dict()
        assert set(d.keys()) == {"level", "code", "message"}
