"""Procedural pixel-art textures for tiles, objects, walls, items, characters and bosses.

1x1 tiles are authored at native 16x16. Multi-tile objects, icons and characters are
authored at half resolution and scaled up 2x for a chunkier pixel look.
A PNG in images/textures/tiles/<name>.png or images/textures/items/<name>.png
replaces the generated texture of the same name.
"""
import os
import random
import zlib

import pygame

from settings import TILE_SIZE, TEXTURE_OVERRIDE_DIR
from tiles import TILES, T, WALLS, W
from items import ITEMS

PX = 2
VARIANTS = 3


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------

def _clamp(v):
    return 0 if v < 0 else 255 if v > 255 else int(v)


def shade(c, f):
    out = (_clamp(c[0] * f), _clamp(c[1] * f), _clamp(c[2] * f))
    return out + (c[3],) if len(c) == 4 else out


def _rng(name, variant=0):
    return random.Random(zlib.crc32(name.encode()) * 7 + variant)


def _canvas(w=16, h=16):
    return pygame.Surface((w, h), pygame.SRCALPHA)


def _up(surf, scale=PX):
    return pygame.transform.scale(surf, (surf.get_width() * scale, surf.get_height() * scale))


def _noise_fill(s, rng, base, shades=(0.86, 0.93, 1.0, 1.0, 1.07), alpha=255):
    w, h = s.get_size()
    for y in range(h):
        for x in range(w):
            c = shade(base, rng.choice(shades))
            s.set_at((x, y), c + (alpha,))


def _spots(s, rng, color, count, size=1):
    w, h = s.get_size()
    for _ in range(count):
        x, y = rng.randrange(w), rng.randrange(h)
        for dx in range(size):
            if x + dx < w:
                s.set_at((x + dx, y), color)


def _rocks(s, rng, base, count):
    """Cobble outlines: highlight on the top-left, shadow on the bottom-right."""
    hi, lo = shade(base, 1.22), shade(base, 0.68)
    for _ in range(count):
        x0, y0 = rng.randrange(-2, 13), rng.randrange(-2, 13)
        w, h = rng.randint(4, 7), rng.randint(3, 5)
        for x in range(x0, x0 + w):
            if 0 <= x < 16:
                if 0 <= y0 < 16:
                    s.set_at((x, y0), hi)
                if 0 <= y0 + h < 16:
                    s.set_at((x, y0 + h), lo)
        for y in range(y0, y0 + h + 1):
            if 0 <= y < 16:
                if 0 <= x0 < 16:
                    s.set_at((x0, y), hi)
                if 0 <= x0 + w < 16:
                    s.set_at((x0 + w, y), lo)


def _outline(s, color):
    """Dark 1px outline around the opaque pixels of a sprite canvas."""
    w, h = s.get_size()
    src = s.copy()
    for y in range(h):
        for x in range(w):
            if src.get_at((x, y)).a != 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and src.get_at((nx, ny)).a > 0:
                    s.set_at((x, y), color)
                    break


# ----------------------------------------------------------------------
# tile textures (16x16)
# ----------------------------------------------------------------------

def _t_dirt(rng, base=(139, 96, 64)):
    s = _canvas()
    _noise_fill(s, rng, base)
    _spots(s, rng, shade(base, 0.7), 5, 2)
    _spots(s, rng, shade(base, 1.2), 4, 1)
    return s


def _t_grass_on(rng, soil, greens):
    s = _t_dirt(rng, soil)
    h = 3
    for x in range(16):
        h = max(2, min(5, h + rng.choice((-1, 0, 0, 1))))
        for y in range(h):
            s.set_at((x, y), shade(greens, rng.choice((0.92, 1.0, 1.08))))
        s.set_at((x, h), shade(greens, 0.68))
        if rng.random() < 0.3:
            s.set_at((x, 0), shade(greens, 1.25))
    return s


def _t_stone(rng, base=(125, 125, 130)):
    s = _canvas()
    _noise_fill(s, rng, base, (0.9, 0.95, 1.0, 1.04))
    _rocks(s, rng, base, 4)
    return s


def _t_sand(rng, base=(219, 196, 130)):
    s = _canvas()
    _noise_fill(s, rng, base, (0.92, 0.97, 1.0, 1.03))
    _spots(s, rng, shade(base, 0.8), 6)
    return s


def _t_sandstone(rng):
    base = (196, 152, 96)
    s = _canvas()
    off = rng.randrange(4)
    for y in range(16):
        band = (y + off) // 4
        c = shade(base, (0.94, 1.04, 0.98, 1.08)[band % 4])
        for x in range(16):
            s.set_at((x, y), shade(c, rng.choice((0.95, 1.0, 1.04))))
        if (y + off) % 4 == 3:
            for x in range(16):
                if rng.random() < 0.8:
                    s.set_at((x, y), shade(base, 0.74))
    return s


def _t_snow(rng):
    base = (236, 242, 250)
    s = _canvas()
    _noise_fill(s, rng, base, (0.96, 0.98, 1.0, 1.02))
    _spots(s, rng, (200, 215, 238), 6, 2)
    return s


def _t_ice(rng):
    base = (160, 212, 240)
    s = _canvas()
    for y in range(16):
        for x in range(16):
            s.set_at((x, y), shade(base, 1.08 - y * 0.01 + rng.choice((-0.03, 0, 0.03))))
    for _ in range(2):
        x0, y0 = rng.randrange(-6, 12), rng.randrange(0, 10)
        for i in range(7):
            if 0 <= x0 + i < 16 and 0 <= y0 + i < 16:
                s.set_at((x0 + i, y0 + i), (228, 246, 255))
    _spots(s, rng, shade(base, 0.82), 4)
    return s


def _t_mud(rng):
    s = _t_dirt(rng, (92, 68, 70))
    return s


def _t_ash(rng):
    base = (78, 74, 80)
    s = _canvas()
    _noise_fill(s, rng, base)
    _spots(s, rng, (125, 112, 110), 6)
    _spots(s, rng, shade(base, 0.7), 5, 2)
    return s


def _t_ore(rng, color, rim):
    """Darkened stone with three large outlined nuggets so ores read clearly at a glance."""
    s = _t_stone(rng)
    s.fill((205, 205, 205), special_flags=pygame.BLEND_RGB_MULT)
    spots = [(rng.randint(1, 5), rng.randint(1, 5)), (rng.randint(8, 11), rng.randint(2, 6)),
             (rng.randint(3, 9), rng.randint(9, 12))]
    for x, y in spots:
        w, h = rng.randint(3, 4), rng.randint(3, 4)
        pygame.draw.rect(s, rim, (x - 1, y - 1, w + 2, h + 2), border_radius=1)
        pygame.draw.rect(s, color, (x, y, w, h))
        s.set_at((x, y), shade(color, 1.35))
        s.set_at((x + 1, y), shade(color, 1.2))
        s.set_at((x + w - 1, y + h - 1), shade(color, 0.75))
    return s


def _t_cobweb(rng):
    s = _canvas()
    col = (235, 235, 240, 190)
    for a, b in (((0, 0), (15, 15)), ((15, 0), (0, 15)), ((8, 0), (8, 15)), ((0, 8), (15, 8))):
        pygame.draw.line(s, col, a, b)
    for r in (3, 6):
        pygame.draw.rect(s, (235, 235, 240, 140), (8 - r, 8 - r, r * 2, r * 2), 1)
    return s


def _t_lore_note(rng):
    s = _canvas()
    pygame.draw.rect(s, (150, 140, 105), (3, 2, 10, 14), border_radius=2)
    pygame.draw.rect(s, (95, 88, 65), (3, 2, 10, 14), 1, border_radius=2)
    for y in (5, 8, 11):
        pygame.draw.line(s, (90, 80, 60), (5, y), (10, y))
    s.set_at((7, 3), (255, 230, 120))
    s.set_at((8, 3), (255, 230, 120))
    return s


