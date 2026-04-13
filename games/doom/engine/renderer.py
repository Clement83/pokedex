"""Rendu du frame complet :
  - plafond / sol (gradient)
  - murs (vectorisé numpy via surfarray)
  - sprites enemies (billboard)
  - HUD (santé, munitions, arme)
"""
import pygame
import numpy as np
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, RENDER_W, RENDER_H, HALF_H,
    COL_CEILING, COL_FLOOR, WALL_COLORS,
)

# ── Surfaces internes ─────────────────────────────────────────────────────────
_buf  = None   # surface 240×160 (render buffer)

# ── Indices pré-calculés ──────────────────────────────────────────────────────
_Y   = np.arange(RENDER_H, dtype=np.float32)          # (H,)
_Y2D = _Y[np.newaxis, :]                               # (1, H) pour broadcast

# Gradient plafond : sombre en haut, clair vers l'horizon
_CEIL_T = (_Y[:HALF_H] / max(HALF_H - 1, 1)).astype(np.float32)  # 0→1
_CEIL_COL = np.array([
    (COL_CEILING[0] + _CEIL_T * 18).clip(0, 255),
    (COL_CEILING[1] + _CEIL_T * 18).clip(0, 255),
    (COL_CEILING[2] + _CEIL_T * 30).clip(0, 255),
], dtype=np.uint8).T   # shape (HALF_H, 3)

# Gradient sol : clair à l'horizon, sombre en bas
_FLOOR_T = ((_Y[HALF_H:] - HALF_H) / max(RENDER_H - HALF_H - 1, 1)).astype(np.float32)
_FLOOR_COL = np.array([
    (COL_FLOOR[0] * (1.0 - _FLOOR_T * 0.55)).clip(0, 255),
    (COL_FLOOR[1] * (1.0 - _FLOOR_T * 0.55)).clip(0, 255),
    (COL_FLOOR[2] * (1.0 - _FLOOR_T * 0.55)).clip(0, 255),
], dtype=np.uint8).T   # shape (RENDER_H-HALF_H, 3)

# Couleurs de mur pour les 5 types, shape (5+1, 3) indexé par wall_type
_WPAL = np.zeros((8, 3), dtype=np.float32)
for _wt, _wc in WALL_COLORS.items():
    if _wt < 8:
        _WPAL[_wt] = _wc


def init():
    """Initialise les surfaces internes (appeler après pygame.init)."""
    global _buf
    _buf = pygame.Surface((RENDER_W, RENDER_H))


