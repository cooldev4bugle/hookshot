import pytest
from hookshot.transformer import Transformer, TransformError


@pytest.fixture
def transformer():
    return Transformer()


def test_set_header_overrides(transformer):
    transformer.set_header("X-Custom", "hello")
    result = transformer.apply_headers({"content-type": "application/json"})
    assert result["x-custom"] == "hello"
    assert result["content-type"] == "application/json"


def test_set_header_normalises_to_lower(transformer):
    transformer.set_header("Authorization", "Bearer tok")
    result = transformer.apply_headers({})
    assert result["authorization"] == "Bearer tok"


def test_remove_header(transformer):
    transformer.remove_header("X-Secret")
    result = transformer.apply_headers({"x-secret": "shh", "content-type": "text/plain"})
    assert "x-secret" not in result
    assert result["content-type"] == "text/plain"


def test_remove_header_case_insensitive(transformer):
    transformer.remove_header("Authorization")
    result = transformer.apply_headers({"authorization": "Bearer abc"})
    assert "authorization" not in result


def test_set_header_empty_name_raises(transformer):
    with pytest.raises(TransformError):
        transformer.set_header("", "value")


def test_remove_header_empty_name_raises(transformer):
    with pytest.raises(TransformError):
        transformer.remove_header("")


def test_apply_body_no_template_returns_original(transformer):
    body = b'{"event": "push"}'
    assert transformer.apply_body(body) == body


def test_apply_body_with_template(transformer):
    transformer.set_body_template('{"wrapped": "{event}"}')
    result = transformer.apply_body(b"", context={"event": "push"})
    assert result == b'{"wrapped": "push"}'


def test_apply_body_missing_variable_raises(transformer):
    transformer.set_body_template("{missing_key}")
    with pytest.raises(TransformError, match="Missing template variable"):
        transformer.apply_body(b"", context={})


def test_set_body_template_non_string_raises(transformer):
    with pytest.raises(TransformError):
        transformer.set_body_template(123)


def test_chaining_returns_self(transformer):
    result = transformer.set_header("X-A", "1").remove_header("X-B")
    assert result is transformer


def test_to_dict(transformer):
    transformer.set_header("x-env", "prod").remove_header("cookie")
    d = transformer.to_dict()
    assert d["header_overrides"] == {"x-env": "prod"}
    assert "cookie" in d["header_removals"]
    assert d["body_template"] is None
