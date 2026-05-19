"""Middleware helpers to auto-label incoming requests after they are stored."""

from typing import List
from hookshot.labeler import Labeler
from hookshot.models import WebhookRequest
from hookshot.storage import RequestStore


def attach_labels(request: WebhookRequest, labeler: Labeler, store: RequestStore) -> List[str]:
    """Apply labeler rules to *request* and persist the result as tags.

    Labels are stored in the request's ``tags`` set so they are visible via
    the normal request inspection endpoints.  Returns the list of labels that
    were applied.
    """
    labels = labeler.label(request)
    if labels:
        if not hasattr(request, "tags") or request.tags is None:
            request.tags = set()
        for lbl in labels:
            request.tags.add(lbl)
        store.save(request)
    return labels


def build_labeler_hook(labeler: Labeler, store: RequestStore):
    """Return a callable suitable for use as a post-receive hook.

    Usage::

        hook = build_labeler_hook(labeler, store)
        # after storing a request:
        hook(webhook_request)
    """

    def _hook(request: WebhookRequest) -> List[str]:
        return attach_labels(request, labeler, store)

    return _hook
