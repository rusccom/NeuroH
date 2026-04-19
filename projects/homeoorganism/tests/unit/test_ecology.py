from dataclasses import replace

import numpy as np

from homeoorganism.config.body_config import BodyConfig
from homeoorganism.config.ecology_config import EcologyConfig
from homeoorganism.config.env_config import EnvConfig
from homeoorganism.config.loader import load_config
from homeoorganism.config.relocation_mode import RelocationMode
from homeoorganism.config.reward_config import RewardConfig
from homeoorganism.domain.enums import ActionType, CellType
from homeoorganism.env.biome_templates import BIOME_TEMPLATES
from homeoorganism.env.ecology import EcologyLayer, candidate_cells, count_nodes
from homeoorganism.env.gym_env import HomeoGridEnv
from homeoorganism.env.world_generator import WorldGenerator
from homeoorganism.env.world_state import set_cell


def test_regen_reaches_target_count(env_config):
    state = _state_with_missing_resources(env_config, 0, 0)
    config = EcologyConfig(1, 1, 2, 2, 0.0, None, 1000, 0.0)
    state = _run_ecology(state, config, 8, True)
    assert count_nodes(state.tiles, CellType.FOOD) == 2
    assert count_nodes(state.tiles, CellType.WATER) == 2


def test_regen_deadline_resampled_on_skip(env_config):
    state = _state_with_missing_resources(env_config, 0, 0)
    block_resource_area(state, CellType.FOOD)
    block_resource_area(state, CellType.WATER)
    layer = EcologyLayer(EcologyConfig(1, 1, 2, 2, 0.0, None, 1000, 0.0), np.random.default_rng(7))
    layer.reset()
    state = replace(state, step_idx=1)
    next_state, relocated = layer.apply(state, True, RelocationMode.CONTINUOUS_PERIODIC)
    assert relocated is False
    assert layer._skipped_regens >= 2
    assert layer._next_food_regen_tick > 1
    assert layer._next_water_regen_tick > 1
    assert next_state is state


def test_periodic_relocation_statistical(env_config):
    state = _state_with_missing_resources(env_config, 2, 2)
    config = EcologyConfig(35, 35, 2, 2, 0.25, None, 1000, 0.5)
    layer = EcologyLayer(config, np.random.default_rng(3))
    layer.reset()
    relocations = 0
    for tick in range(1, 10_001):
        state = replace(state, step_idx=tick)
        state, relocated = layer.apply(state, False, RelocationMode.CONTINUOUS_PERIODIC)
        relocations += int(relocated)
    assert 2 <= relocations <= 8


def test_regen_and_relocation_never_coincide(env_config):
    state = _state_with_missing_resources(env_config, 1, 2)
    layer = EcologyLayer(EcologyConfig(1, 1, 2, 2, 0.0, None, 3, 1.0), np.random.default_rng(5))
    layer.reset()
    layer._next_food_regen_tick = 3
    layer._next_water_regen_tick = 99
    state = replace(state, step_idx=3)
    next_state, relocated = layer.apply(state, True, RelocationMode.CONTINUOUS_PERIODIC)
    assert relocated is True
    assert count_nodes(next_state.tiles, CellType.FOOD) == 1


def test_continuous_no_regen_has_no_regeneration(env_config):
    state = _state_with_missing_resources(env_config, 0, 0)
    config = EcologyConfig(1, 1, 2, 2, 0.0, None, 1000, 0.0)
    state = _run_ecology(state, config, 20, False)
    assert count_nodes(state.tiles, CellType.FOOD) == 0
    assert count_nodes(state.tiles, CellType.WATER) == 0


def test_episodic_mode_uses_old_relocation():
    env = HomeoGridEnv(
        EnvConfig(
            enable_relocation=True,
            relocation_mode=RelocationMode.EPISODIC_FIXED,
            relocation_step=2,
            relocation_probability=1.0,
        ),
        BodyConfig(),
        RewardConfig(),
    )
    env.reset(seed=11)
    _, _, _, _, info1 = env.step(ActionType.WAIT)
    _, _, _, _, info2 = env.step(ActionType.WAIT)
    assert info1.resource_relocated is False
    assert info2.resource_relocated is True


def test_loader_converts_relocation_mode_string(tmp_path):
    config_path = tmp_path / "env.yaml"
    config_path.write_text(
        "run_id: rc4-env\nenv:\n  relocation_mode: continuous_periodic\n",
        encoding="utf-8",
    )
    config = load_config(config_path)
    assert config.env.relocation_mode == RelocationMode.CONTINUOUS_PERIODIC


def _run_ecology(state, config, ticks, enabled):
    layer = EcologyLayer(config, np.random.default_rng(1))
    layer.reset()
    for tick in range(1, ticks + 1):
        state = replace(state, step_idx=tick)
        state, _ = layer.apply(state, enabled, RelocationMode.CONTINUOUS_PERIODIC)
    return state


def _state_with_missing_resources(env_config, food_count, water_count):
    generator = WorldGenerator(env_config, BodyConfig())
    state = generator.generate(seed=7)
    state = _set_resource_count(state, CellType.FOOD, food_count)
    return _set_resource_count(state, CellType.WATER, water_count)


def _set_resource_count(state, cell, keep_count):
    tiles = np.array(state.tiles, copy=True)
    cells = candidate_cells(cell, state.biome_id, np.random.default_rng(0))
    for pos in cells[keep_count:]:
        set_cell(tiles, pos, CellType.EMPTY)
    return replace(state, tiles=tiles)


def block_resource_area(state, cell):
    template = BIOME_TEMPLATES[state.biome_id]
    center = template.food_center if cell == CellType.FOOD else template.water_center
    for pos in candidate_cells(cell, state.biome_id, np.random.default_rng(0)):
        if pos == center:
            set_cell(state.tiles, pos, CellType.ROUGH)
            continue
        set_cell(state.tiles, pos, CellType.ROUGH)
