"""Build monitoring snapshots for continuous lives."""

from __future__ import annotations

from dataclasses import dataclass
from time import time

from homeoorganism.agent.belief_map import BeliefMap
from homeoorganism.agent.working_buffer import WorkingBuffer
from homeoorganism.analytics.windowed_metrics import ContinuousMetrics
from homeoorganism.config.relocation_mode import RelocationMode
from homeoorganism.decision.status_translator import StatusTranslator
from homeoorganism.domain.enums import CellType, ResourceType
from homeoorganism.env.ecology import count_nodes
from homeoorganism.env.gym_env import HomeoGridEnv
from homeoorganism.monitoring.domain.dto import (
    BeliefMapView,
    BlobVisualState,
    BodyTelemetry,
    MemoryTelemetry,
    NeedTelemetry,
    PlannerTelemetry,
    WorldTelemetry,
)
from homeoorganism.monitoring.domain.life_snapshot import CompletedLifeSummary, LifeSnapshot
from homeoorganism.orchestration.run_state_store import RunStateStore


@dataclass
class LifeSnapshotBuilder:
    belief_map: BeliefMap
    working_buffer: WorkingBuffer
    metrics: ContinuousMetrics
    run_state_store: RunStateStore
    translator: StatusTranslator
    env: HomeoGridEnv
    life_max_ticks: int

    def build(self, run_id: str, life_id: int, obs, completed_lives) -> LifeSnapshot:
        state = self.working_buffer.state
        need = state.need_state
        source, execution_mode, fast_conf, slow_conf, selected_conf = self._memory_inputs(state)
        return LifeSnapshot(
            ts_ms=int(time() * 1000),
            run_id=run_id,
            episode_id=life_id,
            run_state=self.run_state_store.get_run_state(),
            behavior_mode=self.translator.behavior_mode(need.active_need if need else None, state.selected_action),
            body=self._body(obs),
            need=self._need(need),
            memory=self._memory(state, source, execution_mode, fast_conf, slow_conf, selected_conf),
            planner=self._planner(state),
            world=self._world(obs, state),
            belief_map=self._belief(),
            blob=self._blob(fast_conf, slow_conf, need.critical if need else False, obs),
            life_id=life_id,
            current_tick=obs.step_idx,
            life_max_ticks=self.life_max_ticks,
            completed_lives=self._completed_lives(completed_lives),
            current_energy_ratio_100=self._ratio(100, 0),
            current_water_ratio_100=self._ratio(100, 1),
            current_deficit_variance=self._variance(100),
            long_window_energy_ratio=self._ratio(1000, 0),
            long_window_water_ratio=self._ratio(1000, 1),
            current_food_count=self._resource_count(CellType.FOOD),
            current_water_count=self._resource_count(CellType.WATER),
            next_relocation_tick=self._next_relocation_tick(),
        )

    def _world(self, obs, state) -> WorldTelemetry:
        target = self._target(state)
        path = [[pose.x, pose.y] for pose in state.current_plan.waypoints]
        biome = state.biome_id.value if state.biome_id else None
        return WorldTelemetry(
            biome_id=biome,
            pose=[obs.pose.x, obs.pose.y, int(obs.pose.dir)],
            target=target,
            path=path,
            step_idx=obs.step_idx,
            total_reward=0.0,
        )

    def _target(self, state) -> list[int] | None:
        proposal = state.selected_proposal
        if proposal is None or proposal.exact_cell is None:
            return None
        return [proposal.exact_cell.x, proposal.exact_cell.y]

    def _belief(self) -> BeliefMapView:
        return BeliefMapView(
            known_mask=self.belief_map.known_mask.astype(int).tolist(),
            tile_ids=self.belief_map.tile_ids.tolist(),
            frontier_cells=[[cell.x, cell.y] for cell in self.belief_map.get_frontier_cells()],
            observed_food=self._resources(ResourceType.FOOD),
            observed_water=self._resources(ResourceType.WATER),
        )

    def _blob(self, fast_conf: float, slow_conf: float, critical: bool, obs) -> BlobVisualState:
        need = self.working_buffer.state.need_state
        energy = need.energy_deficit if need else 0.0
        water = need.water_deficit if need else 0.0
        uncertainty = 1 - max(fast_conf, slow_conf, 0.0)
        instability = 1.0 if obs.body.last_collision else 0.0
        return BlobVisualState(
            stress=(energy + water) / 2,
            uncertainty=uncertainty,
            instability=instability,
            scale_x=1.0 + 0.45 * energy,
            scale_y=1.0 + 0.45 * water,
            scale_z=1.0 + 0.45 * uncertainty,
            pulse_hz=0.3 + 1.7 * ((energy + water) / 2),
            noise_amp=0.01 + 0.08 * instability,
            halo_level=0.2 + 0.8 * (1.0 if critical else 0.0),
        )

    def _resources(self, rtype: ResourceType) -> list[list[int]]:
        return [[pos.x, pos.y] for pos in self.belief_map.get_known_resources(rtype, 9999)]

    def _memory_inputs(self, state):
        proposal = state.selected_proposal
        source = proposal.source if proposal else None
        execution_mode = "none" if proposal is None else proposal.execution_mode.value
        fast_conf = 0.0 if state.fast_proposal is None else state.fast_proposal.confidence
        slow_conf = 0.0 if state.slow_proposal is None else state.slow_proposal.confidence
        selected_conf = 0.0 if proposal is None else proposal.confidence
        return source, execution_mode, fast_conf, slow_conf, selected_conf

    def _body(self, obs) -> BodyTelemetry:
        return BodyTelemetry(
            energy=obs.body.energy,
            water=obs.body.water,
            alive=obs.body.alive,
            last_collision=obs.body.last_collision,
        )

    def _need(self, need) -> NeedTelemetry:
        energy = 0.0 if need is None else need.energy_deficit
        water = 0.0 if need is None else need.water_deficit
        active = None if need is None or need.active_need is None else need.active_need.value
        critical = False if need is None else need.critical
        return NeedTelemetry(
            energy_deficit=energy,
            water_deficit=water,
            active_need=active,
            critical=critical,
            dominance=abs(energy - water),
        )

    def _memory(self, state, source, execution_mode: str, fast_conf: float, slow_conf: float, selected_conf: float) -> MemoryTelemetry:
        guidance_source = self.translator.decision_source(source)
        fast_target = None if state.fast_proposal is None or state.fast_proposal.exact_cell is None else [state.fast_proposal.exact_cell.x, state.fast_proposal.exact_cell.y]
        slow_region_size = 0 if state.slow_proposal is None else len(state.slow_proposal.region_cells)
        return MemoryTelemetry(
            guidance_source=guidance_source,
            decision_source=guidance_source,
            execution_mode=execution_mode,
            fast_confidence=fast_conf,
            slow_confidence=slow_conf,
            selected_confidence=selected_conf,
            fast_target=fast_target,
            slow_region_size=slow_region_size,
        )

    def _planner(self, state) -> PlannerTelemetry:
        return PlannerTelemetry(
            plan_valid=state.current_plan.valid,
            plan_cost=state.current_plan.cost,
            path_len=len(state.current_plan.waypoints),
            frontier_count=len(self.belief_map.get_frontier_cells()),
        )

    def _completed_lives(self, completed_lives) -> list[CompletedLifeSummary]:
        return [
            CompletedLifeSummary(
                life_id=life.life_id,
                duration_ticks=life.tick,
                end_reason=life.end_reason or "unknown",
            )
            for life in completed_lives
        ]

    def _ratio(self, window_size: int, index: int) -> float | None:
        ratios = self._window(window_size).current_ratios()
        if ratios is None:
            return None
        return ratios[index]

    def _variance(self, window_size: int) -> float | None:
        collector = self._window(window_size)
        if collector.current_ratios() is None:
            return None
        return collector._deficit_variance()

    def _window(self, window_size: int):
        return self.metrics._rolling[window_size]

    def _resource_count(self, cell: CellType) -> int:
        if self.env.state is None:
            return 0
        return count_nodes(self.env.state.tiles, cell)

    def _next_relocation_tick(self) -> int | None:
        if not self.env.env_config.enable_relocation:
            return None
        if self.env.env_config.relocation_mode != RelocationMode.CONTINUOUS_PERIODIC:
            return None
        return getattr(self.env.ecology, "_next_relocation_tick", None)
