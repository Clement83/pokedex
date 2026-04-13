"""Raycaster DDA entièrement vectorisé (numpy).

cast_rays(player, grid)
  → perp_dist   float32[N]   distances perpendiculaires aux murs
  → wall_type   int8[N]      type de mur touché (0 si rien)
  → side        int8[N]      0 = face EW, 1 = face NS (NS = plus sombre)
  → wall_x      float32[N]   position fractionnaire sur la face [0, 1)
"""
import numpy as np
from config import N_RAYS, MAX_DDA_STEPS

_TINY = 1e-30


def cast_rays(player, grid):
    """Lance N_RAYS rayons simultanément via DDA vectorisé."""
    MAP_H, MAP_W = grid.shape
    N = N_RAYS

    # Coordonnée caméra : de -1 (gauche) à +1 (droite)
    cam = (2.0 * np.arange(N, dtype=np.float32) / N) - 1.0

    # Direction de chaque rayon
    rdx = (player.dx + player.px * cam).astype(np.float32)
    rdy = (player.dy + player.py * cam).astype(np.float32)

    # Cellule de départ
    mx = np.full(N, int(player.x), dtype=np.int32)
    my = np.full(N, int(player.y), dtype=np.int32)

    # delta_dist : distance pour traverser 1 cellule dans chaque axe
    # np.where remplace les valeurs proches de 0 AVANT la division (pas après)
    ddx = np.abs(1.0 / np.where(np.abs(rdx) < _TINY, _TINY, rdx))
    ddy = np.abs(1.0 / np.where(np.abs(rdy) < _TINY, _TINY, rdy))

    # Direction de marche sur la grille
    step_x = np.where(rdx < 0, -1, 1).astype(np.int32)
    step_y = np.where(rdy < 0, -1, 1).astype(np.int32)

    # Distance initiale jusqu'à la première frontière de cellule
    sdx = np.where(rdx < 0,
                   (player.x - mx) * ddx,
                   (mx + 1.0 - player.x) * ddx).astype(np.float32)
    sdy = np.where(rdy < 0,
                   (player.y - my) * ddy,
                   (my + 1.0 - player.y) * ddy).astype(np.float32)

    # DDA loop (entièrement numpy, toutes les colonnes à la fois)
    hit       = np.zeros(N, dtype=bool)
    side      = np.zeros(N, dtype=np.int8)
    wall_type = np.zeros(N, dtype=np.int8)

    for _ in range(MAX_DDA_STEPS):
        if hit.all():
            break

        alive = ~hit
        go_x  = alive & (sdx < sdy)
        go_y  = alive & ~go_x

        # Avancer en X
        sdx = np.where(go_x, sdx + ddx, sdx)
        mx  = np.where(go_x, mx + step_x, mx)
        side = np.where(go_x, 0, side).astype(np.int8)

        # Avancer en Y
        sdy = np.where(go_y, sdy + ddy, sdy)
        my  = np.where(go_y, my + step_y, my)
        side = np.where(go_y, 1, side).astype(np.int8)

        # Clamp hors-carte → mur fictif
        cx = np.clip(mx, 0, MAP_W - 1)
        cy = np.clip(my, 0, MAP_H - 1)

        cell   = grid[cy, cx].astype(np.int8)
        new_hit = alive & ((cell > 0) |
                           (mx < 0) | (mx >= MAP_W) |
                           (my < 0) | (my >= MAP_H))
        wall_type = np.where(new_hit, np.where(cell > 0, cell, 1), wall_type).astype(np.int8)
        hit |= new_hit

    # Distance perpendiculaire (évite l'effet fish-eye)
    perp = np.where(side == 0, sdx - ddx, sdy - ddy).astype(np.float32)
    perp = np.maximum(perp, 0.001)

    # Position fractionnaire sur la face du mur (pour les textures)
    hit_x = np.where(
        side == 0,
        player.y + perp * rdy,
        player.x + perp * rdx,
    )
    wx = (hit_x - np.floor(hit_x)).astype(np.float32)

    return perp, wall_type, side, wx
