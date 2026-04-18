"""Biome templates used for world generation."""

from __future__ import annotations

from dataclasses import dataclass

from homeoorganism.domain.enums import BiomeId
from homeoorganism.domain.types import Vec2


@dataclass(frozen=True)
class BiomeTemplate:
    biome_id: BiomeId
    landmark_id: int
    food_center: Vec2
    water_center: Vec2
    rough_centers: tuple[Vec2, ...]


BIOME_TEMPLATES = {
    BiomeId.A: BiomeTemplate(
        biome_id=BiomeId.A,
        landmark_id=1,
        food_center=Vec2(2, 2),
        water_center=Vec2(8, 8),
        rough_centers=(Vec2(8, 2), Vec2(7, 3), Vec2(8, 3)),
    ),
    BiomeId.B: BiomeTemplate(
        biome_id=BiomeId.B,
        landmark_id=2,
        food_center=Vec2(8, 2),
        water_center=Vec2(2, 8),
        rough_centers=(Vec2(2, 2), Vec2(3, 2), Vec2(2, 3)),
    ),
    BiomeId.C: BiomeTemplate(
        biome_id=BiomeId.C,
        landmark_id=3,
        food_center=Vec2(5, 2),
        water_center=Vec2(5, 8),
        rough_centers=(Vec2(2, 5), Vec2(3, 5), Vec2(2, 6)),
    ),
    BiomeId.D: BiomeTemplate(
        biome_id=BiomeId.D,
        landmark_id=4,
        food_center=Vec2(2, 5),
        water_center=Vec2(8, 5),
        rough_centers=(Vec2(5, 2), Vec2(5, 3), Vec2(6, 2)),
    ),
}
