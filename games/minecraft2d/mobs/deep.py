"""
Mobs des profondeurs : IA uniquement (spawn géré par manager.py).

Hiérarchie de profondeur (tiles sous la surface) :
  surf+20..+45  → MOB_TROLL  : troll des cavernes, 6 HP, dmg=2, épée Bois min
  surf+45..+65  → MOB_WORM   : ver fouisseur,      9 HP, dmg=3, épée Fer min
  surf+65+      → MOB_WRAITH : spectre abyssal,   12 HP, dmg=4, épée Or min
  surf+75+      → MOB_GORGON : La Gorgone,        50 HP, dmg=6, épée Or min (très rare)
"""
import math
import random

import pygame

from config import (
    GRAVITY, MAX_FALL_SPEED, JUMP_VEL, TILE_AIR, TILE_WATER, TILE_OBSIDIAN, TILE_PORTAL,
    PLAYER_W, PLAYER_H, TILE_SIZE, ROWS,
)
from mobs.base import (
    MOB_TROLL, MOB_WORM, MOB_TENDRIL, MOB_GORGON,
    _mw, _mh,
)
from mobs.physics import _solid, _move_mob_x, _move_mob_y
from mobs.armor import _apply_contact_dmg, combat_roll, _CRIT_MULT

TENDRIL_REACH  = 6.0   # rayon d'attaque tentacules (tiles)
TENDRIL_DETECT = 10.0  # rayon de détection (tiles)

# ── Constantes Gorgone ────────────────────────────────────────────────────────
GORGON_BODY_HEIGHT = 20.0   # longueur du corps (tiles) ≈ 1 écran plein
GORGON_SWING_MAX   =  9.0   # balancement maxi depuis l'ancre (tiles)
GORGON_CHASE_SPD   =  4.5   # vitesse de swing en chasse (tiles/s)
GORGON_IDLE_SPD    =  1.2   # vitesse de balancement idle (tiles/s)
GORGON_IDLE_AMP    =  3.5   # amplitude oscillation idle (tiles)
GORGON_IDLE_FREQ   =  0.35  # fréquence oscillation idle (Hz)
GORGON_DETECT_R    = 20.0   # rayon de détection (tiles)

# Régénération par contact avec l'eau (au pied)
GORGON_REGEN_PERIOD = 1.5   # secondes par PV regen
# Charge attack
GORGON_CHARGE_WINDUP   = 0.4   # délai avant le dash (telegraph esquive)
GORGON_CHARGE_DASH     = 0.3   # durée du dash
GORGON_CHARGE_SPEED    = 25.0  # vitesse pendant le dash (tiles/s)
GORGON_CHARGE_COOLDOWN = 4.0
GORGON_CHARGE_NOISE_CHANCE = 0.10
# Marche continue qui compte comme bruit
GORGON_WALK_NOISE_DELAY = 2.0  # secondes de marche cumulée avant déclenchement bruit
# Blocs que la Gorgone NE casse PAS
GORGON_UNBREAKABLE = (TILE_AIR, TILE_WATER, TILE_OBSIDIAN, TILE_PORTAL)

# ── Crachat vert (missile balistique) ────────────────────────────────────────
GORGON_SPIT_RANGE     = 22.0  # tiles, déclenchement volley
GORGON_SPIT_GRAVITY   =  6.5  # tiles/s² (chute lente, arc tranquille)
GORGON_SPIT_VY0       = -5.0  # vitesse verticale initiale (montée douce)
GORGON_SPIT_VX_CAP    =  6.5  # vitesse horizontale max (déplacement lent)
GORGON_SPIT_DMG       = 3
GORGON_SPIT_LIFETIME  = 7.0
GORGON_SPIT_HIT_R     = 0.55  # rayon de collision joueur (tiles)

# ── Pattern d'attaque (machine à phases) ─────────────────────────────────────
# Cycle : idle → volley → decision → (windup→dash | cooldown) → idle
GORGON_PHASE_IDLE_DUR     = 8.0    # repos avant volley (s)
GORGON_VOLLEY_COUNT       = 3      # nb de boules par volley standard
GORGON_BARRAGE_COUNT      = 5      # nb de boules pour la volley "barrage"
GORGON_BARRAGE_EVERY      = 3      # tous les N cycles, la volley devient barrage
GORGON_VOLLEY_GAP         = 0.6    # délai entre boules d'une volley (s)
GORGON_PHASE_COOLDOWN_DUR = 3.0    # repos après attaque (s)
GORGON_CHARGE_DECIDE_R    = 12.0   # distance pour choisir charge plutôt que cooldown
GORGON_NOISE_INTERRUPT_CD = 6.0    # cooldown global noise→charge (anti-spam)
GORGON_BARRAGE_SPREAD     = 4.5    # demi-écart latéral max pour le barrage (tiles)

