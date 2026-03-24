"""
HUD : hotbar, icônes pixel-art d'outils et d'équipements.
"""
import pygame

from config import (
    HOTBAR_Y,
    TILE_COLORS, TILE_NAMES,
    TOOL_HAND, TOOL_PICKAXE, TOOL_PLACER, TOOL_SWORD, TOOL_FLAG, TOOL_CRAFT,
    TOOL_NAMES,
    EQUIP_HEAD, EQUIP_BODY, EQUIP_FEET, EQUIP_SWORD,
    EQUIP_NAMES,
    MAT_WOOD, MAT_IRON, MAT_GOLD, MAT_COLORS, MAT_NAMES,
    TILE_AIR,
)
from scenes.game.inventory import Inventory

# ── Dimensions hotbar ─────────────────────────────────────────────────────────
_HOTBAR_SLOT_W = 28
_HOTBAR_SLOT_H = 22
_HOTBAR_PAD    = 3
HOTBAR_TOTAL   = _HOTBAR_SLOT_W * 5 + _HOTBAR_PAD * 4   # largeur totale (px)
HOTBAR_SLOT_H  = _HOTBAR_SLOT_H   # accessible pour le loop

HEART_W   = 6   # largeur d'un cœur (pour positionnement dans loop.py)
HEART_GAP = 3


