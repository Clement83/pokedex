"""
Mobs des profondeurs : IA uniquement (spawn géré par manager.py).

Hiérarchie de profondeur (tiles sous la surface) :
  surf+20..+45  → MOB_TROLL  : troll des cavernes, 6 HP, dmg=2, épée Bois min
  surf+45..+65  → MOB_WORM   : ver fouisseur,      9 HP, dmg=3, épée Fer min
  surf+65+      → MOB_WRAITH : spectre abyssal,   12 HP, dmg=4, épée Or min
"""
import math

from config import GRAVITY, MAX_FALL_SPEED, JUMP_VEL
from mobs.base import (
    MOB_TROLL, MOB_WORM, MOB_TENDRIL,
    _mw,
)
from mobs.physics import _solid, _move_mob_x, _move_mob_y
from mobs.armor import _apply_contact_dmg, combat_roll, _CRIT_MULT

TENDRIL_REACH  = 6.0   # rayon d'attaque tentacules (tiles)
TENDRIL_DETECT = 10.0  # rayon de détection (tiles)


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
    mob._fly_phase  += dt
    mob._tendril_cd  = max(0.0, mob._tendril_cd - dt)

    # La Vrille gère tout elle-même (stationnaire, pas de _apply_contact_dmg)
    if mob.mob_type == MOB_TENDRIL:
        _update_tendril(mob, dt, players)
        return

    player, dist = _nearest(mob, players)
    dir_to = math.copysign(1.0, player.x - mob.x) if player else 1.0

    if mob.mob_type == MOB_TROLL:
        _ai_troll(mob, dt, dist, dir_to, world)
    elif mob.mob_type == MOB_WORM:
        _ai_worm(mob, dt, dist, dir_to, player)
    else:  # MOB_WRAITH – collision correcte (plus de traversement de mur)
        _ai_wraith(mob, dt, dist, dir_to, player, world)

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
    # Limiter la vitesse pour éviter le tunnel effect excessif
    speed = math.hypot(mob.vx, mob.vy)
    if speed > 0.32:
        mob.vx *= 0.32 / speed
        mob.vy *= 0.32 / speed
    # Le ver traverse le terrain (intentionnel : ver fouisseur)
    mob.x += mob.vx * dt
    mob.y += mob.vy * dt


def _ai_wraith(mob, dt, dist, dir_to, player, world):
    """Spectre : vole avec collision correcte (ne traverse plus les murs)."""
    if dist <= 20.0:         mob.state = "chase"; mob._state_cd = 5.0
    elif mob._state_cd <= 0: mob.state = "idle"
    if mob.state == "chase" and player:
        mob.vx = 3.0 * dir_to
        mob.vy = (player.y - mob.center_row()) * 1.8 + math.sin(mob._fly_phase) * 0.4
    else:
        mob._wander_cd -= dt
        if mob._wander_cd <= 0:
            mob._wander_dir = 1 if mob._rng.random() > 0.5 else -1
            mob._wander_cd  = 3.0 + mob._rng.random() * 4.0
        mob.vx = 1.5 * mob._wander_dir
        mob.vy = math.sin(mob._fly_phase) * 0.8
    # Collision physique (plus de traversement de mur)
    _move_mob_x(mob, world, mob.vx * dt)
    _move_mob_y(mob, world, mob.vy * dt)


# ── Boss Végétal : La Vrille ((MOB_TENDRIL) – stationnaire ──────────────────────

def _update_tendril(mob, dt, players):
    """La Vrille ne bouge pas. Détecte les joueurs à proximité, attaque à portée."""
    player, dist = _nearest(mob, players)

    if dist <= TENDRIL_DETECT:
        mob.state = "active"
    else:
        mob.state = "idle"
        return

    # Attaque par tentacules quand le joueur est à portée
    if dist <= TENDRIL_REACH and mob._tendril_cd <= 0 and player:
        raw_dmg = 3
        hit, crit = combat_roll(player, mob.mob_type)
        if hit:
            dmg = raw_dmg * _CRIT_MULT if crit else raw_dmg
            player.hp = max(0, player.hp - dmg)
            player._dmg_flash = 0.6 if crit else 0.4
        mob._tendril_cd = 2.0   # 1 attaque toutes les 2 secondes
