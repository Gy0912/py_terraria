"""Special structures planned once per world from the seed.

Each structure is a blueprint of tiles, walls and multi-tile objects that chunk
generation stamps into whichever chunks it overlaps.
"""
import random

from settings import *
from tiles import T, W, TILES, AIR
from items import ITEMS, LOOT, SPECIAL_LOOT

CHEST_SLOTS = 20


class Structure:
    def __init__(self, kind):
        self.kind = kind
        self.tiles = {}       # (x, y) -> tile id (AIR carves)
        self.walls = {}       # (x, y) -> wall id
        self.objects = []     # (tile id, ax, ay)
        self.chests = []      # (ax, ay, slots)
        self.npc = None       # (npc kind, x, y) bound NPC waiting to be rescued
        self.bbox = None

    def set(self, x, y, name):
        self.tiles[(x, y)] = T[name] if isinstance(name, str) else name

    def wall(self, x, y, name):
        self.walls[(x, y)] = W[name]

    def rect(self, x0, y0, x1, y1, name):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                self.set(x, y, name)

    def wall_rect(self, x0, y0, x1, y1, name):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                self.wall(x, y, name)

    def box(self, x0, y0, x1, y1, block, wall):
        """Hollow room: solid outline, air inside with a background wall everywhere."""
        self.rect(x0, y0, x1, y1, block)
        self.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, "air")
        self.wall_rect(x0, y0, x1, y1, wall)

    def obj(self, name, ax, ay):
        tid = T[name]
        w, h = TILES[tid].size
        for dx in range(w):
            for dy in range(h):
                self.tiles[(ax + dx, ay + dy)] = tid
        self.objects.append((tid, ax, ay))
        return ax, ay

    def chest(self, ax, ay, loot_key, rng):
        self.obj("chest", ax, ay)
        self.chests.append((ax, ay, roll_chest(loot_key, rng)))

    def door(self, x, y_bottom):
        self.obj("door", x, y_bottom - 2)

    def finish(self):
        xs = [x for x, _ in self.tiles] + [x for x, _ in self.walls]
        ys = [y for _, y in self.tiles] + [y for _, y in self.walls]
        self.bbox = (min(xs), min(ys), max(xs), max(ys))
        return self


def roll_chest(loot_key, rng):
    slots = [None] * CHEST_SLOTS
    i = 0
    special = rng.choice(SPECIAL_LOOT[loot_key])
    slots[i] = [special, 1]
    i += 1
    for name, lo, hi, chance in LOOT[loot_key]:
        if rng.random() < chance and i < CHEST_SLOTS:
            slots[i] = [name, min(rng.randint(lo, hi), ITEMS[name].max_stack)]
            i += 1
    return slots


# ----------------------------------------------------------------------
# builders
# ----------------------------------------------------------------------

def _foundation(s, x0, x1, floor_y, block="dirt"):
    for x in range(x0, x1 + 1):
        for y in range(floor_y + 1, floor_y + 4):
            s.set(x, y, block)


def surface_cabin(x0, floor_y, rng):
    s = Structure("surface_cabin")
    w, h = 14, 9
    x1, top = x0 + w - 1, floor_y - h + 1
    s.rect(x0 - 1, top - 6, x1 + 1, floor_y - 1, "air")        # clear hills / trees above
    s.box(x0, top, x1, floor_y, "wood", "wood_wall")
    s.rect(x0 + 1, top - 1, x1 - 1, top - 1, "wood")             # roof ridge
    s.rect(x0 + 3, top - 2, x1 - 3, top - 2, "wood")
    _foundation(s, x0, x1, floor_y)
    s.rect(x0, floor_y - 3, x0, floor_y - 1, "air")
    s.door(x0, floor_y - 1)
    s.obj("bed", x0 + 2, floor_y - 2)
    s.chest(x1 - 3, floor_y - 2, "surface_cabin", rng)
    s.set(x0 + 7, top + 2, "torch")
    return s.finish()


def underground_cabin(x0, y0, rng):
    s = Structure("underground_cabin")
    w, h = 12, 8
    x1, y1 = x0 + w - 1, y0 + h - 1
    s.rect(x0 - 2, y0 - 1, x1 + 2, y1 - 1, "air")
    s.box(x0, y0, x1, y1, "wood", "wood_wall")
    s.rect(x0, y1 - 3, x0, y1 - 1, "air")
    s.rect(x1, y1 - 3, x1, y1 - 1, "air")
    s.chest(x0 + 5, y1 - 2, "underground_cabin", rng)
    s.set(x0 + 2, y0 + 2, "torch")
    s.set(x1 - 2, y0 + 2, "torch")
    if rng.random() < 0.5:
        s.obj("workbench", x0 + 2, y1 - 1)
    return s.finish()


