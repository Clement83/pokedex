"""
Fonctions de bruit déterministe et constructeurs de structures procédurales.
Extrait de world.py pour garder les fichiers sous 300 lignes.
"""
from config import (
    TILE_AIR, TILE_STONE, TILE_WOOD, TILE_COAL,
    TILE_BRICK, TILE_CHEST, TILE_OBSIDIAN, TILE_GLASS,
    TILE_SAND, TILE_SNOW, TILE_ICE, TILE_GOLD_ORE,
)


# ── Bruit déterministe ────────────────────────────────────────────────────────

def _hash1(n, seed):
    n = (n + seed * 0x9E3779B9) & 0xFFFF_FFFF
    n = (n ^ (n >> 16)) & 0xFFFF_FFFF
    n = (n * 0x45D9F3B) & 0xFFFF_FFFF
    n = (n ^ (n >> 16)) & 0xFFFF_FFFF
    return (n & 0xFFFF) / 0xFFFF


def _hash2(x, y, seed):
    n = (x + y * 2971 + seed * 0x9E3779B9) & 0xFFFF_FFFF
    n = (n ^ (n >> 16)) & 0xFFFF_FFFF
    n = (n * 0x45D9F3B) & 0xFFFF_FFFF
    n = (n ^ (n >> 16)) & 0xFFFF_FFFF
    return (n & 0xFFFF) / 0xFFFF


def _smooth1(col, freq, seed):
    """Bruit 1D smoothstep déterministe."""
    x  = col * freq; ix = int(x); t = x - ix; t = t * t * (3 - 2 * t)
    return _hash1(ix, seed) + (_hash1(ix + 1, seed) - _hash1(ix, seed)) * t


def _smooth2(col, row, freq, seed):
    """Bruit 2D bilinéaire smoothstep déterministe."""
    x  = col * freq;  ix = int(x);  tx = x - ix;  tx = tx * tx * (3 - 2 * tx)
    y  = row * freq;  iy = int(y);  ty = y - iy;  ty = ty * ty * (3 - 2 * ty)
    a  = _hash2(ix,     iy,     seed)
    b  = _hash2(ix + 1, iy,     seed)
    c  = _hash2(ix,     iy + 1, seed)
    d  = _hash2(ix + 1, iy + 1, seed)
    return a*(1-tx)*(1-ty) + b*tx*(1-ty) + c*(1-tx)*ty + d*tx*ty


# ── Constructeurs de structures ───────────────────────────────────────────────

def _build_castle(col, seed):
    """Château médiéval ~11×9 blocs."""
    blocks = {}; W = 11
    for dc in range(1, W - 1):
        for dr in range(-8, 0): blocks[(dc, dr)] = TILE_AIR
    for dr in range(-8, 1):
        blocks[(0, dr)] = TILE_BRICK; blocks[(W-1, dr)] = TILE_BRICK
    for dc in range(W):
        blocks[(dc, 0)] = TILE_BRICK; blocks[(dc, -8)] = TILE_BRICK
    for dr in range(-5, 0):
        blocks[(2, dr)] = TILE_BRICK; blocks[(W-3, dr)] = TILE_BRICK
    for dc in (4, 5, 6):
        blocks[(dc, 0)] = TILE_AIR; blocks[(dc, -1)] = TILE_AIR
    blocks[(4, -4)] = TILE_GLASS; blocks[(6, -4)] = TILE_GLASS
    for dc in range(0, W, 2): blocks[(dc, -9)] = TILE_BRICK
    blocks[(W - 2, -1)] = TILE_CHEST
    return blocks


def _build_pirate_ship(col, seed):
    """Épave de navire pirate ~14×8."""
    blocks = {}
    for dc in range(1, 13):
        for dr in (-1, 0): blocks[(dc, dr)] = TILE_WOOD
    for dr in range(-6, 0):
        blocks[(0, dr)] = TILE_WOOD; blocks[(13, dr)] = TILE_WOOD
    for dc in range(1, 13): blocks[(dc, -2)] = TILE_WOOD
    blocks[(6, -2)] = TILE_AIR; blocks[(7, -2)] = TILE_AIR
    for dc in range(1, 13): blocks[(dc, -1)] = TILE_AIR
    for dr in range(-8, -1): blocks[(7, dr)] = TILE_WOOD
    for dr in range(-7, -4):
        blocks[(5, dr)] = TILE_WOOD; blocks[(6, dr)] = TILE_WOOD
    blocks[(6, -8)] = TILE_WOOD; blocks[(7, -9)] = TILE_WOOD; blocks[(8, -8)] = TILE_WOOD
    blocks[(3, 0)] = TILE_CHEST; blocks[(10, 0)] = TILE_CHEST
    blocks[(0, -3)] = TILE_AIR; blocks[(0, -2)] = TILE_AIR
    return blocks