def draw_tool_icon(screen, tool, sx, sy, sw, sh, mat=None):
    """Icône pixel-art de l'outil centrée dans le slot (sw×sh)."""
    R = pygame.draw.rect

    if tool == TOOL_HAND:
        skin = (235, 186, 135)
        shad = (175, 125, 80)
        ox = sx + (sw - 16) // 2
        oy = sy + (sh - 12) // 2
        R(screen, skin, (ox + 0,  oy + 0, 2, 6))
        R(screen, skin, (ox + 3,  oy + 0, 2, 8))
        R(screen, skin, (ox + 6,  oy + 1, 2, 7))
        R(screen, skin, (ox + 9,  oy + 2, 2, 6))
        R(screen, skin, (ox + 0,  oy + 7, 12, 5))
        R(screen, shad, (ox + 0,  oy + 11, 12, 1))
        R(screen, skin, (ox + 11, oy + 8,  4, 3))
        R(screen, shad, (ox + 11, oy + 11, 4, 1))
        R(screen, shad, (ox + 2,  oy + 6, 1, 1))
        R(screen, shad, (ox + 5,  oy + 7, 1, 1))
        R(screen, shad, (ox + 8,  oy + 7, 1, 1))

    elif tool == TOOL_PICKAXE:
        _mat_steel = {MAT_WOOD: (155, 100, 42), MAT_IRON: (195, 198, 215), MAT_GOLD: (255, 200, 0)}
        _mat_dstl  = {MAT_WOOD: (100,  62, 20), MAT_IRON: ( 95,  98, 120), MAT_GOLD: (190, 145, 0)}
        _mat_shine = {MAT_WOOD: (200, 145, 80), MAT_IRON: (235, 238, 248), MAT_GOLD: (255, 230, 80)}
        HNDL  = (155, 100, 42)
        HSHAD = (100,  62, 20)
        STEEL = _mat_steel.get(mat, (195, 198, 215))
        DSTL  = _mat_dstl.get(mat,  ( 95,  98, 120))
        SHINE = _mat_shine.get(mat, (235, 238, 248))
        ox = sx + (sw - 14) // 2
        oy = sy + (sh - 14) // 2
        R(screen, HNDL,  (ox + 0, oy + 11, 2, 3))
        R(screen, HNDL,  (ox + 2, oy +  9, 2, 2))
        R(screen, HSHAD, (ox + 1, oy + 12, 1, 2))
        R(screen, HNDL,  (ox + 4, oy +  7, 2, 2))
        R(screen, HSHAD, (ox + 5, oy +  8, 1, 1))
        R(screen, HNDL,  (ox + 6, oy +  5, 2, 2))
        R(screen, STEEL, (ox + 5, oy +  3, 5, 4))
        R(screen, DSTL,  (ox + 5, oy +  3, 5, 4), 1)
        R(screen, SHINE, (ox + 6, oy +  4, 2, 1))
        R(screen, STEEL, (ox +  9, oy +  0, 3, 3))
        R(screen, SHINE, (ox +  9, oy +  0, 3, 1))
        R(screen, DSTL,  (ox + 11, oy +  0, 1, 3))
        R(screen, DSTL,  (ox +  9, oy +  2, 3, 1))
        R(screen, STEEL, (ox +  9, oy +  7, 3, 3))
        R(screen, DSTL,  (ox + 11, oy +  7, 1, 3))
        R(screen, DSTL,  (ox +  9, oy +  9, 3, 1))

    elif tool == TOOL_PLACER:
        METAL = (140, 140, 158)
        DARK  = ( 75,  75,  92)
        SHINE = (215, 215, 230)
        CUBE  = (200, 140,  50)
        CHIGH = (230, 175,  70)
        ox = sx + (sw - 16) // 2
        oy = sy + (sh - 12) // 2
        R(screen, METAL, (ox + 0, oy + 3, 10, 5))
        R(screen, SHINE, (ox + 1, oy + 3,  8, 1))
        R(screen, METAL, (ox + 10, oy + 4, 4, 3))
        R(screen, DARK,  (ox + 10, oy + 4, 4, 1))
        R(screen, DARK,  (ox + 2,  oy + 8, 4, 4))
        R(screen, METAL, (ox + 2,  oy + 8, 3, 3))
        R(screen, DARK,  (ox + 5,  oy + 7, 2, 1))
        R(screen, CUBE,  (ox + 13, oy + 2, 3, 4))
        R(screen, CHIGH, (ox + 13, oy + 2, 3, 1))
        R(screen, CHIGH, (ox + 13, oy + 2, 1, 4))
        R(screen, DARK,  (ox + 15, oy + 4, 1, 2))

    elif tool == TOOL_SWORD:
        _blade_cols = {MAT_WOOD: (170, 120, 50), MAT_IRON: (205, 208, 220), MAT_GOLD: (240, 195, 20)}
        BLADE = _blade_cols.get(mat, (205, 208, 220))
        SHINE = (245, 248, 255)
        DARK  = ( 80,  90, 115)
        GUARD = (200, 162,  30)
        GRIP  = (120,  72,  28)
        ox = sx + (sw - 14) // 2
        oy = sy + (sh - 14) // 2
        R(screen, GRIP,  (ox +  0, oy + 12, 2, 2))
        R(screen, GRIP,  (ox +  2, oy + 10, 2, 2))
        R(screen, GUARD, (ox +  1, oy +  8, 6, 2))
        R(screen, (230, 185, 50), (ox + 1, oy + 8, 6, 1))
        R(screen, BLADE, (ox +  4, oy +  7, 2, 2))
        R(screen, BLADE, (ox +  6, oy +  5, 2, 2))
        R(screen, BLADE, (ox +  8, oy +  3, 2, 2))
        R(screen, BLADE, (ox + 10, oy +  1, 2, 2))
        R(screen, BLADE, (ox + 12, oy +  0, 2, 2))
        R(screen, SHINE, (ox +  4, oy +  7, 1, 1))
        R(screen, SHINE, (ox +  6, oy +  5, 1, 1))
        R(screen, SHINE, (ox +  8, oy +  3, 1, 1))
        R(screen, SHINE, (ox + 10, oy +  1, 1, 1))
        R(screen, DARK,  (ox +  5, oy +  8, 1, 1))
        R(screen, DARK,  (ox +  7, oy +  6, 1, 1))
        R(screen, DARK,  (ox +  9, oy +  4, 1, 1))
        R(screen, DARK,  (ox + 11, oy +  2, 1, 1))

    elif tool == TOOL_FLAG:
        fc   = mat if mat else (255, 80, 80)
        POLE = (160, 130, 80)
        ox = sx + (sw - 10) // 2
        oy = sy + (sh - 14) // 2
        R(screen, POLE, (ox + 1, oy + 3,  2, 11))
        R(screen, fc,   (ox + 3, oy + 3,  7,  2))
        R(screen, fc,   (ox + 3, oy + 5,  5,  2))
        R(screen, fc,   (ox + 3, oy + 7,  3,  2))
        R(screen, (220, 200, 120), (ox + 1, oy + 1, 2, 2))

    elif tool == TOOL_CRAFT:
        WOOD  = (155, 100, 42)
        WDARK = (100,  62, 20)
        WLGHT = (195, 145, 75)
        # Couleur du dessus selon le tier de la table
        _TIER_TOPS = {
            1: (180, 120, 55),    # bois
            2: (170, 170, 185),   # fer
            3: (255, 200,   0),   # or
            4: ( 80, 220, 235),   # diamant
        }
        _TIER_SHINE = {
            1: (210, 160, 85),
            2: (215, 215, 230),
            3: (255, 230, 80),
            4: (140, 240, 250),
        }
        tier = mat if isinstance(mat, int) else 1
        TOP   = _TIER_TOPS.get(tier, (180, 120, 55))
        SHINE = _TIER_SHINE.get(tier, (210, 160, 85))
        ox = sx + (sw - 16) // 2
        oy = sy + (sh - 12) // 2
        # Surface de la table
        R(screen, TOP,   (ox + 1, oy,     14,  4))
        R(screen, SHINE, (ox + 1, oy,     14,  1))
        R(screen, WDARK, (ox + 1, oy + 3, 14,  1))
        # Planches verticales
        R(screen, WOOD,  (ox,     oy + 4,  3,  8))
        R(screen, WDARK, (ox,     oy + 4,  1,  8))
        R(screen, WOOD,  (ox + 13,oy + 4,  3,  8))
        R(screen, WDARK, (ox + 15,oy + 4,  1,  8))
        # Traverse du bas
        R(screen, WOOD,  (ox + 3, oy + 10, 10, 2))
        R(screen, WDARK, (ox + 3, oy + 11, 10, 1))
        # Haches croisées sur la surface (mini outils)
        R(screen, (195, 198, 215), (ox + 5, oy + 1, 3, 1))
        R(screen, (100,  62,  20), (ox + 4, oy + 1, 1, 2))


