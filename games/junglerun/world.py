"""Monde du runner : génération procédurale, joueur, plateformes, événements.

Chaque joueur possède son propre `World` indépendant (split-screen). Le monde
scrolle horizontalement à vitesse `speed` ; le joueur reste fixe à l'écran
(`PLAYER_SCREEN_X`).
"""
import random
import math
from dataclasses import dataclass, field
from typing import Optional

from config import (
    VIEW_W, VIEW_H,
    GRAVITY, JUMP_VY, DOUBLE_JUMP_VY,
    PLAYER_W, PLAYER_H, PLAYER_SCREEN_X,
    START_SPEED, SPEED_RAMP, MAX_SPEED, BOULDER_BOOST,
    GROUND_Y_BASE, GROUND_Y_MIN, GROUND_Y_MAX,
    PLATFORM_W_MIN, PLATFORM_W_MAX, GAP_MIN, GAP_MAX, DOUBLE_JUMP_GAP,
    BRITTLE_CHANCE, ROCK_CHANCE, BRANCH_CHANCE, FEATHER_CHANCE,
    BOULDER_INTERVAL_MIN, BOULDER_INTERVAL_MAX, BOULDER_DURATION,
)


# ── Entités ──────────────────────────────────────────────────────────────────
@dataclass
class Platform:
    x: float
    y: float
    w: float
    h: float
    brittle: bool = False
    decay_t: Optional[float] = None     # countdown avant destruction (brittle stepped)
    has_vine: bool = False              # trampoline auto sur la plateforme
    rock: Optional[float] = None        # x du rocher posé dessus (None sinon)
    branch_x: Optional[float] = None    # x de la branche basse au-dessus
    feather: Optional[float] = None     # x de la plume sur la plateforme
    vine_used: bool = False


@dataclass
class Player:
    x: float = 0.0          # position en coords monde (= distance parcourue depuis le départ)
    y: float = 0.0          # y dans la viewport (0 = haut)
    vy: float = 0.0
    on_ground: bool = False
    jumps_left: int = 2
    alive: bool = True
    death_x: float = 0.0
    shield: bool = False
    flash_t: float = 0.0    # invuln courte après usage de plume


