from pathlib import Path

import pytest

from homeoorganism.app.run import build_runtime
from homeoorganism.config.body_config import BodyConfig
from homeoorganism.config.env_config import EnvConfig
from homeoorganism.config.memory_config import MemoryConfig
from homeoorganism.config.planner_config import PlannerConfig
from homeoorganism.config.reward_config import RewardConfig


@pytest.fixture
def env_config():
    return EnvConfig()


@pytest.fixture
def body_config():
    return BodyConfig()


@pytest.fixture
def reward_config():
    return RewardConfig()


@pytest.fixture
def memory_config():
    return MemoryConfig()


@pytest.fixture
def planner_config():
    return PlannerConfig()


@pytest.fixture
def runtime(tmp_path: Path):
    return build_runtime("configs/full.yaml")
