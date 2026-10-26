"""World rendering with per-chunk surface caches."""
from collections import OrderedDict

import pygame

from settings import *
from tiles import TILES, SOLID, AIR, T
from textures import shade

TS = TILE_SIZE
CS = CHUNK_SIZE
CACHE_LIMIT = 72
WALL_DEPTH = 30   # rows below the surface that get a natural background wall
_WATER = T["water"]
_LEAVES = {T["leaves"], T["jungle_leaves"], T["boreal_leaves"]}
_CANOPY = _LEAVES | {T["tree"]}
_EDGE = [shade(td.color, 0.55) for td in TILES]


class WorldRenderer:
    def __init__(self, world, assets):
        self.world = world
        self.assets = assets
        self.cache = OrderedDict()   # (cx, cy) -> (version, surface)

    def _build(self, cx, cy):
        world = self.world
        data = world.chunk(cx, cy)
        surf = pygame.Surface((CS * TS, CS * TS), pygame.SRCALPHA)
        x0, y0 = cx * CS, cy * CS
        get = world.get_tile
        assets = self.assets
        surface = world.surface
        column_biome = world.gen.column_biome
        for ly in range(CS):
            for lx in range(CS):
                tid = data[ly * CS + lx]
                tx, ty = x0 + lx, y0 + ly
                sx, sy = lx * TS, ly * TS
                if not SOLID[tid] and 0 <= tx < WORLD_W and 0 < ty - surface[tx] <= WALL_DEPTH:
                    surf.blit(assets.walls[column_biome[tx]], (sx, sy))
                if tid == AIR:
                    continue
                if tid == _WATER and get(tx, ty - 1) == AIR:
                    surf.blit(assets.water_top, (sx, sy))
                    continue
                if tid in _LEAVES:
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
                    surf.fill(edge, (sx, sy, TS, 2))
                if down:
                    surf.fill(edge, (sx, sy + TS - 2, TS, 2))
                if left:
                    surf.fill(edge, (sx, sy, 2, TS))
                if right:
                    surf.fill(edge, (sx + TS - 2, sy, 2, TS))
                clear = (0, 0, 0, 0)
                if up and left:
                    surf.fill(clear, (sx, sy, 4, 2))
                    surf.fill(clear, (sx, sy, 2, 4))
                if up and right:
                    surf.fill(clear, (sx + TS - 4, sy, 4, 2))
                    surf.fill(clear, (sx + TS - 2, sy, 2, 4))
                if down and left:
                    surf.fill(clear, (sx, sy + TS - 2, 4, 2))
                    surf.fill(clear, (sx, sy + TS - 4, 2, 4))
                if down and right:
                    surf.fill(clear, (sx + TS - 4, sy + TS - 2, 4, 2))
                    surf.fill(clear, (sx + TS - 2, sy + TS - 4, 2, 4))
        return surf

    def chunk_surface(self, cx, cy):
        key = (cx, cy)
        self.world.chunk(cx, cy)
        version = self.world.chunk_version[key]
        entry = self.cache.get(key)
        if entry is None or entry[0] != version:
            entry = (version, self._build(cx, cy))
            self.cache[key] = entry
        self.cache.move_to_end(key)
        while len(self.cache) > CACHE_LIMIT:
            self.cache.popitem(last=False)
        return entry[1]

    def draw(self, surf, cam):
        cam_x, cam_y = int(cam.x), int(cam.y)
        size = CS * TS
        cx0 = max(0, cam_x // size)
        cy0 = max(0, cam_y // size)
        cx1 = min((WORLD_W - 1) // CS, (cam_x + SCREEN_WIDTH) // size)
        cy1 = min((WORLD_H - 1) // CS, (cam_y + SCREEN_HEIGHT) // size)
        for cy in range(cy0, cy1 + 1):
            for cx in range(cx0, cx1 + 1):
                surf.blit(self.chunk_surface(cx, cy), (cx * size - cam_x, cy * size - cam_y))

    def draw_cracks(self, surf, cam):
        for (tx, ty), (dmg, _) in self.world.tile_damage.items():
            hp = TILES[self.world.get_tile(tx, ty)].hp
            if hp <= 0:
                continue
            stage = min(3, int(dmg / hp * 4))
            sx, sy = cam.apply(tx * TS, ty * TS)
            if -TS < sx < SCREEN_WIDTH and -TS < sy < SCREEN_HEIGHT:
                surf.blit(self.assets.cracks[stage], (sx, sy))