def draw_equip_icon(screen, eslot, mat_color, sx, sy, sw, sh):
    """Icône pixel-art de l'équipement centrée dans le slot (sw×sh)."""
    c    = mat_color if mat_color else (80, 80, 80)
    dark = (max(0, c[0]-70), max(0, c[1]-70), max(0, c[2]-70))
    R    = pygame.draw.rect

    if eslot == EQUIP_HEAD:
        ox = sx + (sw - 16) // 2
        oy = sy + (sh - 9)  // 2
        R(screen, c, (ox+3, oy,    10, 1))
        R(screen, c, (ox+1, oy+1,  14, 1))
        R(screen, c, (ox,   oy+2,  16, 1))
        R(screen, c, (ox,   oy+3,  16, 3))
        R(screen, (15,15,15), (ox+4, oy+3, 8, 3))
        R(screen, c, (ox,    oy+6,  5, 3))
        R(screen, c, (ox+11, oy+6,  5, 3))

    elif eslot == EQUIP_BODY:
        ox = sx + (sw - 16) // 2
        oy = sy + (sh - 12) // 2
        R(screen, c, (ox,   oy,    16,  2))
        R(screen, (15,15,15), (ox+5, oy, 6, 2))
        R(screen, c, (ox+1, oy+2,  14, 10))
        R(screen, dark, (ox+7, oy+3,  2,  8))
        R(screen, dark, (ox+3, oy+5,  2,  2))
        R(screen, dark, (ox+11,oy+5,  2,  2))

    elif eslot == EQUIP_FEET:
        ox = sx + (sw - 14) // 2
        oy = sy + (sh - 7)  // 2
        R(screen, c, (ox,    oy,   5, 5))
        R(screen, c, (ox,    oy+5, 7, 2))
        R(screen, c, (ox+9,  oy,   5, 5))
        R(screen, c, (ox+7,  oy+5, 7, 2))

    elif eslot == EQUIP_SWORD:
        ox = sx + (sw - 12) // 2
        oy = sy + (sh - 14) // 2
        SILVER = (200, 200, 210)
        GOLD_H = (220, 180, 40)
        blade  = SILVER if not mat_color else c
        handle = GOLD_H if not mat_color else dark
        R(screen, blade,  (ox + 5, oy,     2, 10))
        R(screen, blade,  (ox + 4, oy + 1, 4,  1))
        R(screen, blade,  (ox + 3, oy + 2, 6,  1))
        R(screen, (240, 240, 245), (ox + 5, oy + 1, 1, 7))
        R(screen, handle, (ox,     oy + 10, 12, 2))
        R(screen, (100, 65, 35),  (ox + 5, oy + 12, 2, 2))


