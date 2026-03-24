"""
Physique des mobs : collision et déplacement.
"""
from config import ROWS, TILE_AIR, TILE_LAVA, TILE_WATER
from mobs.base import _mw, _mh

_NON_SOLID = (TILE_AIR, TILE_LAVA, TILE_WATER)


def _solid(world, col, row):
    if row < 0 or row >= ROWS:
        return True
    return world.get(col, row) not in _NON_SOLID


def _mob_cols(mob):
    return list(range(int(mob.x), int(mob.x + _mw(mob.mob_type) - 0.01) + 1))


def _mob_rows(mob):
    return list(range(int(mob.y), int(mob.y + _mh(mob.mob_type) - 0.01) + 1))


def _move_mob_x(mob, world, dx):
    mob.x += dx
    mw    = _mw(mob.mob_type)
    left  = int(mob.x)
    right = int(mob.x + mw - 0.01)
    rows  = _mob_rows(mob)
    if dx > 0:
        for r in rows:
            if _solid(world, right, r):
                mob.x  = right - mw
                mob.vx = 0.0
                break
    elif dx < 0:
        for r in rows:
            if _solid(world, left, r):
                mob.x  = left + 1.0
                mob.vx = 0.0
                break


def _move_mob_y(mob, world, dy):
    mob.y += dy
    mh     = _mh(mob.mob_type)
    top    = int(mob.y)
    bottom = int(mob.y + mh - 0.01)
    cols   = _mob_cols(mob)
    if dy > 0:
        mob.on_ground = False
        for c in cols:
            if _solid(world, c, bottom):
                mob.y         = bottom - mh
                mob.vy        = 0.0
                mob.on_ground = True
                break
    elif dy < 0:
        for c in cols:
            if _solid(world, c, top):
                mob.y  = top + 1.0
                mob.vy = 0.0
                break


def _eject_mob(mob, world):
    """Éjecte un mob hors de tout bloc solide (appelé au spawn)."""
    mh = _mh(mob.mob_type)
    mw = _mw(mob.mob_type)
    for _ in range(ROWS):
        top    = int(mob.y)
        bottom = int(mob.y + mh - 0.01)
        cols   = list(range(int(mob.x), int(mob.x + mw - 0.01) + 1))
        if not any(_solid(world, c, r)
                   for r in range(top, bottom + 1) for c in cols):
            break
        mob.y -= 1.0
    mob.vy = min(mob.vy, 0.0)
