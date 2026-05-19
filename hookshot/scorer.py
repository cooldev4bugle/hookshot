"""Request scorer — assigns a numeric quality/anomaly score to captured requests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from hookshot.models import WebhookRequest


class ScoreError(Exception):
    pass


@dataclass
class ScoreBreakdown:
    label: str
    delta: float
    reason: str

    def to_dict(self) -> dict:
        return {"label": self.label, "delta": self.delta, "reason": self.reason}


@dataclass
class ScoreResult:
    request_id: str
    score: float
    breakdowns: List[ScoreBreakdown] = field(default_factory=list)

    @property
    def grade(self) -> str:
        if self.score >= 80:
            return "A"
        if self.score >= 60:
            return "B"
        if self.score >= 40:
            return "C"
        return "D"

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "score": round(self.score, 2),
            "grade": self.grade,
            "breakdowns": [b.to_dict() for b in self.breakdowns],
        }


class Scorer:
    """Score a WebhookRequest on several heuristics, starting from 100."""

    BASE_SCORE = 100.0

    def score(self, request: WebhookRequest) -> ScoreResult:
        if request is None:
            raise ScoreError("request must not be None")

        s = self.BASE_SCORE
        breakdowns: List[ScoreBreakdown] = []

        # Penalise missing Content-Type
        if not request.content_type:
            s -= 20
            breakdowns.append(ScoreBreakdown("content_type", -20, "missing Content-Type header"))

        # Penalise very large bodies (> 512 KB)
        body_len = len(request.body) if request.body else 0
        if body_len > 512 * 1024:
            s -= 15
            breakdowns.append(ScoreBreakdown("body_size", -15, "body exceeds 512 KB"))

        # Penalise missing User-Agent
        headers = {k.lower(): v for k, v in (request.headers or {}).items()}
        if "user-agent" not in headers:
            s -= 10
            breakdowns.append(ScoreBreakdown("user_agent", -10, "missing User-Agent header"))

        # Reward JSON payloads with valid structure
        if request.is_json:
            s += 5
            breakdowns.append(ScoreBreakdown("json_body", +5, "well-formed JSON body"))

        return ScoreResult(
            request_id=request.id,
            score=max(0.0, min(100.0, s)),
            breakdowns=breakdowns,
        )
