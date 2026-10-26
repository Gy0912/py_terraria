"""Deterministic, seed-based terrain generation.

Every tile is a pure function of (seed, x, y), so chunks can be generated lazily
in any order and always agree with their neighbours.
"""
import math
import random

from settings import *
from tiles import T, AIR, SOLID

_A = AIR
_DIRT, _GRASS, _STONE = T["dirt"], T["grass"], T["stone"]
_SAND, _SANDSTONE, _SNOW, _ICE = T["sand"], T["sandstone"], T["snow"], T["ice"]
_MUD, _JGRASS, _ASH = T["mud"], T["jungle_grass"], T["ash"]
_COPPER, _IRON, _GOLD, _HELLSTONE = T["copper_ore"], T["iron_ore"], T["gold_ore"], T["hellstone"]
_WATER, _LAVA = T["water"], T["lava"]
_TREE, _CACTUS, _MUSHROOM = T["tree"], T["cactus"], T["mushroom"]
_POT, _CRYSTAL = T["pot"], T["life_crystal"]
_LEAVES = {"forest": T["leaves"], "jungle": T["jungle_leaves"], "snow": T["boreal_leaves"]}


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
        self.dirt_depth = [5 + int(noise1(x * 0.05, seed + 3) * 7) for x in range(WORLD_W)]
        self.trees = self._plan_trees()

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
        jitter = int((noise1(y * 0.08, self.seed + 77) - 0.5) * 24)
        return self.column_biome[max(0, min(WORLD_W - 1, x + jitter))]

    # -------------------- surface --------------------

    def _surface_heights(self):
        amp_by = {"forest": 9, "jungle": 16, "snow": 13, "desert": 6, "ocean": 4}
        raw = [amp_by[b] for b in self.column_biome]
        prefix = [0]
        for v in raw:
            prefix.append(prefix[-1] + v)
        win = 40
        ocean_w = WORLD_W // 10
        heights = []
        for x in range(WORLD_W):
            lo, hi = max(0, x - win), min(WORLD_W, x + win + 1)
            amp = (prefix[hi] - prefix[lo]) / (hi - lo)
            n = fbm2(x * 0.012, 0.5, self.seed + 1, 3)
            m = noise1(x * 0.09, self.seed + 2)
            h = SURFACE_LEVEL + (n - 0.5) * 3.2 * amp + (m - 0.5) * 3
            edge = min(x, WORLD_W - 1 - x)
            if edge < ocean_w:
                t = 1 - edge / ocean_w
                h += t * t * 42
            heights.append(int(h))
        return heights

    def _plan_trees(self):
        trees = {}
        last = -10
        chance = {"forest": 0.16, "jungle": 0.24, "snow": 0.12, "desert": 0.06}
        s = self.surface
        for x in range(3, WORLD_W - 3):
            b = self.column_biome[x]
            c = chance.get(b, 0)
            if c == 0:
                continue
            spacing = 7 if b == "desert" else 4
            if x - last < spacing:
                continue
            if abs(s[x - 1] - s[x]) > 1 or abs(s[x + 1] - s[x]) > 1:
                continue
            if rand01(x, 7, self.seed) >= c:
                continue
            r = rand01(x, 8, self.seed)
            if b == "desert":
                trees[x] = (2 + int(r * 3), _CACTUS, None)
            else:
                height = 5 + int(r * 7) + (4 if b == "jungle" else 0)
                trees[x] = (height, _TREE, _LEAVES[b])
            last = x
        return trees

    # -------------------- tiles --------------------

    def _is_cave(self, x, y, depth):
        seed = self.seed
        n = fbm2(x * 0.022, y * 0.034, seed + 11)
        width = 0.022 + min(depth, 300) / 300 * 0.03
        if abs(n - 0.5) < width:
            return True
        m = fbm2(x * 0.05, y * 0.065, seed + 23)
        return m > 0.71 - min(depth, 400) / 400 * 0.07

    def _hell_tile(self, x, y):
        seed = self.seed
        top = HELL_LINE + 12 + int(noise1(x * 0.05, seed + 41) * 12)
        bottom = WORLD_H - 32 + int(noise1(x * 0.04, seed + 42) * 14)
        if top < y < bottom and fbm2(x * 0.03, y * 0.05, seed + 31) > 0.36:
            return _LAVA if y >= LAVA_LINE else _A
        if noise2(x * 0.3, y * 0.3, seed + 404) > 0.8:
            return _HELLSTONE
        return _ASH

    def base_tile(self, x, y):
        if x < 0 or x >= WORLD_W or y < 0:
            return _A
        if y >= WORLD_H - 3:
            return _ASH
        s = self.surface[x]
        if y < s:
            if self.column_biome[x] == "ocean" and y >= SEA_LEVEL:
                return _WATER
            return _A
        if y >= HELL_LINE:
            return self._hell_tile(x, y)
        depth = y - s
        if depth > 8 and self._is_cave(x, y, depth):
            return _A
        seed = self.seed
        bb = self.block_biome(x, y)
        if depth == 0:
            return {"forest": _GRASS, "jungle": _JGRASS, "snow": _SNOW}.get(bb, _SAND)
        if depth <= self.dirt_depth[x]:
            return {"forest": _DIRT, "jungle": _MUD, "snow": _SNOW}.get(bb, _SAND)

        # underground base block depends on the biome above
        pocket = noise2(x * 0.09, y * 0.09, seed + 5)
        if bb == "desert" and depth < 150:
            base = _SAND if pocket > 0.68 else _SANDSTONE
        elif bb == "snow" and depth < 260:
            base = _SNOW if pocket > 0.7 else (_STONE if pocket < 0.22 else _ICE)
        elif bb == "jungle" and y < HELL_LINE - 30:
            base = _STONE if pocket > 0.7 else _MUD
        else:
            base = _DIRT if pocket > (0.64 if depth < 60 else 0.72) else _STONE

        if y > HELL_LINE - 20 and rand01(x, y, seed + 9) > (HELL_LINE - y) / 20:
            return _ASH

        # ores (deeper ores take priority)
        if base == _DIRT or base == _SAND or base == _SNOW:
            return base
        if y > CAVERN_LINE - 40 and noise2(x * 0.28, y * 0.28, seed + 303) > 0.86:
            return _GOLD
        if depth > 25 and noise2(x * 0.28, y * 0.28, seed + 202) > 0.85:
            return _IRON
        if depth < 260 and noise2(x * 0.28, y * 0.28, seed + 101) > 0.83:
            return _COPPER
        return base

    # -------------------- chunks --------------------

    def generate_chunk(self, cx, cy):
        cs = CHUNK_SIZE
        x0, y0 = cx * cs, cy * cs
        seed = self.seed
        base = self.base_tile
        data = bytearray(cs * cs)
        for ly in range(cs):
            y = y0 + ly
            row = ly * cs
            for lx in range(cs):
                data[row + lx] = base(x0 + lx, y)

        def at(lx, ly):
            if 0 <= lx < cs and 0 <= ly < cs:
                return data[ly * cs + lx]
            return base(x0 + lx, y0 + ly)

        # decorations that depend on neighbouring base tiles
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
                elif t == _A and y > self.surface[x] + 15 and SOLID[at(lx, ly + 1)]:
                    r = rand01(x, y, seed + 55)
                    if y - self.surface[x] > 120 and y < HELL_LINE and r < 0.0018:
                        data[i] = _CRYSTAL
                    elif r < 0.012:
                        data[i] = _POT

        # trees and cacti (planned per column, so they cross chunk borders consistently)
        for x in range(x0 - 2, x0 + cs + 2):
            tree = self.trees.get(x)
            if tree is None:
                continue
            height, trunk, leaves = tree
            s = self.surface[x]
            top = s - height
            if top - 4 > y0 + cs or s < y0:
                continue
            if 0 <= x - x0 < cs:
                for y in range(top, s):
                    if y0 <= y < y0 + cs:
                        data[(y - y0) * cs + (x - x0)] = trunk
            if leaves is not None:
                for dy in range(-4, 1):
                    span = 1 if dy in (-4, 0) else 2
                    for dx in range(-span, span + 1):
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
                if rand01(x, 11, seed) < 0.05 and data[(y - y0) * cs + lx] == _A:
                    data[(y - y0) * cs + lx] = _MUSHROOM
        return data