# ── Mouvement de tête organique (sinus de sinus) ─────────────────────────────
GORGON_HEAD_FOLLOW_RATE = 1.4   # vitesse de drift du centre vers focus (1/s)
GORGON_HEAD_TREMOR_AMP  = 0.35  # micro-tremor (tiles)
GORGON_HEAD_TREMOR_FRQ  = 3.1   # tremor rate (Hz)


def _nearest(mob, players):
    best_p, best_d = None, 1e9
    for p in players:
        d = math.hypot(mob.center_col() - p.x, mob.center_row() - p.y)
        if d < best_d:
            best_d, best_p = d, p
    return best_p, best_d


# ── IA principale ─────────────────────────────────────────────────────────────

def _update_deep_mob(mob, dt, players, world):
    """IA + déplacement + dégâts de contact pour les mobs des profondeurs."""
    mob._fly_phase  += dt
    mob._tendril_cd  = max(0.0, mob._tendril_cd - dt)

    # La Vrille gère tout elle-même (stationnaire, pas de _apply_contact_dmg)
    if mob.mob_type == MOB_TENDRIL:
        _update_tendril(mob, dt, players)
        return

    # La Gorgone gère tout elle-même (stationnaire, détection sonore)
    if mob.mob_type == MOB_GORGON:
        _update_gorgon(mob, dt, players, world)
        return

    player, dist = _nearest(mob, players)
    dir_to = math.copysign(1.0, player.x - mob.x) if player else 1.0

    if mob.mob_type == MOB_TROLL:
        _ai_troll(mob, dt, dist, dir_to, world)
    elif mob.mob_type == MOB_WORM:
        _ai_worm(mob, dt, dist, dir_to, player)
    else:  # MOB_WRAITH – collision correcte (plus de traversement de mur)
        _ai_wraith(mob, dt, dist, dir_to, player, world)

    _apply_contact_dmg(mob, players)


def _ai_troll(mob, dt, dist, dir_to, world):
    """Troll : lent, trapu, suit le joueur à courte portée."""
    if dist <= 9.0:          mob.state = "chase"; mob._state_cd = 3.0
    elif mob._state_cd <= 0: mob.state = "idle"
    cy = mob.center_row()
    if mob.state == "chase":
        mob.vx = 2.2 * dir_to
        nc = int(mob.x + dir_to * (_mw(MOB_TROLL) + 0.1))
        if mob.on_ground and mob._jump_cd <= 0 and _solid(world, nc, int(cy)):
            mob.vy = JUMP_VEL * 0.9; mob._jump_cd = 0.7
    else:
        mob._wander_cd -= dt
        if mob._wander_cd <= 0:
            mob._wander_dir = 1 if mob._rng.random() > 0.5 else -1
            mob._wander_cd  = 3.0 + mob._rng.random() * 4.0
        mob.vx = 1.0 * mob._wander_dir
    mob.vy = min(mob.vy + GRAVITY * dt, MAX_FALL_SPEED)
    _move_mob_x(mob, world, mob.vx * dt)
    _move_mob_y(mob, world, mob.vy * dt)


def _ai_worm(mob, dt, dist, dir_to, player):
    """Ver fouisseur : traverse le terrain, charge en ligne droite."""
    if dist <= 12.0:         mob.state = "chase"; mob._state_cd = 4.0
    elif mob._state_cd <= 0: mob.state = "idle"
    if mob.state == "chase" and player:
        mob.vx = 4.5 * dir_to
        mob.vy = (player.y - mob.center_row()) * 1.5
    else:
        mob._wander_cd -= dt
        if mob._wander_cd <= 0:
            mob._wander_dir = 1 if mob._rng.random() > 0.5 else -1
            mob._wander_cd  = 2.0 + mob._rng.random() * 3.0
        mob.vx = 2.0 * mob._wander_dir
        mob.vy = 0.0
    # Limiter la vitesse pour éviter le tunnel effect excessif
    speed = math.hypot(mob.vx, mob.vy)
    if speed > 0.32:
        mob.vx *= 0.32 / speed
        mob.vy *= 0.32 / speed
    # Le ver traverse le terrain (intentionnel : ver fouisseur)
    mob.x += mob.vx * dt
    mob.y += mob.vy * dt


