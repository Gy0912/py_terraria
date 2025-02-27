import random
from settings import *

class World:
    def __init__(self):
        self.biome_map = self.generate_biomes()

    def generate_biomes(self):
        biomes = ["ocean"] * 20 + ["forest"] * 26 + ["snow"] * 18 + ["jungle"] * 18 + ["desert"] * 18
        random.shuffle(biomes[1:-1])

        biome_map = [[None for _ in range(HELL_HEIGHT)] for _ in range(MAP_WIDTH)]

        for x in range(MAP_WIDTH):
            biome_index = int(x / (MAP_WIDTH / 100))
            surface_biome = biomes[biome_index]

            for y in range(HELL_HEIGHT):
                if y < SKY_HEIGHT:
                    biome_map[x][y] = "sky"
                elif SKY_HEIGHT <= y < GROUND_HEIGHT:
                    biome_map[x][y] = surface_biome
                elif GROUND_HEIGHT <= y < CAVE_HEIGHT:
                    if surface_biome == "forest" or surface_biome == "desert":
                        biome_map[x][y] = "under_ground"
                    elif surface_biome == "snow":
                        biome_map[x][y] = "under_snow"
                    elif surface_biome == "jungle":
                        biome_map[x][y] = "under_jungle"
                    elif surface_biome == "ocean":
                        biome_map[x][y] = "under_ocean"
                elif CAVE_HEIGHT <= y < HELL_HEIGHT:
                    biome_map[x][y] = "cave"
                elif HELL_HEIGHT <= y < MAP_HEIGHT:
                    biome_map[x][y] = "hell"
                else:
                    biome_map[x][y] = "void"
        return biome_map

    def get_biome(self, x, y):
        if 0 <= x < MAP_WIDTH and 0 <= y < HELL_HEIGHT:
            return self.biome_map[x][y]
        return "void"
