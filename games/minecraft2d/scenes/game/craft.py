"""
Système de craft : recettes et menu de fabrication in-game.
Déclenché par KB_J1_CRAFT (C) ou KB_J2_CRAFT (N).
"""
import pygame

from config import (
    TILE_WOOD, TILE_STONE, TILE_IRON_ORE, TILE_GOLD_ORE, TILE_DIAMOND_ORE,
    EQUIP_SWORD, EQUIP_PICKAXE, EQUIP_HEAD, EQUIP_BODY, EQUIP_FEET,
    MAT_WOOD, MAT_IRON, MAT_GOLD, MAT_DIAMOND,
    EQUIP_NAMES, TILE_NAMES,
    SCREEN_WIDTH, SCREEN_HEIGHT,
)

# ── Recettes ──────────────────────────────────────────────────────────────────
# Format : (résultat, {tile: count_requis}, label_coût)
CRAFT_RECIPES = [
    # ── Pioches ──
    ((EQUIP_PICKAXE, MAT_WOOD),    {TILE_WOOD:        3}, "Bois x3"),
    ((EQUIP_PICKAXE, MAT_IRON),    {TILE_IRON_ORE:    3}, "Minerai Fer x3"),
    ((EQUIP_PICKAXE, MAT_GOLD),    {TILE_GOLD_ORE:    3}, "Minerai Or x3"),
    ((EQUIP_PICKAXE, MAT_DIAMOND), {TILE_DIAMOND_ORE: 3}, "Minerai Diamant x3"),
    # ── Épées ────
    ((EQUIP_SWORD,   MAT_WOOD),    {TILE_WOOD:        2}, "Bois x2"),
    ((EQUIP_SWORD,   MAT_IRON),    {TILE_IRON_ORE:    2}, "Minerai Fer x2"),
    ((EQUIP_SWORD,   MAT_GOLD),    {TILE_GOLD_ORE:    2}, "Minerai Or x2"),
    ((EQUIP_SWORD,   MAT_DIAMOND), {TILE_DIAMOND_ORE: 2}, "Minerai Diamant x2"),
    # ── Armures Fer ──
    ((EQUIP_HEAD,    MAT_IRON),    {TILE_IRON_ORE:    3}, "Minerai Fer x3"),
    ((EQUIP_BODY,    MAT_IRON),    {TILE_IRON_ORE:    5}, "Minerai Fer x5"),
    ((EQUIP_FEET,    MAT_IRON),    {TILE_IRON_ORE:    2}, "Minerai Fer x2"),
    # ── Armures Or ──
    ((EQUIP_HEAD,    MAT_GOLD),    {TILE_GOLD_ORE:    3}, "Minerai Or x3"),
    ((EQUIP_BODY,    MAT_GOLD),    {TILE_GOLD_ORE:    5}, "Minerai Or x5"),
    ((EQUIP_FEET,    MAT_GOLD),    {TILE_GOLD_ORE:    2}, "Minerai Or x2"),
    # ── Armures Diamant ──
    ((EQUIP_HEAD,    MAT_DIAMOND), {TILE_DIAMOND_ORE: 3}, "Minerai Diamant x3"),
    ((EQUIP_BODY,    MAT_DIAMOND), {TILE_DIAMOND_ORE: 5}, "Minerai Diamant x5"),
    ((EQUIP_FEET,    MAT_DIAMOND), {TILE_DIAMOND_ORE: 2}, "Minerai Diamant x2"),
]


def _has_resources(inventory, ingredients):
    """Vérifie que l'inventaire contient tous les ingrédients requis."""
    res_map = {tile: count for tile, count in inventory.resources}
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

_MENU_W = 180
_MENU_H = 200
_ROW_H  = 18
_PAD    = 6


class CraftMenu:
    """Menu de craft affiché en overlay. open/close via toggle()."""

    def __init__(self):
        self.visible  = False
        self._sel     = 0      # index sélectionné dans les recettes filtrées
        self._recipes = []     # recettes disponibles (cache)
        self._all     = False  # False = seulement craftables, True = toutes

    def toggle(self):
        self.visible = not self.visible
        self._sel    = 0

    def close(self):
        self.visible = False

    def _refresh(self, inventory):
        if self._all:
            self._recipes = CRAFT_RECIPES[:]
        else:
            self._recipes = [r for r in CRAFT_RECIPES
                             if _has_resources(inventory, r[1])]

    def navigate(self, dy):
        if not self._recipes:
            return
        self._sel = (self._sel + dy) % len(self._recipes)

    def craft(self, inventory):
        """Tente de crafter la recette sélectionnée. Retourne le nom crafté ou None."""
        if not self._recipes:
            return None
        result, ingredients, _ = self._recipes[self._sel]
        if not _has_resources(inventory, ingredients):
            return None
        _consume_resources(inventory, ingredients)
        inventory.add_equip(result)
        return EQUIP_NAMES.get(result, "?")

    def draw(self, screen, inventory, player_color, font):
        """Dessine le menu craft centré à l'écran."""
        self._refresh(inventory)

        mx = (SCREEN_WIDTH  - _MENU_W) // 2
        my = (SCREEN_HEIGHT - _MENU_H) // 2

        # Fond
        surf = pygame.Surface((_MENU_W, _MENU_H), pygame.SRCALPHA)
        surf.fill((20, 20, 30, 220))
        screen.blit(surf, (mx, my))
        pygame.draw.rect(screen, player_color, (mx, my, _MENU_W, _MENU_H), 2)

        # Titre
        title = font.render("[ CRAFT ]  C=fermer", True, player_color)
        screen.blit(title, (mx + _PAD, my + _PAD))
        pygame.draw.line(screen, player_color,
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

        for vi, (result, ingredients, cost) in enumerate(visible):
            ri   = start + vi
            ry   = my + 22 + vi * _ROW_H
            act  = (ri == self._sel)
            bg   = (60, 50, 10) if act else (30, 30, 40)
            pygame.draw.rect(screen, bg, (mx + 2, ry, _MENU_W - 4, _ROW_H - 1))

            name  = EQUIP_NAMES.get(result, "?")
            color = (255, 230, 80) if act else (200, 200, 200)
            can   = _has_resources(inventory, ingredients)
            if not can:
                color = (100, 100, 100)

            label = font.render(f"{name}  [{cost}]", True, color)
            screen.blit(label, (mx + _PAD, ry + 2))

        # Légende
        legend = font.render("↑↓ nav  E=craft  Tab=tout", True, (120, 120, 120))
        screen.blit(legend, (mx + _PAD, my + _MENU_H - 14))