def _ai_wraith(mob, dt, dist, dir_to, player, world):
    """Spectre : vole avec collision correcte (ne traverse plus les murs)."""
    if dist <= 20.0:         mob.state = "chase"; mob._state_cd = 5.0
    elif mob._state_cd <= 0: mob.state = "idle"
    if mob.state == "chase" and player:
        mob.vx = 3.0 * dir_to
        mob.vy = (player.y - mob.center_row()) * 1.8 + math.sin(mob._fly_phase) * 0.4
    else:
        mob._wander_cd -= dt
        if mob._wander_cd <= 0:
            mob._wander_dir = 1 if mob._rng.random() > 0.5 else -1
            mob._wander_cd  = 3.0 + mob._rng.random() * 4.0
        mob.vx = 1.5 * mob._wander_dir
        mob.vy = math.sin(mob._fly_phase) * 0.8
    # Collision physique (plus de traversement de mur)
    _move_mob_x(mob, world, mob.vx * dt)
    _move_mob_y(mob, world, mob.vy * dt)


# ── Boss Végétal : La Vrille ((MOB_TENDRIL) – stationnaire ──────────────────────

def _update_tendril(mob, dt, players):
    """La Vrille ne bouge pas. Détecte les joueurs à proximité, attaque à portée."""
    player, dist = _nearest(mob, players)

    if dist <= TENDRIL_DETECT:
        mob.state = "active"
    else:
        mob.state = "idle"
        return

    # Attaque par tentacules quand le joueur est à portée
    if dist <= TENDRIL_REACH and mob._tendril_cd <= 0 and player:
        raw_dmg = 3
        hit, crit = combat_roll(player, mob.mob_type)
        if hit:
            dmg = raw_dmg * _CRIT_MULT if crit else raw_dmg
            player.hp = max(0, player.hp - dmg)
            player._dmg_flash = 0.6 if crit else 0.4
        mob._tendril_cd = 2.0   # 1 attaque toutes les 2 secondes


# ── Boss Reptilien : La Gorgone (MOB_GORGON) – serpent ancré, swing G/D ──────

# Compteur global d'événements bruit injectés depuis l'extérieur (mine, etc.)
# Incrémenté par actions.py quand un joueur casse un bloc dans l'arène.
_GORGON_NOISE_PENDING = 0

# Liste mondiale des crachats verts actifs (vidée à la sortie de l'arène).
# Chaque entrée : [x_tile, y_tile, vx, vy, age]
_GORGON_SPITS = []

def push_gorgon_noise():
    """Signale un événement bruit (ex: minage) à la Gorgone. Appelé depuis le jeu."""
    global _GORGON_NOISE_PENDING
    _GORGON_NOISE_PENDING += 1


def _consume_gorgon_noise():
    global _GORGON_NOISE_PENDING
    n = _GORGON_NOISE_PENDING
    _GORGON_NOISE_PENDING = 0
    return n


def _gorgon_init_extra(mob):
    """Initialise les attributs propres à la Gorgone (lazy)."""
    if not hasattr(mob, "_phase"):
        # Phase machine : idle | volley | windup | dash | cooldown
        mob._phase           = "idle"
        mob._phase_timer     = GORGON_PHASE_IDLE_DUR
        mob._cycle_count     = 0           # incrémenté à chaque idle→volley
        # Volley state
        mob._volley_left     = 0
        mob._volley_gap      = 0.0
        mob._volley_pattern  = "single"    # "single" | "barrage"
        mob._volley_spread_idx = 0         # index du tir courant dans le barrage
        # Charge / dash
        mob._charge_target_x = 0.0
        mob._charge_dir      = 1.0
        # Drapeau visuel pour le renderer (yeux flash/jaunes)
        mob._charge_state    = "idle"      # "idle" | "windup" | "dash"
        # Regen eau
        mob._regen_timer     = 0.0
        # Bruits joueurs (par index 0/1)
        mob._walk_acc        = [0.0, 0.0]
        mob._prev_on_ground  = [True, True]
        mob._noise_cd        = 0.0          # cooldown global d'interrupt par bruit
        # Blocs cassés (drainés par loop.py)
        mob._break_pending   = []
        # Mouvement de tête organique
        mob._head_center     = None         # initialisé au 1er tick à l'anchor


