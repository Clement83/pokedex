"""
Intelligence artificielle des mobs : mise à jour comportementale par frame.
"""
import math
from config import GRAVITY, MAX_FALL_SPEED, JUMP_VEL, PLAYER_W, PLAYER_H, TILE_SIZE

from mobs.base import (
    MOB_SLIME, MOB_ZOMBIE, MOB_GOLEM,
    MOB_CHICKEN, MOB_FROG, MOB_SEAGULL,
    MOB_SPIDER, MOB_SKELETON, MOB_BAT, MOB_CRAB, MOB_DEMON, MOB_BOAR,
    _PASSIVE_MOBS, _FLYING_MOBS, _DEEP_MOBS, _mw, _mh,
)
from mobs.physics import _solid, _move_mob_x, _move_mob_y
from mobs.armor import _apply_contact_dmg, wears_gold
from mobs.deep import _update_deep_mob


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

def update_mob(mob, dt, players, world):  # noqa: C901
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

    # ── Araignée ──────────────────────────────────────────────────────────────
    elif mob.mob_type == MOB_SPIDER:
        if dist <= 7.0:
            mob.state     = "chase"
            mob._state_cd = 3.0
        elif mob._state_cd <= 0:
            mob.state = "idle"
        if mob.state == "chase":
            mob.vx = 3.0 * dir_to
            # Escalade : si mur devant, monte
            next_col = int(mob.x + dir_to * (_mw(MOB_SPIDER) + 0.1))
            if mob.on_ground and mob._jump_cd <= 0:
                if _solid(world, next_col, int(cy)):
                    mob.vy       = JUMP_VEL * 0.9
                    mob._jump_cd = 0.4
        else:
            mob._wander_cd -= dt
            if mob._wander_cd <= 0:
                mob._wander_dir = 1 if mob._rng.random() > 0.5 else -1
                mob._wander_cd  = 1.0 + mob._rng.random() * 2.0
            mob.vx = 2.0 * mob._wander_dir

    # ── Squelette ─────────────────────────────────────────────────────────────
    elif mob.mob_type == MOB_SKELETON:
        if dist <= 10.0 and _has_los(int(cx), int(cy), int(pcx), int(pcy), world):
            mob.state     = "chase"
            mob._state_cd = 3.0
        elif mob._state_cd <= 0:
            mob.state = "idle"
        if mob.state == "chase":
            # Garde 3-6 tiles de distance (archer)
            if dist < 3.0:
                mob.vx = -2.5 * dir_to
            elif dist > 6.0:
                mob.vx = 2.5 * dir_to
            else:
                mob.vx = mob.vx * 0.7
            if mob.on_ground and mob._jump_cd <= 0:
                next_col = int(mob.x + dir_to * (_mw(MOB_SKELETON) + 0.1))
                if _solid(world, next_col, int(cy)):
                    mob.vy       = JUMP_VEL
                    mob._jump_cd = 0.5
        else:
            mob._wander_cd -= dt
            if mob._wander_cd <= 0:
                mob._wander_dir = 1 if mob._rng.random() > 0.5 else -1
                mob._wander_cd  = 2.0 + mob._rng.random() * 2.0
            mob.vx = 1.0 * mob._wander_dir

    # ── Chauve-souris ─────────────────────────────────────────────────────────
    elif mob.mob_type == MOB_BAT:
        mob._fly_phase += dt * 2.5
        if dist <= 4.0 and mob._state_cd <= 0:
            mob.state     = "chase"
            mob._state_cd = 2.0
        elif mob._state_cd <= 0:
            mob.state = "idle"
        if mob.state == "chase":
            mob.vx = 3.5 * dir_to
            mob.vy = (pcy - cy) * 2.0 + math.sin(mob._fly_phase) * 0.5
        else:
            mob._wander_cd -= dt
            if mob._wander_cd <= 0:
                mob._wander_dir = 1 if mob._rng.random() > 0.5 else -1
                mob._wander_cd  = 1.5 + mob._rng.random() * 3.0
            mob.vx = 2.5 * mob._wander_dir
            mob.vy = math.sin(mob._fly_phase) * 0.8

    # ── Crabe ────────────────────────────────────────────────────────────────
    elif mob.mob_type == MOB_CRAB:
        if dist <= 6.0:
            mob.state     = "chase"
            mob._state_cd = 1.5
        elif mob._state_cd <= 0:
            mob.state = "idle"
        if mob.state == "chase":
            mob.vx = 2.8 * dir_to
        else:
            mob._wander_cd -= dt
            if mob._wander_cd <= 0:
                mob._wander_dir = 1 if mob._rng.random() > 0.5 else -1
                mob._wander_cd  = 1.0 + mob._rng.random() * 2.5
            mob.vx = 1.5 * mob._wander_dir
            check_col = int(mob.x + mob._wander_dir * (_mw(MOB_CRAB) + 0.1))
            if _solid(world, check_col, int(cy)):
                mob._wander_dir *= -1

    # ── Démon ────────────────────────────────────────────────────────────────
    elif mob.mob_type == MOB_DEMON:
        mob._fly_phase += dt * 1.0
        if dist <= 15.0:
            mob.state     = "chase"
            mob._state_cd = 4.0
        elif mob._state_cd <= 0:
            mob.state = "idle"
        if mob.state == "chase":
            mob.vx = 2.2 * dir_to
            mob.vy = (pcy - cy) * 1.5 + math.sin(mob._fly_phase) * 0.4
        else:
            mob._wander_cd -= dt
            if mob._wander_cd <= 0:
                mob._wander_dir = 1 if mob._rng.random() > 0.5 else -1
                mob._wander_cd  = 2.0 + mob._rng.random() * 4.0
            mob.vx = 1.5 * mob._wander_dir
            mob.vy = math.sin(mob._fly_phase) * 0.6

    # ── Sanglier ──────────────────────────────────────────────────────────────
    elif mob.mob_type == MOB_BOAR:
        if player and wears_gold(player): mob.state = "idle"
        elif dist <= 6.0: mob.state = "chase"; mob._state_cd = 2.5
        elif mob._state_cd <= 0: mob.state = "idle"
        if mob.state == "chase":
            mob.vx = 3.5 * dir_to
            nc = int(mob.x + dir_to * (_mw(MOB_BOAR) + 0.1))
            if mob.on_ground and mob._jump_cd <= 0 and _solid(world, nc, int(cy)):
                mob.vy = JUMP_VEL * 0.8; mob._jump_cd = 0.5
        else:
            mob._wander_cd -= dt
            if mob._wander_cd <= 0:
                mob._wander_dir = 1 if mob._rng.random() > 0.5 else -1
                mob._wander_cd  = 2.0 + mob._rng.random() * 3.0
            mob.vx = 2.0 * mob._wander_dir

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
    elif mob.mob_type in _DEEP_MOBS: return _update_deep_mob(mob, dt, players, world)
    # ── Gravité + déplacement ─────────────────────────────────────────────────
    if mob.mob_type in _FLYING_MOBS:
        mob.x += mob.vx * dt
        mob.y += mob.vy * dt
        # Le démon ne peut pas remonter trop haut (évite poursuite infinie en surface)
        if mob.mob_type == MOB_DEMON:
            min_row = world.surface_at(int(mob.center_col())) + 30
            if mob.y < min_row:
                mob.y  = float(min_row)
                if mob.vy < 0:
                    mob.vy = 0.0
    else:
        mob.vy = min(mob.vy + GRAVITY * dt, MAX_FALL_SPEED)
        _move_mob_x(mob, world, mob.vx * dt)
        _move_mob_y(mob, world, mob.vy * dt)

    _apply_contact_dmg(mob, players)



