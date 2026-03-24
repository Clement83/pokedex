"""
Système de craft : recettes et menu de fabrication in-game.
Déclenché par KB_J1_CRAFT (C) ou KB_J2_CRAFT (N).

La table de craft possède un **niveau** (tier 1-4).
Chaque tier débloque de nouvelles recettes et se fabrique
à partir du tier précédent.
"""
import pygame

from config import (
    TILE_WOOD, TILE_STONE, TILE_COAL, TILE_IRON_ORE, TILE_GOLD_ORE, TILE_DIAMOND_ORE,
    TILE_TORCH, TILE_ARROW, TILE_SILK,
    EQUIP_SWORD, EQUIP_PICKAXE, EQUIP_HEAD, EQUIP_BODY, EQUIP_FEET, EQUIP_BOW,
    MAT_WOOD, MAT_IRON, MAT_GOLD, MAT_DIAMOND,
    TOOL_ROD,
    EQUIP_NAMES, TILE_NAMES, TOOL_NAMES,
    SCREEN_WIDTH, SCREEN_HEIGHT,
)

# ── Niveaux de table de craft ────────────────────────────────────────────────
CRAFT_TIER_LABELS = {1: "Bois", 2: "Fer", 3: "Or", 4: "Diamant"}
CRAFT_TIER_COLORS = {
    1: (180, 120,  60),   # brun bois
    2: (170, 170, 185),   # gris fer
    3: (255, 200,   0),   # jaune or
    4: ( 80, 220, 235),   # cyan diamant
}
CRAFT_TABLE_NAMES = {
    2: "Table Craft Fer",
    3: "Table Craft Or",
    4: "Table Craft Diamant",
}

# ── Recettes ─────────────────────────────────────────────────────────────────
# Format : (résultat, {tile: count_requis}, label_coût, tier_requis)
#   résultat = (equip_slot, material)  pour un équipement
#            = ("__upgrade__", tier)    pour améliorer la table de craft
CRAFT_RECIPES = [
    # ── Tier 1 : Table Bois ──────────────────────────────────────────────────
    ((EQUIP_PICKAXE, MAT_WOOD),  {TILE_WOOD: 3},                          "Bois x3",          1),
    ((EQUIP_SWORD,   MAT_WOOD),  {TILE_WOOD: 2},                          "Bois x2",          1),
    (("__tiles__", TILE_TORCH, 4), {TILE_WOOD: 1, TILE_COAL: 1},          "Bois x1 Charbon x1", 1),
    (("__tiles__", TILE_ARROW, 8), {TILE_WOOD: 1, TILE_STONE: 1},         "Bois x1 Pierre x1",  1),
    ((EQUIP_BOW,     MAT_WOOD),  {TILE_WOOD: 2, TILE_SILK: 1},            "Bois x2 Fil x1",   1),
    (("__tool__", TOOL_ROD),     {TILE_WOOD: 2, TILE_SILK: 1},            "Bois x2 Fil x1",   1),
    (("__upgrade__", 2),         {TILE_WOOD: 5, TILE_IRON_ORE: 3},        "Bois x5 Fer x3",   1),
    # ── Tier 2 : Table Fer ───────────────────────────────────────────────────
    ((EQUIP_PICKAXE, MAT_IRON),  {TILE_IRON_ORE: 3},                      "Minerai Fer x3",   2),
    ((EQUIP_SWORD,   MAT_IRON),  {TILE_IRON_ORE: 2},                      "Minerai Fer x2",   2),
    ((EQUIP_BOW,     MAT_IRON),  {TILE_IRON_ORE: 2, TILE_SILK: 1},        "Fer x2 Fil x1",    2),
    ((EQUIP_HEAD,    MAT_IRON),  {TILE_IRON_ORE: 3},                      "Minerai Fer x3",   2),
    ((EQUIP_BODY,    MAT_IRON),  {TILE_IRON_ORE: 5},                      "Minerai Fer x5",   2),
    ((EQUIP_FEET,    MAT_IRON),  {TILE_IRON_ORE: 2},                      "Minerai Fer x2",   2),
    (("__upgrade__", 3),         {TILE_IRON_ORE: 5, TILE_GOLD_ORE: 3},    "Fer x5 Or x3",     2),
    # ── Tier 3 : Table Or ────────────────────────────────────────────────────
    ((EQUIP_PICKAXE, MAT_GOLD),  {TILE_GOLD_ORE: 3},                      "Minerai Or x3",    3),
    ((EQUIP_SWORD,   MAT_GOLD),  {TILE_GOLD_ORE: 2},                      "Minerai Or x2",    3),
    ((EQUIP_HEAD,    MAT_GOLD),  {TILE_GOLD_ORE: 3},                      "Minerai Or x3",    3),
    ((EQUIP_BODY,    MAT_GOLD),  {TILE_GOLD_ORE: 5},                      "Minerai Or x5",    3),
    ((EQUIP_FEET,    MAT_GOLD),  {TILE_GOLD_ORE: 2},                      "Minerai Or x2",    3),
    (("__upgrade__", 4),         {TILE_GOLD_ORE: 5, TILE_DIAMOND_ORE: 3}, "Or x5 Diamant x3", 3),
    # ── Tier 4 : Table Diamant ───────────────────────────────────────────────
    ((EQUIP_PICKAXE, MAT_DIAMOND), {TILE_DIAMOND_ORE: 3},                 "Diamant x3",       4),
    ((EQUIP_SWORD,   MAT_DIAMOND), {TILE_DIAMOND_ORE: 2},                 "Diamant x2",       4),
    ((EQUIP_HEAD,    MAT_DIAMOND), {TILE_DIAMOND_ORE: 3},                 "Diamant x3",       4),
    ((EQUIP_BODY,    MAT_DIAMOND), {TILE_DIAMOND_ORE: 5},                 "Diamant x5",       4),
    ((EQUIP_FEET,    MAT_DIAMOND), {TILE_DIAMOND_ORE: 2},                 "Diamant x2",       4),
]


