"""Replay helpers."""

from __future__ import annotations

import json
from pathlib import Path


def replay_file(file_path: str) -> dict:
    path = Path(file_path)
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            records.append(json.loads(line))
    return {
        "file": str(path),
        "records": len(records),
        "types": sorted({record["type"] for record in records}),
    }
