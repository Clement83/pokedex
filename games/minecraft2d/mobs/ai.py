"""
Intelligence artificielle des mobs : mise à jour comportementale par frame.
"""
import math
from config import GRAVITY, MAX_FALL_SPEED, JUMP_VEL, PLAYER_W, PLAYER_H, TILE_SIZE

from mobs.base import (
    MOB_SLIME, MOB_ZOMBIE, MOB_GOLEM,
    MOB_CHICKEN, MOB_FROG, MOB_SEAGULL,
    _PASSIVE_MOBS, _mw, _mh,
)
from mobs.physics import _solid, _move_mob_x, _move_mob_y


# ── Utilitaires ───────────────────────────────────────────────────────────────

def _nearest_player(mob, players):
    cx = mob.center_col()
    cy = mob.center_row()
    best_p, best_d, best_pcx, best_pcy = None, 1e9, 0.0, 0.0
    for p in players:
        pcx = p.x + PLAYER_W / TILE_SIZE / 2
        pcy = p.y + PLAYER_H / TILE_SIZE / 2
        d   = math.hypot(cx - pcx, cy - pcy)
        if d < best_d:
            best_d, best_p, best_pcx, best_pcy = d, p, pcx, pcy
    return best_p, best_d, best_pcx, best_pcy


def _has_los(col0, row0, col1, row1, world):
    """Ligne de vue (Bresenham approximé)."""
    dc    = col1 - col0
    dr    = row1 - row0
    steps = max(abs(dc), abs(dr), 1)
    for i in range(1, steps):
        t = i / steps
        c = int(col0 + dc * t + 0.5)
        r = int(row0 + dr * t + 0.5)
        if _solid(world, c, r):
            return False
    return True


# ── Logique principale ────────────────────────────────────────────────────────

