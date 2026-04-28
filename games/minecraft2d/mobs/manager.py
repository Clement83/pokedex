"""
Gestionnaire de mobs : spawn, update et dessin.

Améliorations vs legacy :
- _spawned = dict avec cooldown (respawn après 45 s au lieu de blocage permanent)
- Table de règles déclarative (_SPAWN_RULES) → 1 seule méthode _try_spawn
- Densité pré-calculée par bucket (O(n) au lieu de O(n × cols))
- Colonnes shufflées → plus de biais gauche→droite
"""
import math
import random
from collections import Counter
from world import _hash1
from config import (TILE_SIZE, PLAYER_W, PLAYER_H, TILE_AIR, TILE_LAVA, TILE_WATER,
                    ROWS, MAT_TIER, TILE_SAND, TILE_GRASS, TILE_DIRT,
                    BIOME_FOREST, BIOME_DESERT, BIOME_ICE)

from mobs.base import (
    Mob,
    MOB_SLIME, MOB_ZOMBIE, MOB_GOLEM,
    MOB_CHICKEN, MOB_FROG, MOB_SEAGULL,
    MOB_SPIDER, MOB_SKELETON, MOB_BAT, MOB_CRAB, MOB_DEMON, MOB_BOAR,
    MOB_TENDRIL, MOB_TROLL, MOB_WORM, MOB_WRAITH, MOB_GORGON,
    MOB_PENGUIN, MOB_POLAR_BEAR, MOB_SCORPION, MOB_VULTURE,
    MOB_WOLF, MOB_CAT,
    _mw, _mh, _SPAWN_RANGE, _DESPAWN_RANGE, _MOB_MIN_SWORD_TIER,
    _MOB_PW, _MOB_PH, _MOB_HP,
    _MOB_LAVA_RESIST, _MOB_WATER_RESIST, _LAVA_DPS, _WATER_DPS,
)
from mobs.physics import _eject_mob
from mobs.ai import update_mob
from mobs.renderer import draw_mob
from mobs.drops import roll_drops

# ── Table de règles de spawn ────────────────────────────────────────────────
# Chaque règle : (mob_type, hash_mul, hash_off, hash_xor, chance,
#   biome_require, biome_exclude, surface_tiles,
#   mode, depth_min, depth_max, fly_offset, day_only, wander_init)
#
# mode :
#   "surface"     → pose au sommet de la surface, vérifie l'espace libre
#   "underground" → scan profondeur pour air + sol solide
#   "cave_air"    → premier bloc air dans la profondeur (vol/flottant)
#   "flying"      → hauteur fixe au-dessus de la surface

