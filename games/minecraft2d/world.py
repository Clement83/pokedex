"""
Génération du monde infini – accès procédural tile par tile.
Aucune grille complète en mémoire : la tuile est calculée à la demande.
Seules les modifications joueurs (mine/pose) sont stockées dans un dict.
Perf-first : pas de numpy, Python 3.8 compatible, Odroid GO Advance.
"""
import random
from config import (
    ROWS,
    TILE_AIR, TILE_DIRT, TILE_STONE, TILE_GRASS, TILE_SAND, TILE_WOOD, TILE_COAL,
    TILE_BRICK, TILE_CHEST, TILE_OBSIDIAN, TILE_GLASS,
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


# ── Structures procédurales ───────────────────────────────────────────────────
#
# Une structure est définie comme un dict {(dc, dr): tile} dont l'ancre (0,0)
# est le coin supérieur-gauche.  Les coordonnées négatives sont à gauche / au-dessus.
# Les structures aériennes sont ancrées sur la rangée de surface ;
# les souterraines sont ancrées à surface + offset profondeur.

def _build_castle(col, seed):
    """Château médiéval ~11×9 blocs. Ancre = coin bas-gauche de la base."""
    # Tour gauche (3 large × 9 haut), corps central (5 large × 6 haut), tour droite
    blocks = {}
    W = 11   # largeur totale

    # Remplissage intérieur air (nettoie le terrain pour dégager l'espace)
    for dc in range(1, W - 1):
        for dr in range(-8, 0):
            blocks[(dc, dr)] = TILE_AIR

    # Murs extérieurs
    for dr in range(-8, 1):
        blocks[(0, dr)]      = TILE_BRICK
        blocks[(W - 1, dr)]  = TILE_BRICK
    for dc in range(W):
        blocks[(dc, 0)]  = TILE_BRICK  # base
        blocks[(dc, -8)] = TILE_BRICK  # toit

    # Mur central gauche / droite (divise tours du corps)
    for dr in range(-5, 0):
        blocks[(2, dr)]      = TILE_BRICK
        blocks[(W - 3, dr)]  = TILE_BRICK

    # Portes (vides au sol)
    for dc in (4, 5, 6):
        blocks[(dc, 0)]  = TILE_AIR
        blocks[(dc, -1)] = TILE_AIR

    # Fenêtres dans le corps central
    blocks[(4, -4)] = TILE_GLASS
    blocks[(6, -4)] = TILE_GLASS

    # Créneaux du toit (alternés)
    for dc in range(0, W, 2):
        blocks[(dc, -9)] = TILE_BRICK

    # Coffre dans la tour droite (accès par la porte + couloir)
    blocks[(W - 2, -1)] = TILE_CHEST

    return blocks


def _build_pirate_ship(col, seed):
    """Épave de navire pirate ~14×8. Ancre = plancher de cale (sous-sol du bateau)."""
    blocks = {}
    # Coque en bois – forme ellipsoïde grossière
    hull = [
        # (dc, dr, tile)
        # Fond de cale (-3 à -1)
        *[(dc, dr, TILE_WOOD) for dc in range(1, 13) for dr in (-1, 0)],
        # Flancs gauche/droit
        *[(0, dr, TILE_WOOD) for dr in range(-6, 0)],
        *[(13, dr, TILE_WOOD) for dr in range(-6, 0)],
    ]
    for dc, dr, tile in hull:
        blocks[(dc, dr)] = tile

    # Pont
    for dc in range(1, 13):
        blocks[(dc, -2)] = TILE_WOOD
    # Trou dans le pont (descente cale)
    blocks[(6, -2)] = TILE_AIR
    blocks[(7, -2)] = TILE_AIR

    # Intérieur cale dégagé
    for dc in range(1, 13):
        blocks[(dc, -1)] = TILE_AIR

    # Mât (bois au centre, s'élève de -2 à -7)
    for dr in range(-8, -1):
        blocks[(7, dr)] = TILE_WOOD
    # Voile en bois (2 large × 3 haut, accrochée au mât)
    for dr in range(-7, -4):
        blocks[(5, dr)] = TILE_WOOD
        blocks[(6, dr)] = TILE_WOOD

    # Vigie (petite cabane au sommet du mât)
    blocks[(6, -8)]  = TILE_WOOD
    blocks[(7, -9)]  = TILE_WOOD
    blocks[(8, -8)]  = TILE_WOOD

    # Coffre dans la cale
    blocks[(3, 0)] = TILE_CHEST
    blocks[(10, 0)] = TILE_CHEST

    # Trou dans la coque gauche (effet naufrage)
    blocks[(0, -3)] = TILE_AIR
    blocks[(0, -2)] = TILE_AIR

    return blocks


def _build_dungeon(col, surface, seed):
    """Donjon souterrain ~9×5. Ancre = coin supérieur-gauche du couloir."""
    blocks = {}
    W, H = 9, 5
    # Couloir principal
    for dc in range(W):
        blocks[(dc, 0)]      = TILE_BRICK  # plafond
        blocks[(dc, H - 1)]  = TILE_OBSIDIAN  # sol obsidienne
    for dr in range(1, H - 1):
        blocks[(0, dr)]      = TILE_BRICK
        blocks[(W - 1, dr)]  = TILE_BRICK
    # Intérieur vide
    for dc in range(1, W - 1):
        for dr in range(1, H - 1):
            blocks[(dc, dr)] = TILE_AIR
    # Coffre central
    blocks[(4, H - 2)] = TILE_CHEST
    # Piliers charbon (décoratifs / obstacles)
    blocks[(2, H - 2)] = TILE_COAL
    blocks[(6, H - 2)] = TILE_COAL
    # Entrée (trou dans le plafond à gauche)
    blocks[(1, 0)] = TILE_AIR
    blocks[(2, 0)] = TILE_AIR
    return blocks


def _build_pyramid(col, seed):
    """Pyramide aztèque ~11×6. Ancre = coin bas-gauche au niveau du sol."""
    blocks = {}
    levels = [
        (0, 11),  # base  dr=0 : 11 large
        (1,  9),  # dr=-1 :  9 large (décalé de 1)
        (2,  7),
        (3,  5),
        (4,  3),
        (5,  1),  # sommet
    ]
    for dr_neg, width in levels:
        offset = (11 - width) // 2
        for dc in range(offset, offset + width):
            blocks[(dc, -dr_neg)] = TILE_BRICK

    # Crypte sous la pyramide (3 de large × 3 de prof, centrée)
    for dc in range(4, 7):
        for dr in range(1, 4):
            blocks[(dc, dr)] = TILE_AIR
    # Sol obsidienne de la crypte
    for dc in range(4, 7):
        blocks[(dc, 4)] = TILE_OBSIDIAN
    # Coffre dans la crypte
    blocks[(5, 3)] = TILE_CHEST
    return blocks


# ── Catalogue des structures de surface ──────────────────────────────────────
#
# Chaque entrée : (id_unique, probabilité_par_colonne, espace_min_entre_structures)
# La probability est vérifiée via _hash1 sur la colonne candidate.

_STRUCTURES = [
    # (tag,       prob,    min_gap, builder_fn)
    ("castle",   0.003,   120,  _build_castle),
    ("ship",     0.004,   100,  _build_pirate_ship),
    ("pyramid",  0.003,   110,  _build_pyramid),
]


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
        self._struct_cache = {}   # {col_anchor: {(col, row): tile}} – structures déjà calculées

    # ── Structures procédurales ───────────────────────────────────────────

    def _structure_at(self, anchor_col):
        """Retourne le dict {(col, row): tile} de la structure ancrée en anchor_col, ou {}."""
        if anchor_col in self._struct_cache:
            return self._struct_cache[anchor_col]

        result = {}
        for tag, prob, min_gap, builder in _STRUCTURES:
            tag_seed = sum(ord(c) for c in tag)
            if _hash1(anchor_col * 97 + tag_seed, self.seed ^ 0xF00D) >= prob:
                continue
            # Vérifier espacement minimal
            ok = True
            for dc2 in range(-min_gap, 0):
                c2 = anchor_col + dc2
                if _hash1(c2 * 97 + tag_seed, self.seed ^ 0xF00D) < prob:
                    ok = False
                    break
            if not ok:
                continue

            s = self.surface_at(anchor_col)
            blocks = builder(anchor_col, self.seed)
            for (dc, dr), tile in blocks.items():
                result[(anchor_col + dc, s + dr)] = tile
            break  # une seule structure par ancre

        self._struct_cache[anchor_col] = result
        return result

    def _dungeon_at(self, anchor_col):
        """Retourne le dict {(col, row): tile} du donjon ancré en anchor_col, ou {}."""
        key = ("dng", anchor_col)
        if key in self._struct_cache:
            return self._struct_cache[key]

        result = {}
        tag_seed = 0xD0C
        prob = 0.006
        min_gap = 90
        if _hash1(anchor_col * 53 + tag_seed, self.seed ^ 0xBAAD) < prob:
            # Vérifier espacement
            ok = True
            for dc2 in range(-min_gap, 0):
                if _hash1((anchor_col + dc2) * 53 + tag_seed, self.seed ^ 0xBAAD) < prob:
                    ok = False
                    break
            if ok:
                s = self.surface_at(anchor_col)
                depth_offset = STONE_DEPTH + 5 + int(_hash1(anchor_col * 7, self.seed ^ 0xD0D) * 5)
                base_row = s + depth_offset
                blocks = _build_dungeon(anchor_col, s, self.seed)
                for (dc, dr), tile in blocks.items():
                    result[(anchor_col + dc, base_row + dr)] = tile

        self._struct_cache[key] = result
        return result

    def _struct_tile(self, col, row):
        """Cherche si (col, row) appartient à une structure proche. Retourne la tuile ou None."""
        s = self.surface_at(col)
        # Structures de surface : ancres dans col-20..col
        for ac in range(col - 20, col + 1):
            blocks = self._structure_at(ac)
            if (col, row) in blocks:
                return blocks[(col, row)]
        # Donjon souterrain : ancres dans col-12..col
        if row > s + STONE_DEPTH:
            for ac in range(col - 12, col + 1):
                blocks = self._dungeon_at(ac)
                if (col, row) in blocks:
                    return blocks[(col, row)]
        return None

    # ── Terrain procédural ────────────────────────────────────────────────

    def surface_at(self, col):
        """Hauteur de la surface naturelle à la colonne col (row depuis le haut)."""
        h1  = _smooth1(col, TERRAIN_FREQ,       self.seed)
        h2  = _smooth1(col, TERRAIN_FREQ * 2.3, self.seed ^ 0xDEAD) * 0.4
        raw = (h1 + h2) / 1.4
        return int(SURFACE_Y + raw * TERRAIN_AMPLITUDE - TERRAIN_AMPLITUDE / 2)

    def _has_tree(self, col):
        return _hash1(col * 31 + 7, self.seed ^ 0xBEEF) < 0.06

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

        # Structures procédurales (priorité sur tout le reste)
        st = self._struct_tile(col, row)
        if st is not None:
            return st

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
