"""
Système d'armure : réduction de dégâts et neutralité or.

armor_def(player)         -> int  défense totale des pièces portées
wears_gold(player)        -> bool True si au moins 1 pièce est en or
_apply_contact_dmg(mob, players)  gère push + dégâts tenant compte de l'armure
"""
import math

from config import (
    ARMOR_DEF, MAT_GOLD, EQUIP_HEAD, EQUIP_BODY, EQUIP_FEET,
    TILE_SIZE, PLAYER_W, PLAYER_H,
)
from mobs.base import (
    _PASSIVE_MOBS, _GOLD_NEUTRAL_MOBS, _MOB_ATTACK_DMG,
    _mw, _mh, MOB_DEMON,
)

_SLOTS = (EQUIP_HEAD, EQUIP_BODY, EQUIP_FEET)


def armor_def(player):
    """Somme de la défense de toutes les pièces d'armure portées."""
    total = 0
    for slot in _SLOTS:
        worn = player.inventory.worn_equip(slot)
        if worn is not None:
            total += ARMOR_DEF.get(worn[1], 0)
    return total


def wears_gold(player):
    """True si le joueur porte au moins une pièce en or."""
    for slot in _SLOTS:
        worn = player.inventory.worn_equip(slot)
        if worn is not None and worn[1] == MAT_GOLD:
            return True
    return False


def _apply_contact_dmg(mob, players):
    """Gère la collision mob→joueur avec réduction d'armure et neutralité or."""
    if mob.mob_type in _PASSIVE_MOBS:
        return
    if mob._push_cd > 0:
        return

    pw = PLAYER_W / TILE_SIZE
    ph = PLAYER_H / TILE_SIZE
    mw = _mw(mob.mob_type)
    mh = _mh(mob.mob_type)
    raw_dmg = _MOB_ATTACK_DMG.get(mob.mob_type, 1)

    for p in players:
        ox = (mob.x < p.x + pw) and (mob.x + mw > p.x)
        oy = (mob.y < p.y + ph) and (mob.y + mh > p.y)
        if not (ox and oy):
            continue
        # Les mobs neutralisés par l'or n'attaquent pas les joueurs en or
        if mob.mob_type in _GOLD_NEUTRAL_MOBS and wears_gold(p):
            continue
        push = math.copysign(1.0, p.x + pw / 2 - (mob.x + mw / 2))
        p.vx         = push * 5.0
        mob._push_cd = 0.5
        eff = max(0, raw_dmg - armor_def(p))
        if eff > 0:
            was_alive    = p.hp > 0
            p.hp         = max(0, p.hp - eff)
            p._dmg_flash = 0.4
            # Le démon disparaît s'il tue un joueur
            if mob.mob_type == MOB_DEMON and was_alive and p.hp <= 0:
                mob.vanish = True
