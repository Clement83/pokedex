"""
Gestion des mobs pour Minecraft 2D.

Mobs agressifs :
  MOB_SLIME  (0) – souterrain, se réveille si joueur à ≤5 tiles, saut vers lui
  MOB_ZOMBIE (1) – profond (>18 tiles sous surface), errance, poursuite LOS ≤8
  MOB_GOLEM  (2) – surface près des cabanes, alerte si joueur casse un bloc cabane

Mobs passifs (jour uniquement) :
  MOB_CHICKEN (3) – surface, erre et fuit le joueur à <4 tiles
  MOB_FROG    (4) – surface, sauts périodiques, fuit le joueur
  MOB_SEAGULL (5) – en vol, oscille doucement
"""
import math
import random
import pygame

from config import (TILE_SIZE, ROWS, GRAVITY, MAX_FALL_SPEED, JUMP_VEL,
                    PLAYER_W, PLAYER_H, TILE_AIR)
from world import _hash1

# ── Constantes ────────────────────────────────────────────────────────────────
MOB_SLIME   = 0
MOB_ZOMBIE  = 1
MOB_GOLEM   = 2
MOB_CHICKEN = 3
MOB_FROG    = 4
MOB_SEAGULL = 5

_PASSIVE_MOBS = {MOB_CHICKEN, MOB_FROG, MOB_SEAGULL}

# Points de vie par type de mob
_MOB_HP = {
    MOB_SLIME:   2,
    MOB_ZOMBIE:  3,
    MOB_GOLEM:   5,
    MOB_CHICKEN: 1,
    MOB_FROG:    1,
    MOB_SEAGULL: 1,
}

# Dégâts de l'épée par matériau (indices MAT_WOOD=0, MAT_IRON=1, MAT_GOLD=2)
_SWORD_DMG = [1, 2, 3]

# Dimensions pixels
_MOB_PW = {MOB_SLIME: 12, MOB_ZOMBIE: 8,  MOB_GOLEM: 14,
           MOB_CHICKEN: 8, MOB_FROG: 8,   MOB_SEAGULL: 10}
_MOB_PH = {MOB_SLIME: 10, MOB_ZOMBIE: 16, MOB_GOLEM: 18,
           MOB_CHICKEN: 8, MOB_FROG: 7,   MOB_SEAGULL: 6}

# Dimensions tiles (float)
def _mw(t): return _MOB_PW[t] / TILE_SIZE
def _mh(t): return _MOB_PH[t] / TILE_SIZE

# Couleurs de base
_MOB_COLOR = {
    MOB_SLIME:   ( 70, 200,  70),
    MOB_ZOMBIE:  (100, 150,  80),
    MOB_GOLEM:   (160, 140, 120),
    MOB_CHICKEN: (240, 240, 235),
    MOB_FROG:    ( 55, 175,  55),
    MOB_SEAGULL: (235, 235, 235),
}

_SPAWN_RANGE  = 55   # colonnes de chaque côté à scanner
_DESPAWN_RANGE = 70  # au-delà → suppression + réinitialisation spawn


# ── Physique mobs ─────────────────────────────────────────────────────────────

def _solid(world, col, row):
    if row < 0 or row >= ROWS:
        return True
    return world.get(col, row) != TILE_AIR


def _mob_cols(mob):
    return list(range(int(mob.x), int(mob.x + _mw(mob.mob_type) - 0.01) + 1))


def _mob_rows(mob):
    return list(range(int(mob.y), int(mob.y + _mh(mob.mob_type) - 0.01) + 1))


def _move_mob_x(mob, world, dx):
    mob.x += dx
    mw    = _mw(mob.mob_type)
    left  = int(mob.x)
    right = int(mob.x + mw - 0.01)
    rows  = _mob_rows(mob)
    if dx > 0:
        for r in rows:
            if _solid(world, right, r):
                mob.x  = right - mw
                mob.vx = 0.0
                break
    elif dx < 0:
        for r in rows:
            if _solid(world, left, r):
                mob.x  = left + 1.0
                mob.vx = 0.0
                break


