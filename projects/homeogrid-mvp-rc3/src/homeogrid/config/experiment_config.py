"""Experiment configuration."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ExperimentConfig:
    run_id: str
    base_seed: int = 42
    train_episodes: int = 200
    eval_episodes_seen: int = 100
    eval_episodes_relocation: int = 50
    enable_monitoring: bool = True
    save_monitor_stream: bool = True
    save_metrics: bool = True
    run_ablations: bool = True
    ablation_modes: tuple[str, ...] = field(
        default_factory=lambda: (
            "full",
            "no_fast",
            "no_slow",
            "no_interoception",
            "no_rough_cost",
            "full_observation",
        )
    )
