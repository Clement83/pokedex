"""
Gestionnaire de mobs : spawn, update et dessin.
"""
import math
from world import _hash1
from config import TILE_SIZE, PLAYER_W, PLAYER_H, TILE_AIR, ROWS, MAT_TIER, TILE_SAND, TILE_GRASS, TILE_DIRT

from mobs.base import (
    Mob,
    MOB_SLIME, MOB_ZOMBIE, MOB_GOLEM,
    MOB_CHICKEN, MOB_FROG, MOB_SEAGULL,
    MOB_SPIDER, MOB_SKELETON, MOB_BAT, MOB_CRAB, MOB_DEMON, MOB_BOAR,
    _mw, _mh, _SPAWN_RANGE, _DESPAWN_RANGE, _MOB_MIN_SWORD_TIER,
)
from mobs.physics import _eject_mob
from mobs.ai import update_mob
from mobs.renderer import draw_mob
from mobs.drops import roll_drops
from mobs.deep import spawn_deep_mobs


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

        _MAX_MOBS = 20   # cap global pour garder les perfs
        for center_col in centers:
            for col in range(center_col - _SPAWN_RANGE, center_col + _SPAWN_RANGE):
                if len(self._mobs) >= _MAX_MOBS:
                    break
                surf = world.surface_at(col)
                self._try_spawn_golem(col, surf, world, seed)
                self._try_spawn_slime(col, surf, world, seed)
                self._try_spawn_zombie(col, surf, world, seed)
                self._try_spawn_spider(col, surf, world, seed)
                self._try_spawn_skeleton(col, surf, world, seed)
                self._try_spawn_bat(col, surf, world, seed)
                self._try_spawn_demon(col, surf, world, seed)
                spawn_deep_mobs(self._spawned, self._mobs, col, surf, world, seed)
                if not is_night:
                    self._try_spawn_chicken(col, surf, world, seed)
                    self._try_spawn_frog(col, surf, world, seed)
                    self._try_spawn_seagull(col, surf, world, seed)
                    self._try_spawn_crab(col, surf, world, seed)
                    self._try_spawn_boar(col, surf, world, seed)

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
        sc, sr = origin - 1, world.surface_at(origin - 1)
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
        if _hash1(col * 97 + 13, seed ^ 0xC1C2) >= 0.04:   # 0.08 -> 0.04
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
        if _hash1(col * 131 + 29, seed ^ 0xDEAD) >= 0.03:  # 0.06 -> 0.03
            return
        deep_min = surf + 18
        for row in range(deep_min, min(deep_min + 30, ROWS - 2)):
            if world.get(col, row) == TILE_AIR and world.get(col, row + 1) != TILE_AIR:
                top = row - math.ceil(_mh(MOB_ZOMBIE)) + 1
                m   = Mob(col, top, MOB_ZOMBIE, seed)
                _eject_mob(m, world)
                self._mobs.append(m)
                break

    def _try_spawn_spider(self, col, surf, world, seed):
        key = (col, MOB_SPIDER)
        if key in self._spawned:
            return
        self._spawned.add(key)
        if _hash1(col * 113 + 41, seed ^ 0x5B1D) >= 0.035: # 0.07 -> 0.035
            return
        for row in range(surf + 3, min(surf + 25, ROWS - 2)):
            if world.get(col, row) == TILE_AIR and world.get(col, row + 1) != TILE_AIR:
                top = row - math.ceil(_mh(MOB_SPIDER)) + 1
                m   = Mob(col, top, MOB_SPIDER, seed)
                _eject_mob(m, world)
                self._mobs.append(m)
                break

    def _try_spawn_skeleton(self, col, surf, world, seed):
        key = (col, MOB_SKELETON)
        if key in self._spawned:
            return
        self._spawned.add(key)
        if _hash1(col * 143 + 37, seed ^ 0x5CE1) >= 0.025: # 0.05 -> 0.025
            return
        deep_min = surf + 15
        for row in range(deep_min, min(deep_min + 35, ROWS - 2)):
            if world.get(col, row) == TILE_AIR and world.get(col, row + 1) != TILE_AIR:
                top = row - math.ceil(_mh(MOB_SKELETON)) + 1
                m   = Mob(col, top, MOB_SKELETON, seed)
                _eject_mob(m, world)
                self._mobs.append(m)
                break

    def _try_spawn_bat(self, col, surf, world, seed):
        key = (col, MOB_BAT)
        if key in self._spawned:
            return
        self._spawned.add(key)
        if _hash1(col * 79 + 53, seed ^ 0xBA7) >= 0.03:    # 0.06 -> 0.03
            return
        cave_start = surf + 8
        for row in range(cave_start, min(cave_start + 50, ROWS - 2)):
            if world.get(col, row) == TILE_AIR:
                m = Mob(col, float(row), MOB_BAT, seed)
                self._mobs.append(m)
                break

    def _try_spawn_crab(self, col, surf, world, seed):
        key = (col, MOB_CRAB)
        if key in self._spawned:
            return
        self._spawned.add(key)
        if world.get(col, surf) != TILE_SAND:
            return
        if _hash1(col * 67 + 31, seed ^ 0xCBA5) >= 0.02:   # 0.04 -> 0.02
            return
        top = surf - math.ceil(_mh(MOB_CRAB))
        if all(world.get(col, top + k) == TILE_AIR for k in range(math.ceil(_mh(MOB_CRAB)))):
            m = Mob(col, top, MOB_CRAB, seed)
            _eject_mob(m, world)
            self._mobs.append(m)

    def _try_spawn_demon(self, col, surf, world, seed):
        key = (col, MOB_DEMON)
        if key in self._spawned:
            return
        self._spawned.add(key)
        if _hash1(col * 157 + 61, seed ^ 0xDE11) >= 0.006: # 0.012 -> 0.006
            return
        deep_min = surf + 55
        for row in range(deep_min, min(deep_min + 20, ROWS - 2)):
            if world.get(col, row) == TILE_AIR:
                m = Mob(col, float(row), MOB_DEMON, seed)
                self._mobs.append(m)
                break

    def _try_spawn_boar(self, col, surf, world, seed):
        key = (col, MOB_BOAR)
        if key in self._spawned:
            return
        self._spawned.add(key)
        if world.get(col, surf) not in (TILE_GRASS, TILE_DIRT):
            return
        if _hash1(col * 103 + 47, seed ^ 0xB0A1) >= 0.025: # 0.05 -> 0.025
            return
        top = surf - math.ceil(_mh(MOB_BOAR))
        if all(world.get(col, top + k) == TILE_AIR for k in range(math.ceil(_mh(MOB_BOAR)))):
            m = Mob(col, top, MOB_BOAR, seed)
            _eject_mob(m, world)
            self._mobs.append(m)

    def _try_spawn_chicken(self, col, surf, world, seed):
        key = (col, MOB_CHICKEN)
        if key in self._spawned:
            return
        self._spawned.add(key)
        if _hash1(col * 73 + 11, seed ^ 0xC0DE) >= 0.018:  # 0.035 -> 0.018
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
        if _hash1(col * 89 + 17, seed ^ 0xF09B) >= 0.012:  # 0.025 -> 0.012
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
        if _hash1(col * 61 + 23, seed ^ 0xBEEF) >= 0.009:  # 0.018 -> 0.009
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
        self._mobs = [m for m in self._mobs if not m.vanish]

    # ── Attaque épée avec tier + drops ────────────────────────────────────────

    def attack_near(self, px, py, reach, damage, sword_tier=0):
        """Inflige dégâts. Retourne (nb_tués: int, drops: list, nb_immunisés: int)."""
        pw = PLAYER_W / TILE_SIZE
        ph = PLAYER_H / TILE_SIZE
        cx = px + pw / 2
        cy = py + ph / 2

        dead      = []
        all_drops = []
        immune    = 0

        for m in self._mobs:
            dx = m.center_col() - cx
            dy = m.center_row() - cy
            if dx * dx + dy * dy > reach * reach:
                continue
            min_tier = _MOB_MIN_SWORD_TIER.get(m.mob_type, 0)
            if sword_tier < min_tier:
                immune += 1
                continue
            m.hp -= damage
            if m.hp <= 0:
                dead.append(m)
                all_drops.extend(roll_drops(m.mob_type))

        for m in dead:
            self._mobs.remove(m)

        return len(dead), all_drops, immune

    # ── Rendu ─────────────────────────────────────────────────────────────────

    def draw(self, screen, camera):
        for mob in self._mobs:
            draw_mob(screen, mob, camera)