def _t_hellstone(rng):
    base = (72, 26, 22)
    s = _canvas()
    _noise_fill(s, rng, base)
    for _ in range(3):
        x, y = rng.randrange(16), rng.randrange(16)
        for _ in range(8):
            if 0 <= x < 16 and 0 <= y < 16:
                s.set_at((x, y), rng.choice(((255, 110, 40), (255, 160, 60), (255, 200, 90))))
            x += rng.choice((-1, 0, 1))
            y += rng.choice((-1, 0, 1))
    return s


def _t_wood(rng):
    base = (168, 116, 66)
    s = _canvas()
    for plank in range(4):
        c = shade(base, rng.choice((0.92, 1.0, 1.06)))
        joint = rng.randrange(2, 14)
        for y in range(plank * 4, plank * 4 + 4):
            for x in range(16):
                col = shade(c, rng.choice((0.96, 1.0, 1.02)))
                if y % 4 == 3:
                    col = shade(base, 0.62)
                elif x == joint:
                    col = shade(base, 0.7)
                elif rng.random() < 0.12:
                    col = shade(c, 0.82)
                s.set_at((x, y), col)
    return s


def _t_trunk(rng):
    base = (120, 82, 48)
    s = _canvas()
    for y in range(16):
        for x in range(4, 12):
            c = shade(base, rng.choice((0.92, 1.0, 1.06)))
            if x in (6, 9) and rng.random() < 0.8:
                c = shade(base, 0.75)
            s.set_at((x, y), c)
        s.set_at((4, y), shade(base, 0.6))
        s.set_at((11, y), shade(base, 0.6))
    if rng.random() < 0.5:
        ky = rng.randrange(3, 12)
        s.set_at((7, ky), shade(base, 0.5))
        s.set_at((8, ky), shade(base, 0.5))
    return s


def _t_leaves(rng, base):
    s = _canvas()
    _noise_fill(s, rng, base, (0.8, 0.9, 1.0, 1.0, 1.12))
    _spots(s, rng, shade(base, 1.3), 6)
    _spots(s, rng, shade(base, 0.65), 5)
    return s


def ragged_edges(tex, mask, seed):
    """Copy of a canopy tile with leafy holes on exposed sides (mask bits: up, down, left, right)."""
    rng = random.Random(seed)
    out = tex.copy()
    size = out.get_width()
    clear = (0, 0, 0, 0)
    for y in range(size):
        for x in range(size):
            depth = min(x if mask & 4 else 99, size - 1 - x if mask & 8 else 99,
                        y if mask & 1 else 99, size - 1 - y if mask & 2 else 99)
            if depth < 3 and rng.random() < (0.7, 0.4, 0.15)[depth]:
                out.set_at((x, y), clear)
    return out


def _t_bricks(rng, base, mortar_f=0.62, rows=4):
    s = _canvas()
    mortar = shade(base, mortar_f)
    h = 16 // rows
    for row in range(rows):
        off = (row % 2) * 4
        for y in range(row * h, row * h + h):
            for x in range(16):
                c = shade(base, rng.choice((0.93, 1.0, 1.05)))
                if y == row * h + h - 1 or (x + off) % 8 == 7:
                    c = mortar
                elif y == row * h:
                    c = shade(base, 1.12)
                s.set_at((x, y), c)
    return s


def _t_obsidian(rng):
    base = (52, 38, 76)
    s = _canvas()
    _noise_fill(s, rng, base, (0.8, 0.9, 1.0, 1.1))
    for _ in range(3):
        x, y = rng.randrange(14), rng.randrange(14)
        s.set_at((x, y), (150, 120, 200))
        s.set_at((x + 1, y + 1), (110, 85, 160))
    return s


def _t_cloud(rng):
    base = (238, 243, 255)
    s = _canvas()
    _noise_fill(s, rng, base, (0.94, 0.97, 1.0, 1.02))
    _spots(s, rng, (210, 220, 240), 6, 2)
    return s


# ----------------------------------------------------------------------
# multi-tile objects (authored at half resolution, scaled 2x)
# ----------------------------------------------------------------------

def _o_workbench():
    wood = (165, 110, 60)
    s = _canvas(16, 8)
    pygame.draw.rect(s, wood, (0, 0, 16, 3))
    pygame.draw.line(s, shade(wood, 1.2), (0, 0), (15, 0))
    pygame.draw.line(s, shade(wood, 0.6), (0, 3), (15, 3))
    for x in (1, 13):
        pygame.draw.rect(s, shade(wood, 0.85), (x, 4, 2, 4))
    pygame.draw.line(s, shade(wood, 0.75), (3, 6), (12, 6))
    return s


