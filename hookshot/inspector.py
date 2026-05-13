"""Request inspector: highlights anomalies and interesting properties."""

from dataclasses import dataclass, field
from typing import List
from hookshot.models import WebhookRequest


class InspectError(Exception):
    pass


@dataclass
class Insight:
    level: str  # 'info', 'warning', 'error'
    code: str
    message: str

    def to_dict(self):
        return {"level": self.level, "code": self.code, "message": self.message}


@dataclass
class InspectionResult:
    request_id: str
    insights: List[Insight] = field(default_factory=list)

    @property
    def has_warnings(self):
        return any(i.level == "warning" for i in self.insights)

    @property
    def has_errors(self):
        return any(i.level == "error" for i in self.insights)

    def to_dict(self):
        return {
            "request_id": self.request_id,
            "insights": [i.to_dict() for i in self.insights],
            "has_warnings": self.has_warnings,
            "has_errors": self.has_errors,
        }


class Inspector:
    """Inspects a WebhookRequest and returns a list of insights."""

    MAX_BODY_BYTES = 1_048_576  # 1 MB

    def inspect(self, request: WebhookRequest) -> InspectionResult:
        result = InspectionResult(request_id=request.id)

        self._check_content_type(request, result)
        self._check_body_size(request, result)
        self._check_json_body(request, result)
        self._check_missing_user_agent(request, result)

        return result

    def _check_content_type(self, request: WebhookRequest, result: InspectionResult):
        ct = request.content_type
        if not ct:
            result.insights.append(
                Insight("warning", "missing_content_type", "No Content-Type header present.")
            )

    def _check_body_size(self, request: WebhookRequest, result: InspectionResult):
        size = len(request.body) if request.body else 0
        if size == 0:
            result.insights.append(
                Insight("info", "empty_body", "Request body is empty.")
            )
        elif size > self.MAX_BODY_BYTES:
            result.insights.append(
                Insight("warning", "large_body", f"Body is {size} bytes, exceeds 1 MB.")
            )

    def _check_json_body(self, request: WebhookRequest, result: InspectionResult):
        if not request.is_json:
            return
        import json
        try:
            json.loads(request.body)
        except (ValueError, TypeError):
            result.insights.append(
                Insight("error", "invalid_json", "Content-Type is JSON but body is not valid JSON.")
            )

    def _check_missing_user_agent(self, request: WebhookRequest, result: InspectionResult):
        headers = {k.lower(): v for k, v in (request.headers or {}).items()}
        if "user-agent" not in headers:
            result.insights.append(
                Insight("info", "missing_user_agent", "No User-Agent header present.")
            )
