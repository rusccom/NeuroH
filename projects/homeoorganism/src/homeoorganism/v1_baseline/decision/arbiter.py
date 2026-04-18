"""Target source arbitration."""

from dataclasses import dataclass

from homeoorganism.v1_baseline.agent.belief_map import BeliefMap
from homeoorganism.config.memory_config import MemoryConfig
from homeoorganism.domain.enums import TargetSource
from homeoorganism.domain.types import NeedState, TargetProposal


@dataclass
class Arbiter:
    memory_config: MemoryConfig

    def choose(
        self,
        need_state: NeedState,
        fast: TargetProposal | None,
        slow: TargetProposal | None,
        belief_map: BeliefMap,
    ) -> TargetProposal:
        if need_state.active_need is None:
            return TargetProposal(TargetSource.EXPLORE, None, 0.0)
        if fast and fast.exact_cell is not None:
            return fast
        if slow and slow.confidence >= self.memory_config.slow_conf_threshold:
            return slow
        return TargetProposal(TargetSource.EXPLORE, need_state.active_need, 0.0)
