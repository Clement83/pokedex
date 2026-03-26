"""
Tables de loot des mobs : ce que chaque mob laisse en mourant.
"""
import random

from config import (
    TILE_STONE, TILE_IRON_ORE, TILE_GOLD_ORE, TILE_DIAMOND_ORE,
    TILE_SILK,
    TILE_GORGON_HEART,
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
MOB_GORGON     = 22

# Format : liste de (item, count_min, count_max, probabilité)
# item = TILE_xxx (ressource bloc) ou (EQUIP_xxx, MAT_xxx) (équipement)
_MOB_DROPS = {
    MOB_SLIME:    [],
    MOB_ZOMBIE:   [
        (TILE_IRON_ORE, 1, 1, 0.30),
    ],
    MOB_GOLEM:    [
        (TILE_STONE,    2, 4, 1.00),
        (TILE_IRON_ORE, 1, 2, 0.50),
    ],
    MOB_CHICKEN:  [],
    MOB_FROG:     [],
    MOB_SEAGULL:  [],
    MOB_SPIDER:   [
        (TILE_SILK, 1, 2, 0.80),   # fil d'araignée (composant craft arc/canne)
    ],
    MOB_SKELETON: [
        (TILE_STONE,               1, 2, 0.80),
        ((EQUIP_SWORD, MAT_WOOD),  1, 1, 0.08),
    ],
    MOB_BAT:      [],
    MOB_CRAB:     [
        (TILE_STONE, 1, 1, 0.60),
    ],
    MOB_DEMON:    [
        (TILE_GOLD_ORE,    1, 2, 0.60),
        (TILE_DIAMOND_ORE, 1, 1, 0.40),
    ],
    MOB_BOAR:     [
        (TILE_STONE, 1, 2, 0.70),
    ],
    MOB_TROLL:    [
        (TILE_STONE,    2, 4, 0.90),
        (TILE_IRON_ORE, 1, 1, 0.25),
    ],
    MOB_WORM:     [
        (TILE_STONE,    1, 3, 0.80),
        (TILE_IRON_ORE, 1, 2, 0.40),
        (TILE_GOLD_ORE, 1, 1, 0.15),
    ],
    MOB_WRAITH:   [
        (TILE_GOLD_ORE,    1, 2, 0.70),
        (TILE_DIAMOND_ORE, 1, 2, 0.45),
    ],
    MOB_TENDRIL:  [
        # Boss végétal : drops garantis importants
        (TILE_DIAMOND_ORE, 2, 4, 1.00),
        (TILE_GOLD_ORE,    3, 6, 1.00),
    ],
    MOB_PENGUIN:    [],
    MOB_POLAR_BEAR: [
        (TILE_STONE,    2, 4, 0.90),
        (TILE_IRON_ORE, 1, 2, 0.35),
    ],
    MOB_SCORPION:   [
        (TILE_STONE,    1, 2, 0.60),
    ],
    MOB_VULTURE:    [],
    MOB_WOLF:       [
        (TILE_STONE, 1, 2, 0.60),
    ],
    MOB_CAT:        [],
    MOB_GORGON:     [
        # Boss sonique des abysses : loot unique garanti + opulence
        (TILE_GORGON_HEART, 1, 1, 1.00),   # Loot signature, toujours drôppé
        (TILE_DIAMOND_ORE,  2, 4, 1.00),
        (TILE_GOLD_ORE,     4, 8, 1.00),
    ],
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
