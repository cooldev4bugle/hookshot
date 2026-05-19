import time
from dataclasses import dataclass, field
from typing import Optional, List
from hookshot.replayer import Replayer, ReplayResult, ReplayError
from hookshot.models import WebhookRequest


class RetryError(Exception):
    pass


@dataclass
class RetryResult:
    request_id: str
    attempts: int
    succeeded: bool
    last_status: Optional[int]
    errors: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "request_id": self.request_id,
            "attempts": self.attempts,
            "succeeded": self.succeeded,
            "last_status": self.last_status,
            "errors": self.errors,
        }


class Retrier:
    def __init__(self, replayer: Replayer, max_attempts: int = 3, backoff: float = 1.0):
        if max_attempts < 1:
            raise RetryError("max_attempts must be at least 1")
        if backoff < 0:
            raise RetryError("backoff must be non-negative")
        self._replayer = replayer
        self.max_attempts = max_attempts
        self.backoff = backoff

    def retry(self, request: WebhookRequest, _sleep=time.sleep) -> RetryResult:
        errors = []
        last_status = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                result: ReplayResult = self._replayer.replay(request)
                last_status = result.status_code
                if result.success:
                    return RetryResult(
                        request_id=request.id,
                        attempts=attempt,
                        succeeded=True,
                        last_status=last_status,
                        errors=errors,
                    )
                errors.append(f"attempt {attempt}: HTTP {result.status_code}")
            except ReplayError as exc:
                errors.append(f"attempt {attempt}: {exc}")

            if attempt < self.max_attempts:
                _sleep(self.backoff * attempt)

        return RetryResult(
            request_id=request.id,
            attempts=self.max_attempts,
            succeeded=False,
            last_status=last_status,
            errors=errors,
        )
