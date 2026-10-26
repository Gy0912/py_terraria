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
        """Generate a sparse tile dict around the ground surface layer.

        Only tiles near the surface are pre-generated.  Deeper layers can be
        generated later on demand.  Each tile is stored as
        ``self.tiles[(tx, ty)] = tile_type_string``.
        """
        surface_ty = ACTUAL_GROUND_HEIGHT

        for tx in range(ACTUAL_MAP_WIDTH):
            surface_biome = self.get_surface_biome(tx)
            variation = random.randint(-2, 2)
            local_surface = surface_ty + variation

            if surface_biome == "ocean":
                self.tiles[(tx, local_surface)] = "sand"
                for depth in range(1, 6):
                    self.tiles[(tx, local_surface + depth)] = "sand"
            else:
                self.tiles[(tx, local_surface)] = "grass"
                for depth in range(1, 4):
                    self.tiles[(tx, local_surface + depth)] = "dirt"
                for depth in range(4, 8):
                    self.tiles[(tx, local_surface + depth)] = "stone"

    def get_tile(self, tx, ty):
        """Return tile type at tile coords, or None for air."""
        return self.tiles.get((tx, ty))

    def set_tile(self, tx, ty, tile_type):
        """Place or overwrite a tile."""
        self.tiles[(tx, ty)] = tile_type

    def remove_tile(self, tx, ty):
        """Remove (mine) a tile. Returns the old tile type or None."""
        return self.tiles.pop((tx, ty), None)
