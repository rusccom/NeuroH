"""Monitoring DTOs."""

from __future__ import annotations

from pydantic import BaseModel, Field

from homeogrid.monitoring.domain.enums import (
    AlertLevel,
    BehaviorMode,
    DecisionSource,
    RunState,
)


class BodyTelemetry(BaseModel):
    energy: int
    water: int
    alive: bool
    last_collision: bool


class NeedTelemetry(BaseModel):
    energy_deficit: float
    water_deficit: float
    active_need: str | None
    critical: bool
    dominance: float


class MemoryTelemetry(BaseModel):
    guidance_source: DecisionSource
    decision_source: DecisionSource
    execution_mode: str
    fast_confidence: float
    slow_confidence: float
    selected_confidence: float
    fast_target: list[int] | None
    slow_region_size: int


class PlannerTelemetry(BaseModel):
    plan_valid: bool
    plan_cost: float
    path_len: int
    frontier_count: int


class WorldTelemetry(BaseModel):
    biome_id: str | None
    pose: list[int]
    target: list[int] | None
    path: list[list[int]]
    step_idx: int
    total_reward: float


class BeliefMapView(BaseModel):
    known_mask: list[list[int]]
    tile_ids: list[list[int]]
    frontier_cells: list[list[int]]
    observed_food: list[list[int]]
    observed_water: list[list[int]]


class BlobVisualState(BaseModel):
    stress: float
    uncertainty: float
    instability: float
    scale_x: float
    scale_y: float
    scale_z: float
    pulse_hz: float
    noise_amp: float
    halo_level: float


class StepSnapshot(BaseModel):
    ts_ms: int
    run_id: str
    episode_id: int
    run_state: RunState
    behavior_mode: BehaviorMode
    body: BodyTelemetry
    need: NeedTelemetry
    memory: MemoryTelemetry
    planner: PlannerTelemetry
    world: WorldTelemetry
    belief_map: BeliefMapView
    blob: BlobVisualState


class OperatorEvent(BaseModel):
    level: AlertLevel
    code: str
    message: str
    step_idx: int
    ts_ms: int


class EpisodeSummaryView(BaseModel):
    episode_id: int
    biome_id: str | None
    steps: int
    total_reward: float
    died: bool
    death_reason: str | None


class OperatorCommand(BaseModel):
    command_type: str = Field(alias="command")
    enabled: bool | None = None


class CommandResult(BaseModel):
    accepted: bool
    run_state: RunState
    message: str
