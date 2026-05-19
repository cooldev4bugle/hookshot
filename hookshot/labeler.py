"""Automatic labeling of webhook requests based on configurable rules."""

from dataclasses import dataclass, field
from typing import Callable, List, Optional
from hookshot.models import WebhookRequest


class LabelError(Exception):
    pass


@dataclass
class LabelRule:
    label: str
    predicate: Callable[[WebhookRequest], bool]
    description: str = ""

    def matches(self, request: WebhookRequest) -> bool:
        try:
            return self.predicate(request)
        except Exception:
            return False


class Labeler:
    """Applies configurable label rules to requests."""

    def __init__(self) -> None:
        self._rules: List[LabelRule] = []

    def add_rule(self, label: str, predicate: Callable[[WebhookRequest], bool], description: str = "") -> None:
        if not label or not label.strip():
            raise LabelError("Label must be a non-empty string")
        if not callable(predicate):
            raise LabelError("Predicate must be callable")
        self._rules.append(LabelRule(label=label.strip(), predicate=predicate, description=description))

    def remove_rule(self, label: str) -> None:
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.label != label]
        if len(self._rules) == before:
            raise LabelError(f"No rule found for label '{label}'")

    def label(self, request: WebhookRequest) -> List[str]:
        """Return all labels whose rules match the given request."""
        return [rule.label for rule in self._rules if rule.matches(request)]

    def rules(self) -> List[dict]:
        return [{"label": r.label, "description": r.description} for r in self._rules]

    def clear(self) -> None:
        self._rules = []
