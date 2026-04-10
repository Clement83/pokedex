"""
Caméra et cache de chunks (surfaces pré-rendues pour le rendu du monde).
"""
from collections import OrderedDict
import threading
import queue as _queue
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, ROWS,
    TILE_AIR, TILE_COLORS, TILE_CHEST, TILE_LAVA, TILE_WATER, TILE_TORCH,
    TILE_ARROW, TILE_SILK, TILE_FISH, TILE_EGG, TILE_FLAG, TILE_CRAFT, TILE_ROD,
    TILE_PICKAXE_WOOD, TILE_PICKAXE_IRON, TILE_PICKAXE_GOLD, TILE_PICKAXE_DIAMOND,
    TILE_SWORD_WOOD, TILE_SWORD_IRON, TILE_SWORD_GOLD, TILE_SWORD_DIAMOND,
    TILE_BOW_WOOD, TILE_BOW_IRON,
    TILE_HEAD_WOOD, TILE_HEAD_IRON, TILE_HEAD_GOLD, TILE_HEAD_DIAMOND,
    TILE_BODY_WOOD, TILE_BODY_IRON, TILE_BODY_GOLD, TILE_BODY_DIAMOND,
    TILE_FEET_WOOD, TILE_FEET_IRON, TILE_FEET_GOLD, TILE_FEET_DIAMOND,
    TILE_BOOK, TILE_PORTAL_STONE, TILE_PORTAL,
    TILE_FARMLAND,
    TILE_WHEAT_1, TILE_WHEAT_2, TILE_WHEAT_3,
    TILE_CARROT_1, TILE_CARROT_2, TILE_CARROT_3,
    TILE_PUMPKIN_1, TILE_PUMPKIN_2, TILE_PUMPKIN_3,
    TILE_HOE, TILE_BREAD,
    TILE_BUCKET_EMPTY, TILE_BUCKET_WATER,
    BIOME_SKY_COLORS,
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


def _draw_lava_tile(surf, x, y, dc, dr):
    """Lave pixel-art 16×16 avec texture de bulles/veines."""
    # Fond orange
    surf.fill((210, 70, 0), (x, y, 16, 16))
    # Veines plus claires (pattern déterministe basé sur position)
    h = ((dc * 7 + dr * 13) * 2654435761) & 0xFF
    if h < 80:
        surf.fill((255, 140, 20), (x + 2, y + 3, 5, 3))
    if h > 60 and h < 140:
        surf.fill((240, 110, 10), (x + 8, y + 7, 4, 4))
    if h > 120:
        surf.fill((255, 160, 40), (x + 5, y + 11, 6, 2))
    # Reflets lumineux
    if h < 50:
        surf.fill((255, 200, 60), (x + 3, y + 1, 2, 1))
    if h > 180:
        surf.fill((255, 200, 60), (x + 10, y + 9, 2, 1))
    # Bordure sombre
    pygame.draw.rect(surf, (150, 40, 0), (x, y, 16, 16), 1)


def _draw_water_tile(surf, x, y, dc, dr):
    """Eau pixel-art 16×16 avec reflets."""
    surf.fill((35, 80, 180), (x, y, 16, 16))
    h = ((dc * 11 + dr * 7) * 2654435761) & 0xFF
    if h < 90:
        surf.fill((50, 110, 220), (x + 2, y + 4, 6, 2))
    if h > 80 and h < 170:
        surf.fill((60, 120, 230), (x + 8, y + 9, 5, 2))
    if h > 150:
        surf.fill((80, 150, 240), (x + 4, y + 1, 3, 1))
    pygame.draw.rect(surf, (25, 60, 140), (x, y, 16, 16), 1)


def _draw_torch_tile(surf, x, y):
    """Torche pixel-art 16×16 — bâton brun + flamme jaune."""
    # Bâton central
    surf.fill((110, 72, 30),  (x + 7, y + 6,  2, 8))
    surf.fill((80,  50, 15),  (x + 7, y + 13, 2, 2))
    # Tête de la torche
    surf.fill((180, 130, 40), (x + 6, y + 4,  4, 3))
    # Flamme (jaune vif au centre, orange sur les bords)
    surf.fill((255, 200,  20), (x + 7, y + 1,  2, 4))
    surf.fill((255, 140,   0), (x + 6, y + 2,  1, 3))
    surf.fill((255, 140,   0), (x + 9, y + 2,  1, 3))
    surf.fill((255, 240, 100), (x + 7, y + 1,  2, 1))


