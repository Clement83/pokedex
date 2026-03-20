"""
Génération du monde infini – accès procédural tile par tile.
Aucune grille complète en mémoire : la tuile est calculée à la demande.
Seules les modifications joueurs (mine/pose) sont stockées dans un dict.
Perf-first : pas de numpy, Python 3.8 compatible, Odroid GO Advance.
"""
import random
from config import (
    ROWS,
    TILE_AIR, TILE_DIRT, TILE_STONE, TILE_GRASS, TILE_SAND, TILE_WOOD, TILE_COAL, TILE_CHEST,
    SURFACE_Y, TERRAIN_AMPLITUDE, TERRAIN_FREQ, STONE_DEPTH,
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
    x  = col * freq
    ix = int(x)
    t  = x - ix
    t  = t * t * (3 - 2 * t)
    a  = _hash1(ix,     seed)
    b  = _hash1(ix + 1, seed)
    return a + (b - a) * t


def _smooth2(col, row, freq, seed):
    """Bruit 2D bilinéaire smoothstep déterministe."""
    x  = col * freq;  ix = int(x);  tx = x - ix;  tx = tx * tx * (3 - 2 * tx)
    y  = row * freq;  iy = int(y);  ty = y - iy;  ty = ty * ty * (3 - 2 * ty)
    a  = _hash2(ix,     iy,     seed)
    b  = _hash2(ix + 1, iy,     seed)
    c  = _hash2(ix,     iy + 1, seed)
    d  = _hash2(ix + 1, iy + 1, seed)
    return a*(1-tx)*(1-ty) + b*tx*(1-ty) + c*(1-tx)*ty + d*tx*ty


# ── Classe Monde infini ───────────────────────────────────────────────────────

class World:
    """
    Monde procédural infini horizontalement, fini verticalement (ROWS tuiles).
    - Terrain, arbres, caves et charbon générés à la demande pour tout (col, row).
    - Modifications joueurs stockées dans self.mods {(col, row): tile}.
    """

    def __init__(self, seed=None):
        if seed is None:
            seed = random.randint(0, 0xFFFF_FFFF)
        self.seed = int(seed) & 0xFFFF_FFFF
        self.mods = {}    # {(col, row): tile}

    # ── Terrain procédural ────────────────────────────────────────────────

    def surface_at(self, col):
        """Hauteur de la surface naturelle à la colonne col (row depuis le haut)."""
        h1  = _smooth1(col, TERRAIN_FREQ,       self.seed)
        h2  = _smooth1(col, TERRAIN_FREQ * 2.3, self.seed ^ 0xDEAD) * 0.4
        raw = (h1 + h2) / 1.4
        return int(SURFACE_Y + raw * TERRAIN_AMPLITUDE - TERRAIN_AMPLITUDE / 2)

    def _has_tree(self, col):
        return _hash1(col * 31 + 7, self.seed ^ 0xBEEF) < 0.13

    def _tree_height(self, col):
        return 2 + int(_hash1(col * 17 + 3, self.seed ^ 0xBEEF) * 2)   # 2 ou 3

    def _tree_tile(self, col, row):
        """Si (col, row) fait partie d'un arbre, retourne la tuile ; sinon TILE_AIR."""
        for tc in range(col - 2, col + 3):
            if not self._has_tree(tc):
                continue
            ts        = self.surface_at(tc)
            th        = self._tree_height(tc)
            trunk_top = ts - th
            # Tronc
            if col == tc and trunk_top <= row < ts:
                return TILE_WOOD
            # Couronne 5 large × 3 haut, coins coupés
            dc = abs(col - tc)
            dr = row - trunk_top   # relatif au sommet du tronc
            if -2 <= dr <= 1 and dc <= 2:
                if dc == 2 and dr not in (-1, 0):
                    continue
                return TILE_GRASS   # feuilles = vert
        return TILE_AIR

    # ── Cabanes avec coffres ──────────────────────────────────────────────────

    def _cabin_origin(self, col):
        """Retourne la colonne gauche de la cabane dont col fait partie, ou None."""
        # Cabanes espacées toutes ~40 colonnes, largeur 5
        for dc in range(5):
            tc = col - dc
            if _hash1(tc * 73 + 11, self.seed ^ 0xABCD) < 0.025:
                return tc
        return None

    def _cabin_tile(self, col, row):
        """
        Cabane = murs en TILE_WOOD (largeur 5, hauteur 3), sol en TILE_STONE,
        coffre au centre (col+2, surface-1) = TILE_CHEST.
        Retourne la tuile ou TILE_AIR si (col, row) n'est pas dans une cabane.
        """
        origin = self._cabin_origin(col)
        if origin is None:
            return TILE_AIR
        s  = self.surface_at(origin + 2)   # surface au centre de la cabane
        dc = col - origin
        dr = row - (s - 3)                 # dr=0 : toit, dr=2 : plancher
        if not (0 <= dc <= 4 and 0 <= dr <= 3):
            return TILE_AIR
        # Plancher
        if dr == 3:
            return TILE_STONE
        # Murs latéraux et toit
        if dc == 0 or dc == 4 or dr == 0:
            return TILE_WOOD
        # Coffre au centre (dr=2, dc=2)
        if dc == 2 and dr == 2:
            return TILE_CHEST
        return TILE_AIR   # intérieur vide

    def _base_tile(self, col, row):
        """Tuile procédurale sans modifications joueurs."""
        if row <= 0 or row >= ROWS - 1:
            return TILE_STONE
        s = self.surface_at(col)
        if row < s:
            cabin = self._cabin_tile(col, row)
            if cabin != TILE_AIR:
                return cabin
            return self._tree_tile(col, row)
        if row == s:
            # Plancher de cabane prioritaire sur l'herbe
            cabin = self._cabin_tile(col, row)
            if cabin != TILE_AIR:
                return cabin
            is_sand = _hash1(col * 37, self.seed ^ 0x5A4D) < 0.07
            # Coffre rare à la surface (hors sable, hors cabane) ~1/100 colonnes
            if not is_sand and _hash1(col * 137 + 19, self.seed ^ 0xF00D) < 0.010:
                return TILE_CHEST
            return TILE_SAND if is_sand else TILE_GRASS
        if row < s + STONE_DEPTH:
            return TILE_DIRT
        # Cave via bruit 2D
        cave = _smooth2(col, row, 0.18, self.seed ^ 0xCAFE) > 0.67 and row > s + 3
        if cave:
            # Coffre rare sur le sol d'une grotte (tuile du dessous = solide)
            floor_solid = _smooth2(col, row + 1, 0.18, self.seed ^ 0xCAFE) <= 0.67
            if floor_solid and _hash2(col, row, self.seed ^ 0x5E17) < 0.018:
                return TILE_CHEST
            return TILE_AIR
        # Veines de charbon
        if _smooth2(col * 1.3, row * 1.1, 0.22, self.seed ^ 0xC0A1) > 0.80 and row >= s + STONE_DEPTH + 2:
            return TILE_COAL
        return TILE_STONE

    # ── API publique ──────────────────────────────────────────────────────

    def get(self, col, row):
        """Retourne la tuile à (col, row) — modification joueur en priorité."""
        key = (col, row)
        if key in self.mods:
            return self.mods[key]
        if row < 0 or row >= ROWS:
            return TILE_STONE
        return self._base_tile(col, row)

    def set(self, col, row, tile):
        """Enregistre une modification joueur en mémoire."""
        self.mods[(col, row)] = tile

    def chest_loot(self):
        """
        Tire un item d'équipement aléatoire à l'ouverture d'un coffre.
        - Type (tête/corps/pieds) : égalité parfaite
        - Matériau : bois 65 %, fer 28 %, or 7 %
        Retourne (equip_slot, material).
        """
        from config import EQUIP_HEAD, EQUIP_BODY, EQUIP_FEET, MAT_WOOD, MAT_IRON, MAT_GOLD
        equip_slot = random.choice([EQUIP_HEAD, EQUIP_BODY, EQUIP_FEET])
        r = random.random()
        if r < 0.65:
            material = MAT_WOOD
        elif r < 0.93:
            material = MAT_IRON
        else:
            material = MAT_GOLD
        return (equip_slot, material)


def generate(seed=None):
    """Point d'entrée : retourne un World prêt à l'emploi."""
    return World(seed)