def _gorgon_segment_positions(mob):
    """Retourne la liste de positions (cx, cy) en tuiles le long du corps,
    de la tête vers la queue/ancre. Utilisé pour la collision de destruction."""
    head_cx = mob.x + _mw(MOB_GORGON) / 2
    head_cy = mob.y + _mh(MOB_GORGON) / 2
    anchor_cx = mob._anchor_x
    anchor_cy = mob._anchor_row
    SEGS = 24
    for i in range(SEGS + 1):
        t = i / SEGS
        bx = head_cx * (1 - t) + anchor_cx * t
        by = head_cy * (1 - t) + anchor_cy * t
        yield bx, by


def _gorgon_break_blocks_along_body(mob, world):
    """Casse les tiles touchés par le corps/tête (sauf eau, obsidienne, portail)."""
    seen = set()
    for cx, cy in _gorgon_segment_positions(mob):
        col = int(cx)
        row = int(cy)
        for dc in (-1, 0):
            for dr in (-1, 0):
                key = (col + dc, row + dr)
                if key in seen:
                    continue
                seen.add(key)
                tile = world.get(*key)
                if tile in GORGON_UNBREAKABLE:
                    continue
                world.set(*key, TILE_AIR)
                mob._break_pending.append(key)


def _gorgon_emit_noise_from_players(mob, dt, players):
    """Détecte les bruits émis par les joueurs (saut + marche prolongée) et
    retourne le nombre d'événements bruit à compter ce tick."""
    events = 0
    for i, p in enumerate(players[:2]):
        if p is None:
            continue
        # Saut : transition on_ground True → False
        prev_og = mob._prev_on_ground[i]
        cur_og  = p.on_ground
        if prev_og and not cur_og and p.vy < 0:
            events += 1
        mob._prev_on_ground[i] = cur_og
        # Marche : accumule le temps de mouvement horizontal au sol
        if cur_og and abs(p.vx) > 0.5:
            mob._walk_acc[i] += dt
            if mob._walk_acc[i] >= GORGON_WALK_NOISE_DELAY:
                events += 1
                mob._walk_acc[i] = 0.0
        else:
            mob._walk_acc[i] = max(0.0, mob._walk_acc[i] - dt * 0.5)
    return events


def _gorgon_organic_target(mob, dt, focus_x):
    """Calcule la position X cible de la tête : centre qui drifte vers focus_x
    + oscillation principale + micro-tremor. Donne un mouvement de serpent."""
    if mob._head_center is None:
        mob._head_center = focus_x
    # Drift exponentiel vers focus (independent du dt)
    rate = 1.0 - math.exp(-GORGON_HEAD_FOLLOW_RATE * dt)
    mob._head_center += (focus_x - mob._head_center) * rate
    phase = mob._fly_phase
    # Amplitude qui "respire"
    amp = GORGON_IDLE_AMP * (0.7 + 0.3 * math.sin(phase * 0.7))
    osc = math.sin(phase * GORGON_IDLE_FREQ * 2 * math.pi) * amp
    tremor = math.sin(phase * GORGON_HEAD_TREMOR_FRQ) * GORGON_HEAD_TREMOR_AMP
    return mob._head_center + osc + tremor


def _gorgon_spawn_spit(mob, target_cx, target_cy):
    """Crée un crachat vert depuis la bouche de la Gorgone vers la cible."""
    head_cx = mob.x + _mw(MOB_GORGON) / 2
    head_cy = mob.y + _mh(MOB_GORGON) / 2
    # Ballistique simple : on impose vy0 (vers le haut) et on en déduit vx pour
    # arriver près de la cible avec la gravité GORGON_SPIT_GRAVITY.
    dx = target_cx - head_cx
    dy = target_cy - head_cy
    g  = GORGON_SPIT_GRAVITY
    v0y = GORGON_SPIT_VY0
    # Temps de vol : résolution de y(t) = v0y * t + 0.5*g*t² = dy
    # → 0.5*g*t² + v0y*t - dy = 0
    a = 0.5 * g
    b = v0y
    c = -dy
    disc = b * b - 4 * a * c
    if disc < 0:
        # cible inatteignable avec ces paramètres — tir tendu vers le bas
        t_flight = max(0.5, abs(dx) / GORGON_SPIT_VX_CAP)
        v0y = -2.0
    else:
        # racine positive
        t_flight = (-b + math.sqrt(disc)) / (2 * a)
        if t_flight <= 0:
            t_flight = (-b - math.sqrt(disc)) / (2 * a)
        t_flight = max(0.4, t_flight)
    vx = dx / t_flight
    if vx >  GORGON_SPIT_VX_CAP: vx =  GORGON_SPIT_VX_CAP
    if vx < -GORGON_SPIT_VX_CAP: vx = -GORGON_SPIT_VX_CAP
    _GORGON_SPITS.append([head_cx, head_cy, vx, v0y, 0.0])


