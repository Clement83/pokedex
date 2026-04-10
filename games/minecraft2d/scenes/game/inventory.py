"""
Inventaire d'un joueur : outils, ressources et équipements.
"""
from config import (
    TOOL_HAND, TOOL_PICKAXE, TOOL_PLACER, TOOL_SWORD, TOOL_FLAG, TOOL_CRAFT,
    TOOL_BOW, TOOL_ROD, TOOL_TORCH, TOOL_HOE,
    EQUIP_HEAD, EQUIP_BODY, EQUIP_FEET,
    TILE_AIR, TILE_TORCH, TILE_FLAG, TILE_CRAFT, TILE_ROD, TILE_HOE,
    TILE_TOOL_MAP, TOOL_MAT_TO_TILE, EQUIP_TO_TILE, ARMOR_TILE_MAP,
    TILE_NAMES, TOOL_NAMES, EQUIP_NAMES, MAT_NAMES,
)


class Inventory:
    """
    Inventaire à 5 slots :
      SLOT_TOOL (0)  – outil actif (main, pioche, canon, épée, drapeau)
      SLOT_RES  (1)  – blocs récoltés + items-outils
      SLOT_HEAD (2)  – casques
      SLOT_BODY (3)  – plastrons
      SLOT_FEET (4)  – bottes
    """
    SLOT_TOOL = 0
    SLOT_RES  = 1
    SLOT_HEAD = 2
    SLOT_BODY = 3
    SLOT_FEET = 4
    NUM_SLOTS = 5

    EQUIP_SLOT_MAP = {
        SLOT_HEAD: EQUIP_HEAD,
        SLOT_BODY: EQUIP_BODY,
        SLOT_FEET: EQUIP_FEET,
    }

    def __init__(self):
        self.active_slot  = 0
        self.tool         = TOOL_HAND
        self._tool_mat    = None        # matériau de l'outil actif (pioche/épée/arc)
        # Items de départ : drapeau, table de craft
        self.resources    = [
            (TILE_FLAG, 1),
            (TILE_CRAFT, 1),
        ]
        self.resource_idx = 0
        self.craft_tier   = 1           # niveau table de craft (1=Bois … 4=Diamant)
        # Équipements portés : sélection de l'armure active par slot
        # Les pièces sont stockées dans resources (même système que piôches/épées)
        self._equip_sel = {EQUIP_HEAD: 0, EQUIP_BODY: 0, EQUIP_FEET: 0}
        # Conservé vide pour compatibilité (anciennes sauvegardes migrées dans loop.py)
        self.equip = {}
        self.equip_idx = {}   # alias vide pour éventuels accès externes

    # ── Propriétés matériaux actifs ───────────────────────────────────────────

    @property
    def sword_mat(self):
        return self._tool_mat if self.tool == TOOL_SWORD else None

    @property
    def pickaxe_mat(self):
        return self._tool_mat if self.tool == TOOL_PICKAXE else None

    @property
    def bow_mat(self):
        return self._tool_mat if self.tool == TOOL_BOW else None

    @property
    def torch_count(self):
        """Nombre de torches dans les ressources."""
        for t, c in self.resources:
            if t == TILE_TORCH:
                return c
        return 0

    @property
    def active_tool_count(self):
        """Quantité de l'outil actif sélectionné (pour affichage)."""
        if self.tool in (TOOL_PICKAXE, TOOL_SWORD, TOOL_BOW) and self._tool_mat is not None:
            tile = TOOL_MAT_TO_TILE.get((self.tool, self._tool_mat))
            if tile:
                for t, c in self.resources:
                    if t == tile:
                        return c
            return 0
        if self.tool == TOOL_TORCH:
            return self.torch_count
        return 0

    def _has_res(self, tile):
        """Vérifie si le joueur possède au moins 1 exemplaire de cette ressource."""
        for t, c in self.resources:
            if t == tile and c > 0:
                return True
        return False

    def _remove_res(self, tile):
        """Retire 1 exemplaire d'une ressource. Retourne True si succès."""
        for i, (t, c) in enumerate(self.resources):
            if t == tile:
                if c == 1:
                    self.resources.pop(i)
                else:
                    self.resources[i] = (t, c - 1)
                self.resource_idx = max(0, min(self.resource_idx, len(self.resources) - 1))
                return True
        return False

    # ── Équipement porté ──────────────────────────────────────────────────────

    def worn_equip(self, equip_slot):
        """Retourne (equip_slot, mat) de la pièce portée, ou None si aucune."""
        matching = [tile for tile, c in self.resources
                    if c > 0 and ARMOR_TILE_MAP.get(tile, (None,))[0] == equip_slot]
        if not matching:
            return None
        idx = self._equip_sel.get(equip_slot, 0) % len(matching)
        return ARMOR_TILE_MAP[matching[idx]]

    def worn_tile(self, equip_slot):
        """Retourne le tile ID de la pièce d'armure portée, ou None."""
        matching = [tile for tile, c in self.resources
                    if c > 0 and ARMOR_TILE_MAP.get(tile, (None,))[0] == equip_slot]
        if not matching:
            return None
        idx = self._equip_sel.get(equip_slot, 0) % len(matching)
        return matching[idx]

    def add_equip(self, item):
        tile = EQUIP_TO_TILE.get(item)
        if tile:
            self.add(tile)

    def remove_equip(self, item):
        """Retire 1 exemplaire d'un équipement. Retourne True si succès."""
        tile = EQUIP_TO_TILE.get(item)
        if tile:
            return self._remove_res(tile)
        return False

    def unlock_tool(self, tool_id):
        """Débloque un outil en ajoutant son item dans l'inventaire."""
        _TOOL_TILES = {
            TOOL_ROD: TILE_ROD,
            TOOL_FLAG: TILE_FLAG, TOOL_CRAFT: TILE_CRAFT,
        }
        tile = _TOOL_TILES.get(tool_id)
        if tile and not self._has_res(tile):
            self.add(tile)

    def drop_equip(self, equip_slot):
        worn = self.worn_equip(equip_slot)
        if worn is None:
            return None
        self.remove_equip(worn)
        return worn

    # ── Ressources ────────────────────────────────────────────────────────────

    def selected_tile(self):
        if not self.resources:
            return TILE_AIR
        tile, count = self.resources[self.resource_idx]
        return tile if count > 0 else TILE_AIR

    def add(self, tile):
        for i, (t, c) in enumerate(self.resources):
            if t == tile:
                self.resources[i] = (t, c + 1)
                return
        self.resources.append((tile, 1))

    def consume(self):
        if not self.resources:
            return
        t, c = self.resources[self.resource_idx]
        if c <= 0:
            return
        if c == 1:
            self.resources.pop(self.resource_idx)
            self.resource_idx = max(0, min(self.resource_idx, len(self.resources) - 1))
        else:
            self.resources[self.resource_idx] = (t, c - 1)

    # ── Navigation entre slots (← / →) ───────────────────────────────────────

    def slot_next(self):
        self.active_slot = (self.active_slot + 1) % self.NUM_SLOTS

    def slot_prev(self):
        self.active_slot = (self.active_slot - 1) % self.NUM_SLOTS

    # ── Navigation dans le slot actif (↑ / ↓) ────────────────────────────────

    def _tool_items(self):
        """Liste dynamique des outils disponibles (seuls ceux possédés)."""
        items = [TOOL_HAND]
        # Pioches (par matériau, dans l'ordre des resources)
        for tile, _c in self.resources:
            tm = TILE_TOOL_MAP.get(tile)
            if tm and tm[0] == TOOL_PICKAXE:
                items.append(tm)
        items.append(TOOL_PLACER)
        # Épées
        for tile, _c in self.resources:
            tm = TILE_TOOL_MAP.get(tile)
            if tm and tm[0] == TOOL_SWORD:
                items.append(tm)
        # Arcs
        for tile, _c in self.resources:
            tm = TILE_TOOL_MAP.get(tile)
            if tm and tm[0] == TOOL_BOW:
                items.append(tm)
        if self._has_res(TILE_FLAG):
            items.append(TOOL_FLAG)
        if self._has_res(TILE_CRAFT):
            items.append(TOOL_CRAFT)
        if self._has_res(TILE_ROD):
            items.append(TOOL_ROD)
        if self.torch_count > 0:
            items.append(TOOL_TORCH)
        if self._has_res(TILE_HOE):
            items.append(TOOL_HOE)
        return items

    def ensure_valid_tool(self):
        """Si l'outil actif n'est plus disponible, revient à la Main."""
        items = self._tool_items()
        for item in items:
            if isinstance(item, tuple):
                if item[0] == self.tool and item[1] == self._tool_mat:
                    return
            elif item == self.tool:
                return
        self.tool = TOOL_HAND
        self._tool_mat = None

    def _active_tool_idx(self):
        items = self._tool_items()
        if self.tool in (TOOL_SWORD, TOOL_PICKAXE, TOOL_BOW) and self._tool_mat is not None:
            target = (self.tool, self._tool_mat)
        else:
            target = self.tool
        try:
            return items.index(target)
        except ValueError:
            return 0

    def _apply_tool_item(self, item):
        if isinstance(item, tuple):
            self.tool = item[0]
            self._tool_mat = item[1]
        else:
            self.tool = item
            self._tool_mat = None

    def item_next(self):
        s = self.active_slot
        if s == self.SLOT_TOOL:
            items = self._tool_items()
            self._apply_tool_item(items[(self._active_tool_idx() + 1) % len(items)])
        elif s == self.SLOT_RES and len(self.resources) > 1:
            self.resource_idx = (self.resource_idx + 1) % len(self.resources)
        elif s in self.EQUIP_SLOT_MAP:
            eslot = self.EQUIP_SLOT_MAP[s]
            matching = [tile for tile, c in self.resources
                        if c > 0 and ARMOR_TILE_MAP.get(tile, (None,))[0] == eslot]
            if len(matching) > 1:
                self._equip_sel[eslot] = (self._equip_sel.get(eslot, 0) + 1) % len(matching)

    def item_prev(self):
        s = self.active_slot
        if s == self.SLOT_TOOL:
            items = self._tool_items()
            self._apply_tool_item(items[(self._active_tool_idx() - 1) % len(items)])
        elif s == self.SLOT_RES and len(self.resources) > 1:
            self.resource_idx = (self.resource_idx - 1) % len(self.resources)
        elif s in self.EQUIP_SLOT_MAP:
            eslot = self.EQUIP_SLOT_MAP[s]
            matching = [tile for tile, c in self.resources
                        if c > 0 and ARMOR_TILE_MAP.get(tile, (None,))[0] == eslot]
            if len(matching) > 1:
                self._equip_sel[eslot] = (self._equip_sel.get(eslot, 0) - 1) % len(matching)
