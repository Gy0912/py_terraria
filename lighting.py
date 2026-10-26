"""Tile-resolution light map rendered as a smooth darkness overlay."""
import pygame

from settings import *

TS = TILE_SIZE


class Lighting:
    def render(self, surf, world, cam, daylight, dynamic_lights):
        """dynamic_lights: list of (pixel_x, pixel_y, radius_tiles, intensity)."""
        cam_x, cam_y = int(cam.x), int(cam.y)
        tx0 = cam_x // TS - 1
        ty0 = cam_y // TS - 1
        w = SCREEN_WIDTH // TS + 4
        h = SCREEN_HEIGHT // TS + 4
        light = [0.0] * (w * h)

        # sky light fades out over the first rows below the local surface
        for i in range(w):
            s = world.surface_at(tx0 + i)
            for j in range(h):
                d = ty0 + j - s
                if d <= 1:
                    v = daylight
                elif d < 14:
                    v = daylight * (1 - (d - 1) / 13)
                else:
                    v = 0.0
                if ty0 + j >= HELL_LINE:
                    v = max(v, 0.32)
                light[j * w + i] = v

        sources = [(lx, ly, r, inten) for lx, ly, r, inten in
                   world.light_sources(tx0 - 10, ty0 - 10, tx0 + w + 10, ty0 + h + 10)]
        for px, py, r, inten in dynamic_lights:
            sources.append((int(px) // TS, int(py) // TS, r, inten))
        for lx, ly, r, inten in sources:
            cx, cy = lx - tx0, ly - ty0
            for j in range(max(0, cy - r), min(h, cy + r + 1)):
                dy = j - cy
                row = j * w
                for i in range(max(0, cx - r), min(w, cx + r + 1)):
                    dx = i - cx
                    d = (dx * dx + dy * dy) ** 0.5
                    if d > r:
                        continue
                    v = inten * (1 - d / (r + 1))
                    if v > light[row + i]:
                        light[row + i] = v

        buf = bytearray(w * h * 4)
        for k, v in enumerate(light):
            a = 1.0 - (v if v < 1.0 else 1.0)
            buf[k * 4 + 3] = int(a * a * 240 + a * 15) if a > 0 else 0
        small = pygame.image.frombuffer(bytes(buf), (w, h), "RGBA")
        big = pygame.transform.smoothscale(small, (w * TS, h * TS))
        surf.blit(big, (tx0 * TS - cam_x, ty0 * TS - cam_y))
