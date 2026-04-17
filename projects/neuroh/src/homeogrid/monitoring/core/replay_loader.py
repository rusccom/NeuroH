"""Replay history loader."""

from __future__ import annotations

import json
from pathlib import Path


class ReplayLoader:
    def __init__(self, root_dir: str) -> None:
        self._root = Path(root_dir)

    def load(self, run_id: str, episode_id: int) -> dict:
        path = self._root / run_id / f"{episode_id}.jsonl"
        records = []
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    records.append(json.loads(line))
        return {"run_id": run_id, "episode_id": episode_id, "records": records}
