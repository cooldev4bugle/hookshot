"""Tag and label webhook requests for easier organization and filtering."""

from typing import List, Optional


class TagError(Exception):
    pass


class Tagger:
    """Manages tags on stored webhook requests via the RequestStore."""

    MAX_TAG_LENGTH = 32
    MAX_TAGS_PER_REQUEST = 10

    def __init__(self, store):
        if store is None:
            raise TagError("store is required")
        self.store = store
        self._tags: dict = {}  # request_id -> set of tags

    def add_tag(self, request_id: str, tag: str) -> List[str]:
        """Add a tag to a request. Returns current tag list."""
        tag = tag.strip().lower()
        if not tag:
            raise TagError("tag cannot be empty")
        if len(tag) > self.MAX_TAG_LENGTH:
            raise TagError(f"tag exceeds max length of {self.MAX_TAG_LENGTH}")
        if self.store.get(request_id) is None:
            raise TagError(f"request {request_id} not found")
        current = self._tags.setdefault(request_id, set())
        if len(current) >= self.MAX_TAGS_PER_REQUEST:
            raise TagError(f"request already has {self.MAX_TAGS_PER_REQUEST} tags")
        current.add(tag)
        return sorted(current)

    def remove_tag(self, request_id: str, tag: str) -> List[str]:
        """Remove a tag from a request. Returns current tag list."""
        tag = tag.strip().lower()
        current = self._tags.get(request_id, set())
        current.discard(tag)
        return sorted(current)

    def get_tags(self, request_id: str) -> List[str]:
        """Return sorted list of tags for a request."""
        return sorted(self._tags.get(request_id, set()))

    def find_by_tag(self, tag: str) -> list:
        """Return all requests that have the given tag."""
        tag = tag.strip().lower()
        results = []
        for request_id, tags in self._tags.items():
            if tag in tags:
                req = self.store.get(request_id)
                if req is not None:
                    results.append(req)
        return results

    def clear_tags(self, request_id: str) -> None:
        """Remove all tags from a request."""
        self._tags.pop(request_id, None)