def _o_furnace():
    stone = (115, 105, 105)
    s = _canvas(24, 16)
    rng = _rng("furnace_obj")
    for y in range(3, 16):
        for x in range(1, 23):
            c = shade(stone, rng.choice((0.92, 1.0, 1.06)))
            if (y - 3) % 4 == 3 or (x + ((y - 3) // 4) * 3) % 6 == 0:
                c = shade(stone, 0.7)
            s.set_at((x, y), c)
    pygame.draw.rect(s, shade(stone, 0.8), (16, 0, 4, 3))
    pygame.draw.rect(s, (30, 20, 20), (8, 8, 8, 6))
    for x in range(9, 15):
        s.set_at((x, 12 - (x % 2)), (255, 150 + (x * 13) % 80, 40))
        s.set_at((x, 13), (255, 220, 90))
    return s


def _o_anvil():
    base = (85, 85, 95)
    s = _canvas(16, 8)
    pygame.draw.polygon(s, base, [(0, 0), (15, 0), (15, 3), (4, 3), (0, 1)])
    pygame.draw.rect(s, base, (5, 3, 6, 2))
    pygame.draw.rect(s, base, (3, 5, 10, 3))
    pygame.draw.line(s, (150, 150, 165), (1, 0), (15, 0))
    pygame.draw.line(s, (55, 55, 62), (3, 7), (12, 7))
    return s


def _o_chest(body=(160, 110, 50), trim=(200, 170, 60)):
    s = _canvas(16, 16)
    pygame.draw.rect(s, body, (1, 4, 14, 12))
    pygame.draw.rect(s, shade(body, 1.15), (1, 2, 14, 5))
    pygame.draw.line(s, shade(body, 0.6), (1, 7), (14, 7))
    for x in (1, 14):
        pygame.draw.line(s, trim, (x, 2), (x, 15))
    pygame.draw.rect(s, trim, (6, 6, 4, 4))
    s.set_at((7, 8), (40, 30, 20))
    _outline(s, shade(body, 0.45))
    return s


def _o_bed():
    s = _canvas(32, 16)
    wood = (150, 95, 55)
    pygame.draw.rect(s, wood, (0, 2, 3, 14))
    pygame.draw.rect(s, wood, (29, 6, 3, 10))
    pygame.draw.rect(s, (230, 230, 235), (3, 7, 7, 4))
    pygame.draw.rect(s, (180, 50, 55), (9, 7, 20, 5))
    pygame.draw.line(s, (220, 90, 95), (9, 7), (28, 7))
    pygame.draw.rect(s, shade(wood, 0.8), (3, 11, 26, 2))
    pygame.draw.rect(s, wood, (3, 13, 2, 3))
    pygame.draw.rect(s, wood, (26, 13, 2, 3))
    return s


def _o_door():
    wood = (140, 95, 50)
    s = _canvas(8, 24)
    pygame.draw.rect(s, wood, (1, 0, 6, 24))
    for y in (0, 23):
        pygame.draw.line(s, shade(wood, 0.6), (1, y), (6, y))
    pygame.draw.line(s, shade(wood, 0.7), (4, 1), (4, 22))
    pygame.draw.line(s, shade(wood, 1.2), (2, 1), (2, 22))
    s.set_at((5, 12), (220, 200, 90))
    return s


def _o_pylon():
    s = _canvas(16, 24)
    pygame.draw.rect(s, (90, 90, 110), (2, 19, 12, 5))
    pygame.draw.polygon(s, (90, 220, 230), [(8, 1), (13, 9), (8, 17), (3, 9)])
    pygame.draw.polygon(s, (190, 250, 255), [(8, 3), (10, 9), (8, 13), (6, 9)])
    pygame.draw.polygon(s, (40, 120, 140), [(8, 1), (13, 9), (8, 17), (3, 9)], 1)
    return s


def _o_shipping_bin():
    wood = (150, 110, 70)
    s = _canvas(16, 16)
    pygame.draw.rect(s, wood, (0, 5, 16, 11))
    for x in range(0, 16, 4):
        pygame.draw.line(s, shade(wood, 0.7), (x, 5), (x, 15))
    pygame.draw.rect(s, shade(wood, 1.2), (0, 2, 16, 3))
    pygame.draw.polygon(s, (240, 210, 70), [(6, 9), (10, 9), (8, 12)])
    _outline(s, shade(wood, 0.45))
    return s


_OBJ_GEN = {
    "workbench": _o_workbench, "furnace": _o_furnace, "anvil": _o_anvil, "chest": _o_chest,
    "gold_chest": lambda: _o_chest((205, 160, 55), (255, 235, 140)),
    "bed": _o_bed, "door": _o_door, "pylon": _o_pylon, "shipping_bin": _o_shipping_bin,
}


def _t_cactus(rng):
    base = (70, 150, 60)
    s = _canvas()
    for y in range(16):
        for x in range(4, 12):
            c = shade(base, 1.18 if x == 6 else 0.8 if x == 10 else 1.0)
            s.set_at((x, y), c)
        s.set_at((4, y), shade(base, 0.6))
        s.set_at((11, y), shade(base, 0.6))
    for y in range(2, 16, 4):
        s.set_at((3, y + rng.randrange(2)), (235, 232, 190))
        s.set_at((12, y + rng.randrange(2)), (235, 232, 190))
    return s


def _t_torch(rng):
    s = _canvas()
    for y in range(8, 16):
        s.set_at((7, y), (140, 95, 50))
        s.set_at((8, y), (115, 75, 40))
    pygame.draw.ellipse(s, (255, 130, 30), (5, 2, 6, 7))
    pygame.draw.ellipse(s, (255, 210, 80), (6, 3, 4, 5))
    s.set_at((7, 5), (255, 255, 215))
    s.set_at((8, 5), (255, 255, 215))
    return s


def _t_mushroom(rng):
    s = _canvas()
    pygame.draw.rect(s, (235, 225, 205), (6, 10, 4, 6))
    pygame.draw.ellipse(s, (205, 45, 45), (2, 4, 12, 8))
    pygame.draw.ellipse(s, (240, 90, 90), (4, 5, 6, 3))
    for p in ((5, 7), (9, 6), (11, 8), (7, 9)):
        s.set_at(p, (250, 245, 240))
    return s


def _t_crystal(rng):
    s = _canvas()
    pygame.draw.rect(s, (110, 105, 110), (3, 13, 10, 3))
    pygame.draw.polygon(s, (240, 80, 120), [(8, 1), (13, 6), (8, 13), (3, 6)])
    pygame.draw.polygon(s, (255, 165, 195), [(8, 2), (10, 6), (8, 9), (5, 6)])
    s.set_at((7, 4), (255, 235, 245))
    return s


def _t_pot(rng):
    base = (150, 90, 60)
    s = _canvas()
    pygame.draw.ellipse(s, base, (2, 5, 12, 11))
    pygame.draw.rect(s, base, (5, 2, 6, 4))
    pygame.draw.rect(s, shade(base, 1.25), (4, 2, 8, 1))
    for x in range(3, 13):
        s.set_at((x, 10), shade(base, 0.7))
    pygame.draw.line(s, shade(base, 1.3), (4, 7), (4, 11))
    return s


_TILE_GEN = {
    "dirt": _t_dirt,
    "grass": lambda r: _t_grass_on(r, (139, 96, 64), (76, 160, 60)),
    "stone": _t_stone,
    "sand": _t_sand,
    "sandstone": _t_sandstone,
    "snow": _t_snow,
    "ice": _t_ice,
    "mud": _t_mud,
    "jungle_grass": lambda r: _t_grass_on(r, (92, 68, 70), (120, 205, 45)),
    "ash": _t_ash,
    "coal_ore": lambda r: _t_ore(r, (28, 28, 34), (8, 8, 10)),
    "copper_ore": lambda r: _t_ore(r, (240, 130, 55), (115, 50, 20)),
    "iron_ore": lambda r: _t_ore(r, (230, 190, 150), (135, 70, 45)),
    "gold_ore": lambda r: _t_ore(r, (255, 222, 60), (140, 100, 15)),
    "cobweb": _t_cobweb,
    "lore_note": _t_lore_note,
    "hellstone": _t_hellstone,
    "wood": _t_wood,
    "tree": _t_trunk,
    "leaves": lambda r: _t_leaves(r, (60, 150, 50)),
    "jungle_leaves": lambda r: _t_leaves(r, (40, 175, 60)),
    "boreal_leaves": lambda r: _t_leaves(r, (55, 110, 90)),
    "cactus": _t_cactus,
    "torch": _t_torch,
    "mushroom": _t_mushroom,
    "life_crystal": _t_crystal,
    "pot": _t_pot,
    "obsidian": _t_obsidian,
    "cloud": _t_cloud,
    "stone_brick": lambda r: _t_bricks(r, (140, 140, 150)),
    "sandstone_brick": lambda r: _t_bricks(r, (210, 170, 110)),
    "snow_brick": lambda r: _t_bricks(r, (215, 230, 245), 0.8),
    "mud_brick": lambda r: _t_bricks(r, (120, 85, 80)),
    "obsidian_brick": lambda r: _t_bricks(r, (70, 50, 95), 0.55),
}


def _crack_stage(stage):
    rng = _rng("crack")
    s = _canvas()
    for i in range(stage * 2 + 2):
        x, y = 8, 8
        dx, dy = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)))
        for _ in range(3 + stage * 2):
            x += dx if rng.random() < 0.8 else rng.choice((-1, 0, 1))
            y += dy if rng.random() < 0.8 else rng.choice((-1, 0, 1))
            if 0 <= x < 16 and 0 <= y < 16:
                s.set_at((x, y), (20, 15, 10, 200))
    return s


# ----------------------------------------------------------------------
# item icons (16x16)
# ----------------------------------------------------------------------

_WOOD = (140, 95, 50)


def _thick(s, color, pts, width):
    pygame.draw.lines(s, color, False, pts, width)


def _i_pickaxe(c):
    s = _canvas()
    _thick(s, shade(_WOOD, 0.5), [(1, 14), (10, 5)], 3)
    _thick(s, _WOOD, [(1, 14), (10, 5)], 1)
    head = [(4, 3), (7, 1), (11, 1), (14, 4), (14, 8), (13, 11)]
    _thick(s, shade(c, 0.45), head, 4)
    _thick(s, c, head, 2)
    s.set_at((8, 1), shade(c, 1.4))
    s.set_at((13, 4), shade(c, 1.4))
    return s


def _i_axe(c):
    s = _canvas()
    _thick(s, shade(_WOOD, 0.5), [(2, 15), (11, 3)], 3)
    _thick(s, _WOOD, [(2, 15), (11, 3)], 1)
    blade = [(8, 3), (12, 0), (15, 3), (15, 8), (11, 8)]
    pygame.draw.polygon(s, c, blade)
    pygame.draw.polygon(s, shade(c, 0.5), blade, 1)
    s.set_at((13, 2), shade(c, 1.4))
    return s


