"""Seed file loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SeedSet:
    path: Path

    def load(self) -> tuple[int, ...]:
        seeds = []
        for raw_line in self.path.read_text(encoding="utf-8").splitlines():
            line = raw_line.split("#", maxsplit=1)[0].strip()
            if not line:
                continue
            seeds.append(int(line))
        return tuple(seeds)