def _draw_book_tile(surf, x, y):
    """Livre ancien pixel-art 16×16 — couverture brune + pages blanches."""
    surf.fill((45, 42, 48), (x, y, 16, 16))
    pygame.draw.rect(surf, (0, 0, 0), (x, y, 16, 16), 1)
    # Couverture
    surf.fill((120, 80, 30), (x + 2, y + 2, 12, 12))
    surf.fill((90, 55, 15), (x + 2, y + 2, 12, 12))
    # Pages (blanc cassé)
    surf.fill((235, 225, 200), (x + 4, y + 3, 9, 10))
    # Tranche
    surf.fill((200, 190, 160), (x + 3, y + 3, 1, 10))
    # Lignes de texte
    surf.fill((100, 80, 60), (x + 5, y + 5, 6, 1))
    surf.fill((100, 80, 60), (x + 5, y + 7, 5, 1))
    surf.fill((100, 80, 60), (x + 5, y + 9, 7, 1))
    # Fermoir doré
    surf.fill((200, 170, 40), (x + 7, y + 12, 2, 1))


def _draw_portal_stone_tile(surf, x, y, dc, dr):
    """Pierre de portail pixel-art 16×16 — violet sombre avec veines."""
    surf.fill((60, 20, 100), (x, y, 16, 16))
    pygame.draw.rect(surf, (40, 10, 70), (x, y, 16, 16), 1)
    h = ((dc * 13 + dr * 7) * 2654435761) & 0xFF
    # Veines violettes lumineuses
    if h < 100:
        surf.fill((140, 60, 220), (x + 3, y + 4, 4, 2))
    if h > 80 and h < 180:
        surf.fill((120, 50, 200), (x + 8, y + 8, 3, 3))
    if h > 140:
        surf.fill((160, 80, 240), (x + 5, y + 11, 5, 2))
    # Reflet central
    surf.fill((180, 100, 255), (x + 7, y + 7, 2, 2))


def _draw_portal_tile(surf, x, y, dc, dr):
    """Portail actif pixel-art 16×16 — tourbillon violet animé."""
    surf.fill((40, 10, 80), (x, y, 16, 16))
    h = ((dc * 17 + dr * 11) * 2654435761) & 0xFF
    # Spirales violettes (pattern déterministe)
    surf.fill((100, 40, 180), (x + 2, y + 2, 5, 3))
    surf.fill((130, 60, 220), (x + 8, y + 5, 4, 4))
    surf.fill((90, 30, 160), (x + 3, y + 9, 6, 3))
    # Particules lumineuses
    if h < 80:
        surf.fill((200, 140, 255), (x + 4, y + 3, 2, 1))
    if h > 100:
        surf.fill((200, 140, 255), (x + 10, y + 7, 2, 1))
    if h > 60 and h < 160:
        surf.fill((220, 170, 255), (x + 6, y + 11, 1, 1))
    # Centre brillant
    surf.fill((180, 120, 255), (x + 6, y + 6, 4, 4))
    surf.fill((220, 180, 255), (x + 7, y + 7, 2, 2))


# ── Farming tiles pixel-art 16×16 ────────────────────────────────────────────

def _draw_farmland_tile(surf, x, y):
    """Terre labourée : brun avec lignes de sillons."""
    surf.fill((110, 70, 30), (x, y, 16, 16))
    # Sillons horizontaux
    for ry in (3, 7, 11):
        surf.fill((90, 55, 20), (x + 1, y + ry, 14, 1))
    # Grains de terre clairs
    surf.fill((130, 85, 40), (x + 2, y + 5, 2, 1))
    surf.fill((130, 85, 40), (x + 9, y + 9, 2, 1))
    surf.fill((130, 85, 40), (x + 5, y + 13, 2, 1))
    pygame.draw.rect(surf, (0, 0, 0), (x, y, 16, 16), 1)