def _move_mob_y(mob, world, dy):
    mob.y += dy
    mh     = _mh(mob.mob_type)
    top    = int(mob.y)
    bottom = int(mob.y + mh - 0.01)
    cols   = _mob_cols(mob)
    if dy > 0:
        mob.on_ground = False
        for c in cols:
            if _solid(world, c, bottom):
                mob.y         = bottom - mh
                mob.vy        = 0.0
                mob.on_ground = True
                break
    elif dy < 0:
        for c in cols:
            if _solid(world, c, top):
                mob.y  = top + 1.0
                mob.vy = 0.0
                break


def _eject_mob(mob, world):
    """Éjecte un mob hors de tout bloc solide (appelé au spawn)."""
    mh = _mh(mob.mob_type)
    mw = _mw(mob.mob_type)
    for _ in range(ROWS):
        top    = int(mob.y)
        bottom = int(mob.y + mh - 0.01)
        cols   = list(range(int(mob.x), int(mob.x + mw - 0.01) + 1))
        if not any(_solid(world, c, r)
                   for r in range(top, bottom + 1) for c in cols):
            break
        mob.y -= 1.0
    mob.vy = min(mob.vy, 0.0)


# ── Classe Mob ────────────────────────────────────────────────────────────────

class Mob:
    """
    Représente un seul mob.
    x, y  : position tile du coin haut-gauche de la hitbox (float).
    """
    def __init__(self, col, row, mob_type, seed=0):
        self.x         = float(col)
        self.y         = float(row)
        self.vx        = 0.0
        self.vy        = 0.0
        self.mob_type  = mob_type
        self.on_ground = False
        self.state     = "idle"    # "idle" | "chase"
        self._state_cd = 0.0
        self._jump_cd  = 0.0
        self._wander_cd  = 0.0
        self._wander_dir = 1
        self._push_cd    = 0.0
        self._fly_phase  = 0.0   # oscillation verticale mouette
        self.hp          = _MOB_HP[mob_type]   # points de vie
        # RNG déterministe par position de spawn
        self._rng = random.Random(int(col) * 1000 + int(row) + mob_type + seed)

    # ── Helpers géométriques ──────────────────────────────────────────────────

    def center_col(self):
        return self.x + _mw(self.mob_type) / 2

    def center_row(self):
        return self.y + _mh(self.mob_type) / 2

    def px(self):
        """Position pixels (gauche)."""
        return self.x * TILE_SIZE

    def py(self):
        """Position pixels (haut)."""
        return self.y * TILE_SIZE


# ── Manager ───────────────────────────────────────────────────────────────────

