import random
import pygame
from settings import *


class World:
    def __init__(self):
        self.biome_strips = self.generate_biome_strips()
        self.tiles = {}
        self.generate_terrain()

    def generate_biome_strips(self):
        """Generate a 100-element strip array mapping horizontal zones to surface biomes."""
        biomes = ["forest"] * 100

        biomes[:10] = ["ocean"] * 10
        biomes[-10:] = ["ocean"] * 10

        middle_start = 42
        middle_end = middle_start + 16
        biomes[middle_start:middle_end] = ["forest"] * 16

        protected_ranges = [(0, 13), (42, 58), (86, 100)]

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

        return biomes

    def get_surface_biome(self, tile_x):
        """Return the surface biome name for a given tile column."""
        biome_index = int(tile_x / (ACTUAL_MAP_WIDTH / 100))
        biome_index = max(0, min(biome_index, 99))
        return self.biome_strips[biome_index]

    def get_biome(self, pixel_x, pixel_y):
        """Return the biome at a pixel position (computed on-the-fly, no matrix)."""
        tx = pixel_x // TILE_SIZE
        ty = pixel_y // TILE_SIZE
        if not (0 <= tx < ACTUAL_MAP_WIDTH and 0 <= ty < ACTUAL_MAP_HEIGHT):
            return "void"

        surface_biome = self.get_surface_biome(tx)

        if ty < ACTUAL_SKY_HEIGHT:
            return "space"
        elif ty < ACTUAL_GROUND_HEIGHT:
            return surface_biome
        elif ty < ACTUAL_CAVE_HEIGHT:
            if surface_biome in ("forest", "desert"):
                return "under_ground"
            elif surface_biome == "snow":
                return "under_snow"
            elif surface_biome == "jungle":
                return "under_jungle"
            elif surface_biome == "ocean":
                return "under_ocean"
            return "under_ground"
        elif ty < ACTUAL_HELL_HEIGHT:
            return "cave"
        else:
            return "hell"

    # ------------------------------------------------------------------
    # Tile terrain
    # ------------------------------------------------------------------

    def generate_terrain(self):
        """Generate a sparse tile dict with surface, underground, ores, and trees.

        Each tile is stored as ``self.tiles[(tx, ty)] = tile_type_string``.
        """
        surface_ty = ACTUAL_GROUND_HEIGHT
        self._surface_heights = {}

        # ------- Pass 1: surface profile with smooth variation -------
        height = 0
        for tx in range(ACTUAL_MAP_WIDTH):
            height += random.choice([-1, -1, 0, 0, 0, 0, 1, 1])
            height = max(-8, min(8, height))
            self._surface_heights[tx] = surface_ty + height

        # ------- Pass 2: fill columns -------
        underground_depth = 30
        for tx in range(ACTUAL_MAP_WIDTH):
            surface_biome = self.get_surface_biome(tx)
            local_surface = self._surface_heights[tx]

            if surface_biome == "ocean":
                for dy in range(underground_depth):
                    self.tiles[(tx, local_surface + dy)] = "sand"
            else:
                self.tiles[(tx, local_surface)] = "grass"
                for dy in range(1, 4):
                    self.tiles[(tx, local_surface + dy)] = "dirt"
                for dy in range(4, underground_depth):
                    self.tiles[(tx, local_surface + dy)] = "stone"

        # ------- Pass 3: ores (iron, copper, gold) in stone layer -------
        ore_configs = [
            ("iron_ore",   0.008, range(8, underground_depth)),
            ("copper_ore", 0.010, range(6, underground_depth - 5)),
            ("gold_ore",   0.003, range(15, underground_depth)),
        ]
        for ore_type, chance, depth_range in ore_configs:
            for tx in range(ACTUAL_MAP_WIDTH):
                local_surface = self._surface_heights[tx]
                for dy in depth_range:
                    if random.random() < chance:
                        ty = local_surface + dy
                        if self.tiles.get((tx, ty)) == "stone":
                            self.tiles[(tx, ty)] = ore_type

        # ------- Pass 4: simple caves (remove random clusters) -------
        for _ in range(ACTUAL_MAP_WIDTH // 8):
            cx = random.randint(0, ACTUAL_MAP_WIDTH - 1)
            local_surface = self._surface_heights.get(cx, surface_ty)
            cy = local_surface + random.randint(10, underground_depth - 2)
            radius = random.randint(2, 5)
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if dx * dx + dy * dy <= radius * radius:
                        self.tiles.pop((cx + dx, cy + dy), None)

        # ------- Pass 5: trees on grass (forest, jungle, snow) -------
        tree_chance = {"forest": 0.08, "jungle": 0.12, "snow": 0.04, "desert": 0, "ocean": 0}
        tx = 0
        while tx < ACTUAL_MAP_WIDTH:
            biome = self.get_surface_biome(tx)
            chance = tree_chance.get(biome, 0.05)
            if random.random() < chance:
                local_surface = self._surface_heights[tx]
                trunk_h = random.randint(4, 7)
                for dy in range(1, trunk_h + 1):
                    self.tiles[(tx, local_surface - dy)] = "wood"
                top = local_surface - trunk_h
                for lx in range(-2, 3):
                    for ly in range(-2, 1):
                        if (lx, ly) != (0, 0) or True:
                            leaf_pos = (tx + lx, top + ly)
                            if leaf_pos not in self.tiles:
                                self.tiles[leaf_pos] = "leaves"
                tx += random.randint(4, 8)
            else:
                tx += 1

    def get_tile(self, tx, ty):
        """Return tile type at tile coords, or None for air."""
        return self.tiles.get((tx, ty))

    def set_tile(self, tx, ty, tile_type):
        """Place or overwrite a tile."""
        self.tiles[(tx, ty)] = tile_type

    def remove_tile(self, tx, ty):
        """Remove (mine) a tile. Returns the old tile type or None."""
        return self.tiles.pop((tx, ty), None)
