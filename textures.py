"""Procedural pixel-art textures for tiles, items, the player and creatures.

Everything is authored on a small pixel grid and scaled up 2x for a crisp look.
A PNG in images/textures/tiles/<name>.png or images/textures/items/<name>.png
replaces the generated texture of the same name.
"""
import os
import random
import zlib

import pygame

from settings import TILE_SIZE, TEXTURE_OVERRIDE_DIR
from tiles import TILES, T
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


def _t_ore(rng, color):
    s = _t_stone(rng)
    for _ in range(rng.randint(3, 4)):
        cx, cy = rng.randrange(2, 14), rng.randrange(2, 14)
        pts = [(cx, cy), (cx + 1, cy), (cx, cy + 1), (cx - 1, cy), (cx, cy - 1)]
        for p in pts[:rng.randint(3, 5)]:
            s.set_at(p, color)
        s.set_at((cx, cy - 1) if rng.random() < 0.5 else (cx - 1, cy), shade(color, 1.3))
        s.set_at((cx + 1, cy + 1), shade(color, 0.6))
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
    """Copy of a 32px canopy tile with leafy holes on exposed sides (mask bits: up, down, left, right)."""
    rng = random.Random(seed)
    out = tex.copy()
    size = out.get_width()
    clear = (0, 0, 0, 0)
    for y in range(0, size, PX):
        for x in range(0, size, PX):
            px, py = x // PX, y // PX
            depth = min(px if mask & 4 else 99, 15 - px if mask & 8 else 99,
                        py if mask & 1 else 99, 15 - py if mask & 2 else 99)
            if depth < 3 and rng.random() < (0.7, 0.4, 0.15)[depth]:
                out.fill(clear, (x, y, PX, PX))
    return out


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


def _t_workbench(rng):
    wood = (165, 110, 60)
    s = _canvas()
    for x in range(16):
        for y in range(6, 9):
            s.set_at((x, y), shade(wood, 1.1 if y == 6 else 1.0))
        s.set_at((x, 9), shade(wood, 0.6))
    for y in range(10, 16):
        for x in (1, 2, 13, 14):
            s.set_at((x, y), shade(wood, 0.85 if x in (2, 14) else 1.0))
    for x in range(3, 13):
        s.set_at((x, 12), shade(wood, 0.8))
    return s