def _i_sword(c):
    s = _canvas()
    _thick(s, shade(c, 0.45), [(4, 11), (14, 1)], 4)
    _thick(s, c, [(4, 11), (14, 1)], 2)
    _thick(s, shade(c, 1.35), [(6, 8), (13, 1)], 1)
    _thick(s, (120, 90, 50), [(2, 9), (6, 13)], 2)
    _thick(s, _WOOD, [(1, 14), (3, 12)], 2)
    s.set_at((0, 15), (200, 170, 80))
    return s


def _i_bow(c):
    s = _canvas()
    arc = [(5, 1), (9, 2), (12, 5), (13, 8), (12, 11), (9, 14), (5, 15)]
    _thick(s, shade(c, 0.5), arc, 3)
    _thick(s, c, arc, 1)
    pygame.draw.line(s, (220, 220, 220), (5, 1), (5, 15))
    return s


def _i_arrow(c):
    s = _canvas()
    pygame.draw.line(s, _WOOD, (2, 13), (12, 3))
    pygame.draw.polygon(s, (170, 170, 175), [(15, 0), (11, 2), (13, 4)])
    for p in ((1, 12), (2, 14), (3, 13), (1, 14)):
        s.set_at(p, (235, 235, 235))
    return s


def _i_staff(c):
    s = _canvas()
    _thick(s, shade(_WOOD, 0.5), [(1, 15), (10, 6)], 3)
    _thick(s, _WOOD, [(1, 15), (10, 6)], 1)
    pygame.draw.circle(s, shade(c, 0.6), (12, 4), 3)
    pygame.draw.circle(s, c, (12, 4), 2)
    s.set_at((11, 3), (255, 240, 200))
    return s


def _i_bar(c):
    s = _canvas()
    pygame.draw.polygon(s, shade(c, 1.2), [(2, 9), (5, 6), (15, 6), (13, 9)])
    pygame.draw.rect(s, c, (2, 9, 11, 4))
    pygame.draw.polygon(s, shade(c, 0.7), [(13, 9), (15, 6), (15, 10), (13, 12)])
    pygame.draw.line(s, shade(c, 1.45), (6, 7), (12, 7))
    _outline(s, shade(c, 0.4))
    return s


def _i_gel(c):
    s = _canvas()
    pygame.draw.ellipse(s, c + (210,), (2, 5, 12, 9))
    pygame.draw.ellipse(s, shade(c, 0.6) + (230,), (2, 5, 12, 9), 1)
    s.set_at((5, 7), (220, 240, 255))
    s.set_at((6, 7), (220, 240, 255))
    return s


def _i_lens(c):
    s = _canvas()
    pygame.draw.circle(s, (235, 232, 230), (8, 8), 6)
    pygame.draw.circle(s, (60, 110, 190), (9, 8), 3)
    pygame.draw.circle(s, (15, 15, 20), (9, 8), 1)
    s.set_at((10, 6), (255, 255, 255))
    _outline(s, (120, 60, 60))
    return s


def _i_bone(c):
    s = _canvas()
    _thick(s, c, [(4, 12), (12, 4)], 2)
    for p in ((3, 11), (5, 13), (11, 3), (13, 5)):
        pygame.draw.circle(s, c, p, 2)
    _outline(s, shade(c, 0.5))
    return s


def _i_potion(c):
    s = _canvas()
    pygame.draw.rect(s, (200, 222, 232), (6, 2, 4, 4))
    pygame.draw.circle(s, (200, 222, 232), (8, 10), 5)
    pygame.draw.circle(s, c, (8, 10), 4)
    pygame.draw.rect(s, (140, 95, 50), (6, 1, 4, 2))
    s.set_at((6, 8), (255, 220, 225))
    _outline(s, (60, 60, 70))
    return s


def _i_hammer(c):
    s = _canvas()
    _thick(s, shade(_WOOD, 0.5), [(1, 15), (10, 6)], 3)
    _thick(s, _WOOD, [(1, 15), (10, 6)], 1)
    head = [(7, 2), (12, 7), (15, 4), (10, -1)]
    pygame.draw.polygon(s, c, head)
    pygame.draw.polygon(s, shade(c, 0.45), head, 1)
    return s


def _i_helmet(c):
    s = _canvas()
    pygame.draw.ellipse(s, c, (2, 2, 12, 12))
    pygame.draw.rect(s, (0, 0, 0, 0), (2, 9, 12, 7))
    pygame.draw.rect(s, c, (2, 8, 3, 6))
    pygame.draw.rect(s, c, (11, 8, 3, 6))
    pygame.draw.line(s, shade(c, 1.4), (5, 4), (9, 3))
    _outline(s, shade(c, 0.4))
    return s


def _i_chestplate(c):
    s = _canvas()
    pygame.draw.polygon(s, c, [(3, 2), (6, 3), (10, 3), (13, 2), (14, 7), (12, 7), (12, 14), (4, 14),
                               (4, 7), (2, 7)])
    pygame.draw.line(s, shade(c, 0.7), (8, 4), (8, 13))
    pygame.draw.line(s, shade(c, 1.35), (5, 5), (5, 12))
    _outline(s, shade(c, 0.4))
    return s


def _i_greaves(c):
    s = _canvas()
    pygame.draw.rect(s, c, (3, 2, 10, 4))
    pygame.draw.rect(s, c, (3, 6, 4, 8))
    pygame.draw.rect(s, c, (9, 6, 4, 8))
    pygame.draw.rect(s, shade(c, 0.7), (2, 13, 5, 2))
    pygame.draw.rect(s, shade(c, 0.7), (9, 13, 5, 2))
    _outline(s, shade(c, 0.4))
    return s


def _i_boots(c):
    s = _canvas()
    pygame.draw.rect(s, c, (4, 2, 5, 9))
    pygame.draw.rect(s, c, (4, 9, 10, 4))
    pygame.draw.line(s, shade(c, 1.4), (5, 3), (5, 9))
    pygame.draw.line(s, (240, 240, 255), (1, 4), (3, 6))
    pygame.draw.line(s, (240, 240, 255), (1, 8), (3, 9))
    _outline(s, shade(c, 0.4))
    return s


def _i_bottle(c):
    s = _canvas()
    pygame.draw.rect(s, (200, 222, 232), (6, 1, 4, 4))
    pygame.draw.ellipse(s, (200, 222, 232), (3, 4, 10, 11))
    pygame.draw.ellipse(s, c, (5, 7, 6, 5))
    pygame.draw.circle(s, (255, 255, 255), (7, 9), 1)
    _outline(s, (70, 80, 100))
    return s


def _i_mask(c):
    s = _canvas()
    pygame.draw.ellipse(s, c, (1, 3, 14, 10))
    pygame.draw.ellipse(s, (170, 220, 240), (3, 5, 10, 6))
    pygame.draw.line(s, (240, 250, 255), (5, 6), (8, 6))
    pygame.draw.rect(s, shade(c, 0.7), (12, 1, 2, 5))
    _outline(s, shade(c, 0.4))
    return s


def _i_charm(c):
    s = _canvas()
    pygame.draw.line(s, (200, 200, 210), (4, 1), (8, 5))
    pygame.draw.line(s, (200, 200, 210), (12, 1), (8, 5))
    pygame.draw.circle(s, c, (8, 10), 5)
    pygame.draw.circle(s, shade(c, 1.6), (7, 9), 2)
    _outline(s, shade(c, 0.4))
    return s


def _i_band(c):
    s = _canvas()
    pygame.draw.ellipse(s, c, (2, 4, 12, 9), 3)
    pygame.draw.circle(s, (255, 255, 255), (8, 5), 2)
    _outline(s, shade(c, 0.4))
    return s


