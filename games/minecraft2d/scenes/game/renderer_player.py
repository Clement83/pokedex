"""
Rendu du joueur, boussole et cœurs de vie.
"""
import math
import pygame

from config import (
    TILE_SIZE, PLAYER_W, PLAYER_H,
    TOOL_HAND, TOOL_PICKAXE, TOOL_PLACER, TOOL_SWORD, TOOL_FLAG,
    EQUIP_HEAD, EQUIP_BODY, EQUIP_FEET,
    MAT_WOOD, MAT_IRON, MAT_GOLD, MAT_COLORS,
)

# ── Couleurs du bonhomme ──────────────────────────────────────────────────────
_SKIN  = (255, 210, 160)
_BLACK = (  0,   0,   0)
_DARK  = ( 40,  40,  40)

# Surfaces pré-allouées (initialisées au premier appel)
_COMPASS_BG = None

# ── Cœurs ────────────────────────────────────────────────────────────────────
_HEART_MASK = [
    (1, 0), (2, 0), (4, 0), (5, 0),
    (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1),
    (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2),
    (1, 3), (2, 3), (3, 3), (4, 3),
    (2, 4), (3, 4),
]
_HEART_W     = 6
_HEART_GAP   = 3
_HEART_FULL  = (220,  50,  50)
_HEART_EMPTY = ( 70,  20,  20)
_HEART_SHINE = (255, 140, 140)

# Surfaces pré-rendues d'un cœur plein et d'un cœur vide (6×5 px)
_HEART_SURF_FULL  = None
_HEART_SURF_EMPTY = None


def _build_heart_surfs():
    global _HEART_SURF_FULL, _HEART_SURF_EMPTY
    _HEART_SURF_FULL  = pygame.Surface((_HEART_W, 5), pygame.SRCALPHA)
    _HEART_SURF_EMPTY = pygame.Surface((_HEART_W, 5), pygame.SRCALPHA)
    for surf, color, shine in (
        (_HEART_SURF_FULL,  _HEART_FULL,  _HEART_SHINE),
        (_HEART_SURF_EMPTY, _HEART_EMPTY, None),
    ):
        for dx, dy in _HEART_MASK:
            surf.fill(color, (dx, dy, 1, 1))
        if shine:
            surf.fill(shine, (1, 1, 1, 1))


def draw_hearts(surf, hp, max_hp, x, y):
    """Dessine max_hp//2 cœurs en demi-cœurs."""
    global _HEART_SURF_FULL, _HEART_SURF_EMPTY
    if _HEART_SURF_FULL is None:
        _build_heart_surfs()
    n = max_hp // 2
    for i in range(n):
        hx = x + i * (_HEART_W + _HEART_GAP)
        # moitié gauche
        left_filled  = hp > i * 2
        # moitié droite
        right_filled = hp > i * 2 + 1
        # Fond vide (toujours) puis recouvre les moitiés remplies
        surf.blit(_HEART_SURF_EMPTY, (hx, y))
        if left_filled:
            # bliter seulement les 3 pixels gauche du cœur plein
            surf.blit(_HEART_SURF_FULL,  (hx, y), (0, 0, 3, 5))
        if right_filled:
            # bliter seulement les 3 pixels droits
            surf.blit(_HEART_SURF_FULL,  (hx + 3, y), (3, 0, 3, 5))