class MobManager:
    def __init__(self, world):
        self._world   = world
        self._seed    = world.seed
        self._mobs    = []
        self._spawned = set()   # (col, mob_type) déjà tenté

    # ── Spawn déterministe ────────────────────────────────────────────────────

    def spawn_around(self, center_col, is_night=False):
        """
        Scanne les colonnes autour de center_col et génère les mobs.
        Mobs passifs uniquement le jour (is_night=False).
        """
        world = self._world
        seed  = self._seed

        for col in range(center_col - _SPAWN_RANGE,
                         center_col + _SPAWN_RANGE):
            surf = world.surface_at(col)

            # ── Golem : surface à gauche d'une cabane ────────────────────────
            key_g = (col, MOB_GOLEM)
            if key_g not in self._spawned:
                self._spawned.add(key_g)
                origin = world._cabin_origin(col)
                # Un seul Golem par cabane, calculé depuis la colonne d'origine
                if origin is not None and col == origin:
                    if _hash1(col * 53 + 7, seed ^ 0xBABE) < 0.50:
                        sc  = origin - 1          # juste à gauche du mur
                        sr  = world.surface_at(sc)
                        mh_g = _mh(MOB_GOLEM)
                        top_row = sr - math.ceil(mh_g)
                        # Vérifier que l'espace est suffisamment libre
                        free = all(world.get(sc, top_row + k) == TILE_AIR
                                   for k in range(math.ceil(mh_g)))
                        if free:
                            m = Mob(sc, top_row, MOB_GOLEM, seed)
                            _eject_mob(m, world)
                            self._mobs.append(m)

            # ── Slime : cave entre +5 et +40 sous la surface ─────────────────
            key_s = (col, MOB_SLIME)
            if key_s not in self._spawned:
                self._spawned.add(key_s)
                if _hash1(col * 97 + 13, seed ^ 0xC1C2) < 0.08:
                    for row in range(surf + 5, min(surf + 40, ROWS - 2)):
                        if world.get(col, row) == TILE_AIR:
                            if world.get(col, row + 1) != TILE_AIR:
                                mh_s   = _mh(MOB_SLIME)
                                top_row = row - math.ceil(mh_s) + 1
                                m = Mob(col, top_row, MOB_SLIME, seed)
                                _eject_mob(m, world)
                                self._mobs.append(m)
                                break

            # ── Zombie : profond (>18 tiles sous surface) ─────────────────────
            key_z = (col, MOB_ZOMBIE)
            if key_z not in self._spawned:
                self._spawned.add(key_z)
                if _hash1(col * 131 + 29, seed ^ 0xDEAD) < 0.06:
                    deep_min = surf + 18
                    for row in range(deep_min, min(deep_min + 30, ROWS - 2)):
                        if world.get(col, row) == TILE_AIR:
                            if world.get(col, row + 1) != TILE_AIR:
                                mh_z   = _mh(MOB_ZOMBIE)
                                top_row = row - math.ceil(mh_z) + 1
                                m = Mob(col, top_row, MOB_ZOMBIE, seed)
                                _eject_mob(m, world)
                                self._mobs.append(m)
                                break

            # ── Poule : surface, uniquement le jour ───────────────────────────
            key_ch = (col, MOB_CHICKEN)
            if key_ch not in self._spawned and not is_night:
                self._spawned.add(key_ch)
                if _hash1(col * 73 + 11, seed ^ 0xC0DE) < 0.08:
                    sr      = world.surface_at(col)
                    mh_c    = _mh(MOB_CHICKEN)
                    top_row = sr - math.ceil(mh_c)
                    free = all(world.get(col, top_row + k) == TILE_AIR
                               for k in range(math.ceil(mh_c)))
                    if free:
                        m = Mob(col, top_row, MOB_CHICKEN, seed)
                        _eject_mob(m, world)
                        self._mobs.append(m)

            # ── Grenouille : surface, uniquement le jour ──────────────────────
            key_fr = (col, MOB_FROG)
            if key_fr not in self._spawned and not is_night:
                self._spawned.add(key_fr)
                if _hash1(col * 89 + 17, seed ^ 0xF09B) < 0.06:
                    sr      = world.surface_at(col)
                    mh_f    = _mh(MOB_FROG)
                    top_row = sr - math.ceil(mh_f)
                    free = all(world.get(col, top_row + k) == TILE_AIR
                               for k in range(math.ceil(mh_f)))
                    if free:
                        m = Mob(col, top_row, MOB_FROG, seed)
                        _eject_mob(m, world)
                        self._mobs.append(m)

            # ── Mouette : en vol, uniquement le jour ──────────────────────────
            key_sg = (col, MOB_SEAGULL)
            if key_sg not in self._spawned and not is_night:
                self._spawned.add(key_sg)
                if _hash1(col * 61 + 23, seed ^ 0xBEEF) < 0.04:
                    sr      = world.surface_at(col)
                    fly_row = sr - 7
                    if fly_row >= 1:
                        m = Mob(col, float(fly_row), MOB_SEAGULL, seed)
                        m._wander_dir = 1 if m._rng.random() > 0.5 else -1
                        self._mobs.append(m)   # pas d'éjection, vole librement
        self._mobs = [
            m for m in self._mobs
            if abs(m.center_col() - center_col) <= _DESPAWN_RANGE
        ]
        # Libérer les clés hors portée (permettra de respawn si le joueur revient)
        self._spawned = {
            k for k in self._spawned
            if abs(k[0] - center_col) <= _DESPAWN_RANGE
        }

    # ── Alerte Golem ──────────────────────────────────────────────────────────

    def trigger_cabin_break(self, col):
        """Active la poursuite de tous les Golems proches d'une cabane brisée."""
        for m in self._mobs:
            if m.mob_type == MOB_GOLEM and abs(m.center_col() - col) < 15:
                m.state     = "chase"
                m._state_cd = 10.0

    # ── Mise à jour ───────────────────────────────────────────────────────────

    def update(self, dt, players, world):
        for mob in self._mobs:
            _update_mob(mob, dt, players, world)

    # ── Attaque épée ──────────────────────────────────────────────────────────

    def attack_near(self, px, py, reach, damage):
        """
        Inflige `damage` PV à tous les mobs dans `reach` tiles du centre joueur.
        Supprime les mobs à 0 PV. Retourne le nombre de mobs tués.
        """
        pw   = PLAYER_W / TILE_SIZE
        ph   = PLAYER_H / TILE_SIZE
        cx   = px + pw / 2
        cy   = py + ph / 2
        dead = []
        for mob in self._mobs:
            dx = mob.center_col() - cx
            dy = mob.center_row() - cy
            if dx * dx + dy * dy <= reach * reach:
                mob.hp -= damage
                if mob.hp <= 0:
                    dead.append(mob)
        for m in dead:
            self._mobs.remove(m)
        return len(dead)

    # ── Rendu ─────────────────────────────────────────────────────────────────

    def draw(self, screen, camera):
        for mob in self._mobs:
            _draw_mob(screen, mob, camera)


