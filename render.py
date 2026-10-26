"""World rendering: cached chunk surfaces for walls + tiles and for liquids,
multi-tile objects drawn per frame, and mining cracks."""
from collections import OrderedDict

import pygame

from settings import *
from tiles import TILES, SOLID, LIQUID, AIR, IS_OBJECT, LEAF_TILES, T
from textures import shade

TS = TILE_SIZE
CS = CHUNK_SIZE
CACHE_LIMIT = 48
_WATER, _LAVA = T["water"], T["lava"]
_CANOPY = LEAF_TILES | {T["tree"]}
_EDGE = [shade(td.color, 0.55) for td in TILES]
_LIQUID_COLOR = {_WATER: (40, 100, 210, 150), _LAVA: (235, 95, 20, 235)}
_LIQUID_TOP = {_WATER: (150, 200, 255, 200), _LAVA: (255, 200, 80, 255)}


class WorldRenderer:
    def __init__(self, world, assets):
        self.world = world
        self.assets = assets
        self.cache = OrderedDict()        # (cx, cy) -> (version, surface)
        self.liquid_cache = OrderedDict()

    # -------------------- chunk builds --------------------

    def _build(self, cx, cy):
        world = self.world
        data = world.chunk(cx, cy)
        walls = world.walls[(cx, cy)]
        surf = pygame.Surface((CS * TS, CS * TS), pygame.SRCALPHA)
        x0, y0 = cx * CS, cy * CS
        get = world.get_tile
        assets = self.assets
        wall_tex = assets.wall_tex
        clear = (0, 0, 0, 0)
        for ly in range(CS):
            for lx in range(CS):
                i = ly * CS + lx
                tid = data[i]
                sx, sy = lx * TS, ly * TS
                if not SOLID[tid] and walls[i]:
                    surf.blit(wall_tex[walls[i]], (sx, sy))
                if tid == AIR or LIQUID[tid] or IS_OBJECT[tid]:
                    continue
                tx, ty = x0 + lx, y0 + ly
                if tid in LEAF_TILES:
                    mask = ((get(tx, ty - 1) not in _CANOPY) | (get(tx, ty + 1) not in _CANOPY) << 1 |
                            (get(tx - 1, ty) not in _CANOPY) << 2 | (get(tx + 1, ty) not in _CANOPY) << 3)
                    surf.blit(assets.leaf_tex[(tid, mask)], (sx, sy))
                    continue
                tex = assets.tile(tid, tx, ty)
                if tex is None:
                    surf.fill(TILES[tid].color, (sx, sy, TS, TS))
                else:
                    surf.blit(tex, (sx, sy))
                if not SOLID[tid]:
                    continue
                up = not SOLID[get(tx, ty - 1)]
                down = not SOLID[get(tx, ty + 1)]
                left = not SOLID[get(tx - 1, ty)]
                right = not SOLID[get(tx + 1, ty)]
                edge = _EDGE[tid]
                if up:
                    surf.fill(edge, (sx, sy, TS, 1))
                if down:
                    surf.fill(edge, (sx, sy + TS - 1, TS, 1))
                if left:
                    surf.fill(edge, (sx, sy, 1, TS))
                if right:
                    surf.fill(edge, (sx + TS - 1, sy, 1, TS))
                if up and left:
                    surf.fill(clear, (sx, sy, 2, 1))
                    surf.fill(clear, (sx, sy, 1, 2))
                if up and right:
                    surf.fill(clear, (sx + TS - 2, sy, 2, 1))
                    surf.fill(clear, (sx + TS - 1, sy, 1, 2))
                if down and left:
                    surf.fill(clear, (sx, sy + TS - 1, 2, 1))
                    surf.fill(clear, (sx, sy + TS - 2, 1, 2))
                if down and right:
                    surf.fill(clear, (sx + TS - 2, sy + TS - 1, 2, 1))
                    surf.fill(clear, (sx + TS - 1, sy + TS - 2, 1, 2))
        return surf

    def _build_liquid(self, cx, cy):
        world = self.world
        data = world.chunks[(cx, cy)]
        liq = world.liquid[(cx, cy)]
        if not any(liq):
            return None
        surf = pygame.Surface((CS * TS, CS * TS), pygame.SRCALPHA)
        x0, y0 = cx * CS, cy * CS
        for i, level in enumerate(liq):
            if not level:
                continue
            tid = data[i]
            lx, ly = i % CS, i // CS
            above = world.peek_tile(x0 + lx, y0 + ly - 1)
            full = above == tid
            h = TS if full else max(1, level * TS // 8)
            sx, sy = lx * TS, ly * TS + TS - h
            surf.fill(_LIQUID_COLOR[tid], (sx, sy, TS, h))
            if not full:
                surf.fill(_LIQUID_TOP[tid], (sx, sy, TS, 2))
        return surf

    def _cached(self, cache, key, version, builder):
        entry = cache.get(key)
        if entry is None or entry[0] != version:
            entry = (version, builder(*key))
            cache[key] = entry
        cache.move_to_end(key)
        while len(cache) > CACHE_LIMIT:
            cache.popitem(last=False)
        return entry[1]

    # -------------------- drawing --------------------

    def _visible_chunks(self, cam):
        cam_x, cam_y = int(cam.x), int(cam.y)
        size = CS * TS
        cx0 = max(0, cam_x // size)
        cy0 = max(0, cam_y // size)
        cx1 = min((WORLD_W - 1) // CS, (cam_x + SCREEN_WIDTH) // size)
        cy1 = min((WORLD_H - 1) // CS, (cam_y + SCREEN_HEIGHT) // size)
        for cy in range(cy0, cy1 + 1):
            for cx in range(cx0, cx1 + 1):
                yield cx, cy

    def draw(self, surf, cam):
        size = CS * TS
        for key in self._visible_chunks(cam):
            self.world.chunk(*key)
            img = self._cached(self.cache, key, self.world.chunk_version[key], self._build)
            surf.blit(img, (key[0] * size - int(cam.x), key[1] * size - int(cam.y)))

    def draw_objects(self, surf, cam):
        tx0, ty0 = int(cam.x) // TS, int(cam.y) // TS
        tx1, ty1 = tx0 + SCREEN_WIDTH // TS + 1, ty0 + SCREEN_HEIGHT // TS + 1
        world = self.world
        for ax, ay, tid in world.objects_in(tx0, ty0, tx1, ty1):
            if world.peek_tile(ax, ay) != tid:
                continue
            surf.blit(self.assets.obj_tex[tid], cam.apply(ax * TS, ay * TS))

    def draw_liquids(self, surf, cam):
        size = CS * TS
        for key in self._visible_chunks(cam):
            img = self._cached(self.liquid_cache, key, self.world.liquid_version.get(key, 0), self._build_liquid)
            if img is not None:
                surf.blit(img, (key[0] * size - int(cam.x), key[1] * size - int(cam.y)))

    def draw_cracks(self, surf, cam):
        world = self.world
        for table, walls in ((world.tile_damage, False), (world.wall_damage, True)):
            for (tx, ty), (dmg, _) in table.items():
                hp = 40 if walls else TILES[world.get_tile(tx, ty)].hp
                if hp <= 0:
                    continue
                stage = min(3, int(dmg / hp * 4))
                sx, sy = cam.apply(tx * TS, ty * TS)
                if -TS < sx < SCREEN_WIDTH and -TS < sy < SCREEN_HEIGHT:
                    surf.blit(self.assets.cracks[stage], (sx, sy))
