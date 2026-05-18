"""Compare two webhook requests and highlight differences."""

from dataclasses import dataclass, field
from typing import Any


class CompareError(Exception):
    pass


@dataclass
class Diff:
    key: str
    left: Any
    right: Any

    def to_dict(self):
        return {"key": self.key, "left": self.left, "right": self.right}


@dataclass
class CompareResult:
    left_id: str
    right_id: str
    diffs: list = field(default_factory=list)

    @property
    def identical(self):
        return len(self.diffs) == 0

    def to_dict(self):
        return {
            "left_id": self.left_id,
            "right_id": self.right_id,
            "identical": self.identical,
            "diffs": [d.to_dict() for d in self.diffs],
        }


class Comparator:
    """Compare two WebhookRequest objects field by field."""

    COMPARE_FIELDS = ["method", "path", "query_string", "headers", "body"]

    def __init__(self, store):
        if store is None:
            raise CompareError("store is required")
        self._store = store

    def compare(self, left_id: str, right_id: str) -> CompareResult:
        left = self._store.get(left_id)
        right = self._store.get(right_id)

        if left is None:
            raise CompareError(f"request not found: {left_id}")
        if right is None:
            raise CompareError(f"request not found: {right_id}")

        diffs = []
        for key in self.COMPARE_FIELDS:
            lv = getattr(left, key, None)
            rv = getattr(right, key, None)
            if lv != rv:
                diffs.append(Diff(key=key, left=lv, right=rv))

        return CompareResult(left_id=left_id, right_id=right_id, diffs=diffs)