# ── Logique de mise à jour d'un mob ──────────────────────────────────────────

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
    """Ligne de vue (Bresenham approximé, ignore tuiles transparentes)."""
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


def _update_mob(mob, dt, players, world):
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
                mob.vx     = 2.5 * dir_to
                mob.vy     = JUMP_VEL * 0.65
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
            # Saut si un bloc bloque le passage
            if mob.on_ground and mob._jump_cd <= 0:
                next_col = int(mob.x + dir_to * (_mw(MOB_ZOMBIE) + 0.1))
                if _solid(world, next_col, int(cy)):
                    mob.vy       = JUMP_VEL
                    mob._jump_cd = 0.5
        else:
            # Errance aléatoire
            mob._wander_cd -= dt
            if mob._wander_cd <= 0:
                mob._wander_dir = 1 if mob._rng.random() > 0.5 else -1
                mob._wander_cd  = 1.5 + mob._rng.random() * 2.0
            mob.vx = 1.5 * mob._wander_dir
            # Demi-tour au mur
            check_col = int(mob.x + mob._wander_dir * (_mw(MOB_ZOMBIE) + 0.1))
            if _solid(world, check_col, int(cy)):
                mob._wander_dir *= -1
                mob._wander_cd   = 0.0

    # ── Golem ─────────────────────────────────────────────────────────────────
    elif mob.mob_type == MOB_GOLEM:
        # Défensif : attaque uniquement si le joueur s'approche trop près
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
            mob.vx *= 0.8   # friction → décélération

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

    # ── Mouette : vol libre, gestion séparée (pas de gravité) ─────────────────
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
                p.vy         = -4.0
                mob._push_cd = 0.5


# ── Rendu d'un mob ────────────────────────────────────────────────────────────

