"""Request sampler — probabilistic and rate-based sampling of incoming requests."""

import random
from typing import Optional
from hookshot.models import WebhookRequest


class SampleError(Exception):
    pass


class Sampler:
    """Decides whether a request should be kept based on a sampling strategy."""

    def __init__(self, rate: float = 1.0, seed: Optional[int] = None):
        if not (0.0 <= rate <= 1.0):
            raise SampleError("rate must be between 0.0 and 1.0")
        self._rate = rate
        self._rng = random.Random(seed)
        self._seen = 0
        self._kept = 0

    @property
    def rate(self) -> float:
        return self._rate

    def set_rate(self, rate: float) -> None:
        if not (0.0 <= rate <= 1.0):
            raise SampleError("rate must be between 0.0 and 1.0")
        self._rate = rate

    def should_keep(self, request: WebhookRequest) -> bool:
        """Return True if this request should be kept according to the sampling rate."""
        if request is None:
            raise SampleError("request must not be None")
        self._seen += 1
        keep = self._rng.random() < self._rate
        if keep:
            self._kept += 1
        return keep

    def filter(self, requests: list) -> list:
        """Return only the sampled subset of a list of requests."""
        return [r for r in requests if self.should_keep(r)]

    def stats(self) -> dict:
        return {
            "rate": self._rate,
            "seen": self._seen,
            "kept": self._kept,
            "dropped": self._seen - self._kept,
        }

    def reset_stats(self) -> None:
        self._seen = 0
        self._kept = 0