def update_gorgon_spits(dt, players, world, chunks=None, queue_block_fn=None):
    """Met à jour tous les crachats actifs : physique, collisions, dégâts.

    Une boule détruit le bloc qu'elle touche (sauf bloc indestructible)
    et est consommée dans la foulée.
    """
    if not _GORGON_SPITS:
        return
    pw = PLAYER_W / TILE_SIZE
    ph = PLAYER_H / TILE_SIZE
    alive = []
    for s in _GORGON_SPITS:
        s[4] += dt
        if s[4] > GORGON_SPIT_LIFETIME:
            continue
        # Intégration verlet simple
        s[3] += GORGON_SPIT_GRAVITY * dt
        s[0] += s[2] * dt
        s[1] += s[3] * dt
        col = int(s[0])
        row = int(s[1])
        if row < 0 or row >= ROWS:
            continue
        # Collision terrain : la boule se consume contre tout sauf air/eau
        tile = world.get(col, row)
        if tile not in (TILE_AIR, TILE_WATER):
            # Casse le bloc s'il n'est pas dans la liste indestructible
            if tile not in GORGON_UNBREAKABLE:
                world.set(col, row, TILE_AIR)
                if chunks is not None:
                    chunks.update_tile(col, row, TILE_AIR)
                if queue_block_fn is not None:
                    queue_block_fn(col, row, TILE_AIR)
            continue
        # Collision joueur
        hit_player = None
        for p in players:
            pcx = p.x + pw / 2
            pcy = p.y + ph / 2
            if math.hypot(s[0] - pcx, s[1] - pcy) <= GORGON_SPIT_HIT_R + max(pw, ph) * 0.4:
                hit_player = p
                break
        if hit_player is not None:
            was_alive = hit_player.hp > 0
            hit_player.hp = max(0, hit_player.hp - GORGON_SPIT_DMG)
            hit_player._dmg_flash = 0.4
            # léger recul
            push = math.copysign(1.0, s[2]) if s[2] != 0 else 1.0
            hit_player.vx = push * 4.0
            continue
        alive.append(s)
    _GORGON_SPITS[:] = alive


def draw_gorgon_spits(surf, cam_x, cam_y):
    """Affiche chaque crachat comme une boule verte avec halo."""
    if not _GORGON_SPITS:
        return
    for s in _GORGON_SPITS:
        sx = int(s[0] * TILE_SIZE - cam_x)
        sy = int(s[1] * TILE_SIZE - cam_y)
        if sx < -16 or sy < -16 or sx > surf.get_width() + 16 or sy > surf.get_height() + 16:
            continue
        pygame.draw.circle(surf, ( 30,  90,  30), (sx, sy), 7)
        pygame.draw.circle(surf, ( 60, 180,  60), (sx, sy), 5)
        pygame.draw.circle(surf, (140, 240, 110), (sx, sy), 3)
        pygame.draw.circle(surf, (220, 255, 200), (sx - 1, sy - 1), 1)


def clear_gorgon_spits():
    """Vide tous les crachats actifs (à appeler quand le joueur quitte l'arène)."""
    _GORGON_SPITS.clear()


def _gorgon_start_volley(mob):
    """Démarre une nouvelle volley de tirs (standard ou barrage 1x sur 3)."""
    mob._cycle_count += 1
    if mob._cycle_count % GORGON_BARRAGE_EVERY == 0:
        mob._volley_pattern = "barrage"
        mob._volley_left    = GORGON_BARRAGE_COUNT
    else:
        mob._volley_pattern = "single"
        mob._volley_left    = GORGON_VOLLEY_COUNT
    mob._volley_spread_idx = 0
    mob._volley_gap        = 0.4   # petit délai avant le 1er tir
    mob._phase             = "volley"
    mob._phase_timer       = mob._volley_left * GORGON_VOLLEY_GAP + 0.6


