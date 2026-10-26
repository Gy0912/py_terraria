"""Deterministic, seed-based terrain generation.

Every base tile is a pure function of (seed, x, y), so chunks can be generated
lazily in any order and always agree with their neighbours. Structures are
planned once per world and stamped into the chunks they overlap.
"""
import math
import random

from settings import *
from tiles import T, W, AIR, SOLID, LIQUID, TILES
from structures import plan_structures

_A = AIR
_DIRT, _GRASS, _STONE = T["dirt"], T["grass"], T["stone"]
_SAND, _SANDSTONE, _SNOW, _ICE = T["sand"], T["sandstone"], T["snow"], T["ice"]
_MUD, _JGRASS, _ASH = T["mud"], T["jungle_grass"], T["ash"]
_COPPER, _IRON, _GOLD, _HELLSTONE = T["copper_ore"], T["iron_ore"], T["gold_ore"], T["hellstone"]
_WATER, _LAVA = T["water"], T["lava"]
_TREE, _CACTUS, _MUSHROOM = T["tree"], T["cactus"], T["mushroom"]
_POT, _CRYSTAL = T["pot"], T["life_crystal"]
_LEAVES = {"forest": T["leaves"], "jungle": T["jungle_leaves"], "snow": T["boreal_leaves"]}
_NATURAL_WALL = {"forest": W["dirt_wall"], "ocean": W["sand_wall"], "desert": W["sand_wall"],
                 "snow": W["snow_wall"], "jungle": W["mud_wall"]}
_STONE_WALL = W["stone_wall"]


# ----------------------------------------------------------------------
# Noise
# ----------------------------------------------------------------------

def _hash(ix, iy, seed):
    n = (ix * 374761393 + iy * 668265263 + seed * 982451653) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return n ^ (n >> 16)


def rand01(ix, iy, seed):
    return (_hash(ix, iy, seed) & 0xFFFFFF) / 16777215.0


def noise2(x, y, seed):
    ix = math.floor(x)
    iy = math.floor(y)
    fx = x - ix
    fy = y - iy
    u = fx * fx * (3 - 2 * fx)
    v = fy * fy * (3 - 2 * fy)
    a = rand01(ix, iy, seed)
    b = rand01(ix + 1, iy, seed)
    c = rand01(ix, iy + 1, seed)
    d = rand01(ix + 1, iy + 1, seed)
    top = a + (b - a) * u
    bot = c + (d - c) * u
    return top + (bot - top) * v


def fbm2(x, y, seed, octaves=2):
    total = 0.0
    amp = 1.0
    norm = 0.0
    for i in range(octaves):
        total += noise2(x, y, seed + i * 1013) * amp
        norm += amp
        amp *= 0.5
        x *= 2.0
        y *= 2.0
    return total / norm


def noise1(x, seed):
    return noise2(x, 0.5, seed)


# ----------------------------------------------------------------------
# Generator
# ----------------------------------------------------------------------

