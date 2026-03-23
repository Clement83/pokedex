"""
Caméra et cache de chunks (surfaces pré-rendues pour le rendu du monde).
"""
from collections import OrderedDict
import threading
import queue as _queue
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


# ── Cache de chunks 2D ───────────────────────────────────────────────────────
#
# Chaque chunk = CHUNK_COLS colonnes × CHUNK_ROWS rangées pré-rendus en Surface.
# Clé de cache : (cx, cy).  Seuls les chunks visibles sont construits/gardés.

CHUNK_COLS = 16
CHUNK_ROWS = 16                          # 16×16 tuiles = 256×256 px par chunk
_CHUNK_W   = CHUNK_COLS * TILE_SIZE      # 256 px
_CHUNK_H   = CHUNK_ROWS * TILE_SIZE      # 320 px  (était ROWS×16 = 1920+ px)


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
    _MAX_CHUNKS = 32   # chunks 16×16 tuiles — couvre ~3×3 non-split ou 2×(3×3) split

    def __init__(self, world):
        self._world   = world
        self._cache   = OrderedDict()
        self._pending = set()          # (cx, cy) en cours de calcul côté worker
        self._req_q   = _queue.Queue() # main → worker : demandes
        self._ready_q = _queue.Queue() # worker → main : (cx, cy, tile_array)
        self._worker  = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    # ── Thread de calcul ──────────────────────────────────────────────────────
    # Seul endroit où le worker tourne : pas de pygame, uniquement world.get().

    def _worker_loop(self):
        while True:
            cx, cy = self._req_q.get()
            tiles  = self._compute_tiles(cx, cy)
            self._ready_q.put((cx, cy, tiles))

    def _compute_tiles(self, cx, cy):
        """Calcule les tile IDs (pur Python, aucun appel pygame). Thread-safe."""
        col0   = cx * CHUNK_COLS
        row0   = cy * CHUNK_ROWS
        result = []
        for dr in range(CHUNK_ROWS):
            row = row0 + dr
            row_tiles = []
            for dc in range(CHUNK_COLS):
                col = col0 + dc
                row_tiles.append(self._world.get(col, row) if row < ROWS else TILE_AIR)
            result.append(row_tiles)
        return result

    # ── Rendu (main thread uniquement) ───────────────────────────────────────

    def _render_tiles(self, tiles):
        """Construit la pygame.Surface depuis les tile IDs. Main thread only."""
        surf = pygame.Surface((_CHUNK_W, _CHUNK_H))
        ts   = TILE_SIZE
        for dr, row_tiles in enumerate(tiles):
            for dc, tile in enumerate(row_tiles):
                x = dc * ts
                y = dr * ts
                if tile == TILE_CHEST:
                    _draw_chest_tile(surf, x, y)
                else:
                    color = TILE_COLORS[tile]
                    surf.fill(color, (x, y, ts, ts))
                    if tile != TILE_AIR:
                        pygame.draw.rect(surf, (0, 0, 0), (x, y, ts, ts), 1)
        return surf.convert()   # format pixel de l'écran → blits plus rapides

    def flush_ready(self):
        """Intègre les chunks calculés en background. Appelé une fois par frame depuis le main thread."""
        while True:
            try:
                cx, cy, tiles = self._ready_q.get_nowait()
                key = (cx, cy)
                self._pending.discard(key)
                if key not in self._cache:   # ne pas écraser un update_tile récent
                    surf = self._render_tiles(tiles)
                    if len(self._cache) >= self._MAX_CHUNKS:
                        self._cache.popitem(last=False)
                    self._cache[key] = surf
            except _queue.Empty:
                break

    # ── API publique ──────────────────────────────────────────────────────────

    def get(self, cx, cy):
        key = (cx, cy)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        # Soumettre au worker si pas déjà en attente
        if key not in self._pending:
            self._pending.add(key)
            self._req_q.put((cx, cy))
        return None   # pas encore prêt — draw_world ignore ce chunk pour cette frame

    def update_tile(self, col, row, tile):
        """Met à jour une seule tuile dans le chunk en cache — sans rebuild complet."""
        key = (col // CHUNK_COLS, row // CHUNK_ROWS)
        if key not in self._cache:
            return  # pas encore en cache, sera construit correctement à la prochaine frame
        surf = self._cache[key]
        dc = col % CHUNK_COLS
        dr = row % CHUNK_ROWS
        x  = dc * TILE_SIZE
        y  = dr * TILE_SIZE
        ts = TILE_SIZE
        if tile == TILE_CHEST:
            _draw_chest_tile(surf, x, y)
        else:
            color = TILE_COLORS[tile]
            surf.fill(color, (x, y, ts, ts))
            if tile != TILE_AIR:
                pygame.draw.rect(surf, (0, 0, 0), (x, y, ts, ts), 1)

    def invalidate(self, col, row=None):
        if row is None:
            cx = col // CHUNK_COLS
            for k in [k for k in self._cache if k[0] == cx]:
                self._cache.pop(k)
            self._pending = {k for k in self._pending if k[0] != cx}
        else:
            key = (col // CHUNK_COLS, row // CHUNK_ROWS)
            self._cache.pop(key, None)
            self._pending.discard(key)

    def preload_around(self, cam_x, cam_y_or_view_w=0, view_w=None, view_h=SCREEN_HEIGHT):
        # Compat ancienne signature: preload_around(cam_x, view_w)
        if view_w is None:
            view_w = cam_y_or_view_w
            cam_y  = 0
        else:
            cam_y  = cam_y_or_view_w
        cx0 = int(cam_x) // _CHUNK_W - 1
        cx1 = (int(cam_x) + view_w) // _CHUNK_W + 1
        cy0 = max(0, int(cam_y) // _CHUNK_H - 1)
        cy1 = (int(cam_y) + view_h) // _CHUNK_H + 1
        for cy in range(cy0, cy1 + 1):
            for cx in range(cx0, cx1 + 1):
                key = (cx, cy)
                if key not in self._cache and key not in self._pending:
                    self._pending.add(key)
                    self._req_q.put((cx, cy))
