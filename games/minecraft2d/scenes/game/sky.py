"""
Cycle jour / nuit : couleur du ciel, opacité de l'overlay nuit et HUD soleil/lune.
"""
import math
import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT

# ── Paramètres ────────────────────────────────────────────────────────────────
DAY_CYCLE_DURATION = 300.0   # secondes pour un cycle complet (5 min)

#  t ∈ [0, 1)  :  0.00 = aube  0.12 = plein jour  0.65 = fin jour
#                 0.70 = crépuscule  0.75 = nuit  0.95 = nuit  1.00 = aube
_SKY_KEYFRAMES = [
    (0.00, (220, 130,  80)),
    (0.12, (100, 160, 220)),
    (0.62, (100, 160, 220)),
    (0.70, (200,  75,  35)),
    (0.75, ( 30,  15,  55)),
    (0.95, ( 20,  10,  40)),
    (1.00, (220, 130,  80)),
]


def _lerp3(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def sky_color(t):
    for i in range(len(_SKY_KEYFRAMES) - 1):
        t0, c0 = _SKY_KEYFRAMES[i]
        t1, c1 = _SKY_KEYFRAMES[i + 1]
        if t0 <= t <= t1:
            tl = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
            return _lerp3(c0, c1, tl)
    return _SKY_KEYFRAMES[0][1]


def night_alpha(t):
    """Opacité [0–150] de l'overlay nuit."""
    if   0.70 <= t < 0.75: return int(150 * (t - 0.70) / 0.05)
    elif 0.75 <= t < 0.95: return 150
    elif 0.95 <= t < 1.00: return int(150 * (1.00 - t) / 0.05)
    return 0


def is_night(t):
    return t >= 0.68


# Surface pré-allouée pour l'overlay nuit
_night_overlay  = None
_night_last_na  = -1   # dernier alpha rendu → évite le fill si inchangé


def draw_night_overlay(screen, t):
    global _night_overlay, _night_last_na
    na = night_alpha(t)
    if na <= 0:
        return
    if _night_overlay is None:
        _night_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        _night_last_na = -1
    if na != _night_last_na:
        _night_overlay.fill((10, 5, 30, na))
        _night_last_na = na
    screen.blit(_night_overlay, (0, 0))


def draw_sky_hud(screen, t, font):
    """Icône soleil ou lune en top-centre."""
    cx = SCREEN_WIDTH // 2
    cy = 7
    if not is_night(t):
        pygame.draw.circle(screen, (255, 220,  20), (cx, cy), 5)
        pygame.draw.circle(screen, (255, 255, 120), (cx, cy), 3)
    else:
        pygame.draw.circle(screen, (220, 220, 200), (cx, cy), 5)
        pygame.draw.circle(screen, ( 25,  12,  48), (cx + 2, cy - 1), 4)
