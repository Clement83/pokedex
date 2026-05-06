"""Rendu d'une viewport joueur (480x160).

Dessine ciel, plateformes, pickups, joueur, HUD. Le shake éventuel est
appliqué via un offset sur les éléments de gameplay (le ciel reste fixe).
"""
import math
import pygame

from config import (
    VIEW_W, VIEW_H,
    SKY_TOP, SKY_BOTTOM,
    PLATFORM_SOLID, PLATFORM_BRITTLE, PLATFORM_TOP,
    VINE_COLOR, ROCK_COLOR, BRANCH_COLOR, FEATHER_COLOR,
    BOULDER_COLOR, TEXT_COLOR, DEAD_OVERLAY,
    PLAYER_W, PLAYER_H, PLAYER_SCREEN_X,
)
from world import World


_SKY_CACHE: pygame.Surface | None = None


def _get_sky() -> pygame.Surface:
    global _SKY_CACHE
    if _SKY_CACHE is None:
        s = pygame.Surface((VIEW_W, VIEW_H))
        for y in range(VIEW_H):
            t = y / VIEW_H
            r = int(SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * t)
            g = int(SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * t)
            b = int(SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * t)
            pygame.draw.line(s, (r, g, b), (0, y), (VIEW_W, y))
        _SKY_CACHE = s
    return _SKY_CACHE