def mineshaft(x0, y0, length, rng):
    s = Structure("mineshaft")
    x1 = x0 + length
    s.rect(x0, y0, x1, y0 + 3, "air")
    s.rect(x0, y0 + 4, x1, y0 + 4, "wood")
    for x in range(x0, x1 + 1, 7):
        s.rect(x - 1, y0 - 1, x + 1, y0 - 1, "wood")
        s.wall_rect(x, y0, x, y0 + 3, "wood_wall")
        if (x - x0) % 14 == 0:
            s.set(x, y0 + 1, "torch")
    end = x1 - 3 if rng.random() < 0.5 else x0 + 2
    s.chest(end, y0 + 2, "mineshaft", rng)
    return s.finish()


def pyramid(cx, base_y, rng, with_npc):
    s = Structure("pyramid")
    for k in range(21):
        span = 20 - k
        s.rect(cx - span, base_y - k, cx + span, base_y - k, "sandstone_brick")
        if span > 1:
            s.wall_rect(cx - span + 1, base_y - k, cx + span - 1, base_y - k, "sandstone_brick_wall")
    s.rect(cx - 20, base_y + 1, cx + 20, base_y + 3, "sandstone_brick")
    # entrance corridor, shaft and treasure chamber
    s.rect(cx - 19, base_y - 3, cx, base_y - 1, "air")
    s.rect(cx - 2, base_y - 1, cx + 2, base_y + 13, "sandstone_brick")
    s.rect(cx - 1, base_y - 3, cx + 1, base_y + 8, "air")
    s.wall_rect(cx - 1, base_y, cx + 1, base_y + 8, "sandstone_brick_wall")
    s.box(cx - 9, base_y + 7, cx + 9, base_y + 13, "sandstone_brick", "sandstone_brick_wall")
    s.rect(cx - 1, base_y + 7, cx + 1, base_y + 7, "air")
    s.chest(cx + 5, base_y + 11, "pyramid", rng)
    s.set(cx - 7, base_y + 9, "torch")
    s.set(cx + 7, base_y + 9, "torch")
    if with_npc:
        s.npc = ("traveler", cx - 5, base_y + 12)
    return s.finish()


def igloo(cx, floor_y, rng):
    s = Structure("igloo")
    for dx in range(-8, 9):
        for dy in range(-7, 1):
            d = (dx / 8) ** 2 + (dy / 7) ** 2
            if d <= 1:
                s.set(cx + dx, floor_y + dy, "snow_brick" if d > 0.62 else "air")
                s.wall(cx + dx, floor_y + dy, "snow_brick_wall")
    s.rect(cx - 8, floor_y, cx + 8, floor_y, "snow_brick")
    _foundation(s, cx - 8, cx + 8, floor_y, "snow")
    s.rect(cx + 6, floor_y - 3, cx + 8, floor_y - 1, "air")
    s.chest(cx - 4, floor_y - 2, "igloo", rng)
    s.set(cx, floor_y - 5, "torch")
    return s.finish()


def jungle_ruins(x0, floor_y, rng):
    s = Structure("jungle_ruins")
    w, h = 20, 11
    x1, top = x0 + w - 1, floor_y - h + 1
    s.rect(x0, top - 3, x1, floor_y - 1, "air")
    _foundation(s, x0, x1, floor_y, "mud")
    for x in range(x0, x1 + 1):
        for y in range(top, floor_y + 1):
            edge = x in (x0, x1) or y in (top, floor_y) or (y == top + 5 and x not in range(x0 + 8, x0 + 12))
            if edge and (y == floor_y or rng.random() > 0.25):
                s.set(x, y, "mud_brick")
            if rng.random() < 0.75:
                s.wall(x, y, "mud_brick_wall")
    s.rect(x0, floor_y - 3, x0, floor_y - 1, "air")
    s.chest(x1 - 4, top + 3, "jungle_ruins", rng)
    s.set(x0 + 4, top + 7, "torch")
    return s.finish()


def shipwreck(cx, floor_y, rng):
    s = Structure("shipwreck")
    deck = floor_y - 6
    for dy in range(0, 7):
        y = deck + dy
        half = 11 - dy
        for x in range(cx - half, cx + half + 1):
            outline = dy == 6 or x in (cx - half, cx + half) or dy == 0
            s.set(x, y, "wood" if outline else "water")
            if not outline:
                s.wall(x, y, "wood_wall")
    s.rect(cx - 3, deck, cx + 3, deck, "water")
    s.rect(cx + 2, deck - 9, cx + 2, deck - 1, "wood")
    s.chest(cx - 3, deck + 4, "shipwreck", rng)
    return s.finish()


