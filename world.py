"""Chunked world storage: tiles, background walls, liquid levels and multi-tile objects.

Chunks are generated lazily the first time they are touched. Liquids flow with a
small cellular automaton that only touches "active" cells.
"""
import random

from settings import *
from tiles import (TILES, AIR, SOLID, LIQUID, EMITS_LIGHT, BLOCKS_CREATURES, BLOCKS_FLYERS, IS_OBJECT,
                   LEAF_TILES, T)
from worldgen import WorldGen

_OBSIDIAN = T["obsidian"]
CONTAINER_SIZE = {"chest": 20, "gold_chest": 20, "shipping_bin": 20, "furnace": 3, "collector": 20}


class World:
    def __init__(self, seed):
        self.seed = seed
        self.gen = WorldGen(seed)
        self.surface = self.gen.surface
        self.chunks = {}          # (cx, cy) -> bytearray tile ids
        self.walls = {}           # (cx, cy) -> bytearray wall ids
        self.liquid = {}          # (cx, cy) -> bytearray liquid levels 0..8
        self.chunk_version = {}   # tiles + walls render version
        self.liquid_version = {}  # liquid render version
        self.chunk_lights = {}    # (cx, cy) -> [(tx, ty, radius, intensity)]
        self.modified = set()     # chunks that differ from generation (saved to disk)
        self.saved_chunks = {}    # chunk data loaded from a save, applied on first touch
        self.explored = set()     # chunks seen in an earlier session (minimap regenerates them lazily)
        self.tile_damage = {}     # (tx, ty) -> [damage, frames since last hit]
        self.wall_damage = {}
        self.objects = {}         # anchor (ax, ay) -> tile id
        self.obj_cells = {}       # cell -> anchor
        self.containers = {}      # anchor -> list of slots
        self.active_liquid = set()
        self.waiting_liquid = {}  # chunk key -> cells waiting for that chunk to exist
        self.liquid_tick = 0
        self.flags = {}
        self.pending_npcs = []    # (npc kind, tx, ty) bound NPCs inside structures
        self.notes = {}           # (tx, ty) of a lore tablet -> note id
        self.locked = set()       # anchors of locked gold chests
        self.furnaces = {}        # anchor -> [progress frames, batches of fuel left]
        self.spawn_tx = WORLD_W // 2
        self.spawn_ty = self.surface[self.spawn_tx]
        for st in self.gen.structures:
            for tid, ax, ay in st.objects:
                self._register_object(tid, ax, ay)
            for ax, ay, slots in st.chests:
                self.containers[(ax, ay)] = slots
            self.locked.update(st.locked)
            for x, y, note in st.notes:
                self.notes[(x, y)] = note
            if st.npc:
                self.pending_npcs.append(st.npc)

    # -------------------- chunks --------------------

    def chunk(self, cx, cy):
        key = (cx, cy)
        data = self.chunks.get(key)
        if data is None:
            data, walls, liq, objects, _ = self.gen.generate_chunk(cx, cy)
            saved = self.saved_chunks.pop(key, None)
            if saved is not None:
                data, walls, liq = saved
                self.modified.add(key)
            else:
                for tid, ax, ay in objects:
                    self._register_object(tid, ax, ay)
            self.chunks[key] = data
            self.walls[key] = walls
            self.liquid[key] = liq
            self.chunk_version[key] = 0
            self.liquid_version[key] = 0
            self._scan_lights(cx, cy)
            self._activate_new_chunk(cx, cy)
        return data

    def is_generated(self, cx, cy):
        return (cx, cy) in self.chunks

    def _scan_lights(self, cx, cy):
        data = self.chunks[(cx, cy)]
        cs = CHUNK_SIZE
        lights = []
        for i, t in enumerate(data):
            if EMITS_LIGHT[t]:
                x, y = cx * cs + i % cs, cy * cs + i // cs
                r, inten = TILES[t].light
                if IS_OBJECT[t]:
                    if self.obj_cells.get((x, y)) != (x, y):
                        continue
                    w, h = TILES[t].size
                    x, y = x + w // 2, y + h // 2
                lights.append((x, y, r, inten))
        self.chunk_lights[(cx, cy)] = lights

    def _bump(self, tx, ty, liquid_only=False):
        cs = CHUNK_SIZE
        cx, cy = tx // cs, ty // cs
        self.modified.add((cx, cy))
        self.liquid_version[(cx, cy)] = self.liquid_version.get((cx, cy), 0) + 1
        if liquid_only:
            return
        lx, ly = tx % cs, ty % cs
        for dcx, dcy, cond in ((0, 0, True), (-1, 0, lx == 0), (1, 0, lx == cs - 1),
                               (0, -1, ly == 0), (0, 1, ly == cs - 1)):
            key = (cx + dcx, cy + dcy)
            if cond and key in self.chunk_version:
                self.chunk_version[key] += 1

    # -------------------- tiles --------------------

    def get_tile(self, tx, ty):
        if tx < 0 or tx >= WORLD_W or ty < 0 or ty >= WORLD_H:
            return AIR
        cs = CHUNK_SIZE
        return self.chunk(tx // cs, ty // cs)[(ty % cs) * cs + (tx % cs)]

    def peek_tile(self, tx, ty):
        """Tile id, or None when the chunk has not been generated yet (never triggers generation)."""
        if tx < 0 or tx >= WORLD_W or ty >= WORLD_H:
            return T["stone"]
        if ty < 0:
            return AIR
        cs = CHUNK_SIZE
        data = self.chunks.get((tx // cs, ty // cs))
        return None if data is None else data[(ty % cs) * cs + (tx % cs)]

    def is_solid(self, tx, ty):
        if tx < 0 or tx >= WORLD_W or ty >= WORLD_H:
            return True
        if ty < 0:
            return False
        return SOLID[self.get_tile(tx, ty)]

    def blocks_creature(self, tx, ty):
        if tx < 0 or tx >= WORLD_W or ty >= WORLD_H:
            return True
        if ty < 0:
            return False
        return BLOCKS_CREATURES[self.get_tile(tx, ty)]

    def blocks_flyer(self, tx, ty):
        if tx < 0 or tx >= WORLD_W or ty >= WORLD_H:
            return True
        if ty < 0:
            return False
        return BLOCKS_FLYERS[self.get_tile(tx, ty)]

    def set_tile(self, tx, ty, tid):
        if tx < 0 or tx >= WORLD_W or ty < 0 or ty >= WORLD_H:
            return
        cs = CHUNK_SIZE
        cx, cy = tx // cs, ty // cs
        data = self.chunk(cx, cy)
        i = (ty % cs) * cs + (tx % cs)
        old = data[i]
        data[i] = tid
        self.liquid[(cx, cy)][i] = 8 if LIQUID[tid] else 0
        self.tile_damage.pop((tx, ty), None)
        if EMITS_LIGHT[old] or EMITS_LIGHT[tid]:
            self._scan_lights(cx, cy)
        self._bump(tx, ty)
        self.activate_around(tx, ty)

    # -------------------- walls --------------------

    def get_wall(self, tx, ty):
        if tx < 0 or tx >= WORLD_W or ty < 0 or ty >= WORLD_H:
            return 0
        cs = CHUNK_SIZE
        self.chunk(tx // cs, ty // cs)
        return self.walls[(tx // cs, ty // cs)][(ty % cs) * cs + (tx % cs)]

    def set_wall(self, tx, ty, wid):
        if tx < 0 or tx >= WORLD_W or ty < 0 or ty >= WORLD_H:
            return
        cs = CHUNK_SIZE
        self.chunk(tx // cs, ty // cs)
        self.walls[(tx // cs, ty // cs)][(ty % cs) * cs + (tx % cs)] = wid
        self.wall_damage.pop((tx, ty), None)
        self._bump(tx, ty)

    # -------------------- objects --------------------

    def _register_object(self, tid, ax, ay):
        w, h = TILES[tid].size
        self.objects[(ax, ay)] = tid
        for dx in range(w):
            for dy in range(h):
                self.obj_cells[(ax + dx, ay + dy)] = (ax, ay)
        name = TILES[tid].name
        if name in CONTAINER_SIZE and (ax, ay) not in self.containers:
            self.containers[(ax, ay)] = [None] * CONTAINER_SIZE[name]
        if name == "furnace":
            self.furnaces.setdefault((ax, ay), [0, 0])

    def object_at(self, tx, ty):
        return self.obj_cells.get((tx, ty))

    def place_object(self, tid, ax, ay):
        w, h = TILES[tid].size
        for dx in range(w):
            for dy in range(h):
                self.set_tile(ax + dx, ay + dy, tid)
        self._register_object(tid, ax, ay)
        self._scan_lights(ax // CHUNK_SIZE, ay // CHUNK_SIZE)

    def remove_object(self, anchor):
        """Remove the object at anchor; returns (tile id, container slots or None)."""
        tid = self.objects.pop(anchor, None)
        if tid is None:
            return None, None
        self.furnaces.pop(anchor, None)
        self.locked.discard(anchor)
        ax, ay = anchor
        w, h = TILES[tid].size
        for dx in range(w):
            for dy in range(h):
                self.obj_cells.pop((ax + dx, ay + dy), None)
                if self.get_tile(ax + dx, ay + dy) == tid:
                    self.set_tile(ax + dx, ay + dy, AIR)
        return tid, self.containers.pop(anchor, None)

    def objects_in(self, tx0, ty0, tx1, ty1):
        for (ax, ay), tid in self.objects.items():
            if tx0 - 4 <= ax <= tx1 and ty0 - 4 <= ay <= ty1:
                yield ax, ay, tid

    def remove_tree(self, tx, ty):
        """Fell a whole tree/cactus starting at (tx, ty). Returns number of trunk tiles removed."""
        trunk_id = self.get_tile(tx, ty)
        removed = 0
        y = ty
        while self.get_tile(tx, y) == trunk_id:
            self.set_tile(tx, y, AIR)
            removed += 1
            y -= 1
        for dy in range(-7, 2):
            for dx in range(-5, 6):
                if self.get_tile(tx + dx, y + dy) in LEAF_TILES:
                    self.set_tile(tx + dx, y + dy, AIR)
        return removed

    # -------------------- mining damage --------------------

    def damage_tile(self, tx, ty, amount, walls=False):
        table = self.wall_damage if walls else self.tile_damage
        entry = table.get((tx, ty))
        if entry is None:
            entry = [0, 0]
            table[(tx, ty)] = entry
        entry[0] += amount
        entry[1] = 0
        return entry[0]

    def tick_damage(self):
        for table in (self.tile_damage, self.wall_damage):
            dead = []
            for key, entry in table.items():
                entry[1] += 1
                if entry[1] > 240:
                    dead.append(key)
            for key in dead:
                del table[key]

    # -------------------- liquids --------------------

    def liquid_level(self, tx, ty):
        if tx < 0 or tx >= WORLD_W or ty < 0 or ty >= WORLD_H:
            return 0
        cs = CHUNK_SIZE
        liq = self.liquid.get((tx // cs, ty // cs))
        return 0 if liq is None else liq[(ty % cs) * cs + (tx % cs)]

    def _set_liquid(self, tx, ty, tid, level):
        cs = CHUNK_SIZE
        key = (tx // cs, ty // cs)
        i = (ty % cs) * cs + (tx % cs)
        data = self.chunks[key]
        old = data[i]
        data[i] = tid if level > 0 else AIR
        self.liquid[key][i] = level
        if EMITS_LIGHT[old] != EMITS_LIGHT[data[i]]:
            self._scan_lights(*key)
        self._bump(tx, ty, liquid_only=True)

    def place_liquid(self, tx, ty, tid):
        self.chunk(tx // CHUNK_SIZE, ty // CHUNK_SIZE)
        self._set_liquid(tx, ty, tid, 8)
        self.activate_around(tx, ty)

    def activate_around(self, tx, ty):
        for x, y in ((tx, ty), (tx - 1, ty), (tx + 1, ty), (tx, ty - 1), (tx, ty + 1)):
            if 0 <= x < WORLD_W and 0 <= y < WORLD_H:
                self.active_liquid.add((x, y))

    def _activate_new_chunk(self, cx, cy):
        cs = CHUNK_SIZE
        for cell in self.waiting_liquid.pop((cx, cy), ()):
            self.active_liquid.add(cell)
        data = self.chunks[(cx, cy)]
        liq = self.liquid[(cx, cy)]
        for i, lv in enumerate(liq):
            if not lv:
                continue
            lx, ly = i % cs, i // cs
            edge = lx in (0, cs - 1) or ly == cs - 1
            if edge or data[i + cs] == AIR or data[i - 1] == AIR or data[i + 1] == AIR or lv < 8:
                self.active_liquid.add((cx * cs + lx, cy * cs + ly))

    def update_liquids(self, budget=500):
        """Advance the liquid automaton for up to `budget` active cells."""
        self.liquid_tick += 1
        if not self.active_liquid:
            return
        cells = []
        for _ in range(min(budget, len(self.active_liquid))):
            cells.append(self.active_liquid.pop())
        random.shuffle(cells)
        for x, y in cells:
            self._flow(x, y)

    def _wait(self, x, y, nx, ny):
        cs = CHUNK_SIZE
        self.waiting_liquid.setdefault((nx // cs, ny // cs), set()).add((x, y))

    def _flow(self, x, y):
        t = self.peek_tile(x, y)
        if t is None or not LIQUID[t]:
            return
        level = self.liquid_level(x, y)
        # lava touching water hardens into obsidian
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            nt = self.peek_tile(nx, ny)
            if nt is not None and LIQUID[nt] and nt != t:
                if t == T["lava"]:
                    self.set_tile(x, y, _OBSIDIAN)
                    return
                self.set_tile(nx, ny, _OBSIDIAN)
        if t == T["lava"] and self.liquid_tick % 3:
            self.active_liquid.add((x, y))
            return
        start = level
        below = self.peek_tile(x, y + 1)
        if below is None:
            self._wait(x, y, x, y + 1)
        elif below == AIR:
            self._set_liquid(x, y + 1, t, level)
            level = 0
        elif below == t:
            bl = self.liquid_level(x, y + 1)
            move = min(level, 8 - bl)
            if move:
                self._set_liquid(x, y + 1, t, bl + move)
                level -= move
        elif LIQUID[below]:
            self.set_tile(x, y + 1, _OBSIDIAN)
            level = 0
        if level > 1:
            sides = [-1, 1]
            random.shuffle(sides)
            for dx in sides:
                nx = x + dx
                nt = self.peek_tile(nx, y)
                if nt is None:
                    self._wait(x, y, nx, y)
                    continue
                if nt == AIR or nt == t:
                    nl = 0 if nt == AIR else self.liquid_level(nx, y)
                    if level - nl >= 2:
                        move = (level - nl) // 2
                        self._set_liquid(nx, y, t, nl + move)
                        level -= move
                        self.activate_around(nx, y)
                elif LIQUID[nt]:
                    self.set_tile(nx, y, _OBSIDIAN)
                    level = 0
                    break
        if level != start:
            self._set_liquid(x, y, t, level)
            self.activate_around(x, y)
            self.activate_around(x, y + 1)

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
        if self.layer_at(tx, ty) in ("surface", "space"):
            return self.gen.column_biome[tx]
        return self.gen.block_biome(tx, ty)

    def get_biome(self, pixel_x, pixel_y):
        """Background name for a pixel position (relative to the local surface)."""
        tx = int(pixel_x) // TILE_SIZE
        ty = int(pixel_y) // TILE_SIZE
        layer = self.layer_at(tx, ty)
        if layer == "hell":
            return "hell"
        if layer == "space":
            return "space" if ty < SPACE_LINE - 40 else self.biome_at(tx, ty)
        if layer == "cavern":
            return "cave"
        biome = self.biome_at(tx, ty)
        if layer == "surface":
            return biome
        return {"snow": "under_snow", "jungle": "under_jungle", "ocean": "under_ocean"}.get(biome, "under_ground")
