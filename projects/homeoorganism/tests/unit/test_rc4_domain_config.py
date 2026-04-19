from dataclasses import asdict
from pathlib import Path

from homeoorganism.config.ecology_config import EcologyConfig
from homeoorganism.config.loader import load_config
from homeoorganism.domain.life_state import LifeState
from homeoorganism.domain.shift_event import ShiftEvent


def test_load_config_builds_default_ecology():
    config = load_config(Path("configs/full.yaml"))
    assert config.ecology == EcologyConfig()


def test_load_config_reads_explicit_ecology(tmp_path: Path):
    config_path = tmp_path / "rc4.yaml"
    config_path.write_text(
        "run_id: rc4-test\necology:\n  food_regen_mean_ticks: 55\n  relocation_probability: 0.2\n",
        encoding="utf-8",
    )
    config = load_config(config_path)
    assert config.ecology.food_regen_mean_ticks == 55
    assert config.ecology.relocation_probability == 0.2


def test_rc4_domain_objects_are_serializable():
    life = LifeState(1, 10, 1000, None, None)
    shift = ShiftEvent(1, 1000, "relocation", True)
    assert asdict(life)["life_id"] == 1
    assert asdict(shift)["event_type"] == "relocation"