def _is_upgrade(result):
    return isinstance(result, tuple) and len(result) == 2 and result[0] == "__upgrade__"

def _is_tiles(result):
    """Résultat qui produit N ressources (tuiles) dans l'inventaire."""
    return isinstance(result, tuple) and len(result) == 3 and result[0] == "__tiles__"

def _is_tool_unlock(result):
    """Résultat qui débloque un outil (ex. canne à pêche)."""
    return isinstance(result, tuple) and len(result) == 2 and result[0] == "__tool__"

def _result_name(result):
    """Retourne le nom affichable du résultat d'une recette."""
    if _is_upgrade(result):
        return CRAFT_TABLE_NAMES.get(result[1], "Table Craft ?")
    if _is_tiles(result):
        _, tile, count = result
        return f"{TILE_NAMES.get(tile, '?')} ×{count}"
    if _is_tool_unlock(result):
        return TOOL_NAMES.get(result[1], "?")
    return EQUIP_NAMES.get(result, "?")


def _has_resources(res_map, ingredients):
    """Vérifie que res_map contient tous les ingrédients requis."""
    for tile, needed in ingredients.items():
        if res_map.get(tile, 0) < needed:
            return False
    return True


def _consume_resources(inventory, ingredients):
    """Retire les ingrédients de l'inventaire."""
    for tile, needed in ingredients.items():
        remaining = needed
        new_res = []
        for t, c in inventory.resources:
            if t == tile and remaining > 0:
                c -= remaining
                remaining = max(0, -c) if c < 0 else 0
                c = max(0, c)
                if c > 0:
                    new_res.append((t, c))
            else:
                new_res.append((t, c))
        inventory.resources = new_res


# ── Menu de craft ─────────────────────────────────────────────────────────────

_MENU_W = 190
_MENU_H = 200
_ROW_H  = 18
_PAD    = 6