def _draw_mob(screen, mob, camera):
    sx, sy = camera.world_to_screen(mob.px(), mob.py())
    mw = _MOB_PW[mob.mob_type]
    mh = _MOB_PH[mob.mob_type]
    c  = _MOB_COLOR[mob.mob_type]
    dc = tuple(max(0, v - 50) for v in c)

    if mob.mob_type == MOB_SLIME:
        # Corps vert semi-transparent + yeux noirs
        pygame.draw.rect(screen, c,  (sx,     sy,     mw, mh))
        pygame.draw.rect(screen, dc, (sx,     sy,     mw, mh), 1)
        pygame.draw.rect(screen, (0,   0,   0), (sx + 2, sy + 3, 2, 2))
        pygame.draw.rect(screen, (0,   0,   0), (sx + 8, sy + 3, 2, 2))
        pygame.draw.rect(screen, (200, 255, 200), (sx + 1, sy + 1, 3, 1))

    elif mob.mob_type == MOB_ZOMBIE:
        # Silhouette humanoïde verdâtre
        pygame.draw.rect(screen, c,  (sx, sy, mw, mh))
        pygame.draw.rect(screen, dc, (sx, sy, mw, mh), 1)
        pygame.draw.rect(screen, (220,  50,  50), (sx + 1, sy + 3, 2, 2))
        pygame.draw.rect(screen, (220,  50,  50), (sx + 5, sy + 3, 2, 2))
        pygame.draw.rect(screen, dc,              (sx + 2, sy + 8, 4, 1))

    elif mob.mob_type == MOB_GOLEM:
        # Corps trapu gris-brun + yeux oranges
        pygame.draw.rect(screen, c,  (sx, sy, mw, mh))
        pygame.draw.rect(screen, dc, (sx, sy, mw, mh), 2)
        pygame.draw.rect(screen, (220, 140, 40), (sx + 2,  sy + 4, 3, 3))
        pygame.draw.rect(screen, (220, 140, 40), (sx + 9,  sy + 4, 3, 3))
        pygame.draw.line(screen, dc, (sx + 5, sy + 9),  (sx + 7, sy + 14), 1)
        pygame.draw.line(screen, dc, (sx + 9, sy + 7),  (sx + 8, sy + 12), 1)

    elif mob.mob_type == MOB_CHICKEN:
        # ── Poule pixel-art 8×8 ──────────────────────────────────────────────
        dr = pygame.draw.rect
        dr(screen, (240, 240, 235), (sx,     sy + 2, 7, 5))   # corps
        dr(screen, (190, 190, 185), (sx + 1, sy + 3, 5, 2))   # aile grise
        dr(screen, (240, 240, 235), (sx,     sy,     2, 3))    # queue
        dr(screen, (240, 240, 235), (sx + 4, sy + 1, 3, 3))   # tête
        dr(screen, (215,  50,  50), (sx + 4, sy,     2, 1))   # crête rouge
        dr(screen, (225, 140,  35), (sx + 7, sy + 2, 1, 1))   # bec orange
        dr(screen, (  0,   0,   0), (sx + 5, sy + 2, 1, 1))   # œil
        dr(screen, (225, 140,  35), (sx + 2, sy + 7, 1, 2))   # patte g
        dr(screen, (225, 140,  35), (sx + 5, sy + 7, 1, 2))   # patte d

    elif mob.mob_type == MOB_FROG:
        # ── Grenouille pixel-art 8×7 ─────────────────────────────────────────
        dr = pygame.draw.rect
        dr(screen, ( 55, 175,  55), (sx,     sy + 3, 8, 4))   # corps
        dr(screen, (190, 215,  80), (sx + 2, sy + 4, 4, 2))   # ventre clair
        dr(screen, ( 55, 175,  55), (sx + 1, sy + 1, 6, 3))   # tête
        dr(screen, ( 55, 175,  55), (sx,     sy,     2, 2))   # œil gauche
        dr(screen, ( 55, 175,  55), (sx + 6, sy,     2, 2))   # œil droit
        dr(screen, (  0,   0,   0), (sx,     sy,     1, 1))   # pupille g
        dr(screen, (  0,   0,   0), (sx + 7, sy,     1, 1))   # pupille d
        dr(screen, ( 35, 120,  35), (sx + 2, sy + 3, 4, 1))   # bouche
        dr(screen, ( 35, 120,  35), (sx,     sy + 6, 2, 1))   # patte arr g
        dr(screen, ( 35, 120,  35), (sx + 6, sy + 6, 2, 1))   # patte arr d

    elif mob.mob_type == MOB_SEAGULL:
        # ── Mouette pixel-art 10×6 – ailes battent selon fly_phase ───────────
        dr = pygame.draw.rect
        wo = -1 if math.sin(mob._fly_phase) > 0 else 1   # battement aile
        dr(screen, (240, 240, 240), (sx,     sy + 1 + wo, 4, 2))   # aile g
        dr(screen, (170, 178, 185), (sx,     sy + 1 + wo, 2, 1))   # pointe g
        dr(screen, (240, 240, 240), (sx + 6, sy + 1 + wo, 4, 2))   # aile d
        dr(screen, (170, 178, 185), (sx + 8, sy + 1 + wo, 2, 1))   # pointe d
        dr(screen, (240, 240, 240), (sx + 3, sy + 2,      4, 3))   # corps
        dr(screen, (240, 240, 240), (sx + 4, sy,          3, 3))   # tête
        dr(screen, (  0,   0,   0), (sx + 5, sy + 1,      1, 1))   # œil
        dr(screen, (225, 185,  45), (sx + 7, sy + 2,      2, 1))   # bec
