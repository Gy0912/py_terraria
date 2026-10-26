"""Minimap of explored chunks around the player."""
import pygame

from settings import *
from tiles import TILES, AIR, WALLS, T

CS = CHUNK_SIZE
SKY = (110, 160, 220)
CAVE = (35, 28, 24)
_WALL_COLOR = [(0, 0, 0)] + [tuple(int(c * 0.45) for c in TILES[T[w.tile]].color) for w in WALLS[1:]]


class Minimap:
    def __init__(self, world, rect):
        self.world = world
        self.rect = pygame.Rect(rect)
        self.scale = 1
        self.chunk_cache = {}    # (cx, cy) -> (version, liquid version, CSxCS surface)
        self.image = None
        self.timer = 0

    def toggle_zoom(self):
        self.scale = {1: 2, 2: 4, 4: 1}[self.scale]
        self.timer = 0

    def _chunk_img(self, cx, cy):
        key = (cx, cy)
        world = self.world
        version = (world.chunk_version[key], world.liquid_version.get(key, 0))
        entry = self.chunk_cache.get(key)
        if entry and entry[0] == version:
            return entry[1]
        data = world.chunks[key]
        walls = world.walls[key]
        img = pygame.Surface((CS, CS))
        for i, t in enumerate(data):
            x, y = cx * CS + i % CS, cy * CS + i // CS
            if t == AIR:
                if walls[i]:
                    col = _WALL_COLOR[walls[i]]
                else:
                    col = SKY if y < world.surface_at(x) else CAVE
            else:
                col = TILES[t].color
            img.set_at((i % CS, i // CS), col)
        self.chunk_cache[key] = (version, img)
        return img

    def update(self, player):
        self.timer -= 1
        if self.timer > 0 and self.image is not None:
            return
        self.timer = 15
        world = self.world
        tw = self.rect.w // self.scale
        th = self.rect.h // self.scale
        pcx, pcy = player.center()
        tx0 = int(pcx) // TILE_SIZE - tw // 2
        ty0 = int(pcy) // TILE_SIZE - th // 2
        img = pygame.Surface((tw, th))
        img.fill((10, 10, 15))
        budget = 2   # explored chunks from a save are regenerated a few at a time
        for cy in range(ty0 // CS, (ty0 + th) // CS + 1):
            for cx in range(tx0 // CS, (tx0 + tw) // CS + 1):
                if (cx, cy) not in world.chunks and (cx, cy) in world.explored and budget > 0:
                    world.chunk(cx, cy)
                    budget -= 1
                if (cx, cy) in world.chunks:
                    img.blit(self._chunk_img(cx, cy), (cx * CS - tx0, cy * CS - ty0))
        self.image = pygame.transform.scale(img, (tw * self.scale, th * self.scale))

    def draw(self, surf, player, creatures, npcs):
        if self.image is None:
            return
        r = self.rect
        surf.blit(self.image, r.topleft)
        cx, cy = r.center
        pcx, pcy = player.center()

        def dot(pos, color, size=3):
            dx = (pos[0] - pcx) / TILE_SIZE * self.scale
            dy = (pos[1] - pcy) / TILE_SIZE * self.scale
            if abs(dx) < r.w / 2 - 2 and abs(dy) < r.h / 2 - 2:
                pygame.draw.rect(surf, color, (cx + dx - size // 2, cy + dy - size // 2, size, size))

        for c in creatures:
            dot(c.center(), (255, 200, 40) if getattr(c, "is_boss", False) else (230, 50, 50),
                6 if getattr(c, "is_boss", False) else 3)
        for n in npcs:
            dot(n.center(), (90, 230, 120), 4)
        pygame.draw.rect(surf, (255, 255, 255), (cx - 2, cy - 3, 5, 6))
        pygame.draw.rect(surf, (30, 90, 220), (cx - 1, cy - 2, 3, 4))
        pygame.draw.rect(surf, (220, 220, 255), r, 2, border_radius=3)
