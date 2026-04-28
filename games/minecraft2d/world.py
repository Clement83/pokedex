"""
Génération du monde infini – accès procédural tile par tile.
Seules les modifications joueurs (mine/pose) sont stockées dans un dict.
"""
import random
from config import (
    ROWS,
    TILE_AIR, TILE_DIRT, TILE_STONE, TILE_GRASS, TILE_SAND, TILE_WOOD, TILE_COAL,
    TILE_IRON_ORE, TILE_GOLD_ORE, TILE_DIAMOND_ORE, TILE_CHEST,
    TILE_SNOW, TILE_ICE, TILE_LAVA, TILE_WATER, TILE_BOOK,
    SURFACE_Y, TERRAIN_AMPLITUDE, TERRAIN_FREQ, STONE_DEPTH,
    BIOME_FOREST, BIOME_DESERT, BIOME_ICE, BIOME_JUNGLE, BIOME_FREQ,
    BIOME_JUNGLE_THRESHOLD,
)
from world_builders import (
    _hash1, _hash2, _smooth1, _smooth2,
    _build_dungeon, _STRUCTURES,
)


# Structures autorisées par biome
_STRUCTURE_BIOMES = {
    "castle":        (BIOME_FOREST, BIOME_ICE),
    "ship":          (BIOME_FOREST, BIOME_DESERT),
    "pyramid":       (BIOME_DESERT,),
    "great_pyramid": (BIOME_DESERT,),
    "igloo":         (BIOME_ICE,),
}


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

    # ── Biomes ────────────────────────────────────────────────────────────

    def biome_at(self, col):
        """Retourne le biome à la colonne col (bruit 1D lent)."""
        # Zone Gorgone : jungle forcée passé le seuil
        if col >= BIOME_JUNGLE_THRESHOLD:
            return BIOME_JUNGLE
        v = _smooth1(col, BIOME_FREQ, self.seed ^ 0xB10E)
        if v < 0.33:
            return BIOME_ICE
        elif v > 0.66:
            return BIOME_DESERT
        return BIOME_FOREST

    # ── Structures procédurales ───────────────────────────────────────────

    def _structure_at(self, anchor_col):
        """Retourne le dict {(col, row): tile} de la structure ancrée en anchor_col, ou {}."""
        if anchor_col in self._struct_cache:
            return self._struct_cache[anchor_col]

        result = {}
        biome = self.biome_at(anchor_col)
        for tag, prob, min_gap, builder in _STRUCTURES:
            tag_seed = sum(ord(c) for c in tag)
            allowed = _STRUCTURE_BIOMES.get(tag)
            if allowed and biome not in allowed:
                continue
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
        # Structures de surface : ancres dans col-25..col (grande pyramide = 21 de large)
        for ac in range(col - 25, col + 1):
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
        base = int(SURFACE_Y + raw * TERRAIN_AMPLITUDE - TERRAIN_AMPLITUDE / 2)
        # Dunes dans le désert : ondulations supplémentaires (amplitude ±3)
        if self.biome_at(col) == BIOME_DESERT:
            dune = _smooth1(col, 0.04, self.seed ^ 0xD04E)
            base += int(dune * 6 - 3)
        return base

    def _has_tree(self, col):
        biome = self.biome_at(col)
        if biome == BIOME_DESERT:
            return False
        if biome == BIOME_JUNGLE:
            rate = 0.22   # jungle très dense
        elif biome == BIOME_FOREST:
            rate = 0.10
        else:
            rate = 0.035   # glace clairsemée
        return _hash1(col * 31 + 7, self.seed ^ 0xBEEF) < rate

    def _tree_height(self, col):
        if self.biome_at(col) == BIOME_JUNGLE:
            return 4 + int(_hash1(col * 17 + 3, self.seed ^ 0xBEEF) * 3)   # 4 à 6
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
                return TILE_SNOW if self.biome_at(tc) == BIOME_ICE else TILE_GRASS
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
        if self.biome_at(origin) == BIOME_DESERT:
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
        if row <= 0:
            return TILE_STONE
        # Fond du monde = lave (dernières 3 rangées)
        if row >= ROWS - 3:
            return TILE_LAVA
        s = self.surface_at(col)
        biome = self.biome_at(col)

        # Structures procédurales (priorité sur tout le reste)
        st = self._struct_tile(col, row)
        if st is not None:
            return st

        # ── Au-dessus de la surface ──────────────────────────────────────
        if row < s:
            cabin = self._cabin_tile(col, row)
            if cabin != TILE_AIR:
                return cabin
            return self._tree_tile(col, row)

        # ── Lacs de surface (forêt, glace, jungle ; jungle plus fréquent) ─
        if biome == BIOME_DESERT:
            is_lake = False
        else:
            lake_thresh = 0.65 if biome == BIOME_JUNGLE else 0.82
            is_lake = _smooth1(col, 0.06, self.seed ^ 0xAC0A) > lake_thresh

        # ── Surface ──────────────────────────────────────────────────────
        if row == s:
            cabin = self._cabin_tile(col, row)
            if cabin != TILE_AIR:
                return cabin
            # Coffre rare en surface
            if not is_lake and _hash1(col * 137 + 19, self.seed ^ 0xF00D) < 0.004:
                return TILE_CHEST
            if is_lake:
                return TILE_WATER
            if biome == BIOME_DESERT:
                return TILE_SAND
            elif biome == BIOME_ICE:
                if _hash1(col * 43 + 13, self.seed ^ 0x1CE0) < 0.20:
                    return TILE_ICE
                return TILE_SNOW
            else:
                is_sand = _hash1(col * 37, self.seed ^ 0x5A4D) < 0.07
                return TILE_SAND if is_sand else TILE_GRASS

        # ── Sous-surface (avant la pierre) ───────────────────────────────
        if row < s + STONE_DEPTH:
            # Lac : 2 blocs d'eau sous la surface
            if is_lake and row < s + 3:
                return TILE_WATER
            if biome == BIOME_DESERT:
                return TILE_SAND
            elif biome == BIOME_ICE:
                return TILE_ICE if row < s + 3 else TILE_DIRT
            return TILE_DIRT

        # ── Sous-sol profond (identique pour tous les biomes) ────────────
        depth = row - s
        cave = _smooth2(col, row, 0.18, self.seed ^ 0xCAFE) > 0.67 and row > s + 3
        if cave:
            floor_solid = _smooth2(col, row + 1, 0.18, self.seed ^ 0xCAFE) <= 0.67
            if floor_solid and _hash2(col, row, self.seed ^ 0x5E17) < 0.010:
                return TILE_CHEST
            # Eau au sol des caves moyennes (depth 15–45)
            if floor_solid and 15 <= depth <= 45:
                if _hash2(col, row, self.seed ^ 0xAC7A) < 0.25:
                    return TILE_WATER
            # Lave au fond des caves profondes (remplace l'air)
            if floor_solid and depth >= 55:
                lava_chance = min(0.8, (depth - 55) * 0.02)
                if _hash2(col, row, self.seed ^ 0x1A7A) < lava_chance:
                    return TILE_LAVA
            return TILE_AIR
        # Poches d'eau dans la pierre (depth 20–50)
        if 20 <= depth <= 50 and _smooth2(col, row, 0.13, self.seed ^ 0xAC7B) > 0.85:
            return TILE_WATER
        # Poches de lave dans la pierre profonde
        if depth >= 70 and _smooth2(col, row, 0.15, self.seed ^ 0x1A7B) > 0.78:
            return TILE_LAVA
        # Veines de charbon
        if _smooth2(col * 1.3, row * 1.1, 0.22, self.seed ^ 0xC0A1) > 0.80 and row >= s + STONE_DEPTH + 2:
            return TILE_COAL
        # Veines de minerai
        if 10 <= depth <= 45 and _smooth2(col * 1.15, row * 0.95, 0.24, self.seed ^ 0xFE11) > 0.84:
            return TILE_IRON_ORE
        if 28 <= depth <= 65 and _smooth2(col * 1.25, row * 1.05, 0.27, self.seed ^ 0x60D1) > 0.88:
            return TILE_GOLD_ORE
        if depth >= 58 and _smooth2(col * 1.35, row * 1.15, 0.30, self.seed ^ 0xD1A5) > 0.92:
            return TILE_DIAMOND_ORE
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

    def chest_loot(self, depth=0):
        """
        Retourne une liste [(item, count), ...] à l'ouverture d'un coffre.
        item = TILE_xxx (ressource) ou (EQUIP_xxx, MAT_xxx) (équipement).
        Philosophie : matériaux bruts en majorité, équipement rare réservé aux profondeurs.
        depth : profondeur en tuiles sous la surface (0 = surface).
        """
        from config import (EQUIP_HEAD, EQUIP_BODY, EQUIP_FEET, EQUIP_SWORD,
                            EQUIP_PICKAXE, EQUIP_BOW,
                            MAT_WOOD, MAT_IRON, MAT_GOLD, MAT_DIAMOND,
                            TILE_WOOD, TILE_STONE, TILE_COAL,
                            TILE_IRON_ORE, TILE_GOLD_ORE, TILE_DIAMOND_ORE,
                            TILE_SILK, TILE_TORCH, TILE_ARROW, TILE_FISH,
                            TILE_EGG, TILE_ROD, TILE_FLAG,
                            TILE_BONE, TILE_FEATHER, TILE_VENOM, TILE_CRYSTAL,
                            TILE_FANG, TILE_SLIME_BALL,
                            TILE_SEED_WHEAT, TILE_SEED_CARROT, TILE_SEED_PUMPKIN)
        r = random.random
        results = []

        # ── Livre ancien (toutes profondeurs) ─────────────────────────────
        if r() < 0.12: results.append((TILE_BOOK, 1))

        if depth < 20:
            # ── Surface : bois, pierre, charbon + consommables variés ──────
            results.append((TILE_WOOD,  random.randint(2, 4)))
            if r() < 0.25: results.append((TILE_COAL,     random.randint(1, 2)))
            if r() < 0.20: results.append((TILE_STONE,    random.randint(1, 2)))
            # Consommables & composants de craft
            if r() < 0.20: results.append((TILE_TORCH,    random.randint(2, 4)))
            if r() < 0.15: results.append((TILE_SILK,     random.randint(1, 2)))
            if r() < 0.15: results.append((TILE_ARROW,    random.randint(3, 6)))
            if r() < 0.10: results.append((TILE_FISH,     random.randint(1, 2)))
            if r() < 0.08: results.append((TILE_EGG,      random.randint(1, 3)))
            if r() < 0.05: results.append((TILE_FLAG,     1))
            # Matériaux spéciaux (rares en surface)
            if r() < 0.10: results.append((TILE_FEATHER,  random.randint(1, 2)))
            if r() < 0.08: results.append((TILE_BONE,     random.randint(1, 2)))
            if r() < 0.05: results.append((TILE_SLIME_BALL, 1))
            # Graines (farming)
            if r() < 0.15: results.append((TILE_SEED_WHEAT,   random.randint(2, 4)))
            if r() < 0.10: results.append((TILE_SEED_CARROT,  random.randint(1, 3)))
            if r() < 0.08: results.append((TILE_SEED_PUMPKIN, random.randint(1, 2)))
            # Équipement bois très rare (5 %)
            if r() < 0.05:
                eslot = random.choice([EQUIP_SWORD, EQUIP_PICKAXE, EQUIP_BOW,
                                       EQUIP_HEAD, EQUIP_BODY, EQUIP_FEET])
                results.append(((eslot, MAT_WOOD), 1))

        elif depth < 50:
            # ── Grotte : minerai de fer + composants utiles ──────────────────
            if r() < 0.70: results.append((TILE_IRON_ORE, random.randint(1, 2)))
            if r() < 0.40: results.append((TILE_COAL,     random.randint(1, 3)))
            if r() < 0.25: results.append((TILE_STONE,    random.randint(2, 3)))
            # Consommables & composants de craft
            if r() < 0.25: results.append((TILE_SILK,     random.randint(1, 3)))
            if r() < 0.20: results.append((TILE_ARROW,    random.randint(4, 8)))
            if r() < 0.18: results.append((TILE_TORCH,    random.randint(3, 6)))
            if r() < 0.12: results.append((TILE_FISH,     random.randint(1, 3)))
            if r() < 0.10: results.append((TILE_EGG,      random.randint(1, 2)))
            if r() < 0.08: results.append((TILE_WOOD,     random.randint(2, 5)))
            if r() < 0.06: results.append((TILE_ROD,      1))
            # Matériaux spéciaux (plus courants en grotte)
            if r() < 0.18: results.append((TILE_BONE,     random.randint(1, 3)))
            if r() < 0.15: results.append((TILE_VENOM,    random.randint(1, 2)))
            if r() < 0.12: results.append((TILE_FANG,     random.randint(1, 2)))
            if r() < 0.10: results.append((TILE_CRYSTAL,  1))
            if r() < 0.08: results.append((TILE_SLIME_BALL, random.randint(1, 2)))
            # Équipement (Bois 12 %, Fer 5 %)
            if r() < 0.17:
                eslot = random.choice([EQUIP_SWORD, EQUIP_PICKAXE, EQUIP_BOW,
                                       EQUIP_HEAD,  EQUIP_BODY,  EQUIP_FEET])
                mat   = MAT_WOOD if r() < 0.70 else MAT_IRON
                results.append(((eslot, mat), 1))

        else:
            # ── Donjon profond : or + diamant, équipement de qualité ─────────
            if r() < 0.80: results.append((TILE_GOLD_ORE,    random.randint(2, 4)))
            if r() < 0.25: results.append((TILE_DIAMOND_ORE, random.randint(1, 2)))
            # Consommables en quantité généreuse
            if r() < 0.30: results.append((TILE_SILK,     random.randint(2, 4)))
            if r() < 0.30: results.append((TILE_ARROW,    random.randint(6, 12)))
            if r() < 0.20: results.append((TILE_TORCH,    random.randint(4, 8)))
            if r() < 0.15: results.append((TILE_IRON_ORE, random.randint(1, 3)))
            if r() < 0.12: results.append((TILE_FISH,     random.randint(2, 4)))
            if r() < 0.10: results.append((TILE_EGG,      random.randint(2, 4)))
            if r() < 0.08: results.append((TILE_FLAG,     1))
            # Matériaux spéciaux (abondants en donjon)
            if r() < 0.25: results.append((TILE_CRYSTAL,  random.randint(1, 3)))
            if r() < 0.20: results.append((TILE_BONE,     random.randint(2, 4)))
            if r() < 0.18: results.append((TILE_VENOM,    random.randint(1, 3)))
            if r() < 0.15: results.append((TILE_FANG,     random.randint(1, 2)))
            if r() < 0.12: results.append((TILE_SLIME_BALL, random.randint(1, 3)))
            if r() < 0.08: results.append((TILE_FEATHER,  random.randint(2, 4)))
            # Équipement (Fer 20 %, Or 30 %, Diamant 8 %)
            eq_roll = r()
            if eq_roll < 0.08:
                eslot = random.choice([EQUIP_SWORD, EQUIP_PICKAXE, EQUIP_BOW,
                                       EQUIP_HEAD,  EQUIP_BODY,  EQUIP_FEET])
                results.append(((eslot, MAT_DIAMOND), 1))
            elif eq_roll < 0.38:
                eslot = random.choice([EQUIP_SWORD, EQUIP_PICKAXE, EQUIP_BOW,
                                       EQUIP_HEAD,  EQUIP_BODY,  EQUIP_FEET])
                results.append(((eslot, MAT_GOLD), 1))
            elif eq_roll < 0.58:
                eslot = random.choice([EQUIP_SWORD, EQUIP_PICKAXE, EQUIP_BOW,
                                       EQUIP_HEAD,  EQUIP_BODY,  EQUIP_FEET])
                results.append(((eslot, MAT_IRON), 1))

        return results if results else [(TILE_WOOD, 1)]


def generate(seed=None):
    """Point d'entrée : retourne un World prêt à l'emploi."""
    return World(seed)
