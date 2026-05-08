import requests
from typing import Optional
from hookshot.models import WebhookRequest
from hookshot.forwarder import Forwarder, ForwardError


class ReplayError(Exception):
    pass


class ReplayResult:
    def __init__(self, request_id: str, status_code: int, response_body: str, success: bool):
        self.request_id = request_id
        self.status_code = status_code
        self.response_body = response_body
        self.success = success

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "status_code": self.status_code,
            "response_body": self.response_body,
            "success": self.success,
        }


class Replayer:
    def __init__(self, target_url: str, timeout: int = 10):
        if not target_url:
            raise ReplayError("target_url is required for replay")
        self.target_url = target_url
        self.timeout = timeout
        self._forwarder = Forwarder(target_url=target_url, timeout=timeout)

    def replay(self, request: WebhookRequest) -> ReplayResult:
        """Replay a stored webhook request to the target URL."""
        try:
            response = self._forwarder.forward(request)
            try:
                body = response.text
            except Exception:
                body = ""
            return ReplayResult(
                request_id=request.id,
                status_code=response.status_code,
                response_body=body,
                success=200 <= response.status_code < 300,
            )
        except ForwardError as e:
            raise ReplayError(f"Replay failed for request {request.id}: {e}") from e