def _draw_crop_tile(surf, x, y, stage, crop_type):
    """Dessine une culture à son stade de croissance. crop_type: 0=blé, 1=carotte, 2=citrouille."""
    # Fond transparent (ciel)
    # Le fond sera le biome_color, on dessine juste la plante par-dessus
    ts = 16
    if stage == 1:
        # Stade 1 : petites pousses vertes
        green = (80, 160, 40)
        surf.fill(green, (x + 4, y + 12, 2, 4))
        surf.fill(green, (x + 10, y + 13, 2, 3))
        surf.fill((60, 140, 30), (x + 7, y + 11, 1, 5))
    elif stage == 2:
        # Stade 2 : tiges moyennes
        green = (100, 170, 50)
        dark = (70, 140, 35)
        surf.fill(dark, (x + 3, y + 8, 2, 8))
        surf.fill(green, (x + 2, y + 7, 3, 2))
        surf.fill(dark, (x + 7, y + 9, 2, 7))
        surf.fill(green, (x + 6, y + 8, 3, 2))
        surf.fill(dark, (x + 11, y + 10, 2, 6))
        surf.fill(green, (x + 10, y + 9, 3, 2))
    else:
        # Stade 3 : mature
        if crop_type == 0:
            # Blé doré
            stalk = (160, 140, 40)
            head = (210, 190, 60)
            surf.fill(stalk, (x + 2, y + 6, 2, 10))
            surf.fill(stalk, (x + 6, y + 5, 2, 11))
            surf.fill(stalk, (x + 10, y + 6, 2, 10))
            surf.fill(head, (x + 1, y + 3, 4, 4))
            surf.fill(head, (x + 5, y + 2, 4, 4))
            surf.fill(head, (x + 9, y + 3, 4, 4))
            surf.fill((230, 210, 80), (x + 6, y + 2, 2, 2))
        elif crop_type == 1:
            # Carotte : feuilles vertes + pointe orange en bas
            green = (60, 150, 40)
            surf.fill(green, (x + 3, y + 4, 2, 6))
            surf.fill(green, (x + 7, y + 3, 2, 7))
            surf.fill(green, (x + 11, y + 5, 2, 5))
            surf.fill(green, (x + 2, y + 3, 4, 2))
            surf.fill(green, (x + 6, y + 2, 4, 2))
            surf.fill(green, (x + 10, y + 4, 4, 2))
            # Carottes visibles
            surf.fill((230, 130, 30), (x + 3, y + 11, 3, 5))
            surf.fill((230, 130, 30), (x + 8, y + 12, 3, 4))
            surf.fill((240, 150, 40), (x + 4, y + 11, 1, 2))
        else:
            # Citrouille : tige verte + gros fruit orange
            green = (60, 140, 30)
            surf.fill(green, (x + 7, y + 3, 2, 5))
            surf.fill(green, (x + 5, y + 2, 6, 2))
            # Citrouille
            surf.fill((220, 150, 20), (x + 3, y + 8, 10, 7))
            surf.fill((200, 130, 15), (x + 4, y + 9, 8, 5))
            # Lignes de côtes
            surf.fill((180, 120, 10), (x + 7, y + 8, 2, 7))
            surf.fill((240, 170, 30), (x + 5, y + 10, 2, 2))
            # Tige
            surf.fill((100, 80, 20), (x + 7, y + 7, 2, 2))


def _draw_hoe_tile(surf, x, y):
    """Houe pixel-art : manche + lame."""
    surf.fill(_BG_ITEM, (x, y, 16, 16))
    pygame.draw.rect(surf, (0, 0, 0), (x, y, 16, 16), 1)
    # Manche diagonal
    for i in range(8):
        surf.fill(_HANDLE, (x + 3 + i, y + 12 - i, 2, 2))
    # Lame (tête de houe)
    surf.fill((150, 150, 160), (x + 9, y + 2, 5, 3))
    surf.fill((130, 130, 140), (x + 10, y + 5, 3, 1))


def _draw_bread_tile(surf, x, y):
    """Pain pixel-art."""
    surf.fill(_BG_ITEM, (x, y, 16, 16))
    pygame.draw.rect(surf, (0, 0, 0), (x, y, 16, 16), 1)
    # Miche de pain
    surf.fill((200, 160, 80), (x + 3, y + 7, 10, 5))
    surf.fill((180, 140, 60), (x + 4, y + 6, 8, 2))
    surf.fill((220, 180, 100), (x + 5, y + 8, 6, 2))
    surf.fill((170, 130, 50), (x + 3, y + 12, 10, 1))


