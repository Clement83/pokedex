"""
Système de combat : toucher / esquive / critique avec scaling par tier.

combat_roll(player, mob_type) -> (hit, crit)
  - Calcule si le mob touche et si c'est un critique.
  - Chaque pièce d'armure réduit les chances de touche et/ou critique.
  - L'efficacité de l'armure dépend de l'écart de tier avec le mob :
      même tier ou supérieur → pleine efficacité
      1 tier en dessous      → ÷4
      2 tiers en dessous     → ÷16  etc.

wears_gold(player)        -> bool  True si au moins 1 pièce est en or
_apply_contact_dmg(mob, players)  gère push + dégâts via combat_roll
"""
import math
import random

from config import (
    MAT_GOLD, MAT_TIER,
    EQUIP_HEAD, EQUIP_BODY, EQUIP_FEET,
    TILE_SIZE, PLAYER_W, PLAYER_H,
)
from mobs.base import (
    _PASSIVE_MOBS, _GOLD_NEUTRAL_MOBS, _MOB_ATTACK_DMG, _MOB_MIN_SWORD_TIER,
    _mw, _mh, MOB_DEMON,
)

_SLOTS = (EQUIP_HEAD, EQUIP_BODY, EQUIP_FEET)

# ── Paramètres de combat ────────────────────────────────────────────────────
_BASE_HIT_CHANCE  = 0.80    # 80 % de toucher à nu
_BASE_CRIT_CHANCE = 0.40    # 40 % de critique (parmi les touches)
_CRIT_MULT        = 2       # multiplicateur de dégâts critique
_MIN_HIT          = 0.05    # plancher : toujours au moins 5 % de touche
_MIN_CRIT         = 0.02    # plancher : toujours au moins 2 % de critique

# Réductions par pièce d'armure (à pleine efficacité de tier)
#                  (hit_reduction, crit_reduction)
_PIECE_REDUCTIONS = {
    EQUIP_HEAD: (0.10, 0.35),   # casque : réduit surtout les critiques
    EQUIP_BODY: (0.30, 0.00),   # plastron : réduit surtout les touches
    EQUIP_FEET: (0.10, 0.00),   # bottes : réduit un peu les touches
}
# Full set même tier :  hit 80% - 50% = 30 %,  crit 40% - 35% = 5 %


def combat_roll(player, mob_type):
    """
    Calcule si le mob touche et si c'est un critique.
    Retourne (hit: bool, crit: bool).

    Le tier du mob est dérivé de _MOB_MIN_SWORD_TIER (0-3).
    Le tier de l'armure vient de MAT_TIER (1-4).
    Efficacité = 1 / 4^max(0, mob_tier - armor_tier).
    """
    mob_tier = _MOB_MIN_SWORD_TIER.get(mob_type, 0)

    hit_red  = 0.0
    crit_red = 0.0

    for slot in _SLOTS:
        worn = player.inventory.worn_equip(slot)
        if worn is None:
            continue
        armor_tier = MAT_TIER.get(worn[1], 0)

        # Poids d'efficacité selon l'écart de tier
        diff = mob_tier - armor_tier
        weight = 1.0 if diff <= 0 else 1.0 / (4 ** diff)

        hr, cr = _PIECE_REDUCTIONS.get(slot, (0.0, 0.0))
        hit_red  += hr * weight
        crit_red += cr * weight

    hit_chance  = max(_MIN_HIT,  _BASE_HIT_CHANCE  - hit_red)
    crit_chance = max(_MIN_CRIT, _BASE_CRIT_CHANCE - crit_red)

    hit  = random.random() < hit_chance
    crit = hit and (random.random() < crit_chance)
    return hit, crit


def wears_gold(player):
    """True si le joueur porte au moins une pièce en or."""
    for slot in _SLOTS:
        worn = player.inventory.worn_equip(slot)
        if worn is not None and worn[1] == MAT_GOLD:
            return True
    return False


def _apply_contact_dmg(mob, players):
    """Gère la collision mob→joueur avec le système touche/critique."""
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
        mob._push_cd = 0.5

        hit, crit = combat_roll(p, mob.mob_type)
        if hit:
            dmg = raw_dmg * _CRIT_MULT if crit else raw_dmg
            was_alive    = p.hp > 0
            p.hp         = max(0, p.hp - dmg)
            p._dmg_flash = 0.6 if crit else 0.4
            p.vx         = push * 5.0
            # Le démon disparaît s'il tue un joueur
            if mob.mob_type == MOB_DEMON and was_alive and p.hp <= 0:
                mob.vanish = True
        else:
            # Esquive : léger recul mais pas de dégâts
            p.vx = push * 2.5
