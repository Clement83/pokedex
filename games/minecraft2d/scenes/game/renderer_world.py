"""
Rendu du monde : tuiles via cache de chunks, curseur et drapeau de respawn.
"""
import pygame
from config import TILE_SIZE, ROWS, BREAK_BAR_COLOR

from scenes.game.camera import ChunkCache, _CHUNK_W, _CHUNK_H

_CURSOR_SURF = None   # pré-allouée au premier appel


def draw_world(screen, chunks: ChunkCache, camera, break_info):
    """Rendu du terrain via blit de chunks 2D. Aussi dessine la barre de cassage."""
    w      = screen.get_width()
    h      = screen.get_height()
    ts     = TILE_SIZE
    cam_x  = int(camera.x)
    cam_y  = int(camera.y)
    cx0    = cam_x // _CHUNK_W
    cx1    = (cam_x + w - 1) // _CHUNK_W
    cy0    = max(0, cam_y // _CHUNK_H)
    cy1    = (cam_y + h - 1) // _CHUNK_H
    for cy in range(cy0, cy1 + 1):
        for cx in range(cx0, cx1 + 1):
            surf   = chunks.get(cx, cy)
            dest_x = cx * _CHUNK_W - cam_x
            dest_y = cy * _CHUNK_H - cam_y
            screen.blit(surf, (dest_x, dest_y))

    if break_info:
        col, row, progress = break_info
        sx, sy = camera.world_to_screen(col * ts, row * ts)
        pygame.draw.rect(screen, (0, 0, 0),       (sx, sy + ts - 3, ts, 3))
        pygame.draw.rect(screen, BREAK_BAR_COLOR, (sx, sy + ts - 3, int(ts * progress), 3))


def draw_cursor(screen, player, col, row, camera):
    global _CURSOR_SURF
    sx, sy = camera.world_to_screen(col * TILE_SIZE, row * TILE_SIZE)
    ts = TILE_SIZE
    if _CURSOR_SURF is None:
        _CURSOR_SURF = pygame.Surface((ts, ts))
        _CURSOR_SURF.fill((255, 255, 0))
    t = pygame.time.get_ticks()
    alpha = 128 + int(127 * abs((t % 600) / 300 - 1))
    _CURSOR_SURF.set_alpha(alpha)
    screen.blit(_CURSOR_SURF, (sx, sy))


def draw_flag_in_world(screen, flag_x, flag_y, color, camera):
    """Drapeau posé dans le monde (hampe + triangle)."""
    px = int(flag_x * TILE_SIZE)
    py = int(flag_y * TILE_SIZE)
    sx, sy = camera.world_to_screen(px, py - 14)
    R    = pygame.draw.rect
    POLE = (160, 130, 80)
    R(screen, POLE,  (sx,     sy,      2, 14))
    R(screen, color, (sx + 2, sy,      7,  3))
    R(screen, color, (sx + 2, sy + 3,  5,  2))
    R(screen, color, (sx + 2, sy + 5,  3,  2))
    R(screen, (220, 200, 120), (sx, sy - 2, 2, 2))