def update_mob(mob, dt, players, world):
    mob._state_cd = max(0.0, mob._state_cd - dt)
    mob._jump_cd  = max(0.0, mob._jump_cd  - dt)
    mob._push_cd  = max(0.0, mob._push_cd  - dt)

    player, dist, pcx, pcy = _nearest_player(mob, players)
    cx  = mob.center_col()
    cy  = mob.center_row()
    dpx = pcx - cx
    dir_to = math.copysign(1.0, dpx) if abs(dpx) > 0.1 else 1.0

    # ── Slime ─────────────────────────────────────────────────────────────────
    if mob.mob_type == MOB_SLIME:
        if dist <= 5.0:
            mob.state = "chase"
        elif mob._state_cd <= 0:
            mob.state = "idle"
        if mob.state == "chase":
            if mob.on_ground and mob._jump_cd <= 0:
                mob.vx       = 2.5 * dir_to
                mob.vy       = JUMP_VEL * 0.65
                mob._jump_cd = 0.85
        else:
            mob.vx = 0.0

    # ── Zombie ────────────────────────────────────────────────────────────────
    elif mob.mob_type == MOB_ZOMBIE:
        if dist <= 8.0 and _has_los(int(cx), int(cy), int(pcx), int(pcy), world):
            mob.state     = "chase"
            mob._state_cd = 2.5
        elif mob._state_cd <= 0:
            mob.state = "idle"
        if mob.state == "chase":
            mob.vx = 2.0 * dir_to
            if mob.on_ground and mob._jump_cd <= 0:
                next_col = int(mob.x + dir_to * (_mw(MOB_ZOMBIE) + 0.1))
                if _solid(world, next_col, int(cy)):
                    mob.vy       = JUMP_VEL
                    mob._jump_cd = 0.5
        else:
            mob._wander_cd -= dt
            if mob._wander_cd <= 0:
                mob._wander_dir = 1 if mob._rng.random() > 0.5 else -1
                mob._wander_cd  = 1.5 + mob._rng.random() * 2.0
            mob.vx = 1.5 * mob._wander_dir
            check_col = int(mob.x + mob._wander_dir * (_mw(MOB_ZOMBIE) + 0.1))
            if _solid(world, check_col, int(cy)):
                mob._wander_dir *= -1
                mob._wander_cd   = 0.0

    # ── Golem ─────────────────────────────────────────────────────────────────
    elif mob.mob_type == MOB_GOLEM:
        if mob.state == "idle" and dist <= 3.0:
            mob.state     = "chase"
            mob._state_cd = 5.0
        elif mob._state_cd <= 0:
            mob.state = "idle"
        if mob.state == "chase":
            mob.vx = 1.8 * dir_to
            if mob.on_ground and mob._jump_cd <= 0:
                next_col = int(mob.x + dir_to * (_mw(MOB_GOLEM) + 0.1))
                if _solid(world, next_col, int(cy)):
                    mob.vy       = JUMP_VEL * 0.85
                    mob._jump_cd = 0.6
        else:
            mob.vx *= 0.8

    # ── Poule ─────────────────────────────────────────────────────────────────
    elif mob.mob_type == MOB_CHICKEN:
        if dist <= 4.0:
            mob.vx = -dir_to * 3.5
            if mob.on_ground and mob._jump_cd <= 0:
                mob.vy       = JUMP_VEL * 0.5
                mob._jump_cd = 0.55
        else:
            mob._wander_cd -= dt
            if mob._wander_cd <= 0:
                mob._wander_dir = 1 if mob._rng.random() > 0.5 else -1
                mob._wander_cd  = 2.0 + mob._rng.random() * 3.0
            mob.vx = 1.2 * mob._wander_dir
            check_col = int(mob.x + mob._wander_dir * (_mw(MOB_CHICKEN) + 0.1))
            if _solid(world, check_col, int(cy)):
                mob._wander_dir *= -1
                mob._wander_cd   = 0.0

    # ── Grenouille ────────────────────────────────────────────────────────────
    elif mob.mob_type == MOB_FROG:
        if dist <= 3.5 and mob.on_ground and mob._jump_cd <= 0:
            mob.vx       = -dir_to * 4.0
            mob.vy       = JUMP_VEL * 0.68
            mob._jump_cd = 0.9
        elif dist > 3.5:
            mob._wander_cd -= dt
            if mob._wander_cd <= 0:
                mob._wander_dir = 1 if mob._rng.random() > 0.5 else -1
                mob._wander_cd  = 1.2 + mob._rng.random() * 2.5
            if mob.on_ground and mob._jump_cd <= 0:
                mob.vx       = 2.2 * mob._wander_dir
                mob.vy       = JUMP_VEL * 0.62
                mob._jump_cd = 1.0 + mob._rng.random() * 0.8

    # ── Mouette ───────────────────────────────────────────────────────────────
    elif mob.mob_type == MOB_SEAGULL:
        mob._fly_phase += dt * 1.6
        mob._wander_cd -= dt
        if mob._wander_cd <= 0:
            mob._wander_dir = 1 if mob._rng.random() > 0.5 else -1
            mob._wander_cd  = 3.0 + mob._rng.random() * 4.0
        mob.vx = 3.5 * mob._wander_dir
        mob.vy = math.sin(mob._fly_phase) * 0.7
        check_col = int(mob.x + mob._wander_dir * (_mw(MOB_SEAGULL) + 0.2))
        if _solid(world, check_col, int(mob.center_row())):
            mob._wander_dir *= -1
            mob._wander_cd   = 0.0

    # ── Gravité + déplacement ─────────────────────────────────────────────────
    if mob.mob_type == MOB_SEAGULL:
        mob.x += mob.vx * dt
        mob.y += mob.vy * dt
    else:
        mob.vy = min(mob.vy + GRAVITY * dt, MAX_FALL_SPEED)
        _move_mob_x(mob, world, mob.vx * dt)
        _move_mob_y(mob, world, mob.vy * dt)

    # ── Contact joueur → poussée (agressifs seulement) ────────────────────────
    if mob.mob_type in _PASSIVE_MOBS:
        return
    if mob._push_cd <= 0:
        pw = PLAYER_W / TILE_SIZE
        ph = PLAYER_H / TILE_SIZE
        mw = _mw(mob.mob_type)
        mh = _mh(mob.mob_type)
        for p in players:
            ox = (mob.x < p.x + pw) and (mob.x + mw > p.x)
            oy = (mob.y < p.y + ph) and (mob.y + mh > p.y)
            if ox and oy:
                push = math.copysign(1.0, p.x + pw / 2 - (mob.x + mw / 2))
                p.vx         = push * 5.0
                mob._push_cd = 0.5
                p.hp          = max(0, p.hp - 1)
                p._dmg_flash  = 0.4
