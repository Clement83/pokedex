"""
Types de mobs, constantes et classe Mob.

Mobs agressifs  : MOB_SLIME, MOB_ZOMBIE, MOB_GOLEM, MOB_SPIDER,
                  MOB_SKELETON, MOB_CRAB, MOB_DEMON, MOB_BOAR
Mobs passifs    : MOB_CHICKEN, MOB_FROG, MOB_SEAGULL, MOB_BAT
Spécial Or      : MOB_BOAR ignore les joueurs portant de l'or
Mobs profonds   : MOB_TROLL (+20), MOB_WORM (+45), MOB_WRAITH (+65) tiles sous surf
"""
import random
from config import TILE_SIZE, PLAYER_W, PLAYER_H

# ── Identifiants ──────────────────────────────────────────────────────────────
MOB_SLIME    = 0
MOB_ZOMBIE   = 1
MOB_GOLEM    = 2
MOB_CHICKEN  = 3
MOB_FROG     = 4
MOB_SEAGULL  = 5
MOB_SPIDER   = 6   # agressif, chasse sur les murs
MOB_SKELETON = 7   # agressif, garde la distance
MOB_BAT      = 8   # passif le jour, agressif la nuit
MOB_CRAB     = 9   # agressif, plage
MOB_DEMON    = 10  # boss léger, immunisé épées inférieures à Or
MOB_BOAR     = 11  # sanglier : neutre si joueur porte de l'or
MOB_TROLL    = 12  # troll des cavernes (surf+20..+45), lent, robuste
MOB_WORM     = 13  # ver fouisseur   (surf+45..+65), traverse le terrain
MOB_WRAITH   = 14  # spectre abyssal (surf+65+),     volant, très puissant
MOB_TENDRIL  = 15  # boss végétal    (surf+70+), stationnaire, très rare
MOB_PENGUIN    = 16  # pingouin (passif, biome glace)
MOB_POLAR_BEAR = 17  # ours polaire (agressif, biome glace)
MOB_SCORPION   = 18  # scorpion (agressif, biome désert)
MOB_VULTURE    = 19  # vautour (semi-agressif, biome désert, volant)
MOB_WOLF       = 20  # loup (neutre, forêt, apprivoisable → familier combat)
MOB_CAT        = 21  # chat sauvage (passif, apprivoisable → familier déco)
MOB_GORGON     = 22  # La Gorgone – boss végétal, détection sonore, langue perceuse (surf+75+)

_PASSIVE_MOBS       = {MOB_CHICKEN, MOB_FROG, MOB_SEAGULL, MOB_BAT, MOB_PENGUIN, MOB_CAT}
_FLYING_MOBS        = {MOB_SEAGULL, MOB_BAT, MOB_DEMON, MOB_VULTURE}
_GOLD_NEUTRAL_MOBS  = {MOB_BOAR}   # n'attaquent pas un joueur portant de l'or
_DEEP_MOBS          = {MOB_TROLL, MOB_WORM, MOB_WRAITH, MOB_TENDRIL, MOB_GORGON}  # gèrent leur propre déplacement
_TAMEABLE_MOBS      = {MOB_CHICKEN, MOB_WOLF, MOB_CAT}  # domesticables

# ── Stats ─────────────────────────────────────────────────────────────────────
_MOB_HP = {
    MOB_SLIME:    2,
    MOB_ZOMBIE:   3,
    MOB_GOLEM:    5,
    MOB_CHICKEN:  1,
    MOB_FROG:     1,
    MOB_SEAGULL:  1,
    MOB_SPIDER:   3,
    MOB_SKELETON: 4,
    MOB_BAT:      1,
    MOB_CRAB:     3,
    MOB_DEMON:    8,
    MOB_BOAR:     4,
    MOB_TROLL:    6,
    MOB_WORM:     9,
    MOB_WRAITH:   12,
    MOB_TENDRIL:  25,
    MOB_GORGON:   50,  # boss élite
    MOB_PENGUIN:    2,
    MOB_POLAR_BEAR: 8,
    MOB_SCORPION:   3,
    MOB_VULTURE:    3,
    MOB_WOLF:       4,
    MOB_CAT:        2,
}

# Dégâts de l'épée par matériau (MAT_WOOD=0, MAT_IRON=1, MAT_GOLD=2, MAT_DIAMOND=3)
_SWORD_DMG = [1, 2, 3, 5]

