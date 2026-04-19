"""Slow biome-level memory."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from homeoorganism.agent.belief_map import BeliefMap
from homeoorganism.config.memory_config import MemoryConfig
from homeoorganism.domain.enums import BiomeId, CellType, ResourceType, TargetSource
from homeoorganism.domain.types import ReplaySample, TargetProposal, Vec2


BIOME_INDEX = {BiomeId.A: 0, BiomeId.B: 1, BiomeId.C: 2, BiomeId.D: 3}
RESOURCE_INDEX = {ResourceType.FOOD: 0, ResourceType.WATER: 1}


@dataclass
class SlowMemory:
    memory_config: MemoryConfig
    config_hash: str
    enabled: bool = True

    def __post_init__(self) -> None:
        self.heatmaps = np.zeros((4, 2, 11, 11), dtype=np.float32)
        self.episode_count = 0

    def query(
        self,
        biome_id: BiomeId,
        rtype: ResourceType,
        belief_map: BeliefMap,
    ) -> TargetProposal | None:
        if not self.enabled:
            return None
        heatmap = self._masked_heatmap(biome_id, rtype, belief_map)
        if float(heatmap.max()) <= 0:
            return None
        cells = self._top_cells(heatmap)
        confidence = float(1 - np.exp(-heatmap.max()))
        return TargetProposal(
            source=TargetSource.SLOW,
            resource_type=rtype,
            confidence=confidence,
            region_cells=tuple(cells),
        )

    def update(self, samples: list[ReplaySample]) -> None:
        if not self.enabled or not samples:
            return
        for sample in samples:
            self._apply_sample(sample)
        self.heatmaps *= self.memory_config.slow_decay
        self.episode_count += 1

    def save(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        np.savez(
            path,
            heatmaps=self.heatmaps,
            episode_count=self.episode_count,
            config_hash=self.config_hash,
        )

    def load(self, path: str) -> None:
        file_path = Path(path)
        if not file_path.exists():
            return
        data = np.load(file_path, allow_pickle=False)
        self.heatmaps = data["heatmaps"]
        self.episode_count = int(data["episode_count"])

    def _masked_heatmap(
        self,
        biome_id: BiomeId,
        rtype: ResourceType,
        belief_map: BeliefMap,
    ) -> np.ndarray:
        heatmap = np.array(self.heatmaps[BIOME_INDEX[biome_id], RESOURCE_INDEX[rtype]], copy=True)
        heatmap[belief_map.tile_ids == int(CellType.WALL)] = 0.0
        target = CellType.FOOD if rtype == ResourceType.FOOD else CellType.WATER
        known_non_resource = belief_map.known_mask & (belief_map.tile_ids != int(target))
        heatmap[known_non_resource] = 0.0
        return heatmap

    def _top_cells(self, heatmap: np.ndarray) -> list[Vec2]:
        flat = heatmap.reshape(-1)
        top_k = np.argpartition(flat, -self.memory_config.slow_top_k)[-self.memory_config.slow_top_k :]
        ordered = top_k[np.argsort(flat[top_k])[::-1]]
        cells = []
        for index in ordered:
            y, x = divmod(int(index), heatmap.shape[1])
            if heatmap[y, x] <= 0:
                continue
            cells.append(Vec2(x, y))
        return cells

    def _apply_sample(self, sample: ReplaySample) -> None:
        biome = BIOME_INDEX[sample.biome_id]
        resource = RESOURCE_INDEX[sample.resource_type]
        for y in range(max(0, sample.position.y - 1), min(11, sample.position.y + 2)):
            for x in range(max(0, sample.position.x - 1), min(11, sample.position.x + 2)):
                if x == sample.position.x and y == sample.position.y:
                    weight = sample.weight
                else:
                    weight = sample.weight * 0.25
                self.heatmaps[biome, resource, y, x] += weight

