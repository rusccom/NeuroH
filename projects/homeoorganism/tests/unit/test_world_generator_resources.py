from homeoorganism.domain.enums import BiomeId, CellType
from homeoorganism.env.world_generator import WorldGenerator
from homeoorganism.env.world_state import find_cells


def test_world_generator_places_water_nodes(env_config, body_config):
    generator = WorldGenerator(env_config, body_config)
    world = generator.generate(seed=7)
    water = find_cells(world.tiles, CellType.WATER)
    assert len(water) == env_config.water_nodes_per_episode


def test_all_biomes_reachable_across_seeds(env_config, body_config):
    """Regression test for rc3 _pick_biome defect.

    In rc3, np.random.choice(list(BiomeId)) collapsed str-Enum members
    and always returned BiomeId.B. This test ensures all four biomes
    are produced across a range of seeds.
    """
    generator = WorldGenerator(env_config, body_config)
    biomes = {generator.generate(seed=seed).biome_id for seed in range(200)}
    assert biomes == set(BiomeId)