# Dégâts de contact par mob (réduits par l'armure du joueur)
# full Fer (def=3) bloque les mobs dmg=1 ; Golem/Demon percent l'armure légère
_MOB_ATTACK_DMG = {
    MOB_SLIME:    1, MOB_ZOMBIE:   1, MOB_GOLEM:    4,
    MOB_CHICKEN:  0, MOB_FROG:     0, MOB_SEAGULL:  0,
    MOB_SPIDER:   1, MOB_SKELETON: 1, MOB_BAT:      1,
    MOB_CRAB:     1, MOB_DEMON:    6, MOB_BOAR:     1,
    MOB_TROLL:    2, MOB_WORM:     3, MOB_WRAITH:   4,
    MOB_TENDRIL:  3,
    MOB_GORGON:   6,  # langue qui déchire
    MOB_PENGUIN:  0, MOB_POLAR_BEAR: 3, MOB_SCORPION: 2, MOB_VULTURE: 1,
    MOB_WOLF:     1, MOB_CAT: 0,
}

# Tier d'épée minimum pour infliger des dégâts
# 0=main ok, 1=Bois, 2=Fer, 3=Or, 4=Diamant
_MOB_MIN_SWORD_TIER = {
    MOB_SLIME:    0,
    MOB_ZOMBIE:   1,
    MOB_GOLEM:    2,
    MOB_CHICKEN:  0,
    MOB_FROG:     0,
    MOB_SEAGULL:  0,
    MOB_SPIDER:   1,
    MOB_SKELETON: 1,
    MOB_BAT:      0,
    MOB_CRAB:     1,
    MOB_DEMON:    3,
    MOB_BOAR:     1,
    MOB_TROLL:    1,   # épée Bois min
    MOB_WORM:     2,   # épée Fer min
    MOB_WRAITH:   3,   # épée Or min
    MOB_TENDRIL:  3,   # épée Or min, immunisé projectiles
    MOB_GORGON:   3,   # épée Or min (boss profond)
    MOB_PENGUIN:    0,
    MOB_POLAR_BEAR: 2,   # épée Fer min
    MOB_SCORPION:   1,   # épée Bois min
    MOB_VULTURE:    0,
    MOB_WOLF:       0,
    MOB_CAT:        0,
}

# ── Résistances environnementales ────────────────────────────────────────────
# 0.0 = plein dégâts, 1.0 = immunisé
_LAVA_DPS  = 3.0   # dégâts base lave par seconde
_WATER_DPS = 1.0   # dégâts base eau (noyade) par seconde

_MOB_LAVA_RESIST = {
    MOB_DEMON:    1.0,   # créature de feu
    MOB_WRAITH:   1.0,   # spectral
    MOB_GORGON:   1.0,   # boss — immunisé lave/eau (combat uniquement)
    MOB_TENDRIL:  0.8,   # boss végétal, très résistant
    MOB_GOLEM:    0.7,   # pierre
    MOB_WORM:     0.5,   # souterrain
    MOB_TROLL:    0.5,   # robuste
    MOB_SCORPION: 0.3,   # désert, résistant chaleur
    MOB_SLIME:    0.3,   # gélatineux
}

_MOB_WATER_RESIST = {
    MOB_FROG:       1.0,   # amphibien
    MOB_CRAB:       1.0,   # aquatique
    MOB_PENGUIN:    1.0,   # nageur
    MOB_SEAGULL:    1.0,   # oiseau marin
    MOB_POLAR_BEAR: 1.0,   # nageur
    MOB_GORGON:     1.0,   # boss — immunisé lave/eau
    MOB_SLIME:      0.8,   # gélatineux, flotte
    MOB_WOLF:       0.7,   # sait nager
    MOB_CHICKEN:    0.5,   # flotte un peu
    MOB_BOAR:       0.5,   # traverse les cours d'eau
    MOB_CAT:        0.3,   # survit mais n'aime pas
}

# ── Dimensions pixels ─────────────────────────────────────────────────────────
_MOB_PW = {
    MOB_SLIME:    12, MOB_ZOMBIE:   8,  MOB_GOLEM:   14,
    MOB_CHICKEN:  8,  MOB_FROG:     8,  MOB_SEAGULL: 10,
    MOB_SPIDER:   12, MOB_SKELETON: 8,  MOB_BAT:     10,
    MOB_CRAB:     12, MOB_DEMON:    14, MOB_BOAR:    12,
    MOB_TROLL:    14, MOB_WORM:     16, MOB_WRAITH:  12,
    MOB_TENDRIL:  14,
    MOB_GORGON:   32,  # hitbox tête du serpent (corps visuel beaucoup plus grand)
    MOB_PENGUIN:  8,  MOB_POLAR_BEAR: 16, MOB_SCORPION: 12, MOB_VULTURE: 10,
    MOB_WOLF:    12,  MOB_CAT: 8,
}
_MOB_PH = {
    MOB_SLIME:    10, MOB_ZOMBIE:   16, MOB_GOLEM:   18,
    MOB_CHICKEN:  8,  MOB_FROG:     7,  MOB_SEAGULL: 6,
    MOB_SPIDER:   10, MOB_SKELETON: 16, MOB_BAT:     6,
    MOB_CRAB:     8,  MOB_DEMON:    18, MOB_BOAR:    10,
    MOB_TROLL:    18, MOB_WORM:     8,  MOB_WRAITH:  14,
    MOB_TENDRIL:  20,
    MOB_GORGON:   24,  # hitbox tête uniquement (le corps visuel descend sur 20 tuiles)
    MOB_PENGUIN:  10, MOB_POLAR_BEAR: 14, MOB_SCORPION: 8, MOB_VULTURE: 6,
    MOB_WOLF:    10,  MOB_CAT: 6,
}