_SPAWN_RULES = [
    # ── Toujours (jour et nuit) ─────────────────────────────────────────────
    # mob_type       mul  off  xor      chance  biome_req    biome_excl     surf_tiles
    # mode          d_min d_max fly  day_only wander
    (MOB_SLIME,      97,  13, 0xC1C2,  0.04,  None,        None,          None,
     "underground",   5,   40,  0,  False, False),
    (MOB_ZOMBIE,    131,  29, 0xDEAD,  0.03,  None,        None,          None,
     "underground",  18,   48,  0,  False, False),
    (MOB_SPIDER,    113,  41, 0x5B1D,  0.035, None,        BIOME_DESERT,  None,
     "underground",   3,   25,  0,  False, False),
    (MOB_SKELETON,  143,  37, 0x5CE1,  0.025, None,        None,          None,
     "underground",  15,   50,  0,  False, False),
    (MOB_BAT,        79,  53, 0xBA7,   0.03,  None,        None,          None,
     "cave_air",      8,   58,  0,  False, False),
    (MOB_DEMON,     157,  61, 0xDE11,  0.006, None,        None,          None,
     "cave_air",     55,   75,  0,  False, False),
    # deep mobs
    (MOB_TROLL,     167,  71, 0x7011,  0.06,  None,        None,          None,
     "underground",  20,   45,  0,  False, False),
    (MOB_WORM,      181,  83, 0xD0A2,  0.04,  None,        None,          None,
     "cave_air",     45,   65,  0,  False, False),
    (MOB_WRAITH,    193,  97, 0xFA17,  0.006, None,        None,          None,
     "cave_air",     65,   85,  0,  False, False),

    # ── Jour uniquement ─────────────────────────────────────────────────────
    (MOB_CHICKEN,    73,  11, 0xC0DE,  0.018, None,        None,          None,
     "surface",       0,    0,  0,  True,  False),
    (MOB_FROG,       89,  17, 0xF09B,  0.012, BIOME_FOREST, None,         None,
     "surface",       0,    0,  0,  True,  False),
    (MOB_SEAGULL,    61,  23, 0xBEEF,  0.009, None,        BIOME_ICE,     None,
     "flying",        0,    0, -7,  True,  True),
    (MOB_CRAB,       67,  31, 0xCBA5,  0.02,  None,        None,          (TILE_SAND,),
     "surface",       0,    0,  0,  True,  False),
    (MOB_BOAR,      103,  47, 0xB0A1,  0.025, None,        None,          (TILE_GRASS, TILE_DIRT),
     "surface",       0,    0,  0,  True,  False),

    # ── Biome Glace ─────────────────────────────────────────────────────────
    (MOB_PENGUIN,    71,  19, 0xB1CE,  0.025, BIOME_ICE,   None,          None,
     "surface",       0,    0,  0,  True,  False),
    (MOB_POLAR_BEAR,127,  43, 0xBEA1,  0.012, BIOME_ICE,   None,          None,
     "surface",       0,    0,  0,  True,  False),

    # ── Biome Désert ────────────────────────────────────────────────────────
    (MOB_SCORPION,  109,  37, 0x5C01,  0.025, BIOME_DESERT, None,         None,
     "surface",       0,    0,  0,  True,  False),
    (MOB_VULTURE,    83,  29, 0xAF01,  0.015, BIOME_DESERT, None,         None,
     "flying",        0,    0, -8,  True,  True),

    # ── Domesticables ──────────────────────────────────────────────────────
    (MOB_WOLF,      139,  53, 0xD06E,  0.018, BIOME_FOREST, None,         (TILE_GRASS, TILE_DIRT),
     "surface",       0,    0,  0,  True,  False),
    (MOB_CAT,       151,  61, 0xCA7E,  0.012, None,         BIOME_ICE,    None,
     "surface",       0,    0,  0,  True,  False),
]

def _apply_env_damage(mob, world, dt):
    """Applique les dégâts de lave/eau selon les résistances du mob."""
    mw = _mw(mob.mob_type)
    mh = _mh(mob.mob_type)
    in_lava = in_water = False
    for c in range(int(mob.x), int(mob.x + mw - 0.01) + 1):
        for r in range(int(mob.y), int(mob.y + mh - 0.01) + 1):
            t = world.get(c, r)
            if t == TILE_LAVA:
                in_lava = True
            elif t == TILE_WATER:
                in_water = True
    if in_lava:
        resist = _MOB_LAVA_RESIST.get(mob.mob_type, 0.0)
        if resist < 1.0:
            mob._env_dmg += _LAVA_DPS * (1.0 - resist) * dt
    if in_water:
        resist = _MOB_WATER_RESIST.get(mob.mob_type, 0.0)
        if resist < 1.0:
            mob._env_dmg += _WATER_DPS * (1.0 - resist) * dt
    if mob._env_dmg >= 1.0:
        dmg = int(mob._env_dmg)
        mob.hp -= dmg
        mob._env_dmg -= dmg
        mob._hp_bar_timer = 2.0


_RESPAWN_COOLDOWN = 45.0   # secondes avant qu'une colonne puisse re-spawner un mob
_MOB_PER_PLAYER   = 10
_ZONE_HALF        = 20     # ±20 tuiles = zone de 40 tuiles
_ZONE_MAX         =  5