class CraftMenu:
    """Menu de craft affiché en overlay. open/close via toggle()."""

    def __init__(self):
        self.visible  = False
        self._sel     = 0      # index sélectionné dans les recettes filtrées
        self._recipes = []     # recettes disponibles (cache)
        # Surface de fond pré-allouée (jamais ré-allouée)
        self._bg_surf = pygame.Surface((_MENU_W, _MENU_H), pygame.SRCALPHA)
        self._bg_surf.fill((20, 20, 30, 220))

    def toggle(self):
        self.visible = not self.visible
        self._sel    = 0

    def close(self):
        self.visible = False

    def _refresh(self, inventory):
        tier = inventory.craft_tier
        res_map = {tile: count for tile, count in inventory.resources}
        filtered = []
        for r in CRAFT_RECIPES:
            result, ingredients, cost, recipe_tier = r
            if _is_upgrade(result):
                # Upgrade : visible uniquement au tier courant (pas avant, pas après)
                if recipe_tier != tier:
                    continue
            else:
                # Recette classique : visible si tier suffisant
                if recipe_tier > tier:
                    continue
            filtered.append(r)
        self._recipes = filtered
        self._res_map = res_map

    def navigate(self, dy):
        if not self._recipes:
            return
        self._sel = (self._sel + dy) % len(self._recipes)

    def craft(self, inventory):
        """Tente de crafter la recette sélectionnée. Retourne le nom crafté ou None."""
        if not self._recipes:
            return None
        result, ingredients, _, _ = self._recipes[self._sel]
        res_map = {tile: count for tile, count in inventory.resources}
        if not _has_resources(res_map, ingredients):
            return None
        _consume_resources(inventory, ingredients)

        if _is_upgrade(result):
            inventory.craft_tier = result[1]
            return CRAFT_TABLE_NAMES.get(result[1], "Table Craft ?")
        elif _is_tiles(result):
            _, tile, count = result
            for _ in range(count):
                inventory.add(tile)
            return f"{TILE_NAMES.get(tile, '?')} ×{count}"
        elif _is_tool_unlock(result):
            inventory.unlock_tool(result[1])
            return TOOL_NAMES.get(result[1], "?")
        else:
            inventory.add_equip(result)
            return EQUIP_NAMES.get(result, "?")

    def draw(self, screen, inventory, player_color, font):
        """Dessine le menu craft centré dans la surface cible."""
        self._refresh(inventory)

        tier       = inventory.craft_tier
        tier_color = CRAFT_TIER_COLORS.get(tier, player_color)
        tier_label = CRAFT_TIER_LABELS.get(tier, "?")

        sw = screen.get_width()
        mx = (sw - _MENU_W) // 2
        my = (SCREEN_HEIGHT - _MENU_H) // 2

        # Fond (surface réutilisée)
        screen.blit(self._bg_surf, (mx, my))
        pygame.draw.rect(screen, tier_color, (mx, my, _MENU_W, _MENU_H), 2)

        # Titre avec nom du tier
        title = font.render(f"[ CRAFT {tier_label} ]  Alt=fermer", True, tier_color)
        screen.blit(title, (mx + _PAD, my + _PAD))
        pygame.draw.line(screen, tier_color,
                         (mx + _PAD, my + _PAD + 12),
                         (mx + _MENU_W - _PAD, my + _PAD + 12), 1)

        if not self._recipes:
            msg = font.render("Aucune recette disponible", True, (160, 160, 160))
            screen.blit(msg, (mx + _PAD, my + _MENU_H // 2))
            return

        # Recettes scrollées
        max_vis  = (_MENU_H - 40) // _ROW_H
        start    = max(0, self._sel - max_vis + 1)
        visible  = self._recipes[start: start + max_vis]

        for vi, (result, ingredients, cost, recipe_tier) in enumerate(visible):
            ri   = start + vi
            ry   = my + 22 + vi * _ROW_H
            act  = (ri == self._sel)
            can  = _has_resources(self._res_map, ingredients)
            is_up = _is_upgrade(result)

            # Fond de ligne
            if is_up:
                bg = (30, 50, 30) if act else (20, 35, 25)
            else:
                bg = (60, 50, 10) if act else (30, 30, 40)
            pygame.draw.rect(screen, bg, (mx + 2, ry, _MENU_W - 4, _ROW_H - 1))

            # Nom & couleur
            if is_up:
                target_tier = result[1]
                name = f"^ Table {CRAFT_TIER_LABELS[target_tier]}"
                if not can:
                    color = (100, 100, 100)
                elif act:
                    color = CRAFT_TIER_COLORS.get(target_tier, (255, 230, 80))
                else:
                    color = CRAFT_TIER_COLORS.get(target_tier, (200, 200, 200))
            else:
                name = _result_name(result)
                if not can:
                    color = (100, 100, 100)
                elif act:
                    color = (255, 230, 80)
                else:
                    color = (200, 200, 200)

            label = font.render(f"{name}  [{cost}]", True, color)
            screen.blit(label, (mx + _PAD, ry + 2))

        # Légende
        legend = font.render("nav  Action=craft  Alt=fermer", True, (120, 120, 120))
        screen.blit(legend, (mx + _PAD, my + _MENU_H - 14))
