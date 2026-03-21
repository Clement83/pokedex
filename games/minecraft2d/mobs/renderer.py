"""
Rendu pixel-art des mobs.
"""
import math
import pygame

from mobs.base import (
    MOB_SLIME, MOB_ZOMBIE, MOB_GOLEM,
    MOB_CHICKEN, MOB_FROG, MOB_SEAGULL,
    _MOB_PW, _MOB_PH, _MOB_COLOR,
)


def draw_mob(screen, mob, camera):
    sx, sy = camera.world_to_screen(mob.px(), mob.py())
    mw = _MOB_PW[mob.mob_type]
    mh = _MOB_PH[mob.mob_type]
    c  = _MOB_COLOR[mob.mob_type]
    dc = tuple(max(0, v - 50) for v in c)

    if mob.mob_type == MOB_SLIME:
        pygame.draw.rect(screen, c,               (sx,     sy,     mw, mh))
        pygame.draw.rect(screen, dc,              (sx,     sy,     mw, mh), 1)
        pygame.draw.rect(screen, (0,   0,   0),   (sx + 2, sy + 3,  2,  2))
        pygame.draw.rect(screen, (0,   0,   0),   (sx + 8, sy + 3,  2,  2))
        pygame.draw.rect(screen, (200, 255, 200), (sx + 1, sy + 1,  3,  1))

    elif mob.mob_type == MOB_ZOMBIE:
        pygame.draw.rect(screen, c,              (sx, sy, mw, mh))
        pygame.draw.rect(screen, dc,             (sx, sy, mw, mh), 1)
        pygame.draw.rect(screen, (220,  50,  50), (sx + 1, sy + 3, 2, 2))
        pygame.draw.rect(screen, (220,  50,  50), (sx + 5, sy + 3, 2, 2))
        pygame.draw.rect(screen, dc,              (sx + 2, sy + 8, 4, 1))

    elif mob.mob_type == MOB_GOLEM:
        pygame.draw.rect(screen, c,              (sx, sy, mw, mh))
        pygame.draw.rect(screen, dc,             (sx, sy, mw, mh), 2)
        pygame.draw.rect(screen, (220, 140, 40), (sx + 2, sy + 4,  3, 3))
        pygame.draw.rect(screen, (220, 140, 40), (sx + 9, sy + 4,  3, 3))
        pygame.draw.line(screen, dc, (sx + 5, sy + 9),  (sx + 7, sy + 14), 1)
        pygame.draw.line(screen, dc, (sx + 9, sy + 7),  (sx + 8, sy + 12), 1)

    elif mob.mob_type == MOB_CHICKEN:
        dr = pygame.draw.rect
        dr(screen, (240, 240, 235), (sx,     sy + 2, 7, 5))
        dr(screen, (190, 190, 185), (sx + 1, sy + 3, 5, 2))
        dr(screen, (240, 240, 235), (sx,     sy,     2, 3))
        dr(screen, (240, 240, 235), (sx + 4, sy + 1, 3, 3))
        dr(screen, (215,  50,  50), (sx + 4, sy,     2, 1))
        dr(screen, (225, 140,  35), (sx + 7, sy + 2, 1, 1))
        dr(screen, (  0,   0,   0), (sx + 5, sy + 2, 1, 1))
        dr(screen, (225, 140,  35), (sx + 2, sy + 7, 1, 2))
        dr(screen, (225, 140,  35), (sx + 5, sy + 7, 1, 2))

    elif mob.mob_type == MOB_FROG:
        dr = pygame.draw.rect
        dr(screen, ( 55, 175,  55), (sx,     sy + 3, 8, 4))
        dr(screen, (190, 215,  80), (sx + 2, sy + 4, 4, 2))
        dr(screen, ( 55, 175,  55), (sx + 1, sy + 1, 6, 3))
        dr(screen, ( 55, 175,  55), (sx,     sy,     2, 2))
        dr(screen, ( 55, 175,  55), (sx + 6, sy,     2, 2))
        dr(screen, (  0,   0,   0), (sx,     sy,     1, 1))
        dr(screen, (  0,   0,   0), (sx + 7, sy,     1, 1))
        dr(screen, ( 35, 120,  35), (sx + 2, sy + 3, 4, 1))
        dr(screen, ( 35, 120,  35), (sx,     sy + 6, 2, 1))
        dr(screen, ( 35, 120,  35), (sx + 6, sy + 6, 2, 1))

    elif mob.mob_type == MOB_SEAGULL:
        dr = pygame.draw.rect
        wo = -1 if math.sin(mob._fly_phase) > 0 else 1
        dr(screen, (240, 240, 240), (sx,     sy + 1 + wo, 4, 2))
        dr(screen, (170, 178, 185), (sx,     sy + 1 + wo, 2, 1))
        dr(screen, (240, 240, 240), (sx + 6, sy + 1 + wo, 4, 2))
        dr(screen, (170, 178, 185), (sx + 8, sy + 1 + wo, 2, 1))
        dr(screen, (240, 240, 240), (sx + 3, sy + 2,      4, 3))
        dr(screen, (240, 240, 240), (sx + 4, sy,          3, 3))
        dr(screen, (  0,   0,   0), (sx + 5, sy + 1,      1, 1))
        dr(screen, (225, 185,  45), (sx + 7, sy + 2,      2, 1))