class MobManager:
    def __init__(self, world):
        self._world     = world
        self._seed      = world.seed
        self._mobs      = []
        self._spawned   = {}      # (col, mob_type) → expiry_time (horloge interne)
        self._was_night = False
        self._clock     = 0.0     # timer interne pour les cooldowns de respawn
        self._poison_drops = []   # drops des mobs tués par poison (récupérés par le joueur le plus proche)

    # ── Helpers cooldown ────────────────────────────────────────────────────

    def _can_spawn(self, key):
        """True si la colonne est libre de cooldown."""
        if key not in self._spawned:
            return True
        return self._clock >= self._spawned[key]

    def _mark_spawned(self, key):
        self._spawned[key] = self._clock + _RESPAWN_COOLDOWN

    # ── Spawn principal ─────────────────────────────────────────────────────

    def spawn_around(self, centers, is_night=False):
        """Spawn avec budget/joueur, densité par bucket, colonnes shufflées."""
        if isinstance(centers, int):
            centers = [centers]
        world = self._world
        seed  = self._seed

        # Densité pré-calculée par bucket (O(n) au lieu de O(n × cols))
        density = Counter()
        for m in self._mobs:
            density[int(m.center_col()) // _ZONE_HALF] += 1

        for center_col in centers:
            local = sum(
                1 for m in self._mobs
                if abs(m.center_col() - center_col) <= _SPAWN_RANGE
            )

            # Colonnes shufflées → plus de biais gauche→droite
            cols = list(range(center_col - _SPAWN_RANGE,
                              center_col + _SPAWN_RANGE))
            random.shuffle(cols)

            for col in cols:
                if local >= _MOB_PER_PLAYER:
                    break
                bucket = int(col) // _ZONE_HALF
                if density[bucket] >= _ZONE_MAX:
                    continue

                n_before = len(self._mobs)
                surf = world.surface_at(col)

                # Golem (cas spécial : cabane)
                self._try_spawn_golem(col, surf, world, seed)

                # Tendril (cas spécial : espacement 200 cols)
                self._try_spawn_tendril(col, surf, world, seed)

                # Gorgone : spawn uniquement dans l'arène boss (plus dans le monde normal)

                # Tous les mobs génériques via la table
                for rule in _SPAWN_RULES:
                    if rule[12] and is_night:   # day_only
                        continue
                    self._try_spawn(col, surf, world, seed, rule)

                spawned_count = len(self._mobs) - n_before
                local += spawned_count
                # Mise à jour incrémentale de la densité
                for m in self._mobs[-spawned_count:] if spawned_count else ():
                    density[int(m.center_col()) // _ZONE_HALF] += 1

        # Despawn : garde le mob s'il est proche d'AU MOINS UN joueur
        self._mobs = [
            m for m in self._mobs
            if any(abs(m.center_col() - c) <= _DESPAWN_RANGE for c in centers)
        ]
        # Nettoyage des cooldowns pour les colonnes éloignées
        self._spawned = {
            k: v for k, v in self._spawned.items()
            if any(abs(k[0] - c) <= _DESPAWN_RANGE for c in centers)
        }

    # ── Spawn générique (table-driven) ──────────────────────────────────────

    def _try_spawn(self, col, surf, world, seed, rule):
        (mob_type, h_mul, h_off, h_xor, chance,
         biome_req, biome_excl, surf_tiles,
         mode, d_min, d_max, fly_off, _day_only, wander) = rule

        key = (col, mob_type)
        if not self._can_spawn(key):
            return
        self._mark_spawned(key)

        # Contraintes biome
        if biome_req is not None and world.biome_at(col) != biome_req:
            return
        if biome_excl is not None and world.biome_at(col) == biome_excl:
            return

        # Contrainte tuile de surface
        if surf_tiles is not None and world.get(col, surf) not in surf_tiles:
            return

        # Porte probabiliste (hash déterministe)
        if _hash1(col * h_mul + h_off, seed ^ h_xor) >= chance:
            return

        # Spawn selon le mode
        if mode == "surface":
            mh  = _mh(mob_type)
            top = surf - math.ceil(mh)
            if not all(world.get(col, top + k) == TILE_AIR
                       for k in range(math.ceil(mh))):
                return
            m = Mob(col, top, mob_type, seed)
            _eject_mob(m, world)
            self._mobs.append(m)

        elif mode == "underground":
            mh = _mh(mob_type)
            for row in range(surf + d_min, min(surf + d_max, ROWS - 2)):
                if (world.get(col, row) == TILE_AIR
                        and world.get(col, row + 1) != TILE_AIR):
                    top = row - math.ceil(mh) + 1
                    m = Mob(col, top, mob_type, seed)
                    _eject_mob(m, world)
                    self._mobs.append(m)
                    break

        elif mode == "cave_air":
            for row in range(surf + d_min, min(surf + d_max, ROWS - 2)):
                if world.get(col, row) == TILE_AIR:
                    m = Mob(col, float(row), mob_type, seed)
                    self._mobs.append(m)
                    break

        elif mode == "flying":
            fly_row = surf + fly_off
            if fly_row >= 1:
                m = Mob(col, float(fly_row), mob_type, seed)
                if wander:
                    m._wander_dir = 1 if m._rng.random() > 0.5 else -1
                self._mobs.append(m)

    # ── Cas spéciaux ────────────────────────────────────────────────────────

    def _try_spawn_golem(self, col, surf, world, seed):
        key = (col, MOB_GOLEM)
        if not self._can_spawn(key):
            return
        self._mark_spawned(key)
        if world.biome_at(col) == BIOME_DESERT:
            return
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

    def _try_spawn_tendril(self, col, surf, world, seed):
        """La Vrille : boss souterrain très rare (~0.4 %), unique par zone (espacement 200)."""
        key = (col, MOB_TENDRIL)
        if not self._can_spawn(key):
            return
        self._mark_spawned(key)
        if _hash1(col * 251 + 113, seed ^ 0x7E11) >= 0.004:
            return
        # Espacement forcé : pas d'autre Vrille dans les 200 colonnes précédentes
        for dc2 in range(-200, 0):
            if _hash1((col + dc2) * 251 + 113, seed ^ 0x7E11) < 0.004:
                return
        deep_min = surf + 70
        for row in range(deep_min, min(deep_min + 30, ROWS - 2)):
            if (world.get(col, row) == TILE_AIR
                    and world.get(col, row + 1) != TILE_AIR):
                m = Mob(col, float(row), MOB_TENDRIL, seed)
                _eject_mob(m, world)
                self._mobs.append(m)
                break

    def _try_spawn_gorgon(self, col, surf, world, seed):
        """La Gorgone : boss sonique ultra-rare (~0.2%), grande cavité requise.
        Spawn sur le sol d'une cavité dégagée sur au moins 22 tuiles vers le haut.
        Espacement minimum de 150 colonnes entre deux Gorgones."""
        key = (col, MOB_GORGON)
        if not self._can_spawn(key):
            return
        self._mark_spawned(key)
        if _hash1(col * 307 + 137, seed ^ 0xAB5C) >= 0.002:
            return
        # Espacement forcé : pas d'autre Gorgone dans les 150 colonnes précédentes
        for dc2 in range(-150, 0):
            if _hash1((col + dc2) * 307 + 137, seed ^ 0xAB5C) < 0.002:
                return
        # Chercher un sol solide assez profond
        deep_min = surf + 75
        deep_max = min(ROWS - 4, surf + 100)
        for floor_row in range(deep_min, deep_max):
            # Sol solide sous cette tuile ?
            if world.get(col, floor_row) != TILE_AIR:
                continue
            if world.get(col, floor_row + 1) == TILE_AIR:
                continue
            # Vérifier cavité : 22 tuiles d'air au-dessus
            cavity_ok = all(
                world.get(col, floor_row - k) == TILE_AIR
                for k in range(22)
            )
            if not cavity_ok:
                continue
            # Spawn : tête 20 tiles (GORGON_BODY_HEIGHT) au-dessus du sol
            _body_h  = 20
            head_row = max(0, floor_row - _body_h)
            m = Mob(col, float(head_row), MOB_GORGON, seed)
            m._anchor_x   = col + _mw(MOB_GORGON) / 2
            m._anchor_row = float(floor_row)
            # Pas de _eject_mob : la tête est en air libre
            self._mobs.append(m)
            break

    # ── Alerte Golem ────────────────────────────────────────────────────────

    def trigger_cabin_break(self, col):
        """Active la poursuite de tous les Golems proches d'une cabane brisée."""
        for m in self._mobs:
            if m.mob_type == MOB_GOLEM and abs(m.center_col() - col) < 15:
                m.state     = "chase"
                m._state_cd = 10.0

    # ── Mise à jour ─────────────────────────────────────────────────────────

    def update(self, dt, players, world):
        self._clock += dt
        for mob in self._mobs:
            update_mob(mob, dt, players, world)
            if mob.burning:
                mob.burn_timer -= dt
                if mob.burn_timer <= 0:
                    mob.vanish = True
            # Tick poison (1 dégât par seconde pendant la durée)
            if mob._poison_t > 0:
                mob._poison_t  -= dt
                mob._poison_cd -= dt
                if mob._poison_cd <= 0:
                    mob.hp -= 1
                    mob._poison_cd = 1.0
                    mob._hp_bar_timer = 2.0
                    if mob.hp <= 0:
                        mob.vanish = True
                        self._poison_drops.extend(roll_drops(mob.mob_type))
            # Dégâts environnementaux (lave / eau)
            _apply_env_damage(mob, world, dt)
            if mob.hp <= 0 and not mob.vanish:
                mob.vanish = True
                self._poison_drops.extend(roll_drops(mob.mob_type))
            # Timer barre de vie
            if mob._hp_bar_timer > 0:
                mob._hp_bar_timer -= dt
        self._mobs = [m for m in self._mobs if not m.vanish]

    def tick_day_night(self, is_night, world, players):
        """Gère les transitions jour/nuit : spawn zombies la nuit, brûlure à l'aube."""
        just_became_night = is_night and not self._was_night
        just_became_day   = (not is_night) and self._was_night

        if just_became_night:
            for p in players:
                count = random.randint(1, 2)
                for _ in range(count):
                    col  = int(p.x) + random.randint(-8, 8)
                    surf = world.surface_at(col)
                    top  = surf - math.ceil(_mh(MOB_ZOMBIE))
                    if all(world.get(col, top + k) == TILE_AIR
                           for k in range(math.ceil(_mh(MOB_ZOMBIE)))):
                        m = Mob(col, float(top), MOB_ZOMBIE)
                        m._surface_zombie = True
                        _eject_mob(m, world)
                        self._mobs.append(m)

        if just_became_day:
            for mob in self._mobs:
                if (mob.mob_type == MOB_ZOMBIE
                        and getattr(mob, '_surface_zombie', False)
                        and not mob.burning):
                    mob.burning    = True
                    mob.burn_timer = 3.0

        self._was_night = is_night

    # ── Attaque épée avec tier + drops ──────────────────────────────────────

    def attack_near(self, px, py, reach, damage, sword_tier=0, poison=0.0):
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
            m._hp_bar_timer = 2.0
            if poison > 0 and m.hp > 0:
                m._poison_t  = max(m._poison_t, poison)
                m._poison_cd = min(m._poison_cd, 0.0)
            if m.hp <= 0:
                dead.append(m)
                all_drops.extend(roll_drops(m.mob_type))

        for m in dead:
            self._mobs.remove(m)

        # Loups en meute : si un loup est attaqué, les loups proches deviennent agressifs
        if any(m.mob_type == MOB_WOLF for m in dead) or any(
            m.mob_type == MOB_WOLF and m.hp < _MOB_HP.get(MOB_WOLF, 4)
            for m in self._mobs
        ):
            for m in self._mobs:
                if m.mob_type == MOB_WOLF and abs(m.center_col() - cx) < 12:
                    m.state     = "chase"
                    m._state_cd = 8.0

        return len(dead), all_drops, immune

    # ── Rendu ───────────────────────────────────────────────────────────────

    def draw(self, screen, camera):
        vw = camera.view_w
        vh = camera.view_h
        for mob in self._mobs:
            sx, sy = camera.world_to_screen(mob.px(), mob.py())
            mw = _MOB_PW[mob.mob_type]
            mh = _MOB_PH[mob.mob_type]
            # La Gorgone : corps visuel s'étend 320px sous la tête (cf. renderer)
            if mob.mob_type == MOB_GORGON:
                mh = mh + 320
            if sx + mw < 0 or sx > vw or sy + mh < 0 or sy > vh:
                continue
            draw_mob(screen, mob, camera)
