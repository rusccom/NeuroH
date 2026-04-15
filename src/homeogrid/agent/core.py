"""Agent core loop."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from homeogrid.agent.belief_map import BeliefMap
from homeogrid.agent.working_buffer import WorkingBuffer
from homeogrid.decision.arbiter import Arbiter
from homeogrid.decision.biome_inferer import BiomeInferer
from homeogrid.decision.drive_model import DriveModel
from homeogrid.decision.event_detector import EventDetector, belief_like_transform, visible_resources
from homeogrid.decision.explorer_policy import ExplorerPolicy
from homeogrid.domain.enums import CellType, EventType, ResourceType, TargetSource
from homeogrid.domain.events import EVENT_SALIENCE
from homeogrid.domain.types import EpisodeSummary, Observation, SalientEvent, Transition
from homeogrid.memory.fast_memory import FastMemory
from homeogrid.memory.replay_manager import ReplayManager
from homeogrid.memory.slow_memory import SlowMemory
from homeogrid.monitoring.interfaces import NullTelemetryPublisher, TelemetryPublisher
from homeogrid.planning.controller import LowLevelController
from homeogrid.planning.planner import Planner


@dataclass
class AgentCore:
    drive_model: DriveModel
    belief_map: BeliefMap
    biome_inferer: BiomeInferer
    working_buffer: WorkingBuffer
    fast_memory: FastMemory
    slow_memory: SlowMemory
    arbiter: Arbiter
    explorer: ExplorerPolicy
    planner: Planner
    controller: LowLevelController
    event_detector: EventDetector
    replay_manager: ReplayManager
    telemetry: TelemetryPublisher = field(default_factory=NullTelemetryPublisher)

    def __post_init__(self) -> None:
        self._last_obs: Observation | None = None
        self._last_need = None
        self._pending_events: list[SalientEvent] = []

    def begin_episode(self, initial_obs: Observation) -> None:
        self.belief_map.reset()
        self.biome_inferer.reset()
        self.working_buffer.reset()
        self.fast_memory.reset()
        self._pending_events = []
        self._last_need = None
        self.belief_map.update(initial_obs)
        self._last_obs = initial_obs

    def act(self, obs: Observation):
        self.belief_map.update(obs)
        need = self.drive_model.compute(obs.body)
        biome = self.biome_inferer.infer(obs, self.belief_map)
        fast = self._fast_query(need, obs)
        slow = self._slow_query(need, biome)
        selected = self.arbiter.choose(need, fast, slow, self.belief_map)
        selected = self._expand_selected(obs, selected)
        selected = self.planner.prepare_proposal(self.belief_map, obs.pose, selected)
        plan = self.planner.plan(self.belief_map, obs.pose, selected)
        action = self.controller.next_action(obs.pose, selected, plan)
        self.working_buffer.state.need_state = need
        self.working_buffer.state.biome_id = biome
        self.working_buffer.state.fast_proposal = fast
        self.working_buffer.state.slow_proposal = slow
        self.working_buffer.state.selected_proposal = selected
        self.working_buffer.state.selected_action = action
        self.working_buffer.state.current_plan = plan
        self._last_obs = obs
        self._last_need = need
        return action

    def observe_transition(self, transition: Transition) -> None:
        self._remember_visible_resources(transition.next_obs)
        self._handle_missing_expectation(transition)
        next_need = self.drive_model.compute(transition.next_obs.body)
        biome = self.working_buffer.state.biome_id
        events = self.event_detector.detect(transition, self._last_need, next_need, biome, self.belief_map)
        for event in events:
            self.fast_memory.write_event(event)
        self._pending_events.extend(events)
        self._last_obs = transition.next_obs
        self._last_need = next_need

    def end_episode(self, summary: EpisodeSummary) -> None:
        samples = self.replay_manager.build_samples(self.fast_memory.export_events())
        self.slow_memory.update(samples)

    def consume_pending_events(self) -> list[SalientEvent]:
        events = list(self._pending_events)
        self._pending_events.clear()
        return events

    def _fast_query(self, need, obs: Observation):
        if need.active_need is None:
            return None
        return self.fast_memory.query(need.active_need, obs.pose, obs.step_idx)

    def _slow_query(self, need, biome):
        if need.active_need is None or biome is None:
            return None
        return self.slow_memory.query(biome, need.active_need, self.belief_map)

    def _expand_selected(self, obs: Observation, proposal):
        if proposal.source == TargetSource.SLOW and proposal.region_cells:
            regional = self.explorer.propose_in_region(self.belief_map, obs.pose, list(proposal.region_cells))
            return replace(
                proposal,
                exact_cell=regional.exact_cell,
                execution_mode=regional.execution_mode,
            )
        if proposal.source == TargetSource.EXPLORE:
            return self.explorer.propose_global(self.belief_map, obs.pose)
        return proposal

    def _remember_visible_resources(self, obs: Observation) -> None:
        for pos, rtype in visible_resources(obs):
            self.fast_memory.observe_resource(rtype, pos, obs.step_idx)

    def _handle_missing_expectation(self, transition: Transition) -> None:
        proposal = self.working_buffer.state.selected_proposal
        if proposal is None or proposal.exact_cell is None or proposal.resource_type is None:
            return
        if not self._is_visible(transition.next_obs, proposal.exact_cell):
            return
        if self._resource_present(transition.next_obs, proposal.exact_cell, proposal.resource_type):
            return
        self.fast_memory.invalidate_resource(proposal.resource_type, proposal.exact_cell, transition.next_obs.step_idx)
        event = self._expectation_event(transition, proposal)
        self.fast_memory.write_event(event)
        self._pending_events.append(event)

    def _is_visible(self, obs: Observation, target) -> bool:
        radius = obs.tiles.shape[0] // 2
        dx = target.x - obs.pose.x
        dy = target.y - obs.pose.y
        return abs(dx) <= radius and abs(dy) <= radius

    def _resource_present(self, obs: Observation, target, rtype: ResourceType) -> bool:
        radius = obs.tiles.shape[0] // 2
        for row in range(obs.tiles.shape[0]):
            for col in range(obs.tiles.shape[1]):
                pos = belief_like_transform(obs.pose, col - radius, row - radius)
                if pos != target:
                    continue
                tile = CellType(int(obs.tiles[row, col]))
                if rtype == ResourceType.FOOD:
                    return tile == CellType.FOOD
                return tile == CellType.WATER
        return False

    def _expectation_event(self, transition: Transition, proposal) -> SalientEvent:
        return SalientEvent(
            event_type=EventType.EXPECTATION_VIOLATED,
            step_idx=transition.next_obs.step_idx,
            biome_id=self.working_buffer.state.biome_id,
            pose=transition.next_obs.pose,
            resource_type=proposal.resource_type,
            action=transition.action,
            salience=EVENT_SALIENCE[EventType.EXPECTATION_VIOLATED],
            position=proposal.exact_cell,
        )
