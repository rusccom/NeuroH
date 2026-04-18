"""Core value objects."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from homeoorganism.domain.enums import (
    ActionType,
    BiomeId,
    Direction,
    ExecutionMode,
    EventType,
    ResourceType,
    TargetSource,
)


@dataclass(frozen=True)
class Vec2:
    x: int
    y: int


@dataclass(frozen=True)
class Pose:
    x: int
    y: int
    dir: Direction


@dataclass(frozen=True)
class BodyState:
    energy: int
    water: int
    last_collision: bool
    alive: bool


@dataclass(frozen=True)
class NeedState:
    energy_deficit: float
    water_deficit: float
    active_need: ResourceType | None
    critical: bool


@dataclass(frozen=True)
class Observation:
    tiles: np.ndarray
    landmark_ids: np.ndarray
    pose: Pose
    body: BodyState
    step_idx: int


@dataclass(frozen=True)
class TargetProposal:
    source: TargetSource
    resource_type: ResourceType | None
    confidence: float
    exact_cell: Vec2 | None = None
    region_cells: tuple[Vec2, ...] = ()
    stance_pose: Pose | None = None
    execution_mode: ExecutionMode = ExecutionMode.DIRECT


@dataclass(frozen=True)
class Plan:
    valid: bool
    waypoints: tuple[Pose, ...] = ()
    final_dir: Direction | None = None
    cost: float = 0.0


@dataclass(frozen=True)
class StepInfo:
    collision: bool
    entered_rough: bool
    consumed_food: bool
    consumed_water: bool
    action_cost_energy: int
    action_cost_water: int
    resource_relocated: bool
    death_reason: str | None


@dataclass(frozen=True)
class Transition:
    prev_obs: Observation
    action: ActionType
    next_obs: Observation
    reward: float
    terminated: bool
    truncated: bool
    info: StepInfo


@dataclass(frozen=True)
class SalientEvent:
    event_type: EventType
    step_idx: int
    biome_id: BiomeId | None
    pose: Pose
    resource_type: ResourceType | None
    action: ActionType | None
    salience: float
    position: Vec2 | None


@dataclass(frozen=True)
class ReplaySample:
    biome_id: BiomeId
    resource_type: ResourceType
    position: Vec2
    weight: float


@dataclass(frozen=True)
class EpisodeSummary:
    episode_id: int
    biome_id: BiomeId | None
    steps: int
    total_reward: float
    died: bool
    death_reason: str | None


@dataclass
class WorkingMemoryState:
    need_state: NeedState | None = None
    biome_id: BiomeId | None = None
    fast_proposal: TargetProposal | None = None
    slow_proposal: TargetProposal | None = None
    selected_proposal: TargetProposal | None = None
    selected_action: ActionType | None = None
    current_plan: Plan = field(default_factory=lambda: Plan(valid=False))
