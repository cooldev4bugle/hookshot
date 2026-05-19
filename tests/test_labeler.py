"""Tests for hookshot.labeler."""

import pytest
from hookshot.labeler import Labeler, LabelError
from hookshot.models import WebhookRequest


def make_request(method="POST", path="/hook", headers=None, body=b""):
    return WebhookRequest(
        method=method,
        path=path,
        query_string="",
        headers=headers or {"content-type": "application/json"},
        body=body,
    )


@pytest.fixture
def labeler():
    return Labeler()


def test_add_rule_and_label_match(labeler):
    labeler.add_rule("post-hook", lambda r: r.method == "POST" and r.path == "/hook")
    result = labeler.label(make_request(method="POST", path="/hook"))
    assert "post-hook" in result


def test_non_matching_rule_excluded(labeler):
    labeler.add_rule("get-only", lambda r: r.method == "GET")
    result = labeler.label(make_request(method="POST"))
    assert "get-only" not in result


def test_multiple_rules_can_match(labeler):
    labeler.add_rule("is-post", lambda r: r.method == "POST")
    labeler.add_rule("has-json", lambda r: "content-type" in r.headers)
    result = labeler.label(make_request())
    assert "is-post" in result
    assert "has-json" in result


def test_empty_label_raises(labeler):
    with pytest.raises(LabelError):
        labeler.add_rule("", lambda r: True)


def test_whitespace_label_raises(labeler):
    with pytest.raises(LabelError):
        labeler.add_rule("   ", lambda r: True)


def test_non_callable_predicate_raises(labeler):
    with pytest.raises(LabelError):
        labeler.add_rule("bad", "not-a-function")


def test_remove_rule(labeler):
    labeler.add_rule("temp", lambda r: True)
    labeler.remove_rule("temp")
    assert labeler.label(make_request()) == []


def test_remove_unknown_rule_raises(labeler):
    with pytest.raises(LabelError):
        labeler.remove_rule("ghost")


def test_predicate_exception_is_swallowed(labeler):
    labeler.add_rule("boom", lambda r: 1 / 0)
    result = labeler.label(make_request())
    assert "boom" not in result


def test_clear_removes_all_rules(labeler):
    labeler.add_rule("a", lambda r: True)
    labeler.add_rule("b", lambda r: True)
    labeler.clear()
    assert labeler.rules() == []
    assert labeler.label(make_request()) == []


def test_rules_returns_metadata(labeler):
    labeler.add_rule("tagged", lambda r: True, description="marks all")
    rules = labeler.rules()
    assert len(rules) == 1
    assert rules[0]["label"] == "tagged"
    assert rules[0]["description"] == "marks all"
