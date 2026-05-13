"""Tests for the rate limiter module."""

import time
import pytest
from unittest.mock import patch
from hookshot.rate_limiter import RateLimiter, RateLimitError


@pytest.fixture
def limiter():
    return RateLimiter(max_requests=3, window_seconds=60.0)


def test_invalid_max_requests():
    with pytest.raises(RateLimitError):
        RateLimiter(max_requests=0)


def test_invalid_window_seconds():
    with pytest.raises(RateLimitError):
        RateLimiter(max_requests=10, window_seconds=0)


def test_allows_requests_within_limit(limiter):
    assert limiter.is_allowed("127.0.0.1") is True
    assert limiter.is_allowed("127.0.0.1") is True
    assert limiter.is_allowed("127.0.0.1") is True


def test_blocks_request_over_limit(limiter):
    limiter.is_allowed("10.0.0.1")
    limiter.is_allowed("10.0.0.1")
    limiter.is_allowed("10.0.0.1")
    assert limiter.is_allowed("10.0.0.1") is False


def test_different_keys_are_independent(limiter):
    limiter.is_allowed("a")
    limiter.is_allowed("a")
    limiter.is_allowed("a")
    # key "a" is exhausted but "b" should still be allowed
    assert limiter.is_allowed("b") is True


def test_remaining_decrements(limiter):
    assert limiter.remaining("x") == 3
    limiter.is_allowed("x")
    assert limiter.remaining("x") == 2
    limiter.is_allowed("x")
    assert limiter.remaining("x") == 1


def test_remaining_never_negative(limiter):
    for _ in range(10):
        limiter.is_allowed("y")
    assert limiter.remaining("y") == 0


def test_reset_clears_state(limiter):
    limiter.is_allowed("z")
    limiter.is_allowed("z")
    limiter.is_allowed("z")
    assert limiter.is_allowed("z") is False
    limiter.reset("z")
    assert limiter.is_allowed("z") is True


def test_sliding_window_expires_old_requests():
    limiter = RateLimiter(max_requests=2, window_seconds=1.0)
    tick = [0.0]

    def fake_now():
        return tick[0]

    with patch.object(limiter, "_now", side_effect=fake_now):
        limiter.is_allowed("ip")
        limiter.is_allowed("ip")
        assert limiter.is_allowed("ip") is False

        # advance time beyond the window
        tick[0] = 2.0
        assert limiter.is_allowed("ip") is True