def _gorgon_fire_one(mob, player):
    """Tire une boule. En barrage : étale latéralement. Sinon : visée directe."""
    if player is None:
        return
    target_cx = player.x + (PLAYER_W / TILE_SIZE) / 2
    target_cy = player.y + (PLAYER_H / TILE_SIZE) / 2
    if mob._volley_pattern == "barrage":
        # Étalement linéaire : -spread, -spread/2, 0, +spread/2, +spread
        n = max(1, GORGON_BARRAGE_COUNT - 1)
        t = mob._volley_spread_idx / n        # 0..1
        offset = (t - 0.5) * 2.0 * GORGON_BARRAGE_SPREAD
        target_cx += offset
        mob._volley_spread_idx += 1
    _gorgon_spawn_spit(mob, target_cx, target_cy)


def _gorgon_enter_windup(mob, player_x, head_cx):
    """Bascule en phase windup ciblée sur player_x."""
    mob._phase           = "windup"
    mob._phase_timer     = GORGON_CHARGE_WINDUP
    mob._charge_target_x = player_x
    mob._charge_dir      = math.copysign(1.0, player_x - head_cx) if player_x != head_cx else 1.0
    mob._charge_state    = "windup"   # signal pour renderer (yeux flash)


def _update_gorgon(mob, dt, players, world):
    """La Gorgone : serpent ancré, attaques en pattern, regen par contact eau."""
    mob._fly_phase  += dt
    mob._tendril_cd  = max(0.0, mob._tendril_cd - dt)
    _gorgon_init_extra(mob)

    if mob._anchor_x is None:
        mob._anchor_x   = mob.x + _mw(MOB_GORGON) / 2
        mob._anchor_row = mob.y + GORGON_BODY_HEIGHT

    anchor_x   = mob._anchor_x
    anchor_row = mob._anchor_row
    mob.y = anchor_row - GORGON_BODY_HEIGHT
    head_cx = mob.x + _mw(MOB_GORGON) / 2
    half_w  = _mw(MOB_GORGON) / 2

    # ── Régénération par contact eau au pied ─────────────────────────────────
    foot_tile = world.get(int(anchor_x), int(anchor_row))
    if foot_tile == TILE_WATER and mob.hp < mob._max_hp:
        mob._regen_timer += dt
        if mob._regen_timer >= GORGON_REGEN_PERIOD:
            mob._regen_timer = 0.0
            mob.hp = min(mob._max_hp, mob.hp + 1)
            mob._hp_bar_timer = 2.0
    else:
        mob._regen_timer = 0.0

    # ── Détection joueur le plus proche ──────────────────────────────────────
    player, dist = _nearest(mob, players)

    # ── Bruits → interrupt charge (anti-spam via _noise_cd) ──────────────────
    mob._noise_cd  = max(0.0, mob._noise_cd - dt)
    noise_events   = _consume_gorgon_noise()
    noise_events  += _gorgon_emit_noise_from_players(mob, dt, players)
    if (mob._phase in ("idle", "cooldown")
            and mob._noise_cd <= 0
            and player is not None
            and dist <= GORGON_DETECT_R + 10
            and noise_events > 0):
        for _ in range(noise_events):
            if random.random() < GORGON_CHARGE_NOISE_CHANCE:
                _gorgon_enter_windup(mob, player.x + PLAYER_W / (2 * TILE_SIZE), head_cx)
                mob._noise_cd = GORGON_NOISE_INTERRUPT_CD
                break

    mob._phase_timer -= dt

    # ── Phase machine ────────────────────────────────────────────────────────
    if mob._phase == "idle":
        # Repos + oscillation ; on regarde l'anchor (pas le joueur)
        focus = anchor_x
        target_cx = _gorgon_organic_target(mob, dt, focus)
        diff = target_cx - head_cx
        step = math.copysign(min(abs(diff), GORGON_IDLE_SPD * dt), diff) if diff else 0.0
        mob.x += step
        mob.state = "idle"
        if mob._phase_timer <= 0:
            # Volley uniquement si joueur en portée — sinon on prolonge l'idle
            if player is not None and dist <= GORGON_SPIT_RANGE:
                _gorgon_start_volley(mob)
            else:
                mob._phase_timer = GORGON_PHASE_IDLE_DUR * 0.5
        _gorgon_break_blocks_along_body(mob, world)

    elif mob._phase == "volley":
        # Suit le joueur lentement pour tirer "en visant"
        focus = (player.x + PLAYER_W / (2 * TILE_SIZE)) if player else anchor_x
        # Centre clampé pour rester dans l'amplitude de swing
        focus = max(anchor_x - GORGON_SWING_MAX, min(anchor_x + GORGON_SWING_MAX, focus))
        target_cx = _gorgon_organic_target(mob, dt, focus)
        diff = target_cx - head_cx
        step = math.copysign(min(abs(diff), GORGON_CHASE_SPD * dt), diff) if diff else 0.0
        mob.x += step
        mob.state = "chase"
        # Tirs cadencés
        mob._volley_gap -= dt
        if mob._volley_left > 0 and mob._volley_gap <= 0:
            _gorgon_fire_one(mob, player)
            mob._volley_left -= 1
            mob._volley_gap   = GORGON_VOLLEY_GAP
        if mob._volley_left <= 0 and mob._phase_timer <= 0:
            # Décision : charge si proche, cooldown sinon
            if player is not None and dist <= GORGON_CHARGE_DECIDE_R:
                _gorgon_enter_windup(mob, player.x + PLAYER_W / (2 * TILE_SIZE), head_cx)
            else:
                mob._phase       = "cooldown"
                mob._phase_timer = GORGON_PHASE_COOLDOWN_DUR
                mob._charge_state = "idle"
        _gorgon_break_blocks_along_body(mob, world)

    elif mob._phase == "windup":
        # Tête quasi-figée (telegraph). Léger tremor pour montrer la tension.
        focus = mob._charge_target_x
        # Drift très lent (la tête se prépare mais ne bondit pas encore)
        if mob._head_center is None:
            mob._head_center = head_cx
        rate = 1.0 - math.exp(-0.6 * dt)
        mob._head_center += (focus - mob._head_center) * rate
        tremor = math.sin(mob._fly_phase * 18.0) * 0.15  # tremor rapide windup
        target_cx = mob._head_center + tremor
        diff = target_cx - head_cx
        step = math.copysign(min(abs(diff), GORGON_IDLE_SPD * dt * 0.5), diff) if diff else 0.0
        mob.x += step
        mob.state = "chase"
        mob._charge_state = "windup"
        if mob._phase_timer <= 0:
            mob._phase        = "dash"
            mob._phase_timer  = GORGON_CHARGE_DASH
            mob._charge_state = "dash"
        _gorgon_break_blocks_along_body(mob, world)

    elif mob._phase == "dash":
        step = GORGON_CHARGE_SPEED * dt * mob._charge_dir
        mob.x += step
        mob._charge_state = "dash"
        mob.state = "chase"
        # Sync head_center avec la position courante pour éviter un snap au retour
        mob._head_center = mob.x + half_w
        if mob._phase_timer <= 0:
            mob._phase        = "cooldown"
            mob._phase_timer  = GORGON_PHASE_COOLDOWN_DUR
            mob._charge_state = "idle"
        _gorgon_break_blocks_along_body(mob, world)

    elif mob._phase == "cooldown":
        # Recovery : la tête revient en oscillation douce vers anchor
        focus = anchor_x
        target_cx = _gorgon_organic_target(mob, dt, focus)
        diff = target_cx - head_cx
        step = math.copysign(min(abs(diff), GORGON_IDLE_SPD * dt), diff) if diff else 0.0
        mob.x += step
        mob.state = "chase" if (player and dist <= GORGON_DETECT_R) else "idle"
        if mob._phase_timer <= 0:
            mob._phase       = "idle"
            mob._phase_timer = GORGON_PHASE_IDLE_DUR
        _gorgon_break_blocks_along_body(mob, world)

    # Clamp absolu (sécurité dépassement, sauf pendant le dash où on autorise +/-)
    if mob._phase in ("idle", "volley", "cooldown", "windup"):
        mob.x = max(anchor_x - GORGON_SWING_MAX - half_w,
                    min(anchor_x + GORGON_SWING_MAX - half_w, mob.x))
    else:
        # Dash : amplitude étendue
        mob.x = max(anchor_x - (GORGON_SWING_MAX + 6) - half_w,
                    min(anchor_x + (GORGON_SWING_MAX + 6) - half_w, mob.x))

    # Dégâts de contact (tête sur joueur)
    _apply_contact_dmg(mob, players)
