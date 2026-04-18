"""YAML configuration loader."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

import yaml

from homeoorganism.config.body_config import BodyConfig
from homeoorganism.config.env_config import EnvConfig
from homeoorganism.config.experiment_config import ExperimentConfig
from homeoorganism.config.memory_config import MemoryConfig
from homeoorganism.config.monitor_config import MonitorConfig
from homeoorganism.config.planner_config import PlannerConfig
from homeoorganism.config.reward_config import RewardConfig


@dataclass(frozen=True)
class ConfigBundle:
    experiment: ExperimentConfig
    env: EnvConfig
    body: BodyConfig
    reward: RewardConfig
    memory: MemoryConfig
    planner: PlannerConfig
    monitor: MonitorConfig
    config_hash: str


def load_config(path: str | Path) -> ConfigBundle:
    file_path = Path(path)
    raw_text = file_path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw_text) or {}
    return ConfigBundle(
        experiment=_build_experiment(data),
        env=EnvConfig(**data.get("env", {})),
        body=BodyConfig(**data.get("body", {})),
        reward=RewardConfig(**data.get("reward", {})),
        memory=MemoryConfig(**data.get("memory", {})),
        planner=PlannerConfig(**data.get("planner", {})),
        monitor=MonitorConfig(**data.get("monitor", {})),
        config_hash=_hash_text(raw_text),
    )


def _build_experiment(data: dict[str, Any]) -> ExperimentConfig:
    fields = {
        key: value
        for key, value in data.items()
        if key
        not in {
            "env",
            "body",
            "reward",
            "memory",
            "planner",
            "monitor",
        }
    }
    if "ablation_modes" in fields:
        fields["ablation_modes"] = tuple(fields["ablation_modes"])
    return ExperimentConfig(**fields)


def _hash_text(raw_text: str) -> str:
    return sha256(raw_text.encode("utf-8")).hexdigest()
