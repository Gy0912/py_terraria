import random
import pygame
from settings import *

class World:
    def __init__(self):
        self.biome_map = self.generate_biomes()

    def generate_biomes(self):
        biomes = ["forest"] * 100  # 初始化全部为森林

        # 两侧各 10 份设为海洋
        biomes[:10] = ["ocean"] * 10
        biomes[-10:] = ["ocean"] * 10

        # 中间 16 份保持森林
        middle_start = 42
        middle_end = middle_start + 16
        biomes[middle_start:middle_end] = ["forest"] * 16

        # 不允许上述群系被覆盖
        protected_ranges = [(0, 13), (42, 58), (86, 100)]

        # 随机决定丛林雪地的左右并生成
        left_biome, right_biome = random.sample(["snow", "jungle"], 2)
        left_start = random.randint(13, 42 - 28 + 1)
        biomes[left_start:left_start + 28] = [left_biome] * 28
        right_start = random.randint(58, 86 - 28 + 1)
        biomes[right_start:right_start + 28] = [right_biome] * 28

        def is_conflict(start, length):
            end = start + length
            for s, e in protected_ranges:
                if not (end <= s or start >= e):
                    return True
            return False

        # 生成沙漠
        desert_parts = [11, 7]
        is_left = False
        for part_len in desert_parts:
            for i in range(100):
                pos = random.randint(13, 86 - part_len)
                if i == 0:
                    is_left = pos < 42
                elif (pos <= 42 and is_left) or (pos >= 58 and not is_left): 
                    break
                if not is_conflict(pos, part_len):
                    biomes[pos:pos + part_len] = ["desert"] * part_len
                    protected_ranges.append((pos, pos + part_len))
                    break
            else:
                raise RuntimeError("Failed to insert desert part.")
                    
        biome_map = [[None for _ in range(ACTUAL_MAP_HEIGHT)] for _ in range(ACTUAL_MAP_WIDTH)]

        for x in range(ACTUAL_MAP_WIDTH):
            biome_index = int(x / (ACTUAL_MAP_WIDTH / 100))
            surface_biome = biomes[biome_index]

            for y in range(ACTUAL_MAP_HEIGHT):
                if y < ACTUAL_SKY_HEIGHT:
                    biome_map[x][y] = "space"
                elif ACTUAL_SKY_HEIGHT <= y < ACTUAL_GROUND_HEIGHT:
                    biome_map[x][y] = surface_biome
                elif ACTUAL_GROUND_HEIGHT <= y < ACTUAL_CAVE_HEIGHT:
                    if surface_biome == "forest" or surface_biome == "desert":
                        biome_map[x][y] = "under_ground"
                    elif surface_biome == "snow":
                        biome_map[x][y] = "under_snow"
                    elif surface_biome == "jungle":
                        biome_map[x][y] = "under_jungle"
                    elif surface_biome == "ocean":
                        biome_map[x][y] = "under_ocean"
                elif ACTUAL_CAVE_HEIGHT <= y < ACTUAL_HELL_HEIGHT:
                    biome_map[x][y] = "cave"
                elif ACTUAL_HELL_HEIGHT <= y < ACTUAL_MAP_HEIGHT:
                    biome_map[x][y] = "hell"
                else:
                    biome_map[x][y] = "void"
        return biome_map

    def get_biome(self, x, y):
        x = x // TILE_SIZE
        y = y // TILE_SIZE
        if 0 <= x < ACTUAL_MAP_WIDTH and 0 <= y < ACTUAL_MAP_HEIGHT:
            return self.biome_map[x][y]
        return "void"
