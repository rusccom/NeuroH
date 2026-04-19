"""Relocation mode selection."""

from enum import Enum


class RelocationMode(str, Enum):
    DISABLED = "disabled"
    EPISODIC_FIXED = "episodic_fixed"
    CONTINUOUS_PERIODIC = "continuous_periodic"
