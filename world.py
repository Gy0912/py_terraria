import random
from settings import *

class World:
    def __init__(self):
        self.biome_map = self.generate_biomes()

    def generate_biomes(self):
        biomes = ["ocean"] * 1 + ["forest"] * 2.6 + ["snow"] * 1.8 + ["jungle"] * 1.8 + ["desert"] * 1.8
        random.shuffle(biomes[1:-1])

        biome_map = []
        for i in range(MAP_WIDTH):
            biome_index = int(i / (MAP_WIDTH / 10))
            biome_map.append(biomes[biome_index])
        return biome_map

    def get_biome(self, x):
        if 0 <= x < MAP_WIDTH:
            return self.biome_map[x]
        return "forest"
