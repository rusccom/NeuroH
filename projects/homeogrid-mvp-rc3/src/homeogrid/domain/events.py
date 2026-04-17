"""Event helpers and salience defaults."""

from __future__ import annotations

from homeogrid.domain.enums import EventType


EVENT_SALIENCE = {
    EventType.RESOURCE_OBSERVED: 2.0,
    EventType.RESOURCE_CONSUMED: 2.0,
    EventType.EXPECTATION_VIOLATED: 1.5,
    EventType.RESOURCE_RELOCATED: 1.5,
    EventType.COLLISION: 0.5,
    EventType.DEATH: 3.0,
    EventType.NEED_SWITCH: 1.0,
    EventType.BIOME_IDENTIFIED: 1.0,
}