def _i_ring(c):
    s = _canvas()
    pygame.draw.circle(s, (220, 190, 70), (8, 10), 5, 2)
    pygame.draw.polygon(s, c, [(8, 1), (11, 4), (8, 7), (5, 4)])
    _outline(s, (90, 60, 30))
    return s


def _i_horseshoe(c):
    s = _canvas()
    pygame.draw.arc(s, c, (2, 2, 12, 14), 0, 3.14159, 3)
    pygame.draw.rect(s, c, (2, 8, 3, 6))
    pygame.draw.rect(s, c, (11, 8, 3, 6))
    _outline(s, shade(c, 0.4))
    return s


def _i_shield(c):
    s = _canvas()
    pygame.draw.polygon(s, c, [(2, 2), (14, 2), (14, 8), (8, 15), (2, 8)])
    pygame.draw.circle(s, (240, 235, 230), (8, 7), 3)
    pygame.draw.circle(s, (180, 30, 30), (8, 7), 1)
    _outline(s, shade(c, 0.4))
    return s


def _i_star(c):
    s = _canvas()
    pts = [(8, 1), (10, 6), (15, 6), (11, 9), (13, 15), (8, 11), (3, 15), (5, 9), (1, 6), (6, 6)]
    pygame.draw.polygon(s, c, pts)
    pygame.draw.polygon(s, shade(c, 1.5), [(8, 4), (9, 7), (7, 7)])
    _outline(s, shade(c, 0.4))
    return s


def _i_mirror(c):
    s = _canvas()
    pygame.draw.rect(s, _WOOD, (7, 11, 2, 5))
    pygame.draw.ellipse(s, (200, 170, 70), (3, 1, 10, 12))
    pygame.draw.ellipse(s, c, (5, 3, 6, 8))
    pygame.draw.line(s, (255, 255, 255), (6, 4), (7, 6))
    return s


def _i_eye_summon(c):
    s = _canvas()
    pygame.draw.circle(s, (238, 228, 225), (8, 8), 6)
    pygame.draw.circle(s, c, (9, 8), 3)
    pygame.draw.circle(s, (10, 10, 10), (9, 8), 1)
    for p in ((4, 5), (4, 9), (6, 12)):
        s.set_at(p, (200, 40, 40))
    _outline(s, (110, 30, 30))
    return s


def _i_crown(c):
    s = _canvas()
    pygame.draw.polygon(s, (250, 210, 70), [(2, 12), (2, 5), (5, 8), (8, 3), (11, 8), (14, 5), (14, 12)])
    pygame.draw.circle(s, c, (8, 10), 2)
    _outline(s, (120, 90, 20))
    return s


def _i_bag(c):
    s = _canvas()
    pygame.draw.ellipse(s, c, (2, 5, 12, 11))
    pygame.draw.rect(s, c, (6, 2, 4, 4))
    pygame.draw.line(s, (250, 210, 70), (5, 5), (11, 5))
    pygame.draw.circle(s, (250, 210, 70), (8, 11), 2)
    _outline(s, shade(c, 0.4))
    return s


def _i_bucket(c):
    s = _canvas()
    pygame.draw.polygon(s, (170, 170, 180), [(2, 5), (14, 5), (12, 15), (4, 15)])
    pygame.draw.arc(s, (120, 120, 130), (3, 0, 10, 10), 0, 3.14159, 1)
    if c != (170, 170, 180):
        pygame.draw.polygon(s, c, [(3, 6), (13, 6), (12, 9), (4, 9)])
    _outline(s, (70, 70, 80))
    return s


def _i_coin(c):
    s = _canvas()
    pygame.draw.circle(s, c, (8, 8), 6)
    pygame.draw.circle(s, shade(c, 0.75), (8, 8), 4, 1)
    pygame.draw.line(s, shade(c, 1.3), (6, 5), (7, 4))
    _outline(s, shade(c, 0.45))
    return s


def _i_coal(c):
    s = _canvas()
    pygame.draw.polygon(s, (30, 30, 36), [(3, 9), (6, 4), (11, 3), (14, 8), (12, 13), (5, 13)])
    pygame.draw.line(s, (110, 110, 125), (7, 5), (10, 4))
    s.set_at((6, 8), (90, 90, 100))
    _outline(s, (10, 10, 12))
    return s


def _i_lockpick(c):
    s = _canvas()
    pygame.draw.line(s, (200, 200, 210), (2, 14), (11, 5), 2)
    pygame.draw.line(s, (200, 200, 210), (11, 5), (14, 5), 1)
    pygame.draw.line(s, (200, 200, 210), (14, 5), (14, 3), 1)
    pygame.draw.rect(s, (120, 80, 50), (1, 12, 4, 4))
    _outline(s, (60, 60, 70))
    return s


def _i_map(c):
    s = _canvas()
    pygame.draw.rect(s, (220, 200, 150), (2, 3, 12, 10))
    pygame.draw.line(s, (160, 130, 90), (6, 3), (6, 12))
    pygame.draw.line(s, (160, 130, 90), (10, 3), (10, 12))
    pygame.draw.line(s, (200, 40, 40), (8, 6), (11, 9), 2)
    pygame.draw.line(s, (200, 40, 40), (11, 6), (8, 9), 2)
    _outline(s, (110, 85, 50))
    return s


def _i_cardpack(c):
    s = _canvas()
    pygame.draw.rect(s, (90, 60, 160), (4, 1, 9, 13), border_radius=2)
    pygame.draw.rect(s, c, (2, 3, 9, 12), border_radius=2)
    pygame.draw.polygon(s, (255, 230, 120), [(6, 6), (7, 8), (9, 8), (7, 10), (8, 12), (6, 11), (4, 12),
                                             (5, 10), (3, 8), (5, 8)])
    _outline(s, (40, 25, 70))
    return s


def _i_meat(c):
    s = _canvas()
    pygame.draw.ellipse(s, c, (2, 2, 10, 9))
    pygame.draw.line(s, (240, 235, 220), (10, 10), (14, 14), 2)
    pygame.draw.circle(s, (240, 235, 220), (14, 14), 1)
    pygame.draw.line(s, shade(c, 1.3), (4, 4), (7, 3))
    _outline(s, shade(c, 0.45))
    return s


def _i_badge(c):
    s = _canvas()
    pygame.draw.polygon(s, (170, 50, 50), [(5, 0), (8, 6), (11, 0)])
    pygame.draw.circle(s, c, (8, 10), 5)
    pygame.draw.circle(s, shade(c, 0.7), (8, 10), 3, 1)
    s.set_at((7, 9), (255, 250, 220))
    _outline(s, shade(c, 0.4))
    return s


_ICON_GEN = {
    "coal": _i_coal, "lockpick": _i_lockpick, "map": _i_map, "cardpack": _i_cardpack, "meat": _i_meat,
    "badge": _i_badge,
    "pickaxe": _i_pickaxe, "axe": _i_axe, "sword": _i_sword, "bow": _i_bow, "arrow": _i_arrow,
    "staff": _i_staff, "bar": _i_bar, "gel": _i_gel, "lens": _i_lens, "bone": _i_bone,
    "potion": _i_potion, "hammer": _i_hammer, "helmet": _i_helmet, "chestplate": _i_chestplate,
    "greaves": _i_greaves, "boots": _i_boots, "bottle": _i_bottle, "mask": _i_mask, "charm": _i_charm,
    "band": _i_band, "ring": _i_ring, "horseshoe": _i_horseshoe, "shield": _i_shield, "star": _i_star,
    "mirror": _i_mirror, "eye_summon": _i_eye_summon, "crown": _i_crown, "bag": _i_bag,
    "bucket": _i_bucket, "coin": _i_coin,
}
_ICON_FROM_TILE = {"mushroom": "mushroom", "crystal": "life_crystal", "cactus": "cactus"}


# ----------------------------------------------------------------------
# characters
# ----------------------------------------------------------------------