def render_frame(screen: pygame.Surface, player, perp_dist, wall_type,
                 side, entities, gun_kick: float = 0.0,
                 hurt_alpha: int = 0):
    """Rendu complet d'un frame puis blit ×2 sur screen."""
    assert _buf is not None, "Appeler renderer.init() d'abord"

    # ── Pixel buffer ──────────────────────────────────────────────────────
    px = pygame.surfarray.pixels3d(_buf)   # shape (W, H, 3)

    # Plafond / sol (broadcast sur toutes les colonnes)
    px[:, :HALF_H, :] = _CEIL_COL[np.newaxis, :, :]   # (1,HALF_H,3)→(W,H,3)
    px[:, HALF_H:, :] = _FLOOR_COL[np.newaxis, :, :]

    # ── Murs ──────────────────────────────────────────────────────────────
    wall_h = np.clip((RENDER_H / perp_dist).astype(np.int32), 0, RENDER_H * 4)
    wtop   = np.maximum(HALF_H - wall_h // 2, 0)           # (W,)
    wbot   = np.minimum(HALF_H + wall_h // 2, RENDER_H)    # (W,)

    # Couleur de base par type de mur
    wt_safe = np.clip(wall_type.astype(np.int32), 0, 7)
    base    = _WPAL[wt_safe]                                # (W, 3)

    # Assombrir face NS + brouillard de distance
    darken = np.where(side == 1, 0.5, 1.0)[:, np.newaxis]  # (W, 1)
    fog    = np.clip(perp_dist / 9.0, 0.0, 1.0)[:, np.newaxis]
    col    = (base * darken * (1.0 - fog * 0.75)).astype(np.uint8)  # (W, 3)

    # Masque boolean (W, H) → où dessiner le mur
    mask = (_Y2D >= wtop[:, np.newaxis]) & (_Y2D < wbot[:, np.newaxis])  # (W,H)
    px[:] = np.where(mask[:, :, np.newaxis], col[:, np.newaxis, :], px)

    # Z-buffer pour les sprites (distance de mur par colonne)
    z_buf = perp_dist.copy()

    del px   # libérer le lock surfarray

    # ── Sprites ennemis ───────────────────────────────────────────────────
    _draw_sprites(player, entities, z_buf)

    # ── Scale ×2 ──────────────────────────────────────────────────────────
    pygame.transform.scale(_buf, (SCREEN_WIDTH, SCREEN_HEIGHT), screen)

    # ── HUD (dessiné directement sur screen en pleine résolution 480×320) ─
    _draw_hud(screen, player, gun_kick, hurt_alpha)


# ── Sprites ───────────────────────────────────────────────────────────────────

def _draw_sprites(player, entities, z_buf):
    """Billboard sprites pour les ennemis (tri peintre, de plus loin au plus proche)."""
    alive = [e for e in entities if not e.dead]
    if not alive:
        return

    det = player.dx * player.py - player.dy * player.px  # = CAM_PLANE

    # Trier par distance décroissante (peindre les plus lointains d'abord)
    alive.sort(key=lambda e: (e.x - player.x)**2 + (e.y - player.y)**2,
               reverse=True)

    for ent in alive:
        # Vecteur joueur → sprite dans le repère monde
        spx = ent.x - player.x
        spy = ent.y - player.y

        # Transformation dans l'espace caméra
        tx  = ( player.py * spx - player.px * spy) / det
        ty  = (-player.dy * spx + player.dx * spy) / det

        if ty <= 0.05:
            continue    # derrière la caméra

        sc_x = int(RENDER_W / 2 * (1.0 + tx / ty))
        sp_h = abs(int(RENDER_H / ty))
        sp_w = sp_h

        draw_y_start = max(0, HALF_H - sp_h // 2)
        draw_y_end   = min(RENDER_H, HALF_H + sp_h // 2)
        draw_x_start = max(0, sc_x - sp_w // 2)
        draw_x_end   = min(RENDER_W, sc_x + sp_w // 2)

        if draw_x_end <= draw_x_start or draw_y_end <= draw_y_start:
            continue

        color = _sprite_color(ent)

        # Vérification z_buffer colonne par colonne
        for sx in range(draw_x_start, draw_x_end):
            if sx < 0 or sx >= RENDER_W:
                continue
            if ty >= z_buf[sx]:
                continue   # mur devant
            # Ratio vertical pour l'effet corps-centre-tête
            _draw_sprite_col(_buf, sx, draw_y_start, draw_y_end, sp_h, color)


def _sprite_color(ent):
    from engine.entities import Enemy
    if ent.state == Enemy.CHASE:
        return (220, 180, 30)    # jaune = alerte
    if ent.state == Enemy.ATTACK:
        return (220, 70, 30)     # orange = attaque
    return (60, 180, 60)          # vert = idle


def _draw_sprite_col(surf, sx, y0, y1, sp_h, color):
    """Dessine une colonne du sprite avec un dégradé corps/tête simple."""
    # Tête : quart supérieur, légèrement plus clair
    mid   = y0 + sp_h // 4
    tc    = tuple(min(255, c + 40) for c in color)
    pygame.draw.line(surf, tc,  (sx, y0), (sx, min(mid, y1 - 1)))
    pygame.draw.line(surf, color, (sx, min(mid, y1 - 1) + 1), (sx, y1 - 1))


# ── HUD ───────────────────────────────────────────────────────────────────────

_HUD_FONT = None
_GUN_PTS  = None   # points du fusil pré-calculés


def _ensure_fonts():
    global _HUD_FONT
    if _HUD_FONT is None:
        _HUD_FONT = pygame.font.SysFont("Courier New", 14, bold=True)


def _draw_hud(screen: pygame.Surface, player, gun_kick: float, hurt_alpha: int):
    _ensure_fonts()

    SW, SH = SCREEN_WIDTH, SCREEN_HEIGHT

    # ── Overlay rouge si blessé ───────────────────────────────────────────
    if hurt_alpha > 0:
        hurt = pygame.Surface((SW, SH), pygame.SRCALPHA)
        hurt.fill((180, 20, 20, min(hurt_alpha, 160)))
        screen.blit(hurt, (0, 0))

    # ── Bande HUD en bas ─────────────────────────────────────────────────
    hud_rect = pygame.Rect(0, SH - 36, SW, 36)
    pygame.draw.rect(screen, (15, 15, 15), hud_rect)
    pygame.draw.line(screen, (60, 60, 60), (0, SH - 36), (SW, SH - 36), 1)

    hp_pct = max(0.0, player.hp / 100.0)
    hp_col = (int(220 * (1 - hp_pct) + 40 * hp_pct),
              int(50  * (1 - hp_pct) + 210 * hp_pct),
              40)

    # Barre HP
    bar_x, bar_y, bar_w, bar_h = 10, SH - 26, 130, 12
    pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h))
    pygame.draw.rect(screen, hp_col,       (bar_x, bar_y, int(bar_w * hp_pct), bar_h))
    pygame.draw.rect(screen, (80, 80, 80), (bar_x, bar_y, bar_w, bar_h), 1)
    hp_txt = _HUD_FONT.render(f"HP {player.hp}", True, (220, 220, 220))
    screen.blit(hp_txt, (bar_x, SH - 36 + 2))

    # Munitions
    ammo_txt = _HUD_FONT.render(f"AMMO {player.ammo}", True, (210, 175, 50))
    screen.blit(ammo_txt, (SW - 90, SH - 36 + 2))

    # ── Arme (pixel-art procédural centré en bas) ─────────────────────────
    _draw_gun(screen, gun_kick)


def _draw_gun(screen: pygame.Surface, kick: float):
    """Dessine un pistolet pixel-art au centre-bas de l'écran."""
    cx   = SCREEN_WIDTH // 2
    base = SCREEN_HEIGHT - 36 - 4      # juste au-dessus du HUD
    ky   = int(kick * 14)              # décalage vertical lors du tir

    cy   = base - ky
    DARK  = (80, 70, 60)
    LIGHT = (160, 145, 120)
    MUZZ  = (255, 220, 80)

    # Canon (bloc 8×4)
    pygame.draw.rect(screen, DARK,  (cx - 4, cy - 22, 8, 18))
    # Poignée
    pygame.draw.rect(screen, DARK,  (cx - 6, cy - 8,  14, 8))
    # Détails canon
    pygame.draw.rect(screen, LIGHT, (cx - 3, cy - 21, 6, 2))
    pygame.draw.rect(screen, LIGHT, (cx - 3, cy - 15, 6, 2))
    # Bouche canon
    pygame.draw.rect(screen, (50, 50, 50), (cx - 2, cy - 24, 4, 4))

    # Flash de tir si kick élevé
    if kick > 0.4:
        pygame.draw.circle(screen, MUZZ, (cx, cy - 26), int(kick * 10 + 2))