def _draw_bucket_tile(surf, x, y, full):
    """Seau pixel-art 16×16. full=True pour seau d'eau."""
    surf.fill(_BG_ITEM, (x, y, 16, 16))
    pygame.draw.rect(surf, (0, 0, 0), (x, y, 16, 16), 1)
    # Corps du seau (trapèze)
    METAL = (160, 160, 175)
    DARK  = (110, 110, 125)
    SHINE = (200, 200, 215)
    surf.fill(METAL, (x + 4, y + 5, 8, 8))
    surf.fill(METAL, (x + 3, y + 7, 10, 5))
    surf.fill(DARK,  (x + 3, y + 12, 10, 1))
    surf.fill(SHINE, (x + 4, y + 5, 8, 1))
    # Anse
    surf.fill(DARK, (x + 5, y + 3, 1, 3))
    surf.fill(DARK, (x + 10, y + 3, 1, 3))
    surf.fill(DARK, (x + 6, y + 2, 4, 1))
    # Eau si plein
    if full:
        surf.fill((40, 90, 200), (x + 5, y + 7, 6, 4))
        surf.fill((60, 120, 220), (x + 5, y + 7, 6, 1))


# ── Dessin d'une seule tuile (partagé render + update_tile) ──────────────────

def _draw_single_tile(surf, x, y, tile, biome_color, dc=0, dr=0):
    """Dessine la tuile `tile` à (x, y) sur `surf`. biome_color = couleur ciel du biome."""
    ts = TILE_SIZE
    if tile == TILE_CHEST:
        _draw_chest_tile(surf, x, y)
    elif tile == TILE_LAVA:
        _draw_lava_tile(surf, x, y, dc, dr)
    elif tile == TILE_WATER:
        _draw_water_tile(surf, x, y, dc, dr)
    elif tile == TILE_TORCH:
        surf.fill((80, 70, 60), (x, y, ts, ts))
        _draw_torch_tile(surf, x, y)
    elif tile == TILE_CRAFT:
        _draw_craft_tile(surf, x, y)
    elif tile == TILE_ROD:
        _draw_rod_tile(surf, x, y)
    elif tile == TILE_FLAG:
        _draw_flag_item_tile(surf, x, y)
    elif tile == TILE_ARROW:
        _draw_arrow_tile(surf, x, y)
    elif tile == TILE_SILK:
        _draw_silk_tile(surf, x, y)
    elif tile == TILE_FISH:
        _draw_fish_tile(surf, x, y)
    elif tile == TILE_EGG:
        _draw_egg_tile(surf, x, y)
    elif tile in (TILE_PICKAXE_WOOD, TILE_PICKAXE_IRON,
                  TILE_PICKAXE_GOLD, TILE_PICKAXE_DIAMOND):
        _draw_pickaxe_tile(surf, x, y, TILE_COLORS[tile])
    elif tile in (TILE_SWORD_WOOD, TILE_SWORD_IRON,
                  TILE_SWORD_GOLD, TILE_SWORD_DIAMOND):
        _draw_sword_tile(surf, x, y, TILE_COLORS[tile])
    elif tile in (TILE_BOW_WOOD, TILE_BOW_IRON):
        _draw_bow_tile(surf, x, y, TILE_COLORS[tile])
    elif tile in (TILE_HEAD_WOOD, TILE_HEAD_IRON, TILE_HEAD_GOLD, TILE_HEAD_DIAMOND):
        _draw_head_tile(surf, x, y, TILE_COLORS[tile])
    elif tile in (TILE_BODY_WOOD, TILE_BODY_IRON, TILE_BODY_GOLD, TILE_BODY_DIAMOND):
        _draw_body_tile(surf, x, y, TILE_COLORS[tile])
    elif tile in (TILE_FEET_WOOD, TILE_FEET_IRON, TILE_FEET_GOLD, TILE_FEET_DIAMOND):
        _draw_feet_tile(surf, x, y, TILE_COLORS[tile])
    elif tile == TILE_BOOK:
        _draw_book_tile(surf, x, y)
    elif tile == TILE_PORTAL_STONE:
        _draw_portal_stone_tile(surf, x, y, dc, dr)
    elif tile == TILE_PORTAL:
        _draw_portal_tile(surf, x, y, dc, dr)
    # ── Farming ──────────────────────────────────────────────────────────
    elif tile == TILE_FARMLAND:
        _draw_farmland_tile(surf, x, y)
    elif tile in (TILE_WHEAT_1, TILE_WHEAT_2, TILE_WHEAT_3):
        surf.fill(biome_color, (x, y, ts, ts))
        stage = 1 + (tile - TILE_WHEAT_1)
        _draw_crop_tile(surf, x, y, stage, 0)
    elif tile in (TILE_CARROT_1, TILE_CARROT_2, TILE_CARROT_3):
        surf.fill(biome_color, (x, y, ts, ts))
        stage = 1 + (tile - TILE_CARROT_1)
        _draw_crop_tile(surf, x, y, stage, 1)
    elif tile in (TILE_PUMPKIN_1, TILE_PUMPKIN_2, TILE_PUMPKIN_3):
        surf.fill(biome_color, (x, y, ts, ts))
        stage = 1 + (tile - TILE_PUMPKIN_1)
        _draw_crop_tile(surf, x, y, stage, 2)
    elif tile == TILE_HOE:
        _draw_hoe_tile(surf, x, y)
    elif tile == TILE_BREAD:
        _draw_bread_tile(surf, x, y)
    elif tile == TILE_BUCKET_EMPTY:
        _draw_bucket_tile(surf, x, y, False)
    elif tile == TILE_BUCKET_WATER:
        _draw_bucket_tile(surf, x, y, True)
    else:
        color = biome_color if tile == TILE_AIR else TILE_COLORS.get(tile, (200, 50, 200))
        surf.fill(color, (x, y, ts, ts))
        if tile != TILE_AIR:
            pygame.draw.rect(surf, (0, 0, 0), (x, y, ts, ts), 1)