def draw_compass(surf, cam, me, other, surf_w, color):
    """Boussole top-right pointant vers l'autre joueur."""
    R   = 12
    cx  = surf_w - R - 6
    cy  = R + 6
    # Fond statique pré-alloué (même taille, même cercle noir semi-transparent)
    global _COMPASS_BG
    if _COMPASS_BG is None:
        _COMPASS_BG = pygame.Surface((R*2+2, R*2+2), pygame.SRCALPHA)
        pygame.draw.circle(_COMPASS_BG, (0, 0, 0, 110), (R+1, R+1), R+1)
    surf.blit(_COMPASS_BG, (cx - R - 1, cy - R - 1))
    pygame.draw.circle(surf, (50, 50, 50),    (cx, cy), R)
    pygame.draw.circle(surf, (180, 180, 180), (cx, cy), R, 1)
    dx    = (other.px() + PLAYER_W / 2) - (me.px() + PLAYER_W / 2)
    dy    = (other.py() + PLAYER_H / 2) - (me.py() + PLAYER_H / 2)
    angle = math.atan2(dy, dx)
    needle = R - 3
    tip_x  = int(cx + math.cos(angle) * needle)
    tip_y  = int(cy + math.sin(angle) * needle)
    tail_x = int(cx - math.cos(angle) * (needle // 2))
    tail_y = int(cy - math.sin(angle) * (needle // 2))
    pygame.draw.line(surf, (80, 80, 80), (tail_x, tail_y), (cx, cy), 2)
    pygame.draw.line(surf, color,        (cx, cy), (tip_x, tip_y), 2)
    pygame.draw.circle(surf, color, (tip_x, tip_y), 2)
    pygame.draw.circle(surf, (220, 220, 220), (cx, cy), 2)


# Cache des labels J1/J2 : {(idx, font_id): Surface}
_LABEL_CACHE = {}


def draw_player(screen, player, camera, font):
    px, py = camera.world_to_screen(player.px(), player.py())
    c  = player.color
    dc = player.dark_color
    inv = player.inventory

    head_item  = inv.worn_equip(EQUIP_HEAD)
    body_item  = inv.worn_equip(EQUIP_BODY)
    feet_item  = inv.worn_equip(EQUIP_FEET)
    head_color = MAT_COLORS[head_item[1]] if head_item else None
    body_color = MAT_COLORS[body_item[1]] if body_item else None
    feet_color = MAT_COLORS[feet_item[1]] if feet_item else None

    # Tête (10×10), au-dessus de la hitbox
    hx, hy = px, py - 10
    pygame.draw.rect(screen, _SKIN,  (hx,     hy,     10, 10))
    pygame.draw.rect(screen, _DARK,  (hx,     hy,     10, 10), 1)
    pygame.draw.rect(screen, _BLACK, (hx + 2, hy + 3,  2,  2))
    pygame.draw.rect(screen, _BLACK, (hx + 6, hy + 3,  2,  2))
    pygame.draw.rect(screen, _DARK,  (hx + 3, hy + 7,  4,  1))
    if head_color:
        pygame.draw.rect(screen, head_color, (hx,      hy,     10,  3))
        pygame.draw.rect(screen, head_color, (hx - 1,  hy,      1, 10))
        pygame.draw.rect(screen, head_color, (hx + 10, hy,      1, 10))
        pygame.draw.rect(screen, _DARK,      (hx,      hy,     10,  3), 1)

    # Corps (10×10)
    bx, by = px, py
    body_c = body_color if body_color else c
    pygame.draw.rect(screen, body_c, (bx,     by,     10, 10))
    pygame.draw.rect(screen, _DARK,  (bx,     by,     10, 10), 1)
    detail_c = dc if not body_color else tuple(max(0, v - 40) for v in body_color)
    pygame.draw.rect(screen, detail_c, (bx + 3, by + 3,  2,  2))
    pygame.draw.rect(screen, detail_c, (bx + 6, by + 3,  2,  2))
    if body_color:
        pygame.draw.rect(screen, _DARK, (bx + 4, by + 1, 2, 8))

    # Jambes (4×10 chacune)
    lx, ly = px, py + 10
    leg_c = feet_color if feet_color else dc
    pygame.draw.rect(screen, leg_c, (lx,     ly, 4, 10))
    pygame.draw.rect(screen, leg_c, (lx + 6, ly, 4, 10))
    pygame.draw.rect(screen, _DARK, (lx,     ly, 4, 10), 1)
    pygame.draw.rect(screen, _DARK, (lx + 6, ly, 4, 10), 1)
    if feet_color:
        pygame.draw.rect(screen, _DARK, (lx,     ly + 8, 4, 2))
        pygame.draw.rect(screen, _DARK, (lx + 6, ly + 8, 4, 2))

    # Outil en main
    _draw_tool_in_hand(screen, inv, c, px, py)

    # Étiquette J1 / J2 (pré-rendue et cachée)
    key = (player.idx, id(font))
    if key not in _LABEL_CACHE:
        _LABEL_CACHE[key] = font.render("J" + str(player.idx + 1), True, (255, 255, 255))
    label = _LABEL_CACHE[key]
    lw = label.get_width()
    pygame.draw.rect(screen, _BLACK, (px + (10 - lw) // 2 - 1, hy - 9, lw + 2, 9))
    screen.blit(label, (px + (10 - lw) // 2, hy - 9))


def _draw_tool_in_hand(screen, inv, player_color, px, py):
    """Dessine l'outil tenu dans la main droite du joueur."""
    R  = pygame.draw.rect
    tx = px + 11
    ty = py + 2
    tool = inv.tool

    if tool == TOOL_PICKAXE:
        _ph_steel = {MAT_WOOD: (155, 100, 42), MAT_IRON: (195, 198, 215), MAT_GOLD: (255, 200, 0)}
        _ph_dstl  = {MAT_WOOD: (100,  62, 20), MAT_IRON: ( 95,  98, 120), MAT_GOLD: (190, 145, 0)}
        pm    = inv.pickaxe_mat
        HNDL  = (155, 100, 42)
        STEEL = _ph_steel.get(pm, (195, 198, 215))
        DSTL  = _ph_dstl.get(pm,  ( 95,  98, 120))
        R(screen, HNDL,  (tx + 0, ty + 5, 2, 3))
        R(screen, HNDL,  (tx + 2, ty + 3, 2, 2))
        R(screen, STEEL, (tx + 3, ty + 1, 4, 3))
        R(screen, DSTL,  (tx + 3, ty + 1, 4, 3), 1)
        R(screen, STEEL, (tx + 6, ty + 0, 2, 2))
        R(screen, DSTL,  (tx + 7, ty + 0, 1, 2))
        R(screen, STEEL, (tx + 6, ty + 3, 2, 2))
        R(screen, DSTL,  (tx + 7, ty + 4, 1, 1))

    elif tool == TOOL_PLACER:
        METAL = (140, 140, 158); DARK = (75, 75, 92); SHINE = (215, 215, 230)
        R(screen, METAL, (tx + 0, ty + 2, 6, 3))
        R(screen, SHINE, (tx + 0, ty + 2, 6, 1))
        R(screen, METAL, (tx + 6, ty + 3, 3, 2))
        R(screen, DARK,  (tx + 6, ty + 3, 3, 1))
        R(screen, DARK,  (tx + 1, ty + 5, 3, 3))
        R(screen, METAL, (tx + 1, ty + 5, 2, 2))
        R(screen, DARK,  (tx + 4, ty + 4, 1, 1))

    elif tool == TOOL_SWORD:
        _sword_blade = {MAT_WOOD: (170, 120, 50), MAT_IRON: (205, 208, 220), MAT_GOLD: (240, 195, 20)}
        BLADE = _sword_blade.get(inv.sword_mat, (205, 208, 220))
        SHINE = (245, 248, 255); DARK = (80, 90, 115)
        GUARD = (200, 162, 30);  GRIP = (120, 72, 28)
        R(screen, GRIP,  (tx + 0, ty + 6, 2, 2))
        R(screen, GUARD, (tx + 0, ty + 4, 4, 2))
        R(screen, BLADE, (tx + 2, ty + 3, 2, 2))
        R(screen, BLADE, (tx + 4, ty + 1, 2, 2))
        R(screen, BLADE, (tx + 6, ty + 0, 2, 2))
        R(screen, SHINE, (tx + 2, ty + 3, 1, 1))
        R(screen, SHINE, (tx + 4, ty + 1, 1, 1))
        R(screen, SHINE, (tx + 6, ty + 0, 1, 1))
        R(screen, _DARK, (tx + 3, ty + 4, 1, 1))
        R(screen, _DARK, (tx + 5, ty + 2, 1, 1))

    elif tool == TOOL_FLAG:
        POLE = (160, 130, 80)
        fc   = player_color
        R(screen, POLE, (tx + 1, ty + 2, 2, 6))
        R(screen, fc,   (tx + 3, ty + 2, 5, 2))
        R(screen, fc,   (tx + 3, ty + 4, 3, 1))
        R(screen, (220, 200, 120), (tx + 1, ty + 0, 2, 2))
