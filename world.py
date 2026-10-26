"""Chunked world storage. Chunks are generated lazily the first time they are touched."""
from settings import *
from tiles import TILES, AIR, SOLID, LIQUID, EMITS_LIGHT, T
from worldgen import WorldGen

LEAF_TILES = {T["leaves"], T["jungle_leaves"], T["boreal_leaves"]}


class World:
    def __init__(self, seed):
        self.seed = seed
        self.gen = WorldGen(seed)
        self.surface = self.gen.surface
        self.chunks = {}          # (cx, cy) -> bytearray of tile ids
        self.chunk_version = {}   # (cx, cy) -> int, bumped on every change (render caches use it)
        self.chunk_lights = {}    # (cx, cy) -> [(tx, ty, radius, intensity)]
        self.tile_damage = {}     # (tx, ty) -> [damage, frames since last hit]
        self.spawn_tx = WORLD_W // 2
        self.spawn_ty = self.surface[self.spawn_tx]

    # -------------------- chunks --------------------

    def chunk(self, cx, cy):
        key = (cx, cy)
        data = self.chunks.get(key)
        if data is None:
            data = self.gen.generate_chunk(cx, cy)
            self.chunks[key] = data
            self.chunk_version[key] = 0
            self._scan_lights(cx, cy)
        return data

    def _scan_lights(self, cx, cy):
        data = self.chunks[(cx, cy)]
        cs = CHUNK_SIZE
        lights = []
        for i, t in enumerate(data):
            if EMITS_LIGHT[t]:
                r, inten = TILES[t].light
                lights.append((cx * cs + i % cs, cy * cs + i // cs, r, inten))
        self.chunk_lights[(cx, cy)] = lights

    # -------------------- tiles --------------------

    def get_tile(self, tx, ty):
        if tx < 0 or tx >= WORLD_W or ty < 0 or ty >= WORLD_H:
            return AIR
        cs = CHUNK_SIZE
        return self.chunk(tx // cs, ty // cs)[(ty % cs) * cs + (tx % cs)]

    def is_solid(self, tx, ty):
        if tx < 0 or tx >= WORLD_W or ty >= WORLD_H:
            return True
        if ty < 0:
            return False
        return SOLID[self.get_tile(tx, ty)]

    def is_liquid(self, tx, ty):
        return LIQUID[self.get_tile(tx, ty)]

    def set_tile(self, tx, ty, tid):
        if tx < 0 or tx >= WORLD_W or ty < 0 or ty >= WORLD_H:
            return
        cs = CHUNK_SIZE
        cx, cy = tx // cs, ty // cs
        data = self.chunk(cx, cy)
        data[(ty % cs) * cs + (tx % cs)] = tid
        self.tile_damage.pop((tx, ty), None)
        self._scan_lights(cx, cy)
        # neighbours' edge outlines depend on this tile
        lx, ly = tx % cs, ty % cs
        for dcx, dcy, cond in ((0, 0, True), (-1, 0, lx == 0), (1, 0, lx == cs - 1),
                               (0, -1, ly == 0), (0, 1, ly == cs - 1)):
            key = (cx + dcx, cy + dcy)
            if cond and key in self.chunk_version:
                self.chunk_version[key] += 1

    def remove_tile(self, tx, ty):
        old = self.get_tile(tx, ty)
        if old != AIR:
            self.set_tile(tx, ty, AIR)
        return old

    def remove_tree(self, tx, ty):
        """Fell a whole tree/cactus starting at (tx, ty). Returns number of trunk tiles removed."""
        trunk_id = self.get_tile(tx, ty)
        removed = 0
        y = ty
        while self.get_tile(tx, y) == trunk_id:
            self.set_tile(tx, y, AIR)
            removed += 1
            y -= 1
        # canopy around the top of the trunk (y is now the row above the highest trunk tile)
        for dy in range(-3, 2):
            for dx in range(-2, 3):
                if self.get_tile(tx + dx, y + dy) in LEAF_TILES:
                    self.set_tile(tx + dx, y + dy, AIR)
        return removed

    # -------------------- mining damage --------------------

    def damage_tile(self, tx, ty, amount):
        """Add mining damage; returns current damage after the hit."""
        entry = self.tile_damage.get((tx, ty))
        if entry is None:
            entry = [0, 0]
            self.tile_damage[(tx, ty)] = entry
        entry[0] += amount
        entry[1] = 0
        return entry[0]

    def tick_damage(self):
        dead = []
        for key, entry in self.tile_damage.items():
            entry[1] += 1
            if entry[1] > 240:
                dead.append(key)
        for key in dead:
            del self.tile_damage[key]

    # -------------------- lights --------------------

    def light_sources(self, tx0, ty0, tx1, ty1):
        cs = CHUNK_SIZE
        out = []
        for cy in range(ty0 // cs, ty1 // cs + 1):
            for cx in range(tx0 // cs, tx1 // cs + 1):
                lights = self.chunk_lights.get((cx, cy))
                if lights:
                    out.extend(lights)
        return out

    # -------------------- environment queries --------------------

    def surface_at(self, tx):
        return self.surface[max(0, min(WORLD_W - 1, tx))]

    def layer_at(self, tx, ty):
        if ty < SPACE_LINE:
            return "space"
        if ty < self.surface_at(tx) + SURFACE_LAYER_DEPTH:
            return "surface"
        if ty < CAVERN_LINE:
            return "underground"
        if ty < HELL_LINE:
            return "cavern"
        return "hell"

    def biome_at(self, tx, ty):
        """Environmental biome (forest/desert/snow/jungle/ocean) used for blocks and creatures."""
        tx = max(0, min(WORLD_W - 1, tx))
        if self.layer_at(tx, ty) == "surface":
            return self.gen.column_biome[tx]
        return self.gen.block_biome(tx, ty)

    def get_biome(self, pixel_x, pixel_y):
        """Background name for a pixel position (relative to the local surface)."""
        tx = int(pixel_x) // TILE_SIZE
        ty = int(pixel_y) // TILE_SIZE
        layer = self.layer_at(tx, ty)
        if layer in ("space", "hell"):
            return layer
        if layer == "cavern":
            return "cave"
        biome = self.biome_at(tx, ty)
        if layer == "surface":
            return biome
        return {"snow": "under_snow", "jungle": "under_jungle", "ocean": "under_ocean"}.get(biome, "under_ground")