# ── Items plaçables – pixel-art 16×16 ────────────────────────────────────────

_BG_ITEM = (45, 42, 48)    # fond sombre commun aux items
_HANDLE  = (120, 80, 35)   # brun manche


def _draw_pickaxe_tile(surf, x, y, color):
    """Pioche : tête horizontale (couleur matériau) + manche diagonal brun."""
    surf.fill(_BG_ITEM, (x, y, 16, 16))
    pygame.draw.rect(surf, (0, 0, 0), (x, y, 16, 16), 1)
    # Tête (barre + deux pointes)
    surf.fill(color,   (x+2, y+3, 11, 3))
    surf.fill(color,   (x+2, y+5,  2, 2))   # pointe gauche
    surf.fill(color,   (x+11, y+5, 2, 3))   # pointe droite
    # Manche diagonal
    surf.fill(_HANDLE, (x+6,  y+5,  2, 2))
    surf.fill(_HANDLE, (x+7,  y+7,  2, 2))
    surf.fill(_HANDLE, (x+8,  y+9,  2, 2))
    surf.fill(_HANDLE, (x+9,  y+11, 2, 2))
    surf.fill(_HANDLE, (x+10, y+13, 2, 2))


def _draw_sword_tile(surf, x, y, color):
    """Épée : lame diagonale + croisillon doré + manche brun."""
    surf.fill(_BG_ITEM, (x, y, 16, 16))
    pygame.draw.rect(surf, (0, 0, 0), (x, y, 16, 16), 1)
    # Lame (haut-droit → bas-gauche)
    surf.fill(color, (x+9,  y+2,  2, 2))
    surf.fill(color, (x+8,  y+3,  2, 2))
    surf.fill(color, (x+7,  y+4,  2, 2))
    surf.fill(color, (x+6,  y+5,  2, 2))
    surf.fill(color, (x+5,  y+6,  2, 2))
    # Croisillon
    surf.fill((200, 170, 80), (x+3, y+7, 8, 2))
    # Manche
    surf.fill(_HANDLE, (x+4, y+9,  2, 2))
    surf.fill(_HANDLE, (x+3, y+11, 2, 2))


