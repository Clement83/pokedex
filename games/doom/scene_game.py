"""Boucle de jeu principale.

Retourne :
  'win'   – tous les ennemis éliminés
  'dead'  – le joueur est mort
  None    – quitter (SELECT+START)
"""
import pygame
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from config import (
    FPS, BTN_A, BTN_B, BTN_R1, BTN_L1,
    BTN_SELECT, BTN_START, AXIS_DEAD, BULLET_DAMAGE,
)
from engine.map      import GRID, PLAYER_START, PLAYER_START_ANGLE, ENEMY_SPAWNS
from engine.player   import Player
from engine.entities import Enemy
from engine.raycaster import cast_rays
from engine import renderer
from quit_combo import QuitCombo


def run(screen: pygame.Surface, joysticks: list):
    """Boucle principale. Retourne 'win', 'dead' ou None."""

    renderer.init()
    clock   = pygame.time.Clock()
    qc      = QuitCombo()
    joy     = joysticks[0] if joysticks else None

    player  = Player(*PLAYER_START, PLAYER_START_ANGLE)
    enemies = [Enemy(x, y) for x, y in ENEMY_SPAWNS]

    gun_kick   = 0.0     # animation de recul arme [0, 1]
    mmap_alpha = 0       # minimap (toggle)

    while True:
        dt     = min(clock.tick(FPS) / 1000.0, 0.05)
        events = pygame.event.get()

        for e in events:
            qc.handle_event(e)

        if qc.update_and_draw(screen):
            return None

        # ── Lecture des entrées ───────────────────────────────────────────
        keys   = pygame.key.get_pressed()
        fwd, side, turn = _read_movement(keys, joy)
        fired  = _read_fire(keys, joy, events)

        # ── Tir ───────────────────────────────────────────────────────────
        if fired and player.try_fire():
            gun_kick = 1.0
            # Raycaster pour le z-buffer de détection
            perp_dist, wall_type, side_arr, wall_x = cast_rays(player, GRID)
            for ent in enemies:
                if not ent.dead and ent.is_hit_by_shot(player, perp_dist):
                    ent.take_damage(BULLET_DAMAGE)
                    break   # 1 ennemi par tir
        else:
            # Raycaster normal
            perp_dist, wall_type, side_arr, wall_x = cast_rays(player, GRID)

        # ── Mise à jour ───────────────────────────────────────────────────
        player.update(GRID, dt, fwd, side, turn)

        for ent in enemies:
            ent.update(GRID, player, dt)

        gun_kick = max(0.0, gun_kick - dt * 4.0)   # rebond rapide

        # ── Conditions de fin ─────────────────────────────────────────────
        if player.dead:
            return 'dead'
        if all(e.dead for e in enemies):
            return 'win'

        # ── Rendu ─────────────────────────────────────────────────────────
        hurt_alpha = int(player.hurt_timer / 0.3 * 140) if player.hurt_timer > 0 else 0
        renderer.render_frame(screen, player, perp_dist, wall_type, side_arr,
                              enemies, gun_kick, hurt_alpha)

        # Mini-map (debug) – activée par SELECT seul (btn 12) maintenu
        if joy and joy.get_button(BTN_SELECT):
            _draw_minimap(screen, player, enemies)

        # Réticule
        _draw_crosshair(screen)

        pygame.display.flip()


# ── Input helpers ─────────────────────────────────────────────────────────────

def _read_movement(keys, joy):
    """Retourne (fwd, side, turn) ∈ [-1, 1]³."""
    fwd  = 0.0
    side = 0.0
    turn = 0.0

    # Clavier
    if keys[pygame.K_UP]    or keys[pygame.K_w]: fwd  =  1.0
    if keys[pygame.K_DOWN]  or keys[pygame.K_s]: fwd  = -1.0
    if keys[pygame.K_LEFT]:                       turn = -1.0
    if keys[pygame.K_RIGHT]:                      turn =  1.0
    if keys[pygame.K_a]:                          side = -1.0
    if keys[pygame.K_d]:                          side =  1.0

    if joy is None:
        return fwd, side, turn

    # Joystick axe gauche
    ax0 = joy.get_axis(0)
    ax1 = joy.get_axis(1)
    if abs(ax0) > AXIS_DEAD:
        turn = ax0
    if abs(ax1) > AXIS_DEAD:
        fwd  = -ax1   # axe 1 inversé (haut = -1 → avancer)

    # D-pad (hat)
    hat = joy.get_hat(0) if joy.get_numhats() > 0 else (0, 0)
    if hat[1] ==  1: fwd  =  1.0
    if hat[1] == -1: fwd  = -1.0
    if hat[0] == -1: turn = -1.0
    if hat[0] ==  1: turn =  1.0

    # Boutons D-pad (certains firmwares)
    if joy.get_button(8):  fwd  =  1.0
    if joy.get_button(9):  fwd  = -1.0
    if joy.get_button(10): turn = -1.0
    if joy.get_button(11): turn =  1.0

    # Gâchettes : strafe
    if joy.get_button(BTN_R1): side = -1.0
    if joy.get_button(BTN_L1): side =  1.0

    return fwd, side, turn


def _read_fire(keys, joy, events) -> bool:
    if keys[pygame.K_SPACE] or keys[pygame.K_RETURN]:
        return True
    if joy is None:
        return False
    for e in events:
        if e.type == pygame.JOYBUTTONDOWN and e.button == BTN_A:
            return True
    return False


# ── HUD annexes ───────────────────────────────────────────────────────────────

def _draw_crosshair(screen: pygame.Surface):
    cx = pygame.display.get_surface().get_width()  // 2
    cy = (pygame.display.get_surface().get_height() - 36) // 2
    c  = (200, 200, 200)
    pygame.draw.line(screen, c, (cx - 6, cy), (cx + 6, cy), 1)
    pygame.draw.line(screen, c, (cx, cy - 6), (cx, cy + 6), 1)


def _draw_minimap(screen: pygame.Surface, player, enemies):
    """Minimap 20×16 case → 5px/case dans le coin haut-droit."""
    CS   = 5
    OX   = pygame.display.get_surface().get_width()  - GRID.shape[1] * CS - 4
    OY   = 4
    GRID_arr = GRID   # from engine.map

    for gy in range(GRID_arr.shape[0]):
        for gx in range(GRID_arr.shape[1]):
            col = (60, 60, 60) if GRID_arr[gy, gx] == 0 else (140, 110, 80)
            pygame.draw.rect(screen, col, (OX + gx * CS, OY + gy * CS, CS - 1, CS - 1))

    # Joueur
    px = int(OX + player.x * CS)
    py = int(OY + player.y * CS)
    pygame.draw.circle(screen, (80, 180, 255), (px, py), 3)
    # Direction
    pygame.draw.line(screen, (80, 180, 255),
                     (px, py),
                     (int(px + player.dx * 8), int(py + player.dy * 8)), 1)

    # Ennemis
    for e in enemies:
        if not e.dead:
            ex = int(OX + e.x * CS)
            ey = int(OY + e.y * CS)
            pygame.draw.circle(screen, (220, 60, 60), (ex, ey), 2)


# Import tardif pour éviter la circularité
from engine.map import GRID