def draw(surf: pygame.Surface, world: World, player_color, font_hud,
         label: str) -> None:
    """Dessine une viewport complète pour un joueur dans `surf`."""
    surf.blit(_get_sky(), (0, 0))

    # Silhouettes de feuillage en parallax (fond léger).
    _draw_canopy(surf, world.scroll_x)

    # Shake éventuel (séisme).
    sx = sy = 0
    if world.shake_t > 0:
        sx = int(math.sin(world.elapsed * 60.0) * world.shake_mag)
        sy = int(math.cos(world.elapsed * 53.0) * world.shake_mag * 0.5)

    # Boulder visuel pendant l'event : grosse silhouette qui pousse depuis la gauche.
    if world.event_t > 0:
        _draw_boulder(surf, world)

    # ── Plateformes ──────────────────────────────────────────────────────────
    for plat in world.platforms:
        x = int(plat.x - world.scroll_x) + sx
        y = int(plat.y) + sy
        w = int(plat.w)
        h = int(plat.h)

        if x + w < -10 or x > VIEW_W + 10:
            continue

        # Corps (bois).
        body_col = PLATFORM_BRITTLE if plat.brittle else PLATFORM_SOLID
        # Effet de tremblement plus marqué si pourrie en cours d'effondrement.
        if plat.decay_t is not None:
            body_col = (200, 60, 40)
            jitter_x = int(math.sin(plat.decay_t * 80) * 2)
            x += jitter_x
        pygame.draw.rect(surf, body_col, (x, y + 4, w, h))

        # Bande herbe au-dessus.
        pygame.draw.rect(surf, PLATFORM_TOP, (x, y, w, 5))

        # Liane (trampoline).
        if plat.has_vine:
            cx = x + w // 2
            for i in range(5):
                ly = y - 6 - i * 6
                ox = int(math.sin(world.elapsed * 4.0 + i * 0.6) * 3)
                pygame.draw.circle(surf, VINE_COLOR, (cx + ox, ly), 3)

        # Rocher (obstacle).
        if plat.rock is not None:
            ox = int(plat.rock - world.scroll_x) + sx
            pygame.draw.rect(surf, ROCK_COLOR, (ox - 7, y - 14, 14, 14))
            pygame.draw.rect(surf, (50, 45, 40), (ox - 7, y - 14, 14, 14), 1)

        # Branche basse (au-dessus de la plateforme).
        if plat.branch_x is not None:
            ox = int(plat.branch_x - world.scroll_x) + sx
            pygame.draw.rect(surf, BRANCH_COLOR, (ox - 11, y - 38, 22, 6))
            # Petites feuilles pour souligner le danger en haut.
            pygame.draw.circle(surf, (100, 160, 80), (ox - 14, y - 35), 4)
            pygame.draw.circle(surf, (100, 160, 80), (ox + 14, y - 35), 4)

        # Plume (pickup).
        if plat.feather is not None:
            ox = int(plat.feather - world.scroll_x) + sx
            oy = y - 24 + int(math.sin(world.elapsed * 5.0) * 3)
            _draw_feather(surf, ox, oy)

    # ── Joueur ───────────────────────────────────────────────────────────────
    px = PLAYER_SCREEN_X + sx
    py = int(world.player.y) + sy
    color = player_color
    # Clignote si vient d'utiliser plume.
    if world.player.flash_t > 0 and int(world.player.flash_t * 30) % 2 == 0:
        color = (255, 255, 255)
    pygame.draw.rect(surf, color, (px - PLAYER_W // 2, py, PLAYER_W, PLAYER_H),
                     border_radius=3)
    # Petit visage : 2 yeux.
    pygame.draw.circle(surf, (30, 30, 30), (px - 2, py + 5), 1)
    pygame.draw.circle(surf, (30, 30, 30), (px + 4, py + 5), 1)

    # Bouclier plume actif → halo doré autour.
    if world.player.shield:
        halo = pygame.Surface((PLAYER_W + 12, PLAYER_H + 12), pygame.SRCALPHA)
        pygame.draw.ellipse(halo, (255, 230, 120, 110), halo.get_rect())
        surf.blit(halo, (px - PLAYER_W // 2 - 6, py - 6))

    # ── HUD ──────────────────────────────────────────────────────────────────
    hud_bg = pygame.Surface((VIEW_W, 18), pygame.SRCALPHA)
    hud_bg.fill((0, 0, 0, 110))
    surf.blit(hud_bg, (0, 0))
    txt = font_hud.render(f"{label}  ·  {world.distance} m", True, TEXT_COLOR)
    surf.blit(txt, (6, 2))
    if world.player.shield:
        _draw_feather(surf, VIEW_W - 18, 9, scale=0.8)
    if world.event_t > 0:
        warn = font_hud.render("! TREMBLEMENT !", True, (255, 200, 80))
        surf.blit(warn, (VIEW_W // 2 - warn.get_width() // 2, 2))

    # ── Mort ─────────────────────────────────────────────────────────────────
    if not world.player.alive:
        overlay = pygame.Surface((VIEW_W, VIEW_H), pygame.SRCALPHA)
        overlay.fill(DEAD_OVERLAY)
        surf.blit(overlay, (0, 0))
        big = pygame.font.SysFont("Arial", 26, bold=True).render(
            f"{label} – MORT", True, (240, 90, 90))
        surf.blit(big, (VIEW_W // 2 - big.get_width() // 2,
                        VIEW_H // 2 - big.get_height() // 2 - 8))
        sub = font_hud.render(f"distance : {world.distance} m", True, (220, 220, 220))
        surf.blit(sub, (VIEW_W // 2 - sub.get_width() // 2,
                        VIEW_H // 2 + 14))


# ── Détails graphiques ───────────────────────────────────────────────────────
def _draw_canopy(surf: pygame.Surface, scroll_x: float) -> None:
    """Silhouettes de feuillage sombre, parallax x0.4."""
    base_y = VIEW_H - 70
    # Hash déterministe basé sur x : pas besoin d'état.
    s = scroll_x * 0.4
    step = 60
    first = int(s // step) - 1
    for i in range(first, first + (VIEW_W // step) + 4):
        cx = int(i * step - s)
        bump_h = 16 + ((i * 73) % 20)
        col = (30, 60, 40)
        pygame.draw.ellipse(surf, col, (cx - 50, base_y - bump_h, 110, bump_h * 2))
    # Bande sombre de sol distant.
    pygame.draw.rect(surf, (28, 50, 35), (0, VIEW_H - 30, VIEW_W, 30))


def _draw_boulder(surf: pygame.Surface, world: World) -> None:
    """Gros rocher de fond qui pousse depuis la gauche pendant l'event."""
    # Progression : event_t décroît de BOULDER_DURATION → 0
    # Au début (event_t haut), boulder à gauche ; à la fin, plus visible.
    from config import BOULDER_DURATION
    progress = 1.0 - world.event_t / BOULDER_DURATION    # 0 → 1
    cx = int(-80 + progress * 220)
    cy = VIEW_H - 50
    r  = 70
    pygame.draw.circle(surf, BOULDER_COLOR, (cx, cy), r)
    pygame.draw.circle(surf, (50, 35, 25), (cx, cy), r, 3)
    # Petits cailloux qui rebondissent.
    for i in range(4):
        ox = cx + 20 + i * 14
        oy = cy + int(math.sin(world.elapsed * 12 + i) * 4) - 12
        pygame.draw.circle(surf, (60, 45, 35), (ox, oy), 3)


def _draw_feather(surf: pygame.Surface, cx: int, cy: int, scale: float = 1.0) -> None:
    w = int(10 * scale)
    h = int(14 * scale)
    pygame.draw.ellipse(surf, FEATHER_COLOR, (cx - w // 2, cy - h // 2, w, h))
    pygame.draw.line(surf, (200, 180, 100), (cx, cy - h // 2), (cx, cy + h // 2), 1)