class WorldGen:
    def __init__(self, seed):
        self.seed = seed
        self.rng = random.Random(seed)
        self.strips = self._biome_strips()
        self.column_biome = [self.strips[min(99, x * 100 // WORLD_W)] for x in range(WORLD_W)]
        self.surface = self._surface_heights()
        self.dirt_depth = [10 + int(noise1(x * 0.025, seed + 3) * 14) for x in range(WORLD_W)]
        self.wall_depth = [30 + int(noise1(x * 0.02, seed + 4) * 30) for x in range(WORLD_W)]
        self.structures = plan_structures(self)
        self.struct_index = {}
        blocked = set()
        for st in self.structures:
            x0, y0, x1, y1 = st.bbox
            for cx in range(x0 // CHUNK_SIZE, x1 // CHUNK_SIZE + 1):
                for cy in range(y0 // CHUNK_SIZE, y1 // CHUNK_SIZE + 1):
                    self.struct_index.setdefault((cx, cy), []).append(st)
            if y0 < SURFACE_LEVEL + 120:
                blocked.update(range(x0 - 6, x1 + 7))
        self.trees = self._plan_trees(blocked)

    # -------------------- biomes --------------------

    def _biome_strips(self):
        """100 horizontal strips: oceans at both edges, forest centre, snow/jungle/desert between."""
        rng = self.rng
        biomes = ["forest"] * 100
        biomes[:10] = ["ocean"] * 10
        biomes[-10:] = ["ocean"] * 10
        protected = [(0, 13), (42, 58), (86, 100)]

        left_biome, right_biome = rng.sample(["snow", "jungle"], 2)
        left_start = rng.randint(13, 42 - 28 + 1)
        biomes[left_start:left_start + 28] = [left_biome] * 28
        right_start = rng.randint(58, 86 - 28 + 1)
        biomes[right_start:right_start + 28] = [right_biome] * 28

        def conflict(start, length):
            end = start + length
            return any(not (end <= s or start >= e) for s, e in protected)

        # two desert patches, one on each side of the central forest
        first_left = None
        for part_len in (11, 7):
            for _ in range(200):
                pos = rng.randint(13, 86 - part_len)
                left = pos + part_len <= 42
                if not left and pos < 58:
                    continue
                if first_left is not None and left == first_left:
                    continue
                if not conflict(pos, part_len):
                    biomes[pos:pos + part_len] = ["desert"] * part_len
                    protected.append((pos, pos + part_len))
                    first_left = left
                    break
        return biomes

    def block_biome(self, x, y):
        """Column biome with a wavy border so biome edges look organic underground."""
        jitter = int((noise1(y * 0.04, self.seed + 77) - 0.5) * 48)
        return self.column_biome[max(0, min(WORLD_W - 1, x + jitter))]

    # -------------------- surface --------------------

    def _surface_heights(self):
        amp_by = {"forest": 18, "jungle": 30, "snow": 26, "desert": 12, "ocean": 8}
        raw = [amp_by[b] for b in self.column_biome]
        prefix = [0]
        for v in raw:
            prefix.append(prefix[-1] + v)
        win = 80
        ocean_w = WORLD_W // 10
        heights = []
        for x in range(WORLD_W):
            lo, hi = max(0, x - win), min(WORLD_W, x + win + 1)
            amp = (prefix[hi] - prefix[lo]) / (hi - lo)
            n = fbm2(x * 0.006, 0.5, self.seed + 1, 3)
            m = noise1(x * 0.045, self.seed + 2)
            h = SURFACE_LEVEL + (n - 0.5) * 3.2 * amp + (m - 0.5) * 6
            edge = min(x, WORLD_W - 1 - x)
            if edge < ocean_w:
                t = 1 - edge / ocean_w
                h += t * t * 84
            heights.append(int(h))
        return heights

    def _plan_trees(self, blocked):
        trees = {}
        last = -20
        chance = {"forest": 0.14, "jungle": 0.22, "snow": 0.1, "desert": 0.05}
        s = self.surface
        for x in range(5, WORLD_W - 5):
            b = self.column_biome[x]
            c = chance.get(b, 0)
            if c == 0 or x in blocked:
                continue
            spacing = 14 if b == "desert" else 8
            if x - last < spacing:
                continue
            if abs(s[x - 1] - s[x]) > 1 or abs(s[x + 1] - s[x]) > 1:
                continue
            if rand01(x, 7, self.seed) >= c:
                continue
            r = rand01(x, 8, self.seed)
            if b == "desert":
                trees[x] = (4 + int(r * 6), _CACTUS, None)
            else:
                height = 10 + int(r * 12) + (8 if b == "jungle" else 0)
                trees[x] = (height, _TREE, _LEAVES[b])
            last = x
        return trees

    # -------------------- tiles --------------------

    def _is_cave(self, x, y, depth):
        seed = self.seed
        n = fbm2(x * 0.011, y * 0.017, seed + 11)
        width = 0.022 + min(depth, 600) / 600 * 0.03
        if abs(n - 0.5) < width:
            return True
        m = fbm2(x * 0.025, y * 0.0325, seed + 23)
        return m > 0.71 - min(depth, 800) / 800 * 0.07

    def _hell_tile(self, x, y):
        seed = self.seed
        top = HELL_LINE + 24 + int(noise1(x * 0.025, seed + 41) * 24)
        bottom = WORLD_H - 64 + int(noise1(x * 0.02, seed + 42) * 28)
        if top < y < bottom and fbm2(x * 0.015, y * 0.025, seed + 31) > 0.36:
            return _LAVA if y >= LAVA_LINE else _A
        if noise2(x * 0.15, y * 0.15, seed + 404) > 0.8:
            return _HELLSTONE
        return _ASH

    def base_tile(self, x, y):
        if x < 0 or x >= WORLD_W or y < 0:
            return _A
        if y >= WORLD_H - 4:
            return _ASH
        s = self.surface[x]
        if y < s:
            if self.column_biome[x] == "ocean" and y >= SEA_LEVEL:
                return _WATER
            return _A
        if y >= HELL_LINE:
            return self._hell_tile(x, y)
        depth = y - s
        seed = self.seed
        if depth > 16 and self._is_cave(x, y, depth):
            # flooded caves: water pools in the upper layers, lava pockets deep down
            if depth > 60 and y < CAVERN_LINE + 300 and noise2(x * 0.02, y * 0.03, seed + 61) > 0.7:
                return _WATER
            if y > CAVERN_LINE + 250 and noise2(x * 0.02, y * 0.03, seed + 62) > 0.74:
                return _LAVA
            return _A
        bb = self.block_biome(x, y)
        if depth == 0:
            return {"forest": _GRASS, "jungle": _JGRASS, "snow": _SNOW}.get(bb, _SAND)
        if depth <= self.dirt_depth[x]:
            return {"forest": _DIRT, "jungle": _MUD, "snow": _SNOW}.get(bb, _SAND)

        # underground base block depends on the biome above
        pocket = noise2(x * 0.045, y * 0.045, seed + 5)
        if bb == "desert" and depth < 300:
            base = _SAND if pocket > 0.68 else _SANDSTONE
        elif bb == "snow" and depth < 520:
            base = _SNOW if pocket > 0.7 else (_STONE if pocket < 0.22 else _ICE)
        elif bb == "jungle" and y < HELL_LINE - 60:
            base = _STONE if pocket > 0.7 else _MUD
        else:
            base = _DIRT if pocket > (0.64 if depth < 120 else 0.72) else _STONE

        if y > HELL_LINE - 40 and rand01(x, y, seed + 9) > (HELL_LINE - y) / 40:
            return _ASH

        # ores (deeper ores take priority)
        if base == _DIRT or base == _SAND or base == _SNOW:
            return base
        if y > CAVERN_LINE - 80 and noise2(x * 0.18, y * 0.18, seed + 303) > 0.86:
            return _GOLD
        if depth > 50 and noise2(x * 0.18, y * 0.18, seed + 202) > 0.85:
            return _IRON
        if depth < 520 and noise2(x * 0.18, y * 0.18, seed + 101) > 0.83:
            return _COPPER
        return base

    def base_wall(self, x, y):
        s = self.surface[x]
        depth = y - s
        if 2 <= depth <= self.wall_depth[x]:
            return _NATURAL_WALL[self.column_biome[x]]
        if depth > self.wall_depth[x] and y < HELL_LINE and noise2(x * 0.03, y * 0.03, self.seed + 71) > 0.62:
            return _STONE_WALL
        return 0

    # -------------------- chunks --------------------

    def generate_chunk(self, cx, cy):
        """Returns (tiles, walls, liquid levels, objects[(tile id, ax, ay)], structures touched)."""
        cs = CHUNK_SIZE
        x0, y0 = cx * cs, cy * cs
        seed = self.seed
        base = self.base_tile
        data = bytearray(cs * cs)
        walls = bytearray(cs * cs)
        liq = bytearray(cs * cs)
        in_world_x = 0 <= x0 and x0 + cs <= WORLD_W
        for ly in range(cs):
            y = y0 + ly
            row = ly * cs
            for lx in range(cs):
                x = x0 + lx
                t = base(x, y)
                data[row + lx] = t
                if LIQUID[t]:
                    liq[row + lx] = 8
                if (in_world_x or 0 <= x < WORLD_W) and 0 <= y < WORLD_H:
                    walls[row + lx] = self.base_wall(x, y)

        def at(lx, ly):
            if 0 <= lx < cs and 0 <= ly < cs:
                return data[ly * cs + lx]
            return base(x0 + lx, y0 + ly)

        objects = []

        def try_object(tid, lx, ly):
            """Place a 2x2 object with its top-left at (lx, ly) if it fits inside this chunk."""
            if lx > cs - 2 or ly > cs - 2:
                return False
            cells = [(lx, ly), (lx + 1, ly), (lx, ly + 1), (lx + 1, ly + 1)]
            if any(data[b * cs + a] != _A for a, b in cells):
                return False
            if not (SOLID[at(lx, ly + 2)] and SOLID[at(lx + 1, ly + 2)]):
                return False
            for a, b in cells:
                data[b * cs + a] = tid
            objects.append((tid, x0 + lx, y0 + ly))
            return True

        for ly in range(cs):
            y = y0 + ly
            for lx in range(cs):
                x = x0 + lx
                if not (0 <= x < WORLD_W):
                    continue
                i = ly * cs + lx
                t = data[i]
                if t == _MUD and at(lx, ly - 1) == _A and y > self.surface[x]:
                    data[i] = _JGRASS
                elif t == _A and y > self.surface[x] + 30 and y < WORLD_H - 70:
                    r = rand01(x, y, seed + 55)
                    if r < 0.006:
                        if y - self.surface[x] > 240 and y < HELL_LINE and r < 0.0005:
                            try_object(_CRYSTAL, lx, ly)
                        else:
                            try_object(_POT, lx, ly)

        # trees and cacti (planned per column, so they cross chunk borders consistently)
        for x in range(x0 - 5, x0 + cs + 5):
            tree = self.trees.get(x)
            if tree is None:
                continue
            height, trunk, leaves = tree
            s = self.surface[x]
            top = s - height
            if top - 8 > y0 + cs or s < y0:
                continue
            if 0 <= x - x0 < cs:
                for y in range(top, s):
                    if y0 <= y < y0 + cs:
                        data[(y - y0) * cs + (x - x0)] = trunk
            if leaves is not None:
                for dy in range(-7, 1):
                    for dx in range(-4, 5):
                        if (dx / 4.3) ** 2 + ((dy + 3) / 4.0) ** 2 > 1:
                            continue
                        lx, ly = x + dx - x0, top + dy - y0
                        if 0 <= lx < cs and 0 <= ly < cs and data[ly * cs + lx] == _A:
                            data[ly * cs + lx] = leaves

        # surface mushrooms
        for lx in range(cs):
            x = x0 + lx
            if not (0 <= x < WORLD_W) or x in self.trees:
                continue
            y = self.surface[x] - 1
            if y0 <= y < y0 + cs and self.column_biome[x] in ("forest", "jungle"):
                i = (y - y0) * cs + lx
                if rand01(x, 11, seed) < 0.04 and data[i] == _A:
                    data[i] = _MUSHROOM

        # structures
        touched = self.struct_index.get((cx, cy), [])
        for st in touched:
            for (x, y), tid in st.tiles.items():
                lx, ly = x - x0, y - y0
                if 0 <= lx < cs and 0 <= ly < cs:
                    i = ly * cs + lx
                    data[i] = tid
                    liq[i] = 8 if LIQUID[tid] else 0
            for (x, y), wid in st.walls.items():
                lx, ly = x - x0, y - y0
                if 0 <= lx < cs and 0 <= ly < cs:
                    walls[ly * cs + lx] = wid
        # structures overwrite cells, so drop generated objects that were partly erased
        objects = [(tid, ax, ay) for tid, ax, ay in objects
                   if all(data[(ay - y0 + dy) * cs + (ax - x0 + dx)] == tid for dx in (0, 1) for dy in (0, 1))]
        return data, walls, liq, objects, touched
