"""
Mobs des profondeurs : IA et spawn.

Hiérarchie de profondeur (tiles sous la surface) :
  surf+20..+45  → MOB_TROLL  : troll des cavernes, 6 HP, dmg=2, épée Bois min
  surf+45..+65  → MOB_WORM   : ver fouisseur,      9 HP, dmg=3, épée Fer min
  surf+65+      → MOB_WRAITH : spectre abyssal,   12 HP, dmg=4, épée Or min
"""
import math

from world import _hash1
from config import GRAVITY, MAX_FALL_SPEED, JUMP_VEL, TILE_AIR, ROWS
from mobs.base import (
    Mob, MOB_TROLL, MOB_WORM, MOB_WRAITH,
    _mw, _mh,
)
from mobs.physics import _solid, _move_mob_x, _move_mob_y, _eject_mob
from mobs.armor import _apply_contact_dmg


def _nearest(mob, players):
    best_p, best_d = None, 1e9
    for p in players:
        d = math.hypot(mob.center_col() - p.x, mob.center_row() - p.y)
        if d < best_d:
            best_d, best_p = d, p
    return best_p, best_d


# ── IA principale ─────────────────────────────────────────────────────────────

def _update_deep_mob(mob, dt, players, world):
    """IA + déplacement + dégâts de contact pour les mobs des profondeurs."""
    mob._fly_phase += dt
    player, dist = _nearest(mob, players)
    dir_to = math.copysign(1.0, player.x - mob.x) if player else 1.0

    if mob.mob_type == MOB_TROLL:
        _ai_troll(mob, dt, dist, dir_to, world)
    elif mob.mob_type == MOB_WORM:
        _ai_worm(mob, dt, dist, dir_to, player)
    else:  # MOB_WRAITH
        _ai_wraith(mob, dt, dist, dir_to, player)

    _apply_contact_dmg(mob, players)


def _ai_troll(mob, dt, dist, dir_to, world):
    """Troll : lent, trapu, suit le joueur à courte portée."""
    if dist <= 9.0:          mob.state = "chase"; mob._state_cd = 3.0
    elif mob._state_cd <= 0: mob.state = "idle"
    cy = mob.center_row()
    if mob.state == "chase":
        mob.vx = 2.2 * dir_to
        nc = int(mob.x + dir_to * (_mw(MOB_TROLL) + 0.1))
        if mob.on_ground and mob._jump_cd <= 0 and _solid(world, nc, int(cy)):
            mob.vy = JUMP_VEL * 0.9; mob._jump_cd = 0.7
    else:
        mob._wander_cd -= dt
        if mob._wander_cd <= 0:
            mob._wander_dir = 1 if mob._rng.random() > 0.5 else -1
            mob._wander_cd  = 3.0 + mob._rng.random() * 4.0
        mob.vx = 1.0 * mob._wander_dir
    mob.vy = min(mob.vy + GRAVITY * dt, MAX_FALL_SPEED)
    _move_mob_x(mob, world, mob.vx * dt)
    _move_mob_y(mob, world, mob.vy * dt)


def _ai_worm(mob, dt, dist, dir_to, player):
    """Ver fouisseur : traverse le terrain, charge en ligne droite."""
    if dist <= 12.0:         mob.state = "chase"; mob._state_cd = 4.0
    elif mob._state_cd <= 0: mob.state = "idle"
    if mob.state == "chase" and player:
        mob.vx = 4.5 * dir_to
        mob.vy = (player.y - mob.center_row()) * 1.5
    else:
        mob._wander_cd -= dt
        if mob._wander_cd <= 0:
            mob._wander_dir = 1 if mob._rng.random() > 0.5 else -1
            mob._wander_cd  = 2.0 + mob._rng.random() * 3.0
        mob.vx = 2.0 * mob._wander_dir
        mob.vy = 0.0
    # Le ver traverse le terrain (pas de collision physique)
    mob.x += mob.vx * dt
    mob.y += mob.vy * dt


def _ai_wraith(mob, dt, dist, dir_to, player):
    """Spectre : vole librement, traque depuis très loin."""
    if dist <= 20.0:         mob.state = "chase"; mob._state_cd = 5.0
    elif mob._state_cd <= 0: mob.state = "idle"
    if mob.state == "chase" and player:
        mob.vx = 3.5 * dir_to
        mob.vy = (player.y - mob.center_row()) * 2.0 + math.sin(mob._fly_phase) * 0.5
    else:
        mob._wander_cd -= dt
        if mob._wander_cd <= 0:
            mob._wander_dir = 1 if mob._rng.random() > 0.5 else -1
            mob._wander_cd  = 3.0 + mob._rng.random() * 4.0
        mob.vx = 2.0 * mob._wander_dir
        mob.vy = math.sin(mob._fly_phase) * 0.8
    mob.x += mob.vx * dt
    mob.y += mob.vy * dt


# ── Spawn ─────────────────────────────────────────────────────────────────────

def spawn_deep_mobs(spawned, mobs, col, surf, world, seed):
    """Déclenche le spawn des mobs profonds pour une colonne donnée."""
    _try_spawn_troll(spawned, mobs, col, surf, world, seed)
    _try_spawn_worm(spawned, mobs, col, surf, world, seed)
    _try_spawn_wraith(spawned, mobs, col, surf, world, seed)


def _try_spawn_troll(spawned, mobs, col, surf, world, seed):
    key = (col, MOB_TROLL)
    if key in spawned: return
    spawned.add(key)
    if _hash1(col * 167 + 71, seed ^ 0x7011) >= 0.06: return
    deep_min = surf + 20
    for row in range(deep_min, min(deep_min + 25, ROWS - 2)):
        if world.get(col, row) == TILE_AIR and world.get(col, row + 1) != TILE_AIR:
            top = row - math.ceil(_mh(MOB_TROLL)) + 1
            m = Mob(col, top, MOB_TROLL, seed)
            _eject_mob(m, world)
            mobs.append(m)
            break


def _try_spawn_worm(spawned, mobs, col, surf, world, seed):
    key = (col, MOB_WORM)
    if key in spawned: return
    spawned.add(key)
    if _hash1(col * 181 + 83, seed ^ 0xD0A2) >= 0.04: return
    deep_min = surf + 45
    for row in range(deep_min, min(deep_min + 20, ROWS - 2)):
        if world.get(col, row) == TILE_AIR:
            mobs.append(Mob(col, float(row), MOB_WORM, seed))
            break


def _try_spawn_wraith(spawned, mobs, col, surf, world, seed):
    key = (col, MOB_WRAITH)
    if key in spawned: return
    spawned.add(key)
    if _hash1(col * 193 + 97, seed ^ 0xFA17) >= 0.025: return
    deep_min = surf + 65
    for row in range(deep_min, min(deep_min + 20, ROWS - 2)):
        if world.get(col, row) == TILE_AIR:
            mobs.append(Mob(col, float(row), MOB_WRAITH, seed))
            break