# ── Monde ────────────────────────────────────────────────────────────────────
class World:
    """Encapsule la run d'un joueur (génération, collisions, rendu)."""

    def __init__(self, seed: int):
        self.rng = random.Random(seed)
        self.player = Player()
        self.platforms: list[Platform] = []
        self.scroll_x = 0.0          # x monde correspondant au bord gauche de la viewport
        self.speed = START_SPEED
        self.elapsed = 0.0
        self.next_event_in = self.rng.uniform(BOULDER_INTERVAL_MIN, BOULDER_INTERVAL_MAX)
        self.event_t = 0.0           # secondes restantes d'un séisme
        self.shake_t = 0.0
        self.shake_mag = 0.0
        self._spawn_x = 0.0          # prochaine x à laquelle générer
        self._initial_setup()

    # ── Génération ───────────────────────────────────────────────────────────
    def _initial_setup(self):
        # Plateforme de départ large et solide pour ne pas mourir au spawn.
        start = Platform(x=-30, y=GROUND_Y_BASE, w=260, h=VIEW_H - GROUND_Y_BASE,
                         brittle=False)
        self.platforms.append(start)
        self._spawn_x = start.x + start.w
        # Place le joueur sur cette plateforme.
        self.player.x = PLAYER_SCREEN_X
        self.player.y = start.y - PLAYER_H
        self.player.on_ground = True
        # Quelques plateformes d'avance pour amortir le 1er tronçon.
        for _ in range(8):
            self._spawn_next()

    def _spawn_next(self):
        # Gap variable. ~10% de gros gaps qui forcent le double saut.
        if self.rng.random() < 0.10:
            gap = self.rng.uniform(DOUBLE_JUMP_GAP, DOUBLE_JUMP_GAP + 35)
        else:
            gap = self.rng.uniform(GAP_MIN, GAP_MAX)

        x = self._spawn_x + gap
        # Hauteur : oscille autour de GROUND_Y_BASE, contrainte par min/max.
        prev = self.platforms[-1]
        # Variation par rapport à la précédente (max ±28 px) pour rester jouable.
        y_jitter = self.rng.uniform(-28, 28)
        y = max(GROUND_Y_MIN, min(GROUND_Y_MAX, prev.y + y_jitter))

        w = self.rng.uniform(PLATFORM_W_MIN, PLATFORM_W_MAX)
        h = VIEW_H - y + 8
        brittle = self.rng.random() < BRITTLE_CHANCE

        plat = Platform(x=x, y=y, w=w, h=h, brittle=brittle)

        # Contenu sur la plateforme (un seul à la fois pour rester lisible).
        r = self.rng.random()
        if r < ROCK_CHANCE and w > 90:
            plat.rock = x + self.rng.uniform(28, w - 28)
        elif r < ROCK_CHANCE + BRANCH_CHANCE and w > 80:
            plat.branch_x = x + self.rng.uniform(20, w - 20)
        elif r < ROCK_CHANCE + BRANCH_CHANCE + FEATHER_CHANCE and not brittle:
            plat.feather = x + self.rng.uniform(20, w - 20)
        elif self.rng.random() < 0.05 and not brittle:
            plat.has_vine = True

        self.platforms.append(plat)
        self._spawn_x = x + w

    # ── Update ───────────────────────────────────────────────────────────────
    def update(self, dt: float, jump_pressed: bool):
        if not self.player.alive:
            # Le joueur tombe encore mais le monde ne scrolle plus.
            self._update_dead_fall(dt)
            return

        self.elapsed += dt
        # Vitesse qui ramp up progressivement.
        target_speed = min(MAX_SPEED, START_SPEED + SPEED_RAMP * self.elapsed)
        eff_speed = target_speed * (BOULDER_BOOST if self.event_t > 0 else 1.0)
        self.speed = eff_speed

        # Scrolling : le monde avance, donc scroll_x augmente.
        self.scroll_x += eff_speed * dt
        self.player.x = self.scroll_x + PLAYER_SCREEN_X

        # ── Saut ─────────────────────────────────────────────────────────────
        if jump_pressed and self.player.jumps_left > 0:
            if self.player.on_ground:
                self.player.vy = JUMP_VY
                self.player.jumps_left = 1
                self.player.on_ground = False
            else:
                self.player.vy = DOUBLE_JUMP_VY
                self.player.jumps_left = 0

        # ── Gravité ──────────────────────────────────────────────────────────
        self.player.vy += GRAVITY * dt
        next_y = self.player.y + self.player.vy * dt

        # ── Collision avec plateformes (uniquement en chute) ────────────────
        landed = False
        if self.player.vy >= 0:
            for plat in self.platforms:
                # Le joueur touche la plateforme verticalement ?
                if plat.x <= self.player.x + PLAYER_W // 2 and \
                   plat.x + plat.w >= self.player.x - PLAYER_W // 2:
                    # Vient-il de traverser la surface entre cette frame et la suivante ?
                    foot_prev = self.player.y + PLAYER_H
                    foot_next = next_y + PLAYER_H
                    if foot_prev <= plat.y + 0.1 and foot_next >= plat.y:
                        next_y = plat.y - PLAYER_H
                        self.player.vy = 0
                        self.player.on_ground = True
                        self.player.jumps_left = 2
                        landed = True
                        # Trampoline auto sur liane.
                        if plat.has_vine and not plat.vine_used:
                            self.player.vy = JUMP_VY * 0.95
                            self.player.on_ground = False
                            plat.vine_used = True
                        # Plateforme pourrie : démarrer le countdown.
                        if plat.brittle and plat.decay_t is None:
                            plat.decay_t = 0.30
                        break

        if not landed:
            self.player.on_ground = False
        self.player.y = next_y

        # ── Décroissance des plateformes pourries piétinées ─────────────────
        for plat in self.platforms:
            if plat.decay_t is not None:
                plat.decay_t -= dt
        # Suppression effective des plateformes effondrées.
        self.platforms = [p for p in self.platforms
                          if p.decay_t is None or p.decay_t > 0]

        # ── Collisions latérales avec rochers / branches ────────────────────
        self._check_obstacle_hits()

        # ── Pickup plume ─────────────────────────────────────────────────────
        for plat in self.platforms:
            if plat.feather is not None:
                if abs(plat.feather - self.player.x) < 12 and \
                   abs((plat.y - PLAYER_H // 2) - self.player.y) < 26:
                    plat.feather = None
                    self.player.shield = True

        # ── Mort par chute ───────────────────────────────────────────────────
        if self.player.y > VIEW_H + 20:
            self._kill()

        # ── Spawn / cleanup plateformes ──────────────────────────────────────
        # On veut toujours du contenu jusqu'à scroll_x + 2*VIEW_W.
        while self._spawn_x < self.scroll_x + VIEW_W * 2:
            self._spawn_next()
        # Retire celles qui sont totalement passées hors caméra.
        self.platforms = [p for p in self.platforms if p.x + p.w > self.scroll_x - 50]

        # ── Événements aléatoires (séisme + accélération) ────────────────────
        if self.event_t > 0:
            self.event_t -= dt
            self.shake_t = 0.18
            self.shake_mag = 4.0
        self.next_event_in -= dt
        if self.next_event_in <= 0 and self.event_t <= 0:
            self.event_t = BOULDER_DURATION
            self.next_event_in = self.rng.uniform(
                BOULDER_INTERVAL_MIN, BOULDER_INTERVAL_MAX)
            # Marque pourries quelques plateformes à venir pour faire monter la tension.
            future = [p for p in self.platforms if p.x > self.scroll_x + VIEW_W * 0.3]
            for p in future[:3]:
                p.brittle = True

        # Décroissance shake (en dehors de l'event).
        if self.event_t <= 0 and self.shake_t > 0:
            self.shake_t -= dt
            if self.shake_t < 0:
                self.shake_t = 0
                self.shake_mag = 0

        if self.player.flash_t > 0:
            self.player.flash_t -= dt

    def _check_obstacle_hits(self):
        px = self.player.x
        py = self.player.y
        rx0, rx1 = px - PLAYER_W // 2, px + PLAYER_W // 2
        ry0, ry1 = py, py + PLAYER_H
        for plat in self.platforms:
            # Rocher (bloc 14x14 au-dessus de la plateforme).
            if plat.rock is not None:
                ox = plat.rock
                oy = plat.y - 14
                if rx1 > ox - 7 and rx0 < ox + 7 and ry1 > oy and ry0 < oy + 14:
                    self._kill_or_shield()
                    plat.rock = None
                    return
            # Branche basse (bloc 22x10 plus haut au-dessus de la plateforme).
            if plat.branch_x is not None:
                ox = plat.branch_x
                oy = plat.y - 38
                if rx1 > ox - 11 and rx0 < ox + 11 and ry1 > oy and ry0 < oy + 10:
                    self._kill_or_shield()
                    plat.branch_x = None
                    return

    def _kill_or_shield(self):
        if self.player.shield:
            self.player.shield = False
            self.player.flash_t = 0.6
            # Petit boost vers le haut pour s'extraire de la situation.
            self.player.vy = JUMP_VY * 0.7
        else:
            self._kill()

    def _kill(self):
        if not self.player.alive:
            return
        self.player.alive = False
        self.player.death_x = self.player.x
        # Lui donne un petit saut pour la chute "tragique".
        self.player.vy = -180.0

    def _update_dead_fall(self, dt: float):
        # Le joueur continue de tomber pour le visuel, mais le monde fige.
        self.player.vy += GRAVITY * dt
        self.player.y += self.player.vy * dt
        if self.shake_t > 0:
            self.shake_t -= dt
        if self.event_t > 0:
            self.event_t -= dt

    @property
    def distance(self) -> int:
        # Distance "lisible" : on retire la position de spawn du joueur.
        if self.player.alive:
            return int(self.player.x - PLAYER_SCREEN_X)
        return int(self.player.death_x - PLAYER_SCREEN_X)
