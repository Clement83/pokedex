"""
Caméra et cache de chunks (surfaces pré-rendues pour le rendu du monde).
"""
from collections import OrderedDict
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, ROWS,
    TILE_AIR, TILE_COLORS, TILE_CHEST,
)

# ── Caméra ────────────────────────────────────────────────────────────────────

class Camera:
    """Caméra centrée sur un point, en pixels."""

    def __init__(self, view_w=SCREEN_WIDTH, view_h=SCREEN_HEIGHT):
        self.x      = 0.0
        self.y      = 0.0
        self.view_w = view_w
        self.view_h = view_h

    def follow(self, target_px, target_py, dt):
        cx = target_px - self.view_w // 2
        cy = target_py - self.view_h // 2
        max_y = ROWS * TILE_SIZE - self.view_h
        cx = max(0, cx)
        cy = max(0, min(cy, max_y))
        self.x += (cx - self.x) * min(1.0, 8.0 * dt)
        self.y += (cy - self.y) * min(1.0, 8.0 * dt)

    def world_to_screen(self, wx_px, wy_px):
        return int(wx_px - self.x), int(wy_px - self.y)

    def screen_to_tile(self, sx, sy):
        return int((sx + self.x) // TILE_SIZE), int((sy + self.y) // TILE_SIZE)

    def visible_tile_range(self):
        c0 = int(self.x // TILE_SIZE)
        r0 = max(0, int(self.y // TILE_SIZE))
        c1 = c0 + self.view_w // TILE_SIZE + 2
        r1 = min(ROWS, r0 + self.view_h // TILE_SIZE + 2)
        return c0, r0, c1, r1


# ── Cache de chunks ───────────────────────────────────────────────────────────
#
# Chaque chunk = 30 colonnes × ROWS rangées pré-rendus en Surface pygame.
# Invalider un chunk quand un bloc y est modifié.

CHUNK_COLS = 30
_CHUNK_W   = CHUNK_COLS * TILE_SIZE   # 480 px
_CHUNK_H   = ROWS       * TILE_SIZE   # 960 px


def _draw_chest_tile(surf, x, y):
    """Coffre pixel-art 16×16 sur la Surface surf en (x, y)."""
    _C_BK = ( 30,  15,   5)
    _C_GD = (215, 165,   5)
    _C_BR = (115,  65,  20)
    _C_WH = (220, 205, 175)
    dr = surf.fill
    dr(_C_BR,  (x,     y,     16, 16))
    pygame.draw.rect(surf, _C_BK, (x,   y,   16, 16), 1)
    pygame.draw.rect(surf, _C_GD, (x+1, y+1, 14, 14), 1)
    dr(_C_GD,  (x+1,  y+6,  14,  1))
    lx = x + 7
    dr(_C_BK,  (lx,   y+5,   3,   3))
    dr(_C_GD,  (lx,   y+5,   3,   1))
    dr(_C_WH,  (lx+1, y+6,   1,   1))
    dr(_C_WH,  (x+3,  y+2,   4,   1))
    dr(_C_WH,  (x+3,  y+3,   1,   2))
    dr(_C_WH,  (x+3,  y+8,   4,   1))
    dr(_C_WH,  (x+3,  y+9,   1,   2))
    dr(_C_GD,  (x+2,  y+14,  2,   1))
    dr(_C_GD,  (x+12, y+14,  2,   1))


class ChunkCache:
    _MAX_CHUNKS = 8

    def __init__(self, world):
        self._world = world
        self._cache = OrderedDict()

    def _build(self, cx):
        surf = pygame.Surface((_CHUNK_W, _CHUNK_H))
        ts   = TILE_SIZE
        col0 = cx * CHUNK_COLS
        for row in range(ROWS):
            for dc in range(CHUNK_COLS):
                col  = col0 + dc
                tile = self._world.get(col, row)
                x    = dc * ts
                y    = row * ts
                if tile == TILE_CHEST:
                    _draw_chest_tile(surf, x, y)
                else:
                    color = TILE_COLORS[tile]
                    surf.fill(color, (x, y, ts, ts))
                    if tile != TILE_AIR:
                        pygame.draw.rect(surf, (0, 0, 0), (x, y, ts, ts), 1)
        if len(self._cache) >= self._MAX_CHUNKS:
            self._cache.popitem(last=False)
        self._cache[cx] = surf
        return surf

    def get(self, cx):
        if cx in self._cache:
            self._cache.move_to_end(cx)
            return self._cache[cx]
        return self._build(cx)

    def invalidate(self, col):
        self._cache.pop(col // CHUNK_COLS, None)

    def preload_around(self, cam_x, view_w):
        cx0 = int(cam_x) // _CHUNK_W - 1
        cx1 = (int(cam_x) + view_w) // _CHUNK_W + 1
        for cx in range(cx0, cx1 + 1):
            if cx not in self._cache:
                self._build(cx)