def _humanoid(skin, hair, shirt, pants, shoes, frame, zombie=False, skeleton=False,
              helmet=None, armor=None, greaves=None, hat=None, beard=None, robe=None):
    """12x22 humanoid facing right. frame: 0-3 walk cycle, 'idle', 'jump'.

    helmet / armor / greaves are armor colours drawn over the base look;
    hat / beard / robe are NPC costume colours.
    """
    if armor:
        shirt = armor
    if greaves:
        pants = greaves
    s = _canvas(12, 22)
    eye = (25, 25, 40)
    if not skeleton:
        pygame.draw.rect(s, hair, (2, 0, 8, 2))
        pygame.draw.rect(s, hair, (2, 2, 2, 3))
    pygame.draw.rect(s, skin, (4, 2, 5, 6))
    if skeleton:
        s.set_at((7, 4), (20, 20, 20))
        s.set_at((5, 4), (20, 20, 20))
        s.set_at((6, 6), (70, 70, 60))
    else:
        s.set_at((6, 4), (245, 245, 245))
        s.set_at((7, 4), eye)
    pygame.draw.rect(s, skin, (5, 8, 2, 1))
    # torso
    pygame.draw.rect(s, shirt, (3, 9, 6, 6))
    pygame.draw.line(s, shade(shirt, 0.7), (3, 9), (3, 14))
    if skeleton:
        for y in (10, 12):
            pygame.draw.line(s, skin, (4, y), (8, y))
    if zombie:
        s.set_at((5, 12), (0, 0, 0, 0))
        s.set_at((7, 13), skin)
    pygame.draw.line(s, shade(pants, 0.6), (3, 15), (8, 15))
    # legs
    if frame == "jump":
        legs = ((3, 16, 0), (7, 15, 0))
    elif frame == "idle":
        legs = ((4, 16, 0), (6, 16, 0))
    else:
        o = (-1, 0, 1, 0)[frame]
        legs = ((4 + o, 16, 0), (6 - o, 16, 0))
    for i, (lx, ly, _) in enumerate(legs):
        col = shade(pants, 0.8) if i == 0 else pants
        pygame.draw.rect(s, col, (lx, ly, 2, 20 - ly))
        pygame.draw.rect(s, shoes, (lx, 20, 2 + (1 if i == 1 else 0), 2))
    # arms
    if zombie:
        pygame.draw.rect(s, shirt, (6, 9, 3, 2))
        pygame.draw.rect(s, skin, (9, 9, 3, 2))
    else:
        swing = 0 if frame in ("idle", "jump") else (-1, 0, 1, 0)[frame]
        if frame == "jump":
            pygame.draw.rect(s, shirt, (7, 7, 2, 3))
            pygame.draw.rect(s, skin, (7, 5, 2, 2))
        else:
            pygame.draw.rect(s, shade(shirt, 0.9), (6 + swing, 10, 2, 4))
            pygame.draw.rect(s, skin, (6 + swing, 14, 2, 1))
    if robe:
        pygame.draw.rect(s, robe, (3, 9, 6, 11))
        pygame.draw.line(s, shade(robe, 0.7), (3, 9), (3, 19))
        pygame.draw.line(s, shade(robe, 1.3), (6, 10), (6, 18))
    if armor:
        pygame.draw.rect(s, shade(armor, 1.25), (3, 9, 6, 1))
        pygame.draw.rect(s, shade(armor, 1.15), (7, 9, 2, 2))
    if greaves:
        pygame.draw.line(s, shade(greaves, 1.3), (4, 17), (7, 17))
    if beard:
        pygame.draw.rect(s, beard, (4, 6, 5, 3))
        s.set_at((6, 4), (245, 245, 245))
        s.set_at((7, 4), eye)
    if helmet:
        pygame.draw.rect(s, helmet, (2, 0, 8, 3))
        pygame.draw.rect(s, helmet, (2, 3, 2, 3))
        pygame.draw.line(s, shade(helmet, 1.4), (4, 0), (8, 0))
        pygame.draw.line(s, shade(helmet, 0.6), (2, 3), (9, 3))
    if hat:
        pygame.draw.rect(s, hat, (3, 0, 6, 2))
        pygame.draw.rect(s, shade(hat, 0.75), (1, 2, 10, 1))
        s.set_at((5, 1), (250, 220, 90))
    return s


def _bunny(frame):
    s = _canvas(8, 7)
    body = (225, 222, 215)
    pygame.draw.ellipse(s, body, (0, 3, 6, 4))
    pygame.draw.rect(s, body, (5, 1, 3, 3))
    s.set_at((6, 0), body)
    s.set_at((7, 0), (240, 170, 180))
    s.set_at((7, 2), (20, 20, 20))
    s.set_at((0, 3), (255, 255, 255))
    s.set_at((1 + frame, 6), shade(body, 0.7))
    s.set_at((4 - frame, 6), shade(body, 0.7))
    return s


def _penguin(frame):
    s = _canvas(8, 10)
    pygame.draw.ellipse(s, (30, 30, 40), (1, 1, 6, 9))
    pygame.draw.ellipse(s, (240, 240, 245), (3, 3, 4, 6))
    s.set_at((6, 2), (255, 255, 255))
    s.set_at((7, 3), (250, 160, 40))
    s.set_at((2 + frame, 9), (250, 160, 40))
    s.set_at((5 - frame, 9), (250, 160, 40))
    return s


def _bird(up):
    s = _canvas(7, 5)
    pygame.draw.ellipse(s, (90, 120, 200), (1, 2, 5, 3))
    s.set_at((5, 1), (90, 120, 200))
    s.set_at((6, 2), (250, 190, 50))
    s.set_at((5, 2), (20, 20, 20))
    if up:
        pygame.draw.line(s, (60, 90, 170), (2, 2), (1, 0))
        pygame.draw.line(s, (60, 90, 170), (3, 2), (3, 0))
    else:
        pygame.draw.line(s, (60, 90, 170), (2, 3), (1, 4))
    return s


def _firefly(bright):
    s = _canvas(3, 3)
    glow = (200, 255, 120, 255 if bright else 160)
    for p in ((1, 0), (0, 1), (2, 1), (1, 2)):
        s.set_at(p, glow[:3] + (120,))
    s.set_at((1, 1), (255, 255, 200, 255 if bright else 200))
    return s


def _boar(frame):
    s = _canvas(16, 10)
    body = (115, 80, 55)
    pygame.draw.ellipse(s, body, (1, 1, 12, 7))
    pygame.draw.rect(s, shade(body, 0.9), (11, 3, 4, 4))
    s.set_at((15, 5), (200, 140, 130))
    s.set_at((14, 7), (240, 235, 220))
    s.set_at((12, 3), (20, 20, 20))
    pygame.draw.line(s, shade(body, 0.6), (2, 1), (10, 1))
    for i, x in enumerate((3, 5, 9, 11)):
        dy = 1 if (i + frame) % 2 else 0
        pygame.draw.line(s, shade(body, 0.7), (x, 7), (x, 9 - dy))
    return s


def _wolf(frame):
    s = _canvas(17, 10)
    body = (205, 210, 220)
    pygame.draw.ellipse(s, body, (2, 2, 11, 6))
    pygame.draw.rect(s, body, (12, 1, 4, 4))
    s.set_at((12, 0), body)
    s.set_at((14, 0), body)
    s.set_at((16, 3), (60, 60, 70))
    s.set_at((14, 2), (40, 120, 200))
    pygame.draw.line(s, shade(body, 0.8), (0, 2), (2, 4))
    for i, x in enumerate((3, 5, 10, 12)):
        dy = 1 if (i + frame) % 2 else 0
        pygame.draw.line(s, shade(body, 0.75), (x, 7), (x, 9 - dy))
    return s