def draw_hotbar(screen, inventory, x_offset, color, font):
    """
    Hotbar : 5 slots (outil, ressources, tête, corps, pieds).
    x_offset : bord gauche du premier slot en px.
    """
    sw, sh, pad = _HOTBAR_SLOT_W, _HOTBAR_SLOT_H, _HOTBAR_PAD
    y = HOTBAR_Y

    slot_configs = [
        Inventory.SLOT_TOOL,
        Inventory.SLOT_RES,
        Inventory.SLOT_HEAD,
        Inventory.SLOT_BODY,
        Inventory.SLOT_FEET,
    ]

    for i, slot_id in enumerate(slot_configs):
        sx  = x_offset + i * (sw + pad)
        act = (inventory.active_slot == slot_id)
        bg  = (120, 100, 20) if act else (55, 55, 55)
        pygame.draw.rect(screen, bg,    (sx, y, sw, sh))
        pygame.draw.rect(screen, color, (sx, y, sw, sh), 2 if act else 1)

        if slot_id == Inventory.SLOT_TOOL:
            _tool_mat = (
                inventory.sword_mat   if inventory.tool == TOOL_SWORD   else
                inventory.pickaxe_mat if inventory.tool == TOOL_PICKAXE else
                color                 if inventory.tool == TOOL_FLAG    else
                inventory.craft_tier  if inventory.tool == TOOL_CRAFT   else None
            )
            draw_tool_icon(screen, inventory.tool, sx, y, sw, sh, mat=_tool_mat)
            items = inventory._tool_items()
            if len(items) > 1:
                tidx  = inventory._active_tool_idx()
                idx_s = font.render(f"{tidx+1}/{len(items)}", True, (180, 180, 180))
                screen.blit(idx_s, (sx + 1, y + sh - idx_s.get_height()))

        elif slot_id == Inventory.SLOT_RES:
            if inventory.resources:
                tile, count = inventory.resources[inventory.resource_idx]
                pygame.draw.rect(screen, TILE_COLORS[tile],
                                 (sx + 3, y + 3, sh - 6, sh - 6))
                cnt_s = font.render(str(count), True, (255, 255, 255))
                screen.blit(cnt_s, (sx + sw - cnt_s.get_width() - 1,
                                    y + sh - cnt_s.get_height()))
                if len(inventory.resources) > 1:
                    idx_s = font.render(
                        f"{inventory.resource_idx+1}/{len(inventory.resources)}",
                        True, (180, 180, 180))
                    screen.blit(idx_s, (sx + 1, y + sh - idx_s.get_height()))
            else:
                none_s = font.render("—", True, (100, 100, 100))
                screen.blit(none_s, (sx + (sw - none_s.get_width())  // 2,
                                     y  + (sh - none_s.get_height()) // 2))

        else:
            eslot  = Inventory.EQUIP_SLOT_MAP[slot_id]
            item   = inventory.worn_equip(eslot)
            mat_c  = MAT_COLORS[item[1]] if item else None
            draw_equip_icon(screen, eslot, mat_c, sx, y, sw, sh)
            if item:
                lst = inventory.equip[eslot]
                if len(lst) > 1:
                    cnt_s = font.render(str(len(lst)), True, (255, 255, 255))
                    screen.blit(cnt_s, (sx + sw - cnt_s.get_width() - 1,
                                        y + sh - cnt_s.get_height()))

    # ── Nom de l'item actif sous la hotbar ────────────────────────────────────
    s = inventory.active_slot
    if s == Inventory.SLOT_TOOL:
        if inventory.tool == TOOL_SWORD:
            mat_name = MAT_NAMES.get(inventory.sword_mat, "") if inventory.sword_mat is not None else ""
            name = ("Épée " + mat_name).strip()
        elif inventory.tool == TOOL_CRAFT:
            _ct_names = {1: "Bois", 2: "Fer", 3: "Or", 4: "Diamant"}
            name = "Table " + _ct_names.get(inventory.craft_tier, "")
        else:
            name = TOOL_NAMES.get(inventory.tool, "")
    elif s == Inventory.SLOT_RES and inventory.resources:
        name = TILE_NAMES.get(inventory.resources[inventory.resource_idx][0], "?")
    elif s in Inventory.EQUIP_SLOT_MAP:
        eslot = Inventory.EQUIP_SLOT_MAP[s]
        item  = inventory.worn_equip(eslot)
        name  = EQUIP_NAMES.get(item, "—") if item else "—"
    else:
        name = ""
    if name:
        bright = (min(255, color[0] + 80), min(255, color[1] + 80), min(255, color[2] + 80))
        name_s = font.render(name, True, bright)
        nw, nh = name_s.get_size()
        px, py = 3, 1
        bg = pygame.Surface((nw + px * 2, nh + py * 2), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 180))
        screen.blit(bg, (x_offset - px, y + sh + 2 - py))
        screen.blit(name_s, (x_offset, y + sh + 2))
