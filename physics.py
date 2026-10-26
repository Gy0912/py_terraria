"""Axis-separated tile collision shared by the player, creatures and dropped items."""
import math

from settings import TILE_SIZE

TS = TILE_SIZE
MAX_STEP = 12  # pixels per collision sub-step


def _span(x, y, w, h):
    """Tile range covered by a rect; fractional edges count as touching the next tile."""
    return (int(x) // TS, (math.ceil(x + w) - 1) // TS,
            int(y) // TS, (math.ceil(y + h) - 1) // TS)


def rect_solid(world, x, y, w, h):
    left, right, top, bottom = _span(x, y, w, h)
    for tx in range(left, right + 1):
        for ty in range(top, bottom + 1):
            if world.is_solid(tx, ty):
                return True
    return False


def rect_touches(world, x, y, w, h, tile_ids):
    left, right, top, bottom = _span(x, y, w, h)
    for tx in range(left, right + 1):
        for ty in range(top, bottom + 1):
            if world.get_tile(tx, ty) in tile_ids:
                return True
    return False


def move_x(world, x, y, w, h, dx):
    """Move horizontally; returns (new_x, blocked)."""
    while dx != 0:
        step = max(-MAX_STEP, min(MAX_STEP, dx))
        dx -= step
        nx = x + step
        if rect_solid(world, nx, y, w, h):
            if step > 0:
                return ((math.ceil(nx + w) - 1) // TS) * TS - w, True
            return (int(nx) // TS + 1) * TS, True
        x = nx
    return x, False


def move_y(world, x, y, w, h, dy):
    """Move vertically; returns (new_y, landed, hit_ceiling)."""
    while dy != 0:
        step = max(-MAX_STEP, min(MAX_STEP, dy))
        dy -= step
        ny = y + step
        if rect_solid(world, x, ny, w, h):
            if step > 0:
                return ((math.ceil(ny + h) - 1) // TS) * TS - h, True, False
            return (int(ny) // TS + 1) * TS, False, True
        y = ny
    return y, False, False
