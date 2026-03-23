"""
Inventaire d'un joueur : outils, ressources et équipements.
"""
from config import (
    TOOL_HAND, TOOL_PICKAXE, TOOL_PLACER, TOOL_SWORD, TOOL_FLAG, TOOL_CRAFT,
    EQUIP_HEAD, EQUIP_BODY, EQUIP_FEET, EQUIP_SWORD, EQUIP_PICKAXE,
    TILE_AIR, TILE_NAMES, TOOL_NAMES, EQUIP_NAMES, MAT_NAMES,
)


class Inventory:
    """
    Inventaire à 5 slots :
      SLOT_TOOL (0)  – outil actif (main, pioche, canon, épée, drapeau)
      SLOT_RES  (1)  – blocs récoltés
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
        self.resources    = []          # [(tile, count), ...]
        self.resource_idx = 0
        self.swords       = []          # matériaux d'épées trouvées
        self.sword_idx    = 0
        self.pickaxes     = []          # matériaux de pioches trouvées
        self.pickaxe_idx  = 0
        self.equip = {
            EQUIP_HEAD: [],
            EQUIP_BODY: [],
            EQUIP_FEET: [],
        }
        self.equip_idx = {EQUIP_HEAD: 0, EQUIP_BODY: 0, EQUIP_FEET: 0}

    # ── Propriétés matériaux actifs ───────────────────────────────────────────

    @property
    def sword_mat(self):
        return self.swords[self.sword_idx] if self.swords else None

    @property
    def pickaxe_mat(self):
        return self.pickaxes[self.pickaxe_idx] if self.pickaxes else None

    # ── Équipement porté ──────────────────────────────────────────────────────

    def worn_equip(self, equip_slot):
        lst = self.equip[equip_slot]
        if not lst:
            return None
        return lst[self.equip_idx[equip_slot]]

    def add_equip(self, item):
        eslot, mat = item
        if eslot == EQUIP_SWORD:
            if mat not in self.swords:
                self.swords.append(mat)
        elif eslot == EQUIP_PICKAXE:
            if mat not in self.pickaxes:
                self.pickaxes.append(mat)
        else:
            if item not in self.equip[eslot]:
                self.equip[eslot].append(item)

    def drop_equip(self, equip_slot):
        lst = self.equip[equip_slot]
        if not lst:
            return None
        idx  = self.equip_idx[equip_slot]
        item = lst.pop(idx)
        self.equip_idx[equip_slot] = max(0, min(idx, len(lst) - 1))
        return item

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
        if self.pickaxes:
            items = [TOOL_HAND] + [(TOOL_PICKAXE, m) for m in self.pickaxes] + [TOOL_PLACER]
        else:
            items = [TOOL_HAND, TOOL_PICKAXE, TOOL_PLACER]
        for mat in self.swords:
            items.append((TOOL_SWORD, mat))
        items.append(TOOL_FLAG)
        items.append(TOOL_CRAFT)
        return items

    def _active_tool_idx(self):
        items = self._tool_items()
        if self.tool == TOOL_SWORD and self.swords:
            target = (TOOL_SWORD, self.swords[self.sword_idx])
        elif self.tool == TOOL_PICKAXE and self.pickaxes:
            target = (TOOL_PICKAXE, self.pickaxes[self.pickaxe_idx])
        else:
            target = self.tool
        try:
            return items.index(target)
        except ValueError:
            return 0

    def _apply_tool_item(self, item):
        if isinstance(item, tuple):
            if item[0] == TOOL_SWORD:
                self.tool = TOOL_SWORD
                self.sword_idx = self.swords.index(item[1])
            elif item[0] == TOOL_PICKAXE:
                self.tool = TOOL_PICKAXE
                self.pickaxe_idx = self.pickaxes.index(item[1])
        else:
            self.tool = item

    def item_next(self):
        s = self.active_slot
        if s == self.SLOT_TOOL:
            items = self._tool_items()
            self._apply_tool_item(items[(self._active_tool_idx() + 1) % len(items)])
        elif s == self.SLOT_RES and len(self.resources) > 1:
            self.resource_idx = (self.resource_idx + 1) % len(self.resources)
        elif s in self.EQUIP_SLOT_MAP:
            eslot = self.EQUIP_SLOT_MAP[s]
            lst   = self.equip[eslot]
            if len(lst) > 1:
                self.equip_idx[eslot] = (self.equip_idx[eslot] + 1) % len(lst)

    def item_prev(self):
        s = self.active_slot
        if s == self.SLOT_TOOL:
            items = self._tool_items()
            self._apply_tool_item(items[(self._active_tool_idx() - 1) % len(items)])
        elif s == self.SLOT_RES and len(self.resources) > 1:
            self.resource_idx = (self.resource_idx - 1) % len(self.resources)
        elif s in self.EQUIP_SLOT_MAP:
            eslot = self.EQUIP_SLOT_MAP[s]
            lst   = self.equip[eslot]
            if len(lst) > 1:
                self.equip_idx[eslot] = (self.equip_idx[eslot] - 1) % len(lst)