def _draw_bow_tile(surf, x, y, color):
    """Arc : courbe en C (couleur matériau) + corde blanche."""
    surf.fill(_BG_ITEM, (x, y, 16, 16))
    pygame.draw.rect(surf, (0, 0, 0), (x, y, 16, 16), 1)
    # Courbure
    surf.fill(color, (x+5,  y+2,  3, 2))
    surf.fill(color, (x+4,  y+4,  2, 2))
    surf.fill(color, (x+3,  y+6,  2, 4))
    surf.fill(color, (x+4,  y+10, 2, 2))
    surf.fill(color, (x+5,  y+12, 3, 2))
    # Corde
    surf.fill((210, 205, 185), (x+8, y+3, 1, 10))


def _draw_craft_tile(surf, x, y):
    """Table de craft : fond bois + grille 2×2 gravée."""
    surf.fill((155, 105, 48), (x, y, 16, 16))
    pygame.draw.rect(surf, (80, 50, 20), (x, y, 16, 16), 1)
    # Séparateurs de grille
    surf.fill((80, 50, 20), (x+7, y+1, 2, 14))
    surf.fill((80, 50, 20), (x+1, y+7, 14, 2))
    # Cellules légèrement plus sombres
    surf.fill((130, 88, 38), (x+2,  y+2,  4, 4))
    surf.fill((130, 88, 38), (x+10, y+2,  4, 4))
    surf.fill((130, 88, 38), (x+2,  y+10, 4, 4))
    surf.fill((130, 88, 38), (x+10, y+10, 4, 4))


def _draw_rod_tile(surf, x, y):
    """Canne à pêche : bâton diagonal + fil blanc."""
    surf.fill(_BG_ITEM, (x, y, 16, 16))
    pygame.draw.rect(surf, (0, 0, 0), (x, y, 16, 16), 1)
    # Bâton diagonal (bas-gauche → haut-droite)
    surf.fill(_HANDLE, (x+2,  y+12, 2, 2))
    surf.fill(_HANDLE, (x+4,  y+10, 2, 2))
    surf.fill(_HANDLE, (x+6,  y+8,  2, 2))
    surf.fill(_HANDLE, (x+8,  y+6,  2, 2))
    surf.fill(_HANDLE, (x+10, y+4,  2, 2))
    surf.fill(_HANDLE, (x+12, y+3,  2, 2))
    # Fil de pêche depuis le bout
    surf.fill((200, 200, 200), (x+13, y+4, 1, 1))
    surf.fill((200, 200, 200), (x+13, y+5, 1, 3))
    surf.fill((200, 200, 200), (x+12, y+8, 2, 1))


def _draw_flag_item_tile(surf, x, y):
    """Drapeau : hampe dorée + triangle rouge dégradé."""
    surf.fill(_BG_ITEM, (x, y, 16, 16))
    pygame.draw.rect(surf, (0, 0, 0), (x, y, 16, 16), 1)
    surf.fill((180, 140, 70), (x+6, y+2, 2, 12))   # hampe
    surf.fill((220, 50, 50),  (x+8, y+2, 5, 3))
    surf.fill((200, 40, 40),  (x+8, y+5, 4, 2))
    surf.fill((180, 30, 30),  (x+8, y+7, 3, 2))


def _draw_arrow_tile(surf, x, y):
    """Flèche diagonale : corps beige + pointe métal + plumes."""
    surf.fill(_BG_ITEM, (x, y, 16, 16))
    pygame.draw.rect(surf, (0, 0, 0), (x, y, 16, 16), 1)
    _S = (180, 155, 90)    # corps
    _T = (185, 185, 200)   # pointe métal
    _F = (200, 195, 185)   # plumes
    # Corps diagonal
    surf.fill(_S, (x+4, y+11, 2, 2))
    surf.fill(_S, (x+5, y+10, 2, 2))
    surf.fill(_S, (x+6, y+9,  2, 2))
    surf.fill(_S, (x+7, y+8,  2, 2))
    surf.fill(_S, (x+8, y+7,  2, 2))
    # Pointe
    surf.fill(_T, (x+9,  y+6,  2, 2))
    surf.fill(_T, (x+10, y+5,  2, 2))
    surf.fill(_T, (x+11, y+3,  2, 3))
    # Plumes
    surf.fill(_F, (x+2, y+12, 3, 2))
    surf.fill(_F, (x+3, y+11, 2, 2))


