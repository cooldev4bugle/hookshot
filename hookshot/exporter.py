"""Export captured webhook requests to various formats."""
import json
import csv
import io
from typing import List
from hookshot.models import WebhookRequest


class ExportError(Exception):
    pass


class Exporter:
    SUPPORTED_FORMATS = ("json", "csv", "har")

    def __init__(self, requests: List[WebhookRequest]):
        self.requests = requests

    def to_json(self, indent: int = 2) -> str:
        data = [r.to_dict() for r in self.requests]
        return json.dumps(data, indent=indent, default=str)

    def to_csv(self) -> str:
        output = io.StringIO()
        fieldnames = ["id", "received_at", "method", "path", "query_string",
                      "content_type", "body"]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for req in self.requests:
            row = req.to_dict()
            row["body"] = req.body_text
            writer.writerow(row)
        return output.getvalue()

    def to_har(self) -> str:
        entries = []
        for req in self.requests:
            entry = {
                "startedDateTime": req.received_at.isoformat() + "Z",
                "request": {
                    "method": req.method,
                    "url": req.path + ("?" + req.query_string if req.query_string else ""),
                    "headers": [
                        {"name": k, "value": v}
                        for k, v in req.headers.items()
                    ],
                    "postData": {
                        "mimeType": req.content_type or "",
                        "text": req.body_text,
                    },
                },
            }
            entries.append(entry)
        har = {"log": {"version": "1.2", "entries": entries}}
        return json.dumps(har, indent=2, default=str)

    def export(self, fmt: str) -> str:
        fmt = fmt.lower()
        if fmt not in self.SUPPORTED_FORMATS:
            raise ExportError(
                f"Unsupported format '{fmt}'. Choose from: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        return getattr(self, f"to_{fmt}")()
