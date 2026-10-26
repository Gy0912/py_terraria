"""Minimap of explored (already generated) chunks around the player."""
import pygame

from settings import *
from tiles import TILES, AIR

CS = CHUNK_SIZE
SKY = (110, 160, 220)
CAVE = (45, 35, 30)


class Minimap:
    def __init__(self, world, rect):
        self.world = world
        self.rect = pygame.Rect(rect)
        self.scale = 2
        self.chunk_cache = {}    # (cx, cy) -> (version, 16x16 surface)
        self.image = None
        self.timer = 0

    def toggle_zoom(self):
        self.scale = {1: 2, 2: 4, 4: 1}[self.scale]
        self.timer = 0

    def _chunk_img(self, cx, cy):
        key = (cx, cy)
        version = self.world.chunk_version[key]
        entry = self.chunk_cache.get(key)
        if entry and entry[0] == version:
            return entry[1]
        data = self.world.chunks[key]
        img = pygame.Surface((CS, CS))
        for i, t in enumerate(data):
            x, y = cx * CS + i % CS, cy * CS + i // CS
            if t == AIR:
                col = SKY if y < self.world.surface_at(x) else CAVE
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
        tw = self.rect.w // self.scale
        th = self.rect.h // self.scale
        pcx, pcy = player.center()
        tx0 = int(pcx) // TILE_SIZE - tw // 2
        ty0 = int(pcy) // TILE_SIZE - th // 2
        img = pygame.Surface((tw, th))
        img.fill((10, 10, 15))
        for cy in range(ty0 // CS, (ty0 + th) // CS + 1):
            for cx in range(tx0 // CS, (tx0 + tw) // CS + 1):
                if (cx, cy) in self.world.chunks:
                    img.blit(self._chunk_img(cx, cy), (cx * CS - tx0, cy * CS - ty0))
        self.image = pygame.transform.scale(img, (tw * self.scale, th * self.scale))

    def draw(self, surf, player, creatures):
        if self.image is None:
            return
        r = self.rect
        surf.blit(self.image, r.topleft)
        cx, cy = r.center
        pcx, pcy = player.center()
        for c in creatures:
            dx = (c.center()[0] - pcx) / TILE_SIZE * self.scale
            dy = (c.center()[1] - pcy) / TILE_SIZE * self.scale
            if abs(dx) < r.w / 2 and abs(dy) < r.h / 2:
                pygame.draw.rect(surf, (230, 50, 50), (cx + dx - 1, cy + dy - 1, 3, 3))
        pygame.draw.rect(surf, (255, 255, 255), (cx - 2, cy - 3, 5, 6))
        pygame.draw.rect(surf, (30, 90, 220), (cx - 1, cy - 2, 3, 4))
        pygame.draw.rect(surf, (220, 220, 255), r, 2, border_radius=3)
