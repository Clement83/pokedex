"""
Types de mobs, constantes et classe Mob.

Mobs agressifs  : MOB_SLIME, MOB_ZOMBIE, MOB_GOLEM
Mobs passifs    : MOB_CHICKEN, MOB_FROG, MOB_SEAGULL
"""
import random
from config import TILE_SIZE, PLAYER_W, PLAYER_H

# ── Identifiants ──────────────────────────────────────────────────────────────
MOB_SLIME   = 0
MOB_ZOMBIE  = 1
MOB_GOLEM   = 2
MOB_CHICKEN = 3
MOB_FROG    = 4
MOB_SEAGULL = 5

_PASSIVE_MOBS = {MOB_CHICKEN, MOB_FROG, MOB_SEAGULL}

# ── Stats ─────────────────────────────────────────────────────────────────────
_MOB_HP = {
    MOB_SLIME:   2,
    MOB_ZOMBIE:  3,
    MOB_GOLEM:   5,
    MOB_CHICKEN: 1,
    MOB_FROG:    1,
    MOB_SEAGULL: 1,
}

# Dégâts de l'épée par matériau (MAT_WOOD=0, MAT_IRON=1, MAT_GOLD=2)
_SWORD_DMG = [1, 2, 3]

# ── Dimensions pixels ─────────────────────────────────────────────────────────
_MOB_PW = {
    MOB_SLIME: 12, MOB_ZOMBIE: 8,  MOB_GOLEM: 14,
    MOB_CHICKEN: 8, MOB_FROG: 8,   MOB_SEAGULL: 10,
}
_MOB_PH = {
    MOB_SLIME: 10, MOB_ZOMBIE: 16, MOB_GOLEM: 18,
    MOB_CHICKEN: 8, MOB_FROG: 7,   MOB_SEAGULL: 6,
}

def _mw(t): return _MOB_PW[t] / TILE_SIZE
def _mh(t): return _MOB_PH[t] / TILE_SIZE

# ── Couleurs de rendu ─────────────────────────────────────────────────────────
_MOB_COLOR = {
    MOB_SLIME:   ( 70, 200,  70),
    MOB_ZOMBIE:  (100, 150,  80),
    MOB_GOLEM:   (160, 140, 120),
    MOB_CHICKEN: (240, 240, 235),
    MOB_FROG:    ( 55, 175,  55),
    MOB_SEAGULL: (235, 235, 235),
}

# ── Rayon de spawn / despawn ──────────────────────────────────────────────────
_SPAWN_RANGE   = 55
_DESPAWN_RANGE = 70


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
