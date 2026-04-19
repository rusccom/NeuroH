"""Environment configuration."""

from dataclasses import dataclass

from homeoorganism.config.relocation_mode import RelocationMode


@dataclass(frozen=True)
class EnvConfig:
    grid_size: int = 11
    view_size: int = 5
    episode_limit: int = 400
    ecology_enabled: bool = False
    enable_relocation: bool = False
    relocation_mode: RelocationMode = RelocationMode.EPISODIC_FIXED
    relocation_step: int = 150
    relocation_probability: float = 0.25
    food_nodes_per_episode: int = 2
    water_nodes_per_episode: int = 2
    rough_patches_per_episode: int = 3
