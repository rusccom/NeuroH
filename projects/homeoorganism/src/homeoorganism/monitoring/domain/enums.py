"""Monitoring enums."""

from enum import Enum


class RunState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ENDED = "ended"
    ERROR = "error"


class BehaviorMode(str, Enum):
    SEEK_FOOD = "seek_food"
    SEEK_WATER = "seek_water"
    EXPLORE = "explore"
    INTERACT = "interact"
    WAIT = "wait"


class DecisionSource(str, Enum):
    FAST = "fast"
    SLOW = "slow"
    EXPLORE = "explore"
    NONE = "none"


class AlertLevel(str, Enum):
    INFO = "info"
    WARN = "warn"
    CRITICAL = "critical"


class StreamEventType(str, Enum):
    FRAME = "frame"
    ALERT = "alert"
    SUMMARY = "summary"
    HEARTBEAT = "heartbeat"


class OperatorCommandType(str, Enum):
    PAUSE = "pause"
    RESUME = "resume"
    RESET_EPISODE = "reset_episode"
    SAVE_SNAPSHOT = "save_snapshot"
    TOGGLE_DEBUG = "toggle_debug"
