"""Build monitoring snapshots from simulation state."""

from __future__ import annotations

from dataclasses import dataclass
from time import time

from homeoorganism.agent.belief_map import BeliefMap
from homeoorganism.agent.working_buffer import WorkingBuffer
from homeoorganism.analytics.metrics import MetricsCollector
from homeoorganism.decision.status_translator import StatusTranslator
from homeoorganism.domain.enums import ResourceType
from homeoorganism.monitoring.domain.dto import (
    BeliefMapView,
    BlobVisualState,
    BodyTelemetry,
    MemoryTelemetry,
    NeedTelemetry,
    PlannerTelemetry,
    StepSnapshot,
    WorldTelemetry,
)
from homeoorganism.orchestration.run_state_store import RunStateStore


@dataclass
class SnapshotBuilder:
    belief_map: BeliefMap
    working_buffer: WorkingBuffer
    metrics: MetricsCollector
    run_state_store: RunStateStore
    translator: StatusTranslator
    episode_limit: int

    def build(self, run_id: str, episode_id: int, obs) -> StepSnapshot:
        state = self.working_buffer.state
        need = state.need_state
        source, execution_mode, fast_conf, slow_conf, selected_conf = self._memory_inputs(state)
        return StepSnapshot(
            ts_ms=int(time() * 1000),
            run_id=run_id,
            episode_id=episode_id,
            run_state=self.run_state_store.get_run_state(),
            behavior_mode=self.translator.behavior_mode(need.active_need if need else None, state.selected_action),
            body=self._body(obs),
            need=self._need(need),
            memory=self._memory(state, source, execution_mode, fast_conf, slow_conf, selected_conf),
            planner=self._planner(state),
            world=self._world(obs, state),
            belief_map=self._belief(),
            blob=self._blob(fast_conf, slow_conf, need.critical if need else False),
        )

    def _world(self, obs, state) -> WorldTelemetry:
        target = None
        if state.selected_proposal and state.selected_proposal.exact_cell:
            target = self._vec_to_list(state.selected_proposal.exact_cell)
        path = [[pose.x, pose.y] for pose in state.current_plan.waypoints]
        biome = state.biome_id.value if state.biome_id else None
        return WorldTelemetry(
            biome_id=biome,
            pose=[obs.pose.x, obs.pose.y, int(obs.pose.dir)],
            target=target,
            path=path,
            step_idx=obs.step_idx,
            total_reward=self.metrics.total_reward,
        )

    def _belief(self) -> BeliefMapView:
        return BeliefMapView(
            known_mask=self.belief_map.known_mask.astype(int).tolist(),
            tile_ids=self.belief_map.tile_ids.tolist(),
            frontier_cells=[[cell.x, cell.y] for cell in self.belief_map.get_frontier_cells()],
            observed_food=self._resources(ResourceType.FOOD),
            observed_water=self._resources(ResourceType.WATER),
        )

    def _blob(self, fast_conf: float, slow_conf: float, critical: bool) -> BlobVisualState:
        need = self.working_buffer.state.need_state
        energy = need.energy_deficit if need else 0.0
        water = need.water_deficit if need else 0.0
        stress = (energy + water) / 2
        uncertainty = 1 - max(fast_conf, slow_conf, 0.0)
        instability = min(1.0, 0.5 * self.metrics.collision_rate_window() + 0.5 * self.metrics.action_switch_rate_window())
        return BlobVisualState(
            stress=stress,
            uncertainty=uncertainty,
            instability=instability,
            scale_x=1.0 + 0.45 * energy,
            scale_y=1.0 + 0.45 * water,
            scale_z=1.0 + 0.45 * uncertainty,
            pulse_hz=0.3 + 1.7 * stress,
            noise_amp=0.01 + 0.08 * instability,
            halo_level=0.2 + 0.8 * (1.0 if critical else 0.0),
        )

    def _resources(self, rtype: ResourceType) -> list[list[int]]:
        return [[pos.x, pos.y] for pos in self.belief_map.get_known_resources(rtype, 9999)]

    def _vec_to_list(self, vec) -> list[int] | None:
        return None if vec is None else [vec.x, vec.y]

    def _memory_inputs(self, state):
        source = state.selected_proposal.source if state.selected_proposal else None
        execution_mode = "none"
        if state.selected_proposal is not None:
            execution_mode = state.selected_proposal.execution_mode.value
        fast_conf = state.fast_proposal.confidence if state.fast_proposal else 0.0
        slow_conf = state.slow_proposal.confidence if state.slow_proposal else 0.0
        selected_conf = state.selected_proposal.confidence if state.selected_proposal else 0.0
        return source, execution_mode, fast_conf, slow_conf, selected_conf

    def _body(self, obs) -> BodyTelemetry:
        return BodyTelemetry(
            energy=obs.body.energy,
            water=obs.body.water,
            alive=obs.body.alive,
            last_collision=obs.body.last_collision,
        )

    def _need(self, need) -> NeedTelemetry:
        energy = need.energy_deficit if need else 0.0
        water = need.water_deficit if need else 0.0
        active = need.active_need.value if need and need.active_need else None
        critical = need.critical if need else False
        return NeedTelemetry(energy_deficit=energy, water_deficit=water, active_need=active, critical=critical, dominance=abs(energy - water))

    def _memory(self, state, source, execution_mode: str, fast_conf: float, slow_conf: float, selected_conf: float) -> MemoryTelemetry:
        guidance_source = self.translator.decision_source(source)
        return MemoryTelemetry(
            guidance_source=guidance_source,
            decision_source=guidance_source,
            execution_mode=execution_mode,
            fast_confidence=fast_conf,
            slow_confidence=slow_conf,
            selected_confidence=selected_conf,
            fast_target=self._vec_to_list(state.fast_proposal.exact_cell if state.fast_proposal else None),
            slow_region_size=len(state.slow_proposal.region_cells) if state.slow_proposal else 0,
        )

    def _planner(self, state) -> PlannerTelemetry:
        return PlannerTelemetry(
            plan_valid=state.current_plan.valid,
            plan_cost=state.current_plan.cost,
            path_len=len(state.current_plan.waypoints),
            frontier_count=len(self.belief_map.get_frontier_cells()),
        )
