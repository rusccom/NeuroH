from pathlib import Path

import pytest

from homeogrid.app.run import build_runtime
from homeogrid.config.body_config import BodyConfig
from homeogrid.config.env_config import EnvConfig
from homeogrid.config.memory_config import MemoryConfig
from homeogrid.config.planner_config import PlannerConfig
from homeogrid.config.reward_config import RewardConfig


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