def sky_island(cx, cy, rng):
    s = Structure("sky_island")
    half = 20
    for dx in range(-half, half + 1):
        depth = int(10 * (1 - (dx / half) ** 2) ** 0.5) + 1
        for dy in range(depth):
            name = "grass" if dy == 0 else "dirt" if dy < 3 else "cloud"
            s.set(cx + dx, cy + dy, name)
    x0 = cx - 5
    s.box(x0, cy - 7, x0 + 10, cy, "stone_brick", "stone_brick_wall")
    s.rect(x0, cy - 3, x0, cy - 1, "air")
    s.door(x0, cy - 1)
    s.chest(x0 + 6, cy - 2, "sky_island", rng)
    s.set(x0 + 3, cy - 5, "torch")
    return s.finish()


def hell_tower(cx, base_y, rng):
    s = Structure("hell_tower")
    x0, x1 = cx - 6, cx + 6
    top = base_y - 26
    s.box(x0, top, x1, base_y, "obsidian_brick", "obsidian_brick_wall")
    s.rect(x0 - 1, base_y + 1, x1 + 1, base_y + 8, "obsidian_brick")
    # floors 5 rows apart so each one can be reached with a single jump through the gap
    for fy in range(base_y - 5, top + 2, -5):
        s.rect(x0 + 1, fy, x1 - 1, fy, "obsidian_brick")
        gap = x0 + 2 if (base_y - fy) // 5 % 2 else x1 - 4
        s.rect(gap, fy, gap + 2, fy, "air")
        s.set(cx, fy - 3, "torch")
    s.rect(x0, base_y - 3, x0, base_y - 1, "air")
    s.rect(x1, base_y - 3, x1, base_y - 1, "air")
    s.chest(cx - 1, base_y - 22, "hell_tower", rng)
    s.set(cx - 3, base_y - 4, "torch")
    return s.finish()


# ----------------------------------------------------------------------
# planning
# ----------------------------------------------------------------------

def _runs(column_biome, biome):
    runs, start = [], None
    for x, b in enumerate(column_biome + [None]):
        if b == biome and start is None:
            start = x
        elif b != biome and start is not None:
            runs.append((start, x - 1))
            start = None
    return runs


def plan_structures(gen):
    rng = random.Random(gen.seed * 31 + 7)
    surf = gen.surface
    cb = gen.column_biome
    out = []
    taken = []

    def free(x0, y0, x1, y1, margin=6):
        for a in taken:
            if not (x1 + margin < a[0] or x0 - margin > a[2] or y1 + margin < a[1] or y0 - margin > a[3]):
                return False
        return True

    def add(st):
        if st and free(*st.bbox):
            out.append(st)
            taken.append(st.bbox)

    def flat_floor(x0, w):
        hs = surf[x0:x0 + w]
        return max(hs) if max(hs) - min(hs) <= 4 else None

    spawn = WORLD_W // 2
    for a, b in _runs(cb, "forest"):
        for _ in range(max(1, (b - a) // 500)):
            for _try in range(30):
                x0 = rng.randint(a + 10, max(a + 11, b - 25))
                if abs(x0 - spawn) < 60:
                    continue
                floor = flat_floor(x0, 14)
                if floor is not None:
                    add(surface_cabin(x0, floor, rng))
                    break
    for i, (a, b) in enumerate(_runs(cb, "desert")):
        cx = (a + b) // 2 + rng.randint(-20, 20)
        add(pyramid(cx, surf[cx] + 2, rng, with_npc=(i == 0)))
    for a, b in _runs(cb, "snow"):
        for _ in range(2):
            cx = rng.randint(a + 20, b - 20)
            add(igloo(cx, surf[cx], rng))
    for a, b in _runs(cb, "jungle"):
        for _ in range(2):
            x0 = rng.randint(a + 20, b - 40)
            add(jungle_ruins(x0, max(surf[x0:x0 + 20]), rng))
    for a, b in _runs(cb, "ocean"):
        cx = (a + b) // 2 + rng.randint(-60, 60)
        add(shipwreck(cx, surf[cx], rng))
    for _ in range(5):
        cx = rng.randint(700, WORLD_W - 700)
        add(sky_island(cx, rng.randint(SKY_ISLAND_TOP, SKY_ISLAND_BOTTOM), rng))
    for _ in range(45):
        x0 = rng.randint(200, WORLD_W - 220)
        y0 = rng.randint(surf[x0] + 60, HELL_LINE - 80)
        add(underground_cabin(x0, y0, rng))
    for _ in range(12):
        x0 = rng.randint(200, WORLD_W - 300)
        add(mineshaft(x0, rng.randint(surf[x0] + 50, CAVERN_LINE + 150), rng.randint(50, 90), rng))
    for _ in range(7):
        cx = rng.randint(300, WORLD_W - 300)
        add(hell_tower(cx, LAVA_LINE - 3, rng))
    return out
