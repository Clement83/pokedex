"""
Gestionnaire de mobs : spawn, update et dessin.
"""
import math
from world import _hash1
from config import TILE_SIZE, PLAYER_W, PLAYER_H, TILE_AIR, ROWS

from mobs.base import (
    Mob, MOB_SLIME, MOB_ZOMBIE, MOB_GOLEM,
    MOB_CHICKEN, MOB_FROG, MOB_SEAGULL,
    _mw, _mh, _SPAWN_RANGE, _DESPAWN_RANGE,
)
from mobs.physics import _eject_mob
from mobs.ai import update_mob
from mobs.renderer import draw_mob


class MobManager:
    def __init__(self, world):
        self._world   = world
        self._seed    = world.seed
        self._mobs    = []
        self._spawned = set()   # (col, mob_type) déjà tentés

    # ── Spawn déterministe ────────────────────────────────────────────────────

    def spawn_around(self, centers, is_night=False):
        """Scanne les colonnes proches et génère les mobs."""
        if isinstance(centers, int):
            centers = [centers]
        world = self._world
        seed  = self._seed

        for center_col in centers:
            for col in range(center_col - _SPAWN_RANGE, center_col + _SPAWN_RANGE):
                surf = world.surface_at(col)
                self._try_spawn_golem(col, surf, world, seed)
                self._try_spawn_slime(col, surf, world, seed)
                self._try_spawn_zombie(col, surf, world, seed)
                if not is_night:
                    self._try_spawn_chicken(col, surf, world, seed)
                    self._try_spawn_frog(col, surf, world, seed)
                    self._try_spawn_seagull(col, surf, world, seed)

        self._mobs = [
            m for m in self._mobs
            if any(abs(m.center_col() - c) <= _DESPAWN_RANGE for c in centers)
        ]
        self._spawned = {
            k for k in self._spawned
            if any(abs(k[0] - c) <= _DESPAWN_RANGE for c in centers)
        }

    # ── Spawns individuels ────────────────────────────────────────────────────

    def _try_spawn_golem(self, col, surf, world, seed):
        key = (col, MOB_GOLEM)
        if key in self._spawned:
            return
        self._spawned.add(key)
        origin = world._cabin_origin(col)
        if origin is None or col != origin:
            return
        if _hash1(col * 53 + 7, seed ^ 0xBABE) >= 0.50:
            return
        sc  = origin - 1
        sr  = world.surface_at(sc)
        mh  = _mh(MOB_GOLEM)
        top = sr - math.ceil(mh)
        if all(world.get(sc, top + k) == TILE_AIR for k in range(math.ceil(mh))):
            m = Mob(sc, top, MOB_GOLEM, seed)
            _eject_mob(m, world)
            self._mobs.append(m)

    def _try_spawn_slime(self, col, surf, world, seed):
        key = (col, MOB_SLIME)
        if key in self._spawned:
            return
        self._spawned.add(key)
        if _hash1(col * 97 + 13, seed ^ 0xC1C2) >= 0.08:
            return
        for row in range(surf + 5, min(surf + 40, ROWS - 2)):
            if world.get(col, row) == TILE_AIR and world.get(col, row + 1) != TILE_AIR:
                top = row - math.ceil(_mh(MOB_SLIME)) + 1
                m   = Mob(col, top, MOB_SLIME, seed)
                _eject_mob(m, world)
                self._mobs.append(m)
                break

    def _try_spawn_zombie(self, col, surf, world, seed):
        key = (col, MOB_ZOMBIE)
        if key in self._spawned:
            return
        self._spawned.add(key)
        if _hash1(col * 131 + 29, seed ^ 0xDEAD) >= 0.06:
            return
        deep_min = surf + 18
        for row in range(deep_min, min(deep_min + 30, ROWS - 2)):
            if world.get(col, row) == TILE_AIR and world.get(col, row + 1) != TILE_AIR:
                top = row - math.ceil(_mh(MOB_ZOMBIE)) + 1
                m   = Mob(col, top, MOB_ZOMBIE, seed)
                _eject_mob(m, world)
                self._mobs.append(m)
                break

    def _try_spawn_chicken(self, col, surf, world, seed):
        key = (col, MOB_CHICKEN)
        if key in self._spawned:
            return
        self._spawned.add(key)
        if _hash1(col * 73 + 11, seed ^ 0xC0DE) >= 0.035:
            return
        top = surf - math.ceil(_mh(MOB_CHICKEN))
        if all(world.get(col, top + k) == TILE_AIR for k in range(math.ceil(_mh(MOB_CHICKEN)))):
            m = Mob(col, top, MOB_CHICKEN, seed)
            _eject_mob(m, world)
            self._mobs.append(m)

    def _try_spawn_frog(self, col, surf, world, seed):
        key = (col, MOB_FROG)
        if key in self._spawned:
            return
        self._spawned.add(key)
        if _hash1(col * 89 + 17, seed ^ 0xF09B) >= 0.025:
            return
        top = surf - math.ceil(_mh(MOB_FROG))
        if all(world.get(col, top + k) == TILE_AIR for k in range(math.ceil(_mh(MOB_FROG)))):
            m = Mob(col, top, MOB_FROG, seed)
            _eject_mob(m, world)
            self._mobs.append(m)

    def _try_spawn_seagull(self, col, surf, world, seed):
        key = (col, MOB_SEAGULL)
        if key in self._spawned:
            return
        self._spawned.add(key)
        if _hash1(col * 61 + 23, seed ^ 0xBEEF) >= 0.018:
            return
        fly_row = surf - 7
        if fly_row >= 1:
            m = Mob(col, float(fly_row), MOB_SEAGULL, seed)
            m._wander_dir = 1 if m._rng.random() > 0.5 else -1
            self._mobs.append(m)

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
            update_mob(mob, dt, players, world)

    # ── Attaque épée ──────────────────────────────────────────────────────────

    def attack_near(self, px, py, reach, damage):
        """Inflige damage PV aux mobs dans reach tiles. Retourne nb tués."""
        pw = PLAYER_W / TILE_SIZE
        ph = PLAYER_H / TILE_SIZE
        cx = px + pw / 2
        cy = py + ph / 2
        dead = [m for m in self._mobs
                if (m.center_col() - cx) ** 2 + (m.center_row() - cy) ** 2 <= reach ** 2
                and not setattr(m, 'hp', m.hp - damage)]
        # setattr trickery: on décrémente hp en filtrant
        # Réécriture propre :
        dead = []
        for m in self._mobs:
            dx = m.center_col() - cx
            dy = m.center_row() - cy
            if dx * dx + dy * dy <= reach * reach:
                m.hp -= damage
                if m.hp <= 0:
                    dead.append(m)
        for m in dead:
            self._mobs.remove(m)
        return len(dead)

    # ── Rendu ─────────────────────────────────────────────────────────────────

    def draw(self, screen, camera):
        for mob in self._mobs:
            draw_mob(screen, mob, camera)
