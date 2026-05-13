"""Archive webhook requests to a local file for persistence across restarts."""

import json
import os
from typing import List, Optional

from hookshot.models import WebhookRequest
from hookshot.storage import RequestStore


class ArchiveError(Exception):
    pass


class Archiver:
    """Persists requests to a newline-delimited JSON file and can reload them."""

    def __init__(self, store: RequestStore, path: str):
        if not path:
            raise ArchiveError("Archive path must not be empty")
        self._store = store
        self._path = path

    def save(self) -> int:
        """Write all requests in the store to the archive file.
        Returns the number of requests written."""
        requests = self._store.all()
        try:
            with open(self._path, "w", encoding="utf-8") as fh:
                for req in requests:
                    fh.write(json.dumps(req.to_dict()) + "\n")
        except OSError as exc:
            raise ArchiveError(f"Failed to write archive: {exc}") from exc
        return len(requests)

    def load(self) -> int:
        """Read requests from the archive file into the store.
        Skips entries that already exist. Returns number of requests loaded."""
        if not os.path.exists(self._path):
            return 0
        loaded = 0
        try:
            with open(self._path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    req = WebhookRequest(
                        method=data["method"],
                        path=data["path"],
                        query_string=data.get("query_string", ""),
                        headers=data.get("headers", {}),
                        body=data["body"].encode("utf-8") if data.get("body") else b"",
                    )
                    req.id = data["id"]
                    if self._store.get(req.id) is None:
                        self._store.save(req)
                        loaded += 1
        except (OSError, json.JSONDecodeError, KeyError) as exc:
            raise ArchiveError(f"Failed to read archive: {exc}") from exc
        return loaded

    def clear(self) -> None:
        """Remove the archive file if it exists."""
        if os.path.exists(self._path):
            try:
                os.remove(self._path)
            except OSError as exc:
                raise ArchiveError(f"Failed to delete archive: {exc}") from exc