def _scorpion(frame):
    s = _canvas(13, 7)
    body = (200, 160, 90)
    pygame.draw.ellipse(s, body, (3, 3, 7, 4))
    pygame.draw.line(s, body, (3, 4), (1, 2))
    pygame.draw.line(s, body, (1, 2), (2, 0))
    s.set_at((3, 0), (60, 30, 20))
    pygame.draw.line(s, shade(body, 0.85), (9, 4), (12, 3 - frame))
    s.set_at((12, 2 - frame), shade(body, 0.6))
    for x in (4, 6, 8):
        s.set_at((x, 6), shade(body, 0.6))
    return s


def _eye_boss(phase, frame):
    s = _canvas(32, 24)
    pygame.draw.circle(s, (238, 228, 225), (18, 12), 11)
    rng = _rng("eye_boss")
    for _ in range(14):
        x, y = rng.randint(9, 15), rng.randint(4, 20)
        s.set_at((x, y), (200, 50, 55))
        s.set_at((x - 1, y + rng.choice((-1, 1))), (170, 40, 45))
    if phase == 1:
        pygame.draw.circle(s, (60, 110, 200), (25, 12), 5)
        pygame.draw.circle(s, (12, 12, 18), (26, 12), 2)
        s.set_at((24, 10), (255, 255, 255))
    else:
        pygame.draw.circle(s, (90, 10, 15), (25, 12), 6)
        for y in range(7, 18, 2):
            pygame.draw.polygon(s, (240, 235, 220), [(29, y), (25, y + 1), (29, y + 2)])
    for i in range(4):
        y = 7 + i * 3
        wave = 1 if (i + frame) % 2 else -1
        pygame.draw.line(s, (160, 40, 50), (7, y), (1, y + wave), 2)
    _outline(s, (110, 30, 35))
    return s


def _king_slime(squish):
    s = _canvas(48, 32)
    color = (70, 130, 235)
    rect = (0, 14, 48, 18) if squish else (2, 8, 44, 24)
    pygame.draw.ellipse(s, color + (210,), rect)
    pygame.draw.ellipse(s, shade(color, 0.55) + (240,), rect, 1)
    pygame.draw.ellipse(s, (255, 255, 255, 130), (rect[0] + 8, rect[1] + 4, 10, 4))
    ey = rect[1] + rect[3] // 2
    for x in (18, 30):
        pygame.draw.rect(s, (20, 20, 40), (x, ey - 1, 2, 3))
    cy = rect[1] - 1
    pygame.draw.polygon(s, (250, 210, 70), [(16, cy), (16, cy - 7), (20, cy - 3), (24, cy - 9),
                                            (28, cy - 3), (32, cy - 7), (32, cy)])
    pygame.draw.circle(s, (220, 40, 60), (24, cy - 3), 2)
    return s


def _flip_pair(s):
    return s, pygame.transform.flip(s, True, False)


def _slime(color, squish):
    s = _canvas(16, 12)
    rect = (0, 5, 16, 7) if squish else (1, 2, 14, 10)
    pygame.draw.ellipse(s, color + (205,), rect)
    pygame.draw.ellipse(s, shade(color, 0.55) + (235,), rect, 1)
    pygame.draw.ellipse(s, (255, 255, 255, 140), (rect[0] + 3, rect[1] + 2, 4, 2))
    ey = rect[1] + rect[3] // 2
    s.set_at((6, ey), (20, 20, 30))
    s.set_at((10, ey), (20, 20, 30))
    return s


def _bat(color, up):
    s = _canvas(16, 10)
    if up:
        wings = [(6, 4), (1, 0), (0, 4), (3, 5)], [(10, 4), (15, 0), (16, 4), (13, 5)]
    else:
        wings = [(6, 4), (1, 8), (0, 5), (3, 4)], [(10, 4), (15, 8), (16, 5), (13, 4)]
    for wing in wings:
        pygame.draw.polygon(s, shade(color, 0.75), wing)
    pygame.draw.ellipse(s, color, (5, 2, 6, 7))
    s.set_at((6, 1), color)
    s.set_at((9, 1), color)
    s.set_at((7, 4), (255, 60, 60))
    s.set_at((9, 4), (255, 60, 60))
    return s


