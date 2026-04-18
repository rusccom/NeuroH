import numpy as np

from homeoorganism.domain.enums import ActionType, CellType, Direction
from homeoorganism.domain.types import BodyState, Pose, Vec2
from homeoorganism.env.gym_env import HomeoGridEnv
from homeoorganism.env.observation_encoder import ObservationEncoder
from homeoorganism.env.physiology import PhysiologyModel
from homeoorganism.env.reward_model import RewardModel
from homeoorganism.env.world_generator import WorldGenerator
from homeoorganism.env.world_state import GridWorldState, set_cell


def test_world_generator_is_deterministic(env_config, body_config):
    generator = WorldGenerator(env_config, body_config)
    left = generator.generate(seed=7)
    right = generator.generate(seed=7)
    assert left.biome_id == right.biome_id
    assert np.array_equal(left.tiles, right.tiles)


def test_observation_encoder_keeps_forward_up_for_east(env_config):
    tiles = np.full((11, 11), int(CellType.EMPTY), dtype=np.int16)
    tiles[0, :] = tiles[-1, :] = tiles[:, 0] = tiles[:, -1] = int(CellType.WALL)
    set_cell(tiles, Vec2(6, 5), CellType.FOOD)
    state = GridWorldState(
        biome_id="A",
        landmark_id=1,
        tiles=tiles,
        pose=Pose(5, 5, Direction.E),
        body=BodyState(70, 70, False, True),
        step_idx=0,
    )
    obs = ObservationEncoder(env_config).encode(state)
    assert obs.tiles[1, 2] == int(CellType.FOOD)


def test_physiology_handles_collision_and_interact(body_config):
    tiles = np.full((11, 11), int(CellType.EMPTY), dtype=np.int16)
    tiles[0, :] = tiles[-1, :] = tiles[:, 0] = tiles[:, -1] = int(CellType.WALL)
    set_cell(tiles, Vec2(5, 4), CellType.FOOD)
    state = GridWorldState(
        biome_id="A",
        landmark_id=1,
        tiles=tiles,
        pose=Pose(5, 5, Direction.N),
        body=BodyState(50, 50, False, True),
        step_idx=0,
    )
    model = PhysiologyModel(body_config)
    next_state, info = model.apply(state, ActionType.INTERACT)
    assert info.consumed_food is True
    assert next_state.body.energy > state.body.energy


def test_reward_model_applies_penalties(reward_config):
    reward = RewardModel(reward_config).compute(
        BodyState(10, 10, True, False),
        info=type(
            "Info",
            (),
            {"action_cost_energy": 2, "action_cost_water": 2, "collision": True, "death_reason": "x"},
        )(),
    )
    assert reward < -5


def test_homeoorganism_env_runs_one_step(env_config, body_config, reward_config):
    env = HomeoGridEnv(env_config, body_config, reward_config)
    obs, _ = env.reset(seed=5)
    next_obs, reward, terminated, truncated, info = env.step(ActionType.WAIT)
    assert next_obs.step_idx == obs.step_idx + 1
    assert isinstance(reward, float)
    assert terminated is False
    assert truncated is False
