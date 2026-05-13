"""Request summarizer for generating statistics and summaries from stored requests."""

from collections import Counter
from typing import Any


class Summarizer:
    """Generates summary statistics from a collection of webhook requests."""

    def __init__(self, requests: list):
        self.requests = requests

    def method_counts(self) -> dict[str, int]:
        """Return a count of requests grouped by HTTP method."""
        counter = Counter(r.method for r in self.requests)
        return dict(counter)

    def path_counts(self) -> dict[str, int]:
        """Return a count of requests grouped by path."""
        counter = Counter(r.path for r in self.requests)
        return dict(counter)

    def content_type_counts(self) -> dict[str, int]:
        """Return a count of requests grouped by content type."""
        counter = Counter(r.content_type or "unknown" for r in self.requests)
        return dict(counter)

    def total(self) -> int:
        """Return total number of requests."""
        return len(self.requests)

    def to_dict(self) -> dict[str, Any]:
        """Return a full summary as a dictionary."""
        return {
            "total": self.total(),
            "by_method": self.method_counts(),
            "by_path": self.path_counts(),
            "by_content_type": self.content_type_counts(),
        }