def _eye(tail):
    s = _canvas(16, 11)
    pygame.draw.circle(s, (238, 232, 230), (9, 5), 5)
    for p in ((6, 3), (5, 5), (6, 7), (8, 2)):
        s.set_at(p, (200, 60, 60))
    pygame.draw.circle(s, (190, 30, 30), (12, 5), 2)
    s.set_at((13, 5), (10, 10, 10))
    for i in range(4):
        y = 5 + (1 if (i + tail) % 2 else -1) * (i // 2)
        s.set_at((3 - i, y), (180, 40, 50))
    _outline(s, (110, 40, 40))
    return s


def _hornet(color, up):
    s = _canvas(15, 13)
    for i, x in enumerate(range(3, 12, 2)):
        pygame.draw.rect(s, color if i % 2 == 0 else (40, 30, 20), (x, 6, 2, 5))
    pygame.draw.circle(s, (40, 30, 20), (12, 7), 2)
    s.set_at((13, 6), (255, 60, 60))
    s.set_at((1, 9), (40, 30, 20))
    s.set_at((2, 9), (40, 30, 20))
    wy = 1 if up else 3
    pygame.draw.ellipse(s, (220, 235, 255, 170), (5, wy, 6, 4))
    return s


def _crab(color, step):
    s = _canvas(16, 11)
    pygame.draw.ellipse(s, color, (3, 4, 10, 5))
    for i, x in enumerate((4, 6, 9, 11)):
        dy = 1 if (i + step) % 2 else 0
        s.set_at((x, 9 + dy), shade(color, 0.6))
        s.set_at((x, 10), shade(color, 0.6))
    pygame.draw.circle(s, shade(color, 1.1), (2, 3), 2)
    pygame.draw.circle(s, shade(color, 1.1), (13, 3), 2)
    s.set_at((6, 2), (20, 20, 20))
    s.set_at((9, 2), (20, 20, 20))
    s.set_at((6, 3), color)
    s.set_at((9, 3), color)
    _outline(s, shade(color, 0.45))
    return s


# ----------------------------------------------------------------------
# asset store
# ----------------------------------------------------------------------

class Assets:
    def __init__(self):
        self.tile_tex = {}       # tile id -> [16px variants]
        self.obj_tex = {}        # object tile id -> full-size surface (w*16 x h*16)
        self.wall_tex = {}       # wall id -> 16px surface
        self.leaf_tex = {}
        self.cracks = []
        self.icons = {}          # item name -> 32x32
        self.icons_small = {}    # item name -> 20x20 (drops)
        self.player = {}         # frame -> (right, left) for the unarmoured look
        self._player_looks = {}  # armour key -> {frame: (right, left)}
        self.creatures = {}      # kind -> [(right, left), ...]
        self.npcs = {}           # npc kind -> {frame: (right, left)}
        self.bosses = {}

    def _override(self, kind, name, size=(TILE_SIZE, TILE_SIZE)):
        path = os.path.join(TEXTURE_OVERRIDE_DIR, kind, name + ".png")
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(img, size)
        return None

    def load(self):
        for td in TILES:
            size = (td.size[0] * TILE_SIZE, td.size[1] * TILE_SIZE)
            ov = self._override("tiles", td.name, size)
            if td.size != (1, 1):
                if ov is None:
                    gen = _OBJ_GEN.get(td.name)
                    ov = _up(gen()) if gen else _up(_TILE_GEN[td.name](_rng(td.name)))
                self.obj_tex[td.id] = ov
                continue
            gen = _TILE_GEN.get(td.name)
            if ov is not None:
                self.tile_tex[td.id] = [ov]
            elif gen is not None:
                self.tile_tex[td.id] = [gen(_rng(td.name, v)) for v in range(VARIANTS)]
        self.cracks = [_crack_stage(i) for i in range(4)]
        for name in ("leaves", "jungle_leaves", "boreal_leaves"):
            tid = T[name]
            for mask in range(16):
                self.leaf_tex[(tid, mask)] = ragged_edges(self.tile_tex[tid][0], mask, tid * 16 + mask)
        for wd in WALLS[1:]:
            wall = self.tile_tex[T[wd.tile]][0].copy()
            wall.fill((92, 88, 96) if wd.natural else (110, 104, 112), special_flags=pygame.BLEND_RGB_MULT)
            self.wall_tex[wd.id] = wall
        self._load_icons()
        self._load_characters()

    def _load_icons(self):
        for it in ITEMS.values():
            ov = self._override("items", it.name)
            if ov is not None:
                icon = ov
            elif it.kind == "wall":
                icon = pygame.Surface((32, 32), pygame.SRCALPHA)
                icon.blit(pygame.transform.scale(self.wall_tex[W[it.wall]], (22, 22)), (5, 5))
                pygame.draw.rect(icon, (230, 230, 230, 160), (5, 5, 22, 22), 1)
            elif it.icon == "block" or it.icon in _ICON_FROM_TILE:
                tile_name = it.place if it.icon == "block" else _ICON_FROM_TILE[it.icon]
                tid = T[tile_name]
                if tid in self.obj_tex:
                    tex = self.obj_tex[tid]
                    scale = 28 / max(tex.get_size())
                    small = pygame.transform.scale(tex, (max(1, int(tex.get_width() * scale)),
                                                         max(1, int(tex.get_height() * scale))))
                    icon = pygame.Surface((32, 32), pygame.SRCALPHA)
                    icon.blit(small, ((32 - small.get_width()) // 2, (32 - small.get_height()) // 2))
                elif TILES[tid].solid:
                    icon = pygame.Surface((32, 32), pygame.SRCALPHA)
                    icon.blit(pygame.transform.scale(self.tile_tex[tid][0], (22, 22)), (5, 5))
                    pygame.draw.rect(icon, (0, 0, 0, 120), (5, 5, 22, 22), 1)
                else:
                    icon = _up(self.tile_tex[tid][0])
            else:
                icon = _up(_ICON_GEN[it.icon](it.color))
            self.icons[it.name] = icon
            self.icons_small[it.name] = pygame.transform.scale(icon, (20, 20))

    def _load_characters(self):
        look = dict(skin=(240, 200, 160), hair=(110, 70, 40), shirt=(60, 110, 200),
                    pants=(80, 70, 60), shoes=(50, 40, 30))
        for frame in ("idle", "jump", 0, 1, 2, 3):
            self.player[frame] = _flip_pair(_up(_humanoid(frame=frame, **look)))

        def humanoid_frames(skin, hair, shirt, pants, **kw):
            return [_flip_pair(_up(_humanoid(skin, hair, shirt, pants, (40, 35, 30), f, **kw)))
                    for f in (0, 1, 2, 3)]

        self.creatures["zombie"] = humanoid_frames((120, 170, 100), (60, 50, 40), (90, 80, 140),
                                                   (60, 70, 60), zombie=True)
        self.creatures["frozen_zombie"] = humanoid_frames((160, 200, 230), (200, 220, 240),
                                                          (70, 90, 130), (60, 70, 90), zombie=True)
        self.creatures["skeleton"] = humanoid_frames((230, 225, 200), (0, 0, 0), (45, 40, 35),
                                                     (230, 225, 200), skeleton=True)
        slimes = {"green_slime": (80, 200, 80), "blue_slime": (70, 130, 230),
                  "sand_slime": (220, 190, 110), "ice_slime": (150, 210, 255),
                  "jungle_slime": (120, 200, 40), "lava_slime": (255, 110, 30)}
        for kind, col in slimes.items():
            self.creatures[kind] = [_flip_pair(_up(_slime(col, sq))) for sq in (False, True)]
        bats = {"cave_bat": (95, 80, 95), "jungle_bat": (90, 170, 60), "ice_bat": (150, 200, 240),
                "hellbat": (230, 90, 40)}
        for kind, col in bats.items():
            self.creatures[kind] = [_flip_pair(_up(_bat(col, up))) for up in (True, False)]
        self.creatures["demon_eye"] = [_flip_pair(_up(_eye(t))) for t in (0, 1)]
        self.creatures["hornet"] = [_flip_pair(_up(_hornet((230, 200, 40), up))) for up in (True, False)]
        self.creatures["crab"] = [_flip_pair(_up(_crab((220, 70, 60), st))) for st in (0, 1)]
        self.creatures["servant_eye"] = [_flip_pair(pygame.transform.scale(_up(_eye(t)), (22, 15)))
                                         for t in (0, 1)]
        self.creatures["bunny"] = [_flip_pair(_up(_bunny(f))) for f in (0, 1)]
        self.creatures["penguin"] = [_flip_pair(_up(_penguin(f))) for f in (0, 1)]
        self.creatures["bird"] = [_flip_pair(_up(_bird(u))) for u in (True, False)]
        self.creatures["firefly"] = [_flip_pair(_up(_firefly(b))) for b in (True, False)]
        self.creatures["boar"] = [_flip_pair(_up(_boar(f))) for f in (0, 1)]
        self.creatures["snow_wolf"] = [_flip_pair(_up(_wolf(f))) for f in (0, 1)]
        # the scorpion is drawn facing left, so its pair is swapped
        self.creatures["scorpion"] = [_flip_pair(_up(_scorpion(f)))[::-1] for f in (0, 1)]

        npc_looks = {
            "guide": dict(skin=(240, 200, 160), hair=(90, 60, 30), shirt=(70, 140, 70), pants=(90, 70, 50)),
            "merchant": dict(skin=(235, 195, 155), hair=(200, 200, 205), shirt=(150, 110, 60),
                             pants=(70, 60, 50), beard=(225, 225, 230)),
            "nurse": dict(skin=(245, 210, 175), hair=(230, 120, 140), shirt=(250, 250, 250),
                          pants=(250, 250, 250), helmet=(250, 250, 250)),
            "traveler": dict(skin=(230, 195, 160), hair=(180, 180, 190), shirt=(90, 60, 150),
                             pants=(80, 50, 130), hat=(90, 60, 150), robe=(90, 60, 150), beard=(210, 210, 220)),
            "blacksmith": dict(skin=(215, 170, 130), hair=(50, 40, 35), shirt=(130, 90, 60),
                               pants=(60, 55, 55), beard=(60, 45, 35)),
        }
        for kind, look in npc_looks.items():
            self.npcs[kind] = {f: _flip_pair(_up(_humanoid(shoes=(40, 35, 30), frame=f, **look)))
                               for f in ("idle", 0, 1, 2, 3)}
        self.bosses["eye"] = {phase: [_flip_pair(_up(_eye_boss(phase, f))) for f in (0, 1)] for phase in (1, 2)}
        self.bosses["king_slime"] = [_flip_pair(_up(_king_slime(sq))) for sq in (False, True)]

    def player_look(self, head=None, body=None, legs=None):
        """Player frames with armour colours applied (cached per armour combination)."""
        key = (head, body, legs)
        if key not in self._player_looks:
            look = dict(skin=(240, 200, 160), hair=(110, 70, 40), shirt=(60, 110, 200),
                        pants=(80, 70, 60), shoes=(50, 40, 30))
            if head:
                look["helmet"] = ITEMS[head].color
            if body:
                look["armor"] = ITEMS[body].color
            if legs:
                look["greaves"] = ITEMS[legs].color
            self._player_looks[key] = {f: _flip_pair(_up(_humanoid(frame=f, **look)))
                                       for f in ("idle", "jump", 0, 1, 2, 3)}
        return self._player_looks[key]

    def tile(self, tid, tx, ty):
        variants = self.tile_tex.get(tid)
        if not variants:
            return None
        return variants[((tx * 73856093) ^ (ty * 19349663)) % len(variants)]
