"""
Rendu du joueur, boussole et cœurs de vie.
"""
import math
import pygame

from config import (
    TILE_SIZE, PLAYER_W, PLAYER_H,
    TOOL_HAND, TOOL_PICKAXE, TOOL_PLACER, TOOL_SWORD, TOOL_FLAG, TOOL_TORCH,
    TOOL_BOW, TOOL_ROD,
    EQUIP_HEAD, EQUIP_BODY, EQUIP_FEET,
    MAT_WOOD, MAT_IRON, MAT_GOLD, MAT_COLORS,
)

# ── Couleurs du bonhomme ──────────────────────────────────────────────────────
_SKIN  = (255, 210, 160)
_BLACK = (  0,   0,   0)
_DARK  = ( 40,  40,  40)

# ── Effet flamme torche : pixels opaque animés, zéro Surface/alpha ───────────
_FLAME_TICK  = 0
_FLAME_SPEED = 5   # change de pattern toutes les N frames (~6fps à 30fps)

# 4 patterns très différents : base large qui change, et pointe qui danse
_YEL = (255, 210,   0)
_ORG = (255, 110,   0)
_RED = (200,  20,   0)

_FLAME_PATTERNS = [
    # frame 0 : penche fort à gauche
    [( 0, -4, _YEL), (-1, -3, _YEL), (-2, -2, _ORG), (-1, -1, _ORG),
     ( 0, -1, _RED), ( 1,  0, _RED)],
    # frame 1 : droite et haute
    [( 1, -4, _YEL), ( 2, -3, _YEL), ( 1, -2, _ORG), ( 0, -2, _ORG),
     ( 1, -1, _RED), (-1,  0, _RED)],
    # frame 2 : large et basse (flamme écrasée)
    [(-2, -2, _YEL), ( 0, -3, _ORG), ( 2, -2, _YEL), (-1, -1, _ORG),
     ( 1, -1, _ORG), ( 0,  0, _RED)],
    # frame 3 : pointe haute centre
    [( 0, -5, _YEL), (-1, -4, _ORG), ( 1, -3, _ORG), (-1, -2, _RED),
     ( 0, -1, _YEL), ( 0,  0, _RED)],
]

def draw_torch_halo(screen, px, py):
    """Dessine les étincelles de flamme autour de la torche tenue en main."""
    global _FLAME_TICK
    _FLAME_TICK += 1
    pattern = _FLAME_PATTERNS[(_FLAME_TICK // _FLAME_SPEED) % 4]
    # pointe de flamme : tx+1,ty-2 avec tx=px+11, ty=py+2 → (px+12, py)
    fx, fy = px + 12, py
    R = pygame.draw.rect
    for dx, dy, col in pattern:
        R(screen, col, (fx + dx, fy + dy, 1, 1))


# ── Fumée torche : pool fixe de 8 particules, zéro allocation en jeu ─────────
_SMK_MAX  = 8
_SMK_POOL = []        # chaque particule : [x, y, age, wobble_phase]
_SMK_CD   = 0         # compteur spawn
_SMK_INTERVAL = 7     # 1 particule toutes les 7 frames (~4/s à 30fps)
# Palette gris du plus clair (jeune) au plus sombre (vieux)
_SMK_COLS = [(180, 180, 180), (140, 140, 140), (100, 100, 100), (65, 65, 65)]

def draw_smoke(screen, fx, fy, vx):
    """Met à jour et dessine les particules de fumée. fx/fy = pointe de flamme."""
    global _SMK_POOL, _SMK_CD
    # ── Spawn ────────────────────────────────────────────────────────────────
    _SMK_CD -= 1
    if _SMK_CD <= 0 and len(_SMK_POOL) < _SMK_MAX:
        _SMK_POOL.append([float(fx), float(fy - 2), 0, len(_SMK_POOL)])
        _SMK_CD = _SMK_INTERVAL
    # ── Update + draw ────────────────────────────────────────────────────────
    R   = pygame.draw.rect
    keep = []
    trail = -vx * 0.25          # dérive opposée au mouvement (traîne)
    for p in _SMK_POOL:
        # Monte et dérive
        p[1] -= 0.55
        p[0] += trail
        # Léger zigzag déterministe (phase décalée par particule)
        age = int(p[2])
        p[0] += 0.25 if (age + p[3]) % 6 < 3 else -0.25
        p[2] += 1
        if p[2] < 22:           # 22 frames de vie max
            keep.append(p)
            col = _SMK_COLS[min(int(p[2] / 6), 3)]
            R(screen, col, (int(p[0]), int(p[1]), 1, 1))
    _SMK_POOL[:] = keep


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

def draw_hearts(surf, hp, max_hp, x, y):
    """Dessine max_hp//2 cœurs en demi-cœurs, pixel par pixel (pas de cache SRCALPHA)."""
    R = pygame.draw.rect
    n = max_hp // 2
    for i in range(n):
        hx = x + i * (_HEART_W + _HEART_GAP)
        left_filled  = hp > i * 2
        right_filled = hp > i * 2 + 1
        for dx, dy in _HEART_MASK:
            half   = 0 if dx < 3 else 1
            filled = left_filled if half == 0 else right_filled
            R(surf, _HEART_FULL if filled else _HEART_EMPTY, (hx + dx, y + dy, 1, 1))
        if left_filled:
            R(surf, _HEART_SHINE, (hx + 1, y + 1, 1, 1))


def draw_compass(surf, cam, me, other, surf_w, color):
    """Boussole top-right pointant vers l'autre joueur."""
    R   = 12
    cx  = surf_w - R - 6
    cy  = R + 6
    # Fond : cercle foncé semi-transparent (alloué à chaque frame pour éviter les artéfacts)
    _bg = pygame.Surface((R*2+2, R*2+2), pygame.SRCALPHA)
    pygame.draw.circle(_bg, (0, 0, 0, 110), (R+1, R+1), R+1)
    surf.blit(_bg, (cx - R - 1, cy - R - 1))
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

    # Halo torche (dessiné après le corps pour se superposer via BLEND_ADD)
    if inv.tool == TOOL_TORCH:
        draw_torch_halo(screen, px, py)
        draw_smoke(screen, px + 12, py, player.vx)

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

    elif tool == TOOL_TORCH:
        # Bâton en bois tenu verticalement, flamme au sommet
        STICK  = (110,  72,  30)
        HEAD   = (180, 130,  40)
        FLAME  = (255, 210,  30)
        FLAME2 = (255, 130,   0)
        R(screen, STICK,  (tx + 1, ty + 2,  2, 6))   # manche
        R(screen, HEAD,   (tx + 0, ty + 1,  4, 2))   # tête
        R(screen, FLAME,  (tx + 1, ty - 2,  2, 4))   # flamme centrale
        R(screen, FLAME2, (tx + 0, ty - 1,  1, 3))   # flamme bord gauche
        R(screen, FLAME2, (tx + 3, ty - 1,  1, 3))   # flamme bord droit