def _draw_silk_tile(surf, x, y):
    """Toile d'araignée : fils verticaux + horizontaux gris clair."""
    surf.fill((38, 38, 48), (x, y, 16, 16))
    pygame.draw.rect(surf, (0, 0, 0), (x, y, 16, 16), 1)
    _W = (200, 205, 215)
    for col_off in (3, 7, 11):
        surf.fill(_W, (x + col_off, y+2, 1, 12))
    surf.fill(_W, (x+2, y+4,  12, 1))
    surf.fill(_W, (x+2, y+8,  12, 1))
    surf.fill(_W, (x+2, y+12, 12, 1))


def _draw_fish_tile(surf, x, y):
    """Poisson : corps ovale cyan + queue + œil."""
    surf.fill((28, 48, 78), (x, y, 16, 16))
    pygame.draw.rect(surf, (0, 0, 0), (x, y, 16, 16), 1)
    _FC = (60, 190, 190)
    _FS = (45, 155, 155)
    # Corps
    surf.fill(_FC, (x+3, y+6, 8, 4))
    surf.fill(_FC, (x+4, y+5, 6, 6))
    # Queue
    surf.fill(_FS, (x+11, y+5, 3, 2))
    surf.fill(_FS, (x+12, y+7, 2, 2))
    surf.fill(_FS, (x+11, y+9, 3, 2))
    # Œil
    surf.fill((230, 230, 230), (x+5, y+7, 2, 2))
    surf.fill((40,  40,  40),  (x+5, y+7, 1, 1))


def _draw_egg_tile(surf, x, y):
    """Œuf : ovale ivoire avec ombre latérale."""
    surf.fill(_BG_ITEM, (x, y, 16, 16))
    pygame.draw.rect(surf, (0, 0, 0), (x, y, 16, 16), 1)
    _EG = (240, 230, 200)
    _ES = (210, 195, 165)
    surf.fill(_EG, (x+5,  y+3,  6,  2))
    surf.fill(_EG, (x+4,  y+4,  8,  2))
    surf.fill(_EG, (x+3,  y+6,  10, 5))
    surf.fill(_EG, (x+4,  y+11, 8,  2))
    surf.fill(_EG, (x+5,  y+13, 6,  1))
    surf.fill(_ES, (x+9,  y+5,  3,  7))   # ombre droite

def _draw_head_tile(surf, x, y, color):
    """Casque pixel-art 16x16 (forme de heaume)."""
    surf.fill(_BG_ITEM, (x, y, 16, 16))
    pygame.draw.rect(surf, (0, 0, 0), (x, y, 16, 16), 1)
    dark = (max(0, color[0]-60), max(0, color[1]-60), max(0, color[2]-60))
    # Sommet arrondi
    surf.fill(color, (x+4,  y+2,  8,  1))
    surf.fill(color, (x+2,  y+3,  12, 1))
    surf.fill(color, (x+1,  y+4,  14, 1))
    # Corps
    surf.fill(color, (x+1,  y+5,  14, 5))
    surf.fill((20, 20, 20), (x+4, y+5, 8, 5))  # fente visière
    # Joues
    surf.fill(color, (x+1,  y+10, 5, 4))
    surf.fill(color, (x+10, y+10, 5, 4))
    surf.fill(dark,  (x+1,  y+13, 5, 1))
    surf.fill(dark,  (x+10, y+13, 5, 1))


def _draw_body_tile(surf, x, y, color):
    """Plastron pixel-art 16x16."""
    surf.fill(_BG_ITEM, (x, y, 16, 16))
    pygame.draw.rect(surf, (0, 0, 0), (x, y, 16, 16), 1)
    dark = (max(0, color[0]-60), max(0, color[1]-60), max(0, color[2]-60))
    # Encolure
    surf.fill(color, (x+1, y+1, 14, 2))
    surf.fill((20, 20, 20), (x+5, y+1, 6, 2))  # échancrure
    # Corps
    surf.fill(color, (x+1, y+3, 14, 11))
    # Nervure centrale
    surf.fill(dark, (x+7, y+4, 2, 9))
    # Boucles d'épaule
    surf.fill(dark, (x+3, y+6, 2, 2))
    surf.fill(dark, (x+11, y+6, 2, 2))
    surf.fill(dark, (x+1, y+13, 14, 1))


