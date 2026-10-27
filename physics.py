"""Axis-separated tile collision shared by the player, NPCs, creatures and dropped items.

`creature=True` uses the creature solidity table, where closed doors also block;
`creature="flyer"` additionally treats liquids as walls (bats and birds never dive).
"""
import math

from settings import TILE_SIZE

TS = TILE_SIZE
MAX_STEP = 12  # pixels per collision sub-step


def _span(x, y, w, h):
    """Tile range covered by a rect; fractional edges count as touching the next tile."""
    return (int(x) // TS, (math.ceil(x + w) - 1) // TS,
            int(y) // TS, (math.ceil(y + h) - 1) // TS)


def rect_solid(world, x, y, w, h, creature=False):
    if creature == "flyer":
        test = world.blocks_flyer
    else:
        test = world.blocks_creature if creature else world.is_solid
    left, right, top, bottom = _span(x, y, w, h)
    for tx in range(left, right + 1):
        for ty in range(top, bottom + 1):
            if test(tx, ty):
                return True
    return False


def rect_touches(world, x, y, w, h, tile_ids):
    left, right, top, bottom = _span(x, y, w, h)
    for tx in range(left, right + 1):
        for ty in range(top, bottom + 1):
            if world.get_tile(tx, ty) in tile_ids:
                return True
    return False


def rect_liquid(world, x, y, w, h, tile_id):
    """True if the rect overlaps the filled part of any liquid cell of the given type."""
    left, right, top, bottom = _span(x, y, w, h)
    for tx in range(left, right + 1):
        for ty in range(top, bottom + 1):
            if world.get_tile(tx, ty) == tile_id:
                surface_y = (ty + 1) * TS - world.liquid_level(tx, ty) * TS / 8
                if y + h > surface_y:
                    return True
    return False


def point_in_liquid(world, px, py, tile_id):
    tx, ty = int(px) // TS, int(py) // TS
    if world.get_tile(tx, ty) != tile_id:
        return False
    return py >= (ty + 1) * TS - world.liquid_level(tx, ty) * TS / 8


def move_x(world, x, y, w, h, dx, creature=False):
    """Move horizontally; returns (new_x, blocked)."""
    while dx != 0:
        step = max(-MAX_STEP, min(MAX_STEP, dx))
        dx -= step
        nx = x + step
        if rect_solid(world, nx, y, w, h, creature):
            if step > 0:
                return ((math.ceil(nx + w) - 1) // TS) * TS - w, True
            return (int(nx) // TS + 1) * TS, True
        x = nx
    return x, False


def move_y(world, x, y, w, h, dy, creature=False):
    """Move vertically; returns (new_y, landed, hit_ceiling)."""
    while dy != 0:
        step = max(-MAX_STEP, min(MAX_STEP, dy))
        dy -= step
        ny = y + step
        if rect_solid(world, x, ny, w, h, creature):
            if step > 0:
                return ((math.ceil(ny + h) - 1) // TS) * TS - h, True, False
            return (int(ny) // TS + 1) * TS, False, True
        y = ny
    return y, False, False