def _build_dungeon(col, surface, seed):
    """Donjon souterrain ~9×5."""
    blocks = {}; W, H = 9, 5
    for dc in range(W):
        blocks[(dc, 0)] = TILE_BRICK; blocks[(dc, H-1)] = TILE_OBSIDIAN
    for dr in range(1, H-1):
        blocks[(0, dr)] = TILE_BRICK; blocks[(W-1, dr)] = TILE_BRICK
    for dc in range(1, W-1):
        for dr in range(1, H-1): blocks[(dc, dr)] = TILE_AIR
    blocks[(4, H-2)] = TILE_CHEST
    blocks[(2, H-2)] = TILE_COAL; blocks[(6, H-2)] = TILE_COAL
    blocks[(1, 0)] = TILE_AIR; blocks[(2, 0)] = TILE_AIR
    return blocks


def _build_pyramid(col, seed):
    """Pyramide aztèque ~11×6."""
    blocks = {}
    for dr_neg, width in [(0,11),(1,9),(2,7),(3,5),(4,3),(5,1)]:
        offset = (11 - width) // 2
        for dc in range(offset, offset + width): blocks[(dc, -dr_neg)] = TILE_BRICK
    for dc in range(4, 7):
        for dr in range(1, 4): blocks[(dc, dr)] = TILE_AIR
    for dc in range(4, 7): blocks[(dc, 4)] = TILE_OBSIDIAN
    blocks[(5, 3)] = TILE_CHEST
    return blocks


def _build_great_pyramid(col, seed):
    """Grande pyramide du désert ~21×12, salle intérieure avec trésor."""
    blocks = {}
    W = 21
    # Forme pyramidale extérieure (11 niveaux)
    for level in range(11):
        width = W - level * 2
        offset = level
        for dc in range(offset, offset + width):
            blocks[(dc, -level)] = TILE_SAND
    # Sommet en or
    blocks[(10, -11)] = TILE_GOLD_ORE
    # Salle intérieure creuse (7×4)
    for dc in range(7, 14):
        for dr in range(-5, -1):
            blocks[(dc, dr)] = TILE_AIR
    # Sol de la salle en obsidienne
    for dc in range(7, 14):
        blocks[(dc, -1)] = TILE_OBSIDIAN
    # Entrée latérale
    for dr in range(-2, 0):
        blocks[(6, dr)] = TILE_AIR
    # Coffres (2 dans la salle)
    blocks[(9, -2)] = TILE_CHEST
    blocks[(12, -2)] = TILE_CHEST
    # Piliers décoratifs
    for dr in range(-5, -1):
        blocks[(8, dr)] = TILE_SAND
        blocks[(13, dr)] = TILE_SAND
    return blocks


def _build_igloo(col, seed):
    """Igloo en neige/glace ~7×5, petit abri avec coffre."""
    blocks = {}
    # Dôme en neige
    #     XXX       dr=-3
    #    XXXXX      dr=-2
    #   XXXXXXX     dr=-1
    #   X     X     dr=0 (murs)
    #   XXXXXXX     dr=1 (sol)
    for dc in range(2, 5):
        blocks[(dc, -3)] = TILE_SNOW
    for dc in range(1, 6):
        blocks[(dc, -2)] = TILE_SNOW
    for dc in range(0, 7):
        blocks[(dc, -1)] = TILE_SNOW
    # Murs
    blocks[(0, 0)] = TILE_ICE
    blocks[(6, 0)] = TILE_ICE
    # Sol en glace
    for dc in range(0, 7):
        blocks[(dc, 1)] = TILE_ICE
    # Intérieur creux
    for dc in range(1, 6):
        blocks[(dc, 0)] = TILE_AIR
    # Entrée
    blocks[(0, 0)] = TILE_AIR
    # Coffre
    blocks[(4, 0)] = TILE_CHEST
    return blocks


# ── Catalogue des structures de surface ──────────────────────────────────────

_STRUCTURES = [
    ("castle",        0.003, 120, _build_castle),
    ("ship",          0.004, 100, _build_pirate_ship),
    ("pyramid",       0.003, 110, _build_pyramid),
    ("great_pyramid", 0.005,  80, _build_great_pyramid),
    ("igloo",         0.008,  40, _build_igloo),
]
