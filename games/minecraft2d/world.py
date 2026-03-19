"""
Génération du monde et gestion des tuiles.
Perf-first : pas de numpy, Python 3.8 compatible, Odroid GO Advance.
Seed reproductible : deux seeds identiques = monde identique.
"""
import random
from config import (
    COLS, ROWS,
    TILE_AIR, TILE_DIRT, TILE_STONE, TILE_GRASS, TILE_SAND, TILE_WOOD, TILE_COAL,
    SURFACE_Y, TERRAIN_AMPLITUDE, TERRAIN_FREQ, STONE_DEPTH,
    CAVE_PROB, CAVE_ITERATIONS,
)


def _hash_seed(n, seed):
    """Hash déterministe dépendant du seed – produit un float dans [0, 1]."""
    n = n + seed * 0x9E3779B9
    n = (n ^ (n >> 16)) & 0xFFFF_FFFF
    n = (n * 0x45D9F3B) & 0xFFFF_FFFF
    n = (n ^ (n >> 16)) & 0xFFFF_FFFF
    return (n & 0xFFFF) / 0xFFFF


def _smooth_noise(x, freq, seed):
    """Bruit 1D lissé (interpolation smoothstep) dépendant du seed."""
    ix = int(x * freq * 10)
    t  = (x * freq * 10) - ix
    t2 = t * t * (3 - 2 * t)
    a  = _hash_seed(ix,     seed)
    b  = _hash_seed(ix + 1, seed)
    return a + (b - a) * t2


def generate(seed=None):
    """
    Génère le monde et retourne :
      grid   : list[list[int]]   (ROWS × COLS)
      surface: list[int]         hauteur de surface par colonne
      seed   : int               seed utilisé (utile pour l'afficher)
    """
    if seed is None:
        seed = random.randint(0, 0xFFFF_FFFF)

    seed = int(seed) & 0xFFFF_FFFF
    rng  = random.Random(seed)

    # ── Hauteur de surface ─────────────────────────────────────────────────
    # Deux octaves de bruit pour un relief naturel, tout seedé
    surface = []
    for col in range(COLS):
        h1 = _smooth_noise(col, TERRAIN_FREQ,       seed)
        h2 = _smooth_noise(col, TERRAIN_FREQ * 2.3, seed ^ 0xDEAD) * 0.4
        raw = (h1 + h2) / 1.4
        surface.append(int(SURFACE_Y + raw * TERRAIN_AMPLITUDE - TERRAIN_AMPLITUDE / 2))

    # ── Remplissage de base ────────────────────────────────────────────────
    grid = [[TILE_AIR] * COLS for _ in range(ROWS)]

    for col in range(COLS):
        s = surface[col]
        for row in range(ROWS):
            if row < s:
                grid[row][col] = TILE_AIR
            elif row == s:
                grid[row][col] = TILE_GRASS
            elif row < s + STONE_DEPTH:
                grid[row][col] = TILE_DIRT
            else:
                grid[row][col] = TILE_STONE

    # ── Poches de sable en surface ─────────────────────────────────────────
    for col in range(COLS):
        if rng.random() < 0.08:
            s = surface[col]
            for row in range(s, min(s + rng.randint(2, 4), ROWS)):
                grid[row][col] = TILE_SAND

    # ── Veines de charbon ─────────────────────────────────────────────────
    for _ in range(COLS // 5):
        col = rng.randint(2, COLS - 3)
        row = rng.randint(SURFACE_Y + STONE_DEPTH, ROWS - 3)
        for dc in range(-1, 2):
            for dr in range(-1, 2):
                nc, nr = col + dc, row + dr
                if 0 <= nc < COLS and 0 <= nr < ROWS and grid[nr][nc] == TILE_STONE:
                    grid[nr][nc] = TILE_COAL

    # ── Caves (automate cellulaire seedé) ─────────────────────────────────
    cave = [[False] * COLS for _ in range(ROWS)]
    for col in range(COLS):
        for row in range(surface[col] + 4, ROWS - 1):
            cave[row][col] = rng.random() < CAVE_PROB

    for _ in range(CAVE_ITERATIONS):
        new = [[False] * COLS for _ in range(ROWS)]
        for row in range(1, ROWS - 1):
            for col in range(1, COLS - 1):
                count = sum(
                    cave[row + dr][col + dc]
                    for dr in (-1, 0, 1)
                    for dc in (-1, 0, 1)
                    if not (dr == 0 and dc == 0)
                )
                new[row][col] = count >= 5 if cave[row][col] else count >= 4
        cave = new

    for row in range(ROWS):
        for col in range(COLS):
            if row > surface[col] + 2 and cave[row][col]:
                grid[row][col] = TILE_AIR

    # ── Plafond de roche solide ────────────────────────────────────────────
    for col in range(COLS):
        grid[0][col] = TILE_STONE
        grid[ROWS - 1][col] = TILE_STONE

    return grid, surface, seed
