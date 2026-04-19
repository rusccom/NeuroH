"""Need computation."""

from dataclasses import dataclass

from homeoorganism.domain.enums import ResourceType
from homeoorganism.domain.types import BodyState, NeedState


@dataclass
class DriveModel:
    enabled: bool = True
    fixed_need: ResourceType = ResourceType.FOOD

    def compute(self, body: BodyState) -> NeedState:
        if not self.enabled:
            return NeedState(0.0, 0.0, self.fixed_need, False)
        energy_deficit = max(0, 70 - body.energy) / 70
        water_deficit = max(0, 70 - body.water) / 70
        if max(energy_deficit, water_deficit) < 0.1:
            active = None
        else:
            active = ResourceType.FOOD if energy_deficit > water_deficit else ResourceType.WATER
        critical = body.energy < 20 or body.water < 20
        return NeedState(energy_deficit, water_deficit, active, critical)