def _draw_feet_tile(surf, x, y, color):
    """Bottes pixel-art 16x16 (paire)."""
    surf.fill(_BG_ITEM, (x, y, 16, 16))
    pygame.draw.rect(surf, (0, 0, 0), (x, y, 16, 16), 1)
    dark = (max(0, color[0]-60), max(0, color[1]-60), max(0, color[2]-60))
    # Botte gauche
    surf.fill(color, (x+1,  y+3,  6, 8))
    surf.fill(color, (x+1,  y+11, 8, 3))
    surf.fill(dark,  (x+1,  y+13, 8, 1))
    # Botte droite
    surf.fill(color, (x+9,  y+3,  6, 8))
    surf.fill(color, (x+7,  y+11, 8, 3))
    surf.fill(dark,  (x+7,  y+13, 8, 1))

class ChunkCache:
    _MAX_CHUNKS = 16   # chunks 16×16 tuiles — ~6 visibles + marge split screen

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
        """Calcule les tile IDs + biomes par colonne (pur Python). Thread-safe."""
        col0   = cx * CHUNK_COLS
        row0   = cy * CHUNK_ROWS
        w      = self._world
        biomes = [w.biome_at(col0 + dc) for dc in range(CHUNK_COLS)]
        result = []
        activate = []   # liquides procéduraux à activer
        _LIQ = (TILE_LAVA, TILE_WATER)
        for dr in range(CHUNK_ROWS):
            row = row0 + dr
            row_tiles = []
            for dc in range(CHUNK_COLS):
                col = col0 + dc
                t = w.get(col, row) if row < ROWS else TILE_AIR
                row_tiles.append(t)
                # Activer liquide procédural si air en dessous
                if t in _LIQ and (col, row) not in w.mods:
                    if row + 1 < ROWS and w.get(col, row + 1) == TILE_AIR:
                        activate.append((col, row, t))
            result.append(row_tiles)
        return (result, biomes, activate)

    # ── Rendu (main thread uniquement) ───────────────────────────────────────

    def _render_tiles(self, tiles, biomes):
        """Construit la pygame.Surface depuis les tile IDs + biomes. Main thread only."""
        surf = pygame.Surface((_CHUNK_W, _CHUNK_H))
        ts   = TILE_SIZE
        for dr, row_tiles in enumerate(tiles):
            for dc, tile in enumerate(row_tiles):
                x = dc * ts
                y = dr * ts
                _draw_single_tile(surf, x, y, tile,
                                  BIOME_SKY_COLORS[biomes[dc]], dc, dr)
        return surf.convert()

    def flush_ready(self):
        """Intègre les chunks calculés en background. Appelé une fois par frame depuis le main thread."""
        while True:
            try:
                cx, cy, data = self._ready_q.get_nowait()
                tiles, biomes, activate = data
                key = (cx, cy)
                self._pending.discard(key)
                if key not in self._cache:   # ne pas écraser un update_tile récent
                    surf = self._render_tiles(tiles, biomes)
                    if len(self._cache) >= self._MAX_CHUNKS:
                        self._cache.popitem(last=False)
                    self._cache[key] = surf
                # Activer les liquides procéduraux pour le tick liquide
                for col, row, t in activate:
                    if (col, row) not in self._world.mods:
                        self._world.mods[(col, row)] = t
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
        x  = (col % CHUNK_COLS) * TILE_SIZE
        y  = (row % CHUNK_ROWS) * TILE_SIZE
        biome_color = BIOME_SKY_COLORS[self._world.biome_at(col)]
        _draw_single_tile(surf, x, y, tile, biome_color,
                          col % CHUNK_COLS, row % CHUNK_ROWS)

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
        cx0 = int(cam_x) // _CHUNK_W
        cx1 = (int(cam_x) + view_w) // _CHUNK_W
        cy0 = max(0, int(cam_y) // _CHUNK_H)
        cy1 = (int(cam_y) + view_h) // _CHUNK_H
        for cy in range(cy0, cy1 + 1):
            for cx in range(cx0, cx1 + 1):
                key = (cx, cy)
                if key not in self._cache and key not in self._pending:
                    self._pending.add(key)
                    self._req_q.put((cx, cy))
