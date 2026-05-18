"""Request tracer — attaches trace IDs and tracks propagation across forwarded requests."""

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class TraceError(Exception):
    pass


@dataclass
class TraceEntry:
    trace_id: str
    request_id: str
    parent_trace_id: Optional[str] = None
    hops: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "trace_id": self.trace_id,
            "request_id": self.request_id,
            "parent_trace_id": self.parent_trace_id,
            "hops": list(self.hops),
        }


class Tracer:
    TRACE_HEADER = "x-hookshot-trace-id"

    def __init__(self) -> None:
        self._traces: Dict[str, TraceEntry] = {}

    def start_trace(self, request_id: str, incoming_headers: Dict[str, str]) -> TraceEntry:
        """Create a new trace entry for a request, inheriting parent trace if present."""
        if not request_id:
            raise TraceError("request_id is required")

        parent_id = incoming_headers.get(self.TRACE_HEADER)
        trace_id = str(uuid.uuid4())
        entry = TraceEntry(
            trace_id=trace_id,
            request_id=request_id,
            parent_trace_id=parent_id,
            hops=[],
        )
        self._traces[trace_id] = entry
        return entry

    def record_hop(self, trace_id: str, target_url: str) -> None:
        """Record a forwarding hop for an existing trace."""
        entry = self._traces.get(trace_id)
        if entry is None:
            raise TraceError(f"Unknown trace_id: {trace_id}")
        entry.hops.append(target_url)

    def get(self, trace_id: str) -> Optional[TraceEntry]:
        return self._traces.get(trace_id)

    def all(self) -> List[TraceEntry]:
        return list(self._traces.values())

    def inject_header(self, trace_id: str) -> Dict[str, str]:
        """Return headers dict to inject into outbound forwarded request."""
        return {self.TRACE_HEADER: trace_id}

    def clear(self) -> None:
        self._traces.clear()
