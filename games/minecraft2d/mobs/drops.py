"""
Tables de loot des mobs : ce que chaque mob laisse en mourant.
"""
import random

from config import (
    TILE_STONE, TILE_IRON_ORE, TILE_GOLD_ORE, TILE_DIAMOND_ORE,
    TILE_SILK, TILE_BONE, TILE_SLIME_BALL, TILE_FANG, TILE_CRYSTAL,
    TILE_FEATHER, TILE_VENOM, TILE_MAGMA,
    EQUIP_SWORD, EQUIP_PICKAXE, EQUIP_HEAD, EQUIP_BODY, EQUIP_FEET,
    MAT_WOOD, MAT_IRON, MAT_GOLD,
)

# Import en dur des constantes mob pour éviter les dépendances circulaires
MOB_SLIME   = 0
MOB_ZOMBIE  = 1
MOB_GOLEM   = 2
MOB_CHICKEN = 3
MOB_FROG    = 4
MOB_SEAGULL = 5
MOB_SPIDER  = 6
MOB_SKELETON = 7
MOB_BAT     = 8
MOB_CRAB    = 9
MOB_DEMON   = 10
MOB_BOAR    = 11
MOB_TROLL   = 12
MOB_WORM    = 13
MOB_WRAITH  = 14
MOB_TENDRIL = 15
MOB_PENGUIN    = 16
MOB_POLAR_BEAR = 17
MOB_SCORPION   = 18
MOB_VULTURE    = 19
MOB_WOLF       = 20
MOB_CAT        = 21

# Format : liste de (item, count_min, count_max, probabilité)
# item = TILE_xxx (ressource bloc) ou (EQUIP_xxx, MAT_xxx) (équipement)
_MOB_DROPS = {
    MOB_SLIME:    [
        (TILE_SLIME_BALL, 1, 2, 0.70),     # bave (composant flèche explosive)
    ],
    MOB_ZOMBIE:   [
        (TILE_IRON_ORE,   1, 1, 0.30),
        (TILE_BONE,        1, 1, 0.40),     # os
    ],
    MOB_GOLEM:    [
        (TILE_STONE,       2, 4, 1.00),
        (TILE_IRON_ORE,    1, 2, 0.50),
        (TILE_CRYSTAL,     1, 1, 0.60),     # cristal
    ],
    MOB_CHICKEN:  [
        (TILE_FEATHER,     1, 1, 0.60),     # plume
    ],
    MOB_FROG:     [
        (TILE_SLIME_BALL,  1, 1, 0.40),     # bave (grenouille → gluant)
    ],
    MOB_SEAGULL:  [
        (TILE_FEATHER,     1, 2, 0.80),     # plume
    ],
    MOB_SPIDER:   [
        (TILE_SILK,        1, 2, 0.80),     # fil d'araignée
        (TILE_VENOM,       1, 1, 0.55),     # venin
    ],
    MOB_SKELETON: [
        (TILE_STONE,               1, 2, 0.80),
        (TILE_BONE,                1, 2, 0.80),     # os (source principale)
        ((EQUIP_SWORD, MAT_WOOD), 1, 1, 0.08),
    ],
    MOB_BAT:      [
        (TILE_FEATHER,     1, 1, 0.40),     # plume (ailes de chauve-souris)
    ],
    MOB_CRAB:     [
        (TILE_STONE,       1, 1, 0.60),
        (TILE_BONE,        1, 1, 0.35),     # carapace → os
    ],
    MOB_DEMON:    [
        (TILE_GOLD_ORE,    1, 2, 0.60),
        (TILE_DIAMOND_ORE, 1, 1, 0.40),
        (TILE_MAGMA,       1, 2, 0.80),     # cœur de magma (source principale)
        (TILE_FANG,        1, 1, 0.30),     # crocs de démon
    ],
    MOB_BOAR:     [
        (TILE_STONE,       1, 2, 0.70),
        (TILE_FANG,        1, 1, 0.55),     # défenses de sanglier
    ],
    MOB_TROLL:    [
        (TILE_STONE,       2, 4, 0.90),
        (TILE_IRON_ORE,    1, 1, 0.25),
        (TILE_CRYSTAL,     1, 1, 0.40),     # cristal
        (TILE_BONE,        1, 2, 0.50),     # os
    ],
    MOB_WORM:     [
        (TILE_STONE,       1, 3, 0.80),
        (TILE_IRON_ORE,    1, 2, 0.40),
        (TILE_GOLD_ORE,    1, 1, 0.15),
        (TILE_CRYSTAL,     1, 2, 0.50),     # cristal (entrailles)
        (TILE_SLIME_BALL,  1, 2, 0.35),     # bave de ver
    ],
    MOB_WRAITH:   [
        (TILE_GOLD_ORE,    1, 2, 0.70),
        (TILE_DIAMOND_ORE, 1, 2, 0.45),
        (TILE_BONE,        1, 2, 0.50),     # os de spectre
        (TILE_MAGMA,       1, 1, 0.25),     # résidu spectral
    ],
    MOB_TENDRIL:  [
        # Boss végétal : drops garantis importants
        (TILE_DIAMOND_ORE, 2, 4, 1.00),
        (TILE_GOLD_ORE,    3, 6, 1.00),
        (TILE_MAGMA,       2, 3, 1.00),     # cœur incandescent
        (TILE_CRYSTAL,     2, 3, 1.00),     # cristaux de racine
        (TILE_VENOM,       1, 2, 0.60),     # sève toxique
    ],
    MOB_PENGUIN:    [
        (TILE_FEATHER,     1, 1, 0.50),     # plume
    ],
    MOB_POLAR_BEAR: [
        (TILE_STONE,       2, 4, 0.90),
        (TILE_IRON_ORE,    1, 2, 0.35),
        (TILE_FANG,        1, 2, 0.65),     # crocs d'ours
    ],
    MOB_SCORPION:   [
        (TILE_STONE,       1, 2, 0.60),
        (TILE_VENOM,       1, 2, 0.70),     # venin (source principale)
        (TILE_FANG,        1, 1, 0.40),     # dard
    ],
    MOB_VULTURE:    [
        (TILE_FEATHER,     1, 2, 0.80),     # plume
        (TILE_BONE,        1, 1, 0.30),     # os
    ],
    MOB_WOLF:       [
        (TILE_STONE,       1, 2, 0.60),
        (TILE_FANG,        1, 1, 0.50),     # crocs de loup
    ],
    MOB_CAT:        [],
}


def roll_drops(mob_type):
    """
    Retourne la liste des drops pour un mob mort.
    [(item, count), ...] où item est TILE_xxx ou (EQUIP_xxx, MAT_xxx).
    """
    drops = []
    for entry in _MOB_DROPS.get(mob_type, []):
        item, cmin, cmax, prob = entry
        if random.random() < prob:
            count = random.randint(cmin, cmax)
            drops.append((item, count))
    return drops