def _t_furnace(rng):
    stone = (115, 105, 105)
    s = _canvas()
    for y in range(3, 16):
        for x in range(1, 15):
            c = shade(stone, rng.choice((0.92, 1.0, 1.06)))
            if (y - 3) % 4 == 3 or (x + ((y - 3) // 4) * 3) % 6 == 0:
                c = shade(stone, 0.7)
            s.set_at((x, y), c)
    for x in range(10, 13):
        for y in range(0, 3):
            s.set_at((x, y), shade(stone, 0.8))
    pygame.draw.rect(s, (30, 20, 20), (5, 9, 6, 5))
    for x, y in ((6, 12), (7, 11), (8, 12), (9, 11), (7, 12), (8, 11)):
        s.set_at((x, y), (255, rng.randint(120, 200), 40))
    return s


def _t_anvil(rng):
    base = (85, 85, 95)
    s = _canvas()
    pygame.draw.polygon(s, base, [(1, 6), (14, 6), (14, 9), (4, 9), (1, 7)])
    pygame.draw.rect(s, base, (5, 9, 6, 3))
    pygame.draw.rect(s, base, (3, 12, 10, 4))
    for x in range(2, 15):
        s.set_at((x, 6), (145, 145, 160))
    for x in range(3, 13):
        s.set_at((x, 15), (55, 55, 62))
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


def _t_liquid(rng, base, alpha, hilite):
    s = _canvas()
    for y in range(16):
        for x in range(16):
            s.set_at((x, y), shade(base, rng.choice((0.92, 1.0, 1.06))) + (alpha,))
    for _ in range(3):
        x, y = rng.randrange(14), rng.randrange(16)
        s.set_at((x, y), hilite + (alpha,))
        s.set_at((x + 1, y), hilite + (alpha,))
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
    "copper_ore": lambda r: _t_ore(r, (215, 125, 60)),
    "iron_ore": lambda r: _t_ore(r, (200, 175, 160)),
    "gold_ore": lambda r: _t_ore(r, (245, 210, 60)),
    "hellstone": _t_hellstone,
    "wood": _t_wood,
    "tree": _t_trunk,
    "leaves": lambda r: _t_leaves(r, (60, 150, 50)),
    "jungle_leaves": lambda r: _t_leaves(r, (40, 175, 60)),
    "boreal_leaves": lambda r: _t_leaves(r, (55, 110, 90)),
    "cactus": _t_cactus,
    "torch": _t_torch,
    "workbench": _t_workbench,
    "furnace": _t_furnace,
    "anvil": _t_anvil,
    "mushroom": _t_mushroom,
    "life_crystal": _t_crystal,
    "pot": _t_pot,
    "water": lambda r: _t_liquid(r, (40, 100, 210), 150, (110, 170, 245)),
    "lava": lambda r: _t_liquid(r, (235, 95, 20), 235, (255, 200, 70)),
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


_ICON_GEN = {
    "pickaxe": _i_pickaxe, "axe": _i_axe, "sword": _i_sword, "bow": _i_bow, "arrow": _i_arrow,
    "staff": _i_staff, "bar": _i_bar, "gel": _i_gel, "lens": _i_lens, "bone": _i_bone,
    "potion": _i_potion,
}
_ICON_FROM_TILE = {"mushroom": "mushroom", "crystal": "life_crystal", "cactus": "cactus"}


# ----------------------------------------------------------------------
# characters
# ----------------------------------------------------------------------

def _humanoid(skin, hair, shirt, pants, shoes, frame, zombie=False, skeleton=False):
    """12x22 humanoid facing right. frame: 0-3 walk cycle, 'idle', 'jump'."""
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
        self.tile_tex = {}       # tile id -> [variants]
        self.water_top = None
        self.cracks = []
        self.icons = {}          # item name -> 32x32
        self.icons_small = {}    # item name -> 20x20 (drops)
        self.player = {}         # frame -> (right, left)
        self.creatures = {}      # kind -> [(right, left), ...]

    def _override(self, kind, name):
        path = os.path.join(TEXTURE_OVERRIDE_DIR, kind, name + ".png")
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
        return None

    def load(self):
        for td in TILES:
            gen = _TILE_GEN.get(td.name)
            if gen is None:
                continue
            ov = self._override("tiles", td.name)
            if ov is not None:
                self.tile_tex[td.id] = [ov]
                continue
            self.tile_tex[td.id] = [_up(gen(_rng(td.name, v))) for v in range(VARIANTS)]
        top = _t_liquid(_rng("water_top"), (40, 100, 210), 150, (110, 170, 245))
        for x in range(16):
            top.set_at((x, 0), (170, 210, 255, 210))
            top.set_at((x, 1), (120, 175, 245, 180))
        self.water_top = _up(top)
        self.cracks = [_up(_crack_stage(i)) for i in range(4)]
        self.leaf_tex = {}
        for name in ("leaves", "jungle_leaves", "boreal_leaves"):
            tid = T[name]
            for mask in range(16):
                self.leaf_tex[(tid, mask)] = ragged_edges(self.tile_tex[tid][0], mask, tid * 16 + mask)
        self.walls = {}
        for biome, tile_name in (("forest", "dirt"), ("desert", "sand"), ("snow", "snow"),
                                 ("jungle", "mud"), ("ocean", "sand")):
            wall = self.tile_tex[T[tile_name]][0].copy()
            wall.fill((88, 84, 92), special_flags=pygame.BLEND_RGB_MULT)
            self.walls[biome] = wall
        self._load_icons()
        self._load_characters()

    def _load_icons(self):
        for it in ITEMS.values():
            ov = self._override("items", it.name)
            if ov is not None:
                icon = ov
            elif it.icon == "block" or it.icon in _ICON_FROM_TILE:
                tile_name = it.place if it.icon == "block" else _ICON_FROM_TILE[it.icon]
                tex = self.tile_tex[T[tile_name]][0]
                if TILES[T[tile_name]].solid:
                    icon = pygame.Surface((32, 32), pygame.SRCALPHA)
                    small = pygame.transform.scale(tex, (22, 22))
                    icon.blit(small, (5, 5))
                    pygame.draw.rect(icon, (0, 0, 0, 120), (5, 5, 22, 22), 1)
                else:
                    icon = tex.copy()
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

    def tile(self, tid, tx, ty):
        variants = self.tile_tex.get(tid)
        if not variants:
            return None
        return variants[((tx * 73856093) ^ (ty * 19349663)) % len(variants)]
