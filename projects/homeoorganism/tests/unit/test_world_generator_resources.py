from homeoorganism.domain.enums import CellType
from homeoorganism.env.world_generator import WorldGenerator
from homeoorganism.env.world_state import find_cells


def test_world_generator_places_water_nodes(env_config, body_config):
    generator = WorldGenerator(env_config, body_config)
    world = generator.generate(seed=7)
    water = find_cells(world.tiles, CellType.WATER)
    assert len(water) == env_config.water_nodes_per_episode
