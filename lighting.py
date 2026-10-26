"""Light map on a 32px grid (independent of tile size) rendered as a smooth darkness overlay."""
import pygame

from settings import *

LC = LIGHT_CELL
TPC = LIGHT_CELL // TILE_SIZE   # tiles per light cell


class Lighting:
    def render(self, surf, world, cam, daylight, dynamic_lights):
        """dynamic_lights: list of (pixel_x, pixel_y, radius_cells, intensity)."""
        cam_x, cam_y = int(cam.x), int(cam.y)
        cx0 = cam_x // LC - 1
        cy0 = cam_y // LC - 1
        w = SCREEN_WIDTH // LC + 4
        h = SCREEN_HEIGHT // LC + 4
        light = [0.0] * (w * h)

        # sky light fades out over the first cells below the local surface
        fade = 13
        for i in range(w):
            s = world.surface_at((cx0 + i) * TPC + TPC // 2) / TPC
            for j in range(h):
                d = cy0 + j - s
                if d <= 1:
                    v = daylight
                elif d < fade:
                    v = daylight * (1 - (d - 1) / (fade - 1))
                else:
                    v = 0.0
                if (cy0 + j) * TPC >= HELL_LINE:
                    v = max(v, 0.32)
                light[j * w + i] = v

        tx0, ty0 = cx0 * TPC, cy0 * TPC
        sources = [(lx // TPC, ly // TPC, r, inten) for lx, ly, r, inten in
                   world.light_sources(tx0 - 20, ty0 - 20, tx0 + w * TPC + 20, ty0 + h * TPC + 20)]
        for px, py, r, inten in dynamic_lights:
            sources.append((int(px) // LC, int(py) // LC, r, inten))
        for lx, ly, r, inten in sources:
            cx, cy = lx - cx0, ly - cy0
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
        big = pygame.transform.smoothscale(small, (w * LC, h * LC))
        surf.blit(big, (cx0 * LC - cam_x, cy0 * LC - cam_y))
