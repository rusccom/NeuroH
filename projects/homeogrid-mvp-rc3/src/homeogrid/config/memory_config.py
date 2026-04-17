"""Memory configuration."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryConfig:
    fast_max_age: int = 80
    fast_max_events: int = 256
    slow_decay: float = 0.995
    slow_conf_threshold: float = 0.15
    slow_top_k: int = 8
