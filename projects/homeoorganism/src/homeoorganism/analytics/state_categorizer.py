"""State categorization for RC4 windowed metrics."""

from homeoorganism.domain.enums import ResourceType
from homeoorganism.domain.types import BodyState


SETPOINT = 70
LOW_THRESHOLD = 15
DOMINANCE_GAP = 0.10


def classify_state(body: BodyState) -> str:
    if body.energy < LOW_THRESHOLD or body.water < LOW_THRESHOLD:
        return "critical"
    energy_gap, water_gap = normalized_deficits(body)
    if energy_gap - water_gap >= DOMINANCE_GAP:
        return "energy_dominant"
    if water_gap - energy_gap >= DOMINANCE_GAP:
        return "water_dominant"
    return "neutral"


def dominant_resource(body: BodyState) -> ResourceType:
    energy_gap, water_gap = normalized_deficits(body)
    if energy_gap > water_gap:
        return ResourceType.FOOD
    return ResourceType.WATER


def normalized_deficits(body: BodyState) -> tuple[float, float]:
    return ((SETPOINT - body.energy) / SETPOINT, (SETPOINT - body.water) / SETPOINT)
