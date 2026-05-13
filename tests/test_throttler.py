import pytest
from hookshot.throttler import Throttler, ThrottleError


@pytest.fixture
def throttler():
    return Throttler(default_delay_ms=0)


def test_negative_default_delay_raises():
    with pytest.raises(ThrottleError, match="non-negative"):
        Throttler(default_delay_ms=-1)


def test_no_delay_returns_not_delayed(throttler):
    result = throttler.throttle("/webhook")
    assert result.delayed is False
    assert result.delay_ms == 0
    assert result.path == "/webhook"


def test_default_delay_applied(throttler):
    t = Throttler(default_delay_ms=50)
    slept = []
    result = t.throttle("/any", _sleep=slept.append)
    assert result.delayed is True
    assert result.delay_ms == 50
    assert slept == [0.05]


def test_set_path_delay(throttler):
    throttler.set_path_delay("/slow", 200)
    slept = []
    result = throttler.throttle("/slow/endpoint", _sleep=slept.append)
    assert result.delayed is True
    assert result.delay_ms == 200
    assert slept == [0.2]


def test_path_delay_prefix_match(throttler):
    throttler.set_path_delay("/api", 100)
    slept = []
    throttler.throttle("/api/v1/resource", _sleep=slept.append)
    assert slept == [0.1]


def test_non_matching_path_uses_default():
    t = Throttler(default_delay_ms=30)
    t.set_path_delay("/special", 500)
    slept = []
    t.throttle("/other", _sleep=slept.append)
    assert slept == [0.03]


def test_set_path_delay_negative_raises(throttler):
    with pytest.raises(ThrottleError, match="non-negative"):
        throttler.set_path_delay("/bad", -10)


def test_set_path_delay_no_leading_slash_raises(throttler):
    with pytest.raises(ThrottleError, match="start with"):
        throttler.set_path_delay("noslash", 100)


def test_remove_path_delay(throttler):
    throttler.set_path_delay("/tmp", 100)
    throttler.remove_path_delay("/tmp")
    slept = []
    throttler.throttle("/tmp/x", _sleep=slept.append)
    assert slept == []


def test_remove_unknown_path_raises(throttler):
    with pytest.raises(ThrottleError, match="No delay configured"):
        throttler.remove_path_delay("/ghost")


def test_config_returns_state():
    t = Throttler(default_delay_ms=10)
    t.set_path_delay("/hooks", 250)
    cfg = t.config()
    assert cfg["default_delay_ms"] == 10
    assert cfg["path_delays"] == {"/hooks": 250}


def test_to_dict_on_result(throttler):
    result = throttler.throttle("/x")
    d = result.to_dict()
    assert "delayed" in d
    assert "delay_ms" in d
    assert "path" in d
