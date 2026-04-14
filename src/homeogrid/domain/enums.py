"""Domain enums used across the platform."""

from __future__ import annotations

from enum import Enum, IntEnum


class Direction(IntEnum):
    N = 0
    E = 1
    S = 2
    W = 3

    def left(self) -> "Direction":
        return Direction((int(self) - 1) % 4)

    def right(self) -> "Direction":
        return Direction((int(self) + 1) % 4)


class ActionType(IntEnum):
    TURN_LEFT = 0
    TURN_RIGHT = 1
    MOVE_FORWARD = 2
    INTERACT = 3
    WAIT = 4


class CellType(IntEnum):
    UNKNOWN = -1
    EMPTY = 0
    WALL = 1
    FOOD = 2
    WATER = 3
    ROUGH = 4
    LANDMARK = 5


class ResourceType(str, Enum):
    FOOD = "food"
    WATER = "water"


class BiomeId(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class TargetSource(str, Enum):
    FAST = "fast"
    SLOW = "slow"
    EXPLORE = "explore"


class EventType(str, Enum):
    RESOURCE_OBSERVED = "resource_observed"
    RESOURCE_CONSUMED = "resource_consumed"
    EXPECTATION_VIOLATED = "expectation_violated"
    RESOURCE_RELOCATED = "resource_relocated"
    COLLISION = "collision"
    DEATH = "death"
    NEED_SWITCH = "need_switch"
    BIOME_IDENTIFIED = "biome_identified"