def _mw(t): return _MOB_PW[t] / TILE_SIZE
def _mh(t): return _MOB_PH[t] / TILE_SIZE

# ── Couleurs de rendu ─────────────────────────────────────────────────────────
_MOB_COLOR = {
    MOB_SLIME:    ( 70, 200,  70),
    MOB_ZOMBIE:   (100, 150,  80),
    MOB_GOLEM:    (160, 140, 120),
    MOB_CHICKEN:  (240, 240, 235),
    MOB_FROG:     ( 55, 175,  55),
    MOB_SEAGULL:  (235, 235, 235),
    MOB_SPIDER:   ( 40,  30,  40),
    MOB_SKELETON: (220, 215, 200),
    MOB_BAT:      ( 60,  40,  70),
    MOB_CRAB:     (200,  80,  50),
    MOB_DEMON:    (180,  30,  30),
    MOB_BOAR:     (120,  70,  40),
    MOB_TROLL:    ( 60,  90,  50),
    MOB_WORM:     (100,  60,  30),
    MOB_WRAITH:   (160, 180, 255),
    MOB_TENDRIL:  ( 20,  90,  15),  # vert profond végétal
    MOB_PENGUIN:    ( 20,  20,  30),  # noir (ventre blanc dessiné)
    MOB_POLAR_BEAR: (240, 240, 245),  # blanc polaire
    MOB_SCORPION:   (140, 100,  40),  # brun sable
    MOB_VULTURE:    ( 60,  45,  35),  # brun foncé
    MOB_WOLF:       (140, 135, 125),  # gris loup
    MOB_CAT:        (210, 155,  60),  # orange tabby
    MOB_GORGON:     ( 10,  60,   5),  # vert sombre abysse
}

# ── Rayon de spawn / despawn ──────────────────────────────────────────────────
_SPAWN_RANGE   = 35   # tuiles — doit rester < _DESPAWN_RANGE
_DESPAWN_RANGE = 40   # tuiles


# ── Classe Mob ────────────────────────────────────────────────────────────────

class Mob:
    """Un mob. x, y = position tile du coin haut-gauche (float)."""

    def __init__(self, col, row, mob_type, seed=0):
        self.x         = float(col)
        self.y         = float(row)
        self.vx        = 0.0
        self.vy        = 0.0
        self.mob_type  = mob_type
        self.on_ground = False
        self.state     = "idle"    # "idle" | "chase"
        self._state_cd   = 0.0
        self._jump_cd    = 0.0
        self._wander_cd  = 0.0
        self._wander_dir = 1
        self._push_cd    = 0.0
        self._fly_phase  = 0.0    # oscillation verticale mouette
        self.hp          = _MOB_HP[mob_type]
        self.vanish      = False   # True → supprimé au prochain tick
        self.burning     = False   # True → brûle (zombie à l'aube)
        self.burn_timer  = 0.0     # secondes avant mort par brûlure
        self._surface_zombie = False   # zombie spawné en surface la nuit
        self._tendril_cd = 0.0    # cooldown attaque Vrille / Gorgone
        self._anchor_x   = None   # Gorgone : centre-col d'ancrage (tiles, None = non init)
        self._anchor_row = None   # Gorgone : rangée du sol d'ancrage (tiles)
        self._poison_t   = 0.0    # durée restante du poison (secondes)
        self._poison_cd  = 0.0    # cooldown entre deux ticks de poison
        self._max_hp       = self.hp
        self._hp_bar_timer = 0.0  # timer affichage barre de vie (2s après dégâts)
        self._env_dmg      = 0.0  # accumulateur dégâts environnementaux fractionnaires
        self._rng = random.Random(int(col) * 1000 + int(row) + mob_type + seed)

    # ── Helpers géométriques ──────────────────────────────────────────────────

    def center_col(self):
        return self.x + _mw(self.mob_type) / 2

    def center_row(self):
        return self.y + _mh(self.mob_type) / 2

    def px(self):
        """Position pixels coin gauche."""
        return self.x * TILE_SIZE

    def py(self):
        """Position pixels coin haut."""
        return self.y * TILE_SIZE
