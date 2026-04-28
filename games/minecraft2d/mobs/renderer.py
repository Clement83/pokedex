"""
Rendu pixel-art des mobs.
"""
import math
import pygame

from mobs.base import (
    MOB_SLIME, MOB_ZOMBIE, MOB_GOLEM,
    MOB_CHICKEN, MOB_FROG, MOB_SEAGULL,
    MOB_SPIDER, MOB_SKELETON, MOB_BAT, MOB_CRAB, MOB_DEMON, MOB_BOAR,
    MOB_TROLL, MOB_WORM, MOB_WRAITH, MOB_TENDRIL, MOB_GORGON,
    MOB_PENGUIN, MOB_POLAR_BEAR, MOB_SCORPION, MOB_VULTURE,
    MOB_WOLF, MOB_CAT,
    _MOB_PW, _MOB_PH, _MOB_COLOR,
)


def draw_mob(screen, mob, camera):  # noqa: C901
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

    elif mob.mob_type == MOB_SPIDER:
        dr = pygame.draw.rect
        # Corps ovale sombre
        dr(screen, c,             (sx + 2, sy + 3,  8, 6))
        dr(screen, dc,            (sx + 2, sy + 3,  8, 6), 1)
        # Tête plus petite
        dr(screen, c,             (sx + 8, sy + 2,  5, 5))
        # Yeux rouges
        dr(screen, (220,  40,  40),(sx + 9, sy + 3,  1, 1))
        dr(screen, (220,  40,  40),(sx + 11,sy + 3,  1, 1))
        # Pattes (4 paires)
        leg = ( 60, 50, 65)
        dr(screen, leg,            (sx,     sy + 4,  3, 1))
        dr(screen, leg,            (sx,     sy + 6,  3, 1))
        dr(screen, leg,            (sx,     sy + 8,  2, 1))
        dr(screen, leg,            (sx + 10,sy + 4,  2, 1))
        dr(screen, leg,            (sx + 10,sy + 6,  2, 1))

    elif mob.mob_type == MOB_SKELETON:
        dr = pygame.draw.rect
        # Corps
        dr(screen, c,              (sx + 2, sy + 4,  4, 7))
        # Tête
        dr(screen, c,              (sx + 1, sy,      6, 5))
        dr(screen, (  0,   0,   0),(sx + 2, sy + 1,  1, 2))
        dr(screen, (  0,   0,   0),(sx + 5, sy + 1,  1, 2))
        dr(screen, (  0,   0,   0),(sx + 2, sy + 4,  4, 1))
        # Bras
        dr(screen, c,              (sx,     sy + 4,  2, 5))
        dr(screen, c,              (sx + 6, sy + 4,  2, 5))
        # Jambes
        dr(screen, c,              (sx + 2, sy + 11, 2, 5))
        dr(screen, c,              (sx + 4, sy + 11, 2, 5))

    elif mob.mob_type == MOB_BAT:
        dr = pygame.draw.rect
        wing_off = int(math.sin(mob._fly_phase * 3) * 1.5)
        # Ailes
        dr(screen, c,              (sx,     sy + 2 + wing_off, 4, 2))
        dr(screen, c,              (sx + 6, sy + 2 - wing_off, 4, 2))
        # Corps
        dr(screen, c,              (sx + 3, sy + 1, 4, 4))
        # Yeux
        dr(screen, (200, 50, 200), (sx + 4, sy + 2, 1, 1))
        dr(screen, (200, 50, 200), (sx + 6, sy + 2, 1, 1))
        # Oreilles
        dr(screen, c,              (sx + 3, sy,     1, 2))
        dr(screen, c,              (sx + 6, sy,     1, 2))

    elif mob.mob_type == MOB_CRAB:
        dr = pygame.draw.rect
        dk = tuple(max(0, v - 60) for v in c)
        # Carapace
        dr(screen, c,  (sx + 1, sy,     10, 5))
        dr(screen, dk, (sx + 1, sy,     10, 5), 1)
        # Yeux sur tiges
        dr(screen, dk, (sx + 2, sy - 2,  1, 3))
        dr(screen, dk, (sx + 9, sy - 2,  1, 3))
        dr(screen, (  0, 0, 0), (sx + 2, sy - 2, 1, 1))
        dr(screen, (  0, 0, 0), (sx + 9, sy - 2, 1, 1))
        # Pattes (3 paires)
        dr(screen, c,  (sx,     sy + 2,  2, 1))
        dr(screen, c,  (sx,     sy + 4,  2, 1))
        dr(screen, c,  (sx + 10,sy + 2,  2, 1))
        dr(screen, c,  (sx + 10,sy + 4,  2, 1))
        # Pinces
        dr(screen, c,  (sx - 2, sy + 1,  3, 2))
        dr(screen, c,  (sx + 11,sy + 1,  3, 2))

    elif mob.mob_type == MOB_DEMON:
        dr = pygame.draw.rect
        # Corps flamme
        dr(screen, c,              (sx + 2, sy + 4, 10, 10))
        dr(screen, dc,             (sx + 2, sy + 4, 10, 10), 1)
        # Tête cornue
        dr(screen, c,              (sx + 3, sy,     8,  6))
        dr(screen, (255, 120,  20), (sx + 3, sy - 3, 2,  4))
        dr(screen, (255, 120,  20), (sx + 9, sy - 3, 2,  4))
        # Yeux incandescents
        dr(screen, (255, 200,   0), (sx + 4, sy + 1, 2,  2))
        dr(screen, (255, 200,   0), (sx + 8, sy + 1, 2,  2))
        # Ailes
        glow = tuple(min(255, v + 80) for v in c)
        dr(screen, glow,           (sx,     sy + 4, 3, 7))
        dr(screen, glow,           (sx + 11,sy + 4, 3, 7))

    elif mob.mob_type == MOB_BOAR:
        dr  = pygame.draw.rect
        bc  = (120,  70,  40)   # brun
        sc  = (175, 115,  70)   # ventre clair
        tsk = (220, 210, 190)   # défenses ivoire
        dr(screen, bc,  (sx,     sy + 2, 12,  6))  # flancs
        dr(screen, sc,  (sx + 2, sy + 4,  8,  3))  # ventre
        dr(screen, bc,  (sx + 7, sy,      5,  5))  # tête
        dr(screen, bc,  (sx + 9, sy + 3,  3,  2))  # groin
        dr(screen, (  0,   0,   0), (sx + 10, sy + 3, 1, 1))  # narine
        dr(screen, (  0,   0,   0), (sx +  8, sy + 1, 1, 1))  # œil
        dr(screen, tsk, (sx + 11, sy + 5,  1,  3))            # défenses
        dr(screen, tsk, (sx +  9, sy + 5,  1,  2))
        dr(screen, bc,  (sx +  1, sy + 8,  2,  2))            # pattes
        dr(screen, bc,  (sx +  4, sy + 8,  2,  2))
        dr(screen, bc,  (sx +  7, sy + 8,  2,  2))
        dr(screen, bc,  (sx + 10, sy + 8,  2,  2))

    elif mob.mob_type == MOB_TROLL:
        dr  = pygame.draw.rect
        tc  = ( 60,  90,  50)  # vert sombre
        lc  = ( 85, 115,  65)  # ventre clair
        dr(screen, tc, (sx + 1, sy + 6,  12, 10))             # corps massif
        dr(screen, lc, (sx + 3, sy + 9,   8,  5))             # ventre
        dr(screen, tc, (sx + 3, sy,       8,  7))             # tête petite
        dr(screen, (  0,   0,   0), (sx + 4, sy + 2, 2, 2))   # œil gauche
        dr(screen, (  0,   0,   0), (sx + 8, sy + 2, 2, 2))   # œil droit
        dr(screen, lc,              (sx + 5, sy + 5, 3, 1))   # mâchoire
        dr(screen, tc, (sx,     sy + 6,   2,  7))             # bras gauche
        dr(screen, tc, (sx + 12,sy + 6,   2,  7))             # bras droit
        dr(screen, tc, (sx + 2, sy + 14,  4,  4))             # jambe gauche
        dr(screen, tc, (sx + 8, sy + 14,  4,  4))             # jambe droite

    elif mob.mob_type == MOB_WORM:
        dr  = pygame.draw.rect
        wc  = (100,  60,  30)  # marron terreux
        hc  = (140,  90,  50)  # tête plus claire
        dr(screen, wc, (sx + 1, sy + 2,  4, 5))               # segment queue
        dr(screen, wc, (sx + 5, sy + 1,  4, 6))               # segment milieu
        dr(screen, wc, (sx + 9, sy + 1,  4, 6))               # segment avant
        dr(screen, hc, (sx + 12, sy,     4, 7))               # tête
        dr(screen, (  0,   0,   0), (sx + 13, sy + 1, 1, 1))  # Œil
        dr(screen, (180,  30,  30), (sx + 13, sy + 4, 2, 1))  # gueule

    elif mob.mob_type == MOB_WRAITH:
        dr  = pygame.draw.rect
        gh  = (160, 180, 255)  # bleu spectre
        gl  = (210, 220, 255)  # reflet lumineux
        wo  = int(math.sin(mob._fly_phase * 2) * 1.0)
        dr(screen, gh, (sx + 2, sy + wo,       8,  4))         # haut du corps
        dr(screen, gl, (sx + 3, sy + wo,       6,  2))         # reflet
        dr(screen, gh, (sx + 1, sy + 4 + wo,  10,  5))        # milieu
        dr(screen, gh, (sx,     sy + 8 + wo,  12,  3))        # bas
        dr(screen, gh, (sx + 1, sy + 10 + wo,  2,  4))        # effiloche gauche
        dr(screen, gh, (sx + 5, sy + 10 + wo,  2,  3))        # effiloche centre
        dr(screen, gh, (sx + 9, sy + 10 + wo,  2,  4))        # effiloche droite
        dr(screen, (10, 10, 60), (sx + 3, sy + 1 + wo, 2, 2)) # œil gauche
        dr(screen, (10, 10, 60), (sx + 7, sy + 1 + wo, 2, 2)) # œil droit

    elif mob.mob_type == MOB_TENDRIL:
        dr  = pygame.draw.rect
        vc  = ( 20,  90,  15)   # vert profond
        vl  = ( 40, 140,  25)   # vert clair lianes
        vg  = (  0, 200,  80)   # vert lumineux (actif)
        tk  = ( 60,  35,  10)   # brun tronc
        # Corps central (racines tassées)
        dr(screen, tk,  (sx + 2, sy + 10, 10,  8))
        dr(screen, vc,  (sx + 3, sy +  6,  8,  6))
        dr(screen, vl,  (sx + 4, sy +  4,  6,  4))
        dr(screen, vc,  (sx + 5, sy +  2,  4,  4))
        # Yeux végétaux (bioluminescents)
        ey = (  0, 230, 120) if mob.state == "active" else ( 30, 120, 50)
        dr(screen, ey,  (sx + 4, sy +  4,  2,  2))
        dr(screen, ey,  (sx + 8, sy +  4,  2,  2))
        # Tentacules (selon phase d'animation)
        ph = mob._fly_phase
        off1 = int(math.sin(ph * 2.0) * 3)
        off2 = int(math.sin(ph * 2.0 + 2) * 3)
        # Tentacule gauche
        dr(screen, vl,  (sx - 4 + off1,      sy +  5,  5, 2))
        dr(screen, vg,  (sx - 7 + off1,      sy +  4,  4, 1))
        # Tentacule droit
        dr(screen, vl,  (sx + 13 + off2,     sy +  5,  5, 2))
        dr(screen, vg,  (sx + 17 + off2,     sy +  4,  4, 1))
        # Tentacule haut (vers le joueur si actif)
        if mob.state == "active":
            dr(screen, vg, (sx + 6, sy - 4 + off1, 2, 5))
        # Racines au sol
        dr(screen, tk,  (sx + 1, sy + 17,  3,  3))
        dr(screen, tk,  (sx + 6, sy + 17,  2,  3))
        dr(screen, tk,  (sx + 10,sy + 17,  3,  3))

    elif mob.mob_type == MOB_PENGUIN:
        dr = pygame.draw.rect
        bk = ( 20,  20,  30)   # noir
        wh = (230, 235, 240)   # ventre blanc
        yl = (230, 180,  30)   # bec/pattes orange
        # Corps noir
        dr(screen, bk, (sx + 1, sy + 1, 6, 7))
        # Ventre blanc
        dr(screen, wh, (sx + 2, sy + 3, 4, 4))
        # Tête
        dr(screen, bk, (sx + 2, sy,     4, 3))
        # Yeux
        dr(screen, wh, (sx + 3, sy + 1, 1, 1))
        dr(screen, wh, (sx + 5, sy + 1, 1, 1))
        # Bec
        dr(screen, yl, (sx + 6, sy + 2, 2, 1))
        # Pattes
        dr(screen, yl, (sx + 2, sy + 8, 2, 2))
        dr(screen, yl, (sx + 5, sy + 8, 2, 2))
        # Aileron
        dr(screen, bk, (sx,     sy + 3, 2, 4))
        dr(screen, bk, (sx + 6, sy + 3, 2, 4))

    elif mob.mob_type == MOB_POLAR_BEAR:
        dr = pygame.draw.rect
        wh = (240, 240, 245)   # blanc polaire
        dk = (200, 200, 210)   # ombre
        ns = ( 40,  30,  30)   # nez/yeux
        # Corps massif
        dr(screen, wh, (sx + 1, sy + 3, 14, 8))
        dr(screen, dk, (sx + 2, sy + 5, 12, 4))
        # Tête
        dr(screen, wh, (sx + 10, sy,     6, 5))
        # Oreilles
        dr(screen, wh, (sx + 10, sy - 1, 2, 2))
        dr(screen, wh, (sx + 14, sy - 1, 2, 2))
        # Yeux
        dr(screen, ns, (sx + 11, sy + 1, 1, 1))
        dr(screen, ns, (sx + 14, sy + 1, 1, 1))
        # Museau
        dr(screen, dk, (sx + 12, sy + 3, 3, 2))
        dr(screen, ns, (sx + 13, sy + 3, 1, 1))
        # Pattes
        dr(screen, wh, (sx + 2,  sy + 10, 3, 4))
        dr(screen, wh, (sx + 6,  sy + 10, 3, 4))
        dr(screen, wh, (sx + 9,  sy + 10, 3, 4))
        dr(screen, wh, (sx + 12, sy + 10, 3, 4))
        # Griffes
        dr(screen, ns, (sx + 2,  sy + 13, 3, 1))
        dr(screen, ns, (sx + 12, sy + 13, 3, 1))

    elif mob.mob_type == MOB_SCORPION:
        dr = pygame.draw.rect
        sc = (140, 100,  40)   # corps brun
        dk = (100,  70,  25)   # ombre
        st = (180,  50,  30)   # dard rouge
        # Corps
        dr(screen, sc, (sx + 2, sy + 3, 8, 4))
        dr(screen, dk, (sx + 3, sy + 4, 6, 2))
        # Queue recourbée (3 segments vers le haut)
        dr(screen, sc, (sx,     sy + 3, 3, 2))
        dr(screen, sc, (sx - 1, sy + 1, 2, 3))
        dr(screen, sc, (sx,     sy,     2, 2))
        dr(screen, st, (sx + 1, sy - 1, 1, 2))   # dard
        # Pinces
        dr(screen, sc, (sx + 9, sy + 2, 3, 2))
        dr(screen, sc, (sx + 9, sy + 4, 3, 2))
        # Yeux
        dr(screen, (0, 0, 0), (sx + 8, sy + 3, 1, 1))
        # Pattes
        dr(screen, dk, (sx + 3, sy + 6, 2, 2))
        dr(screen, dk, (sx + 5, sy + 6, 2, 2))
        dr(screen, dk, (sx + 7, sy + 6, 2, 2))

    elif mob.mob_type == MOB_VULTURE:
        dr = pygame.draw.rect
        vc = ( 60,  45,  35)   # brun foncé
        vl = ( 90,  70,  50)   # brun clair
        wo = int(math.sin(mob._fly_phase) * 1.5)
        # Ailes
        dr(screen, vc, (sx,     sy + 1 + wo, 3, 2))
        dr(screen, vc, (sx + 7, sy + 1 + wo, 3, 2))
        # Corps
        dr(screen, vc, (sx + 2, sy + 2, 6, 3))
        dr(screen, vl, (sx + 3, sy + 3, 4, 1))
        # Tête (cou nu)
        dr(screen, (180, 100, 80), (sx + 4, sy,     3, 2))
        # Bec
        dr(screen, (180, 150, 50), (sx + 7, sy + 1, 2, 1))
        # Oeil
        dr(screen, (0, 0, 0),      (sx + 5, sy,     1, 1))

    elif mob.mob_type == MOB_WOLF:
        dr = pygame.draw.rect
        wc = (140, 135, 125)   # gris loup
        wl = (170, 165, 155)   # ventre clair
        wd = (100, 95,  85)    # ombre
        # Corps
        dr(screen, wc, (sx + 1, sy + 3, 10, 5))
        dr(screen, wl, (sx + 3, sy + 5,  6, 2))
        # Tête
        dr(screen, wc, (sx + 8, sy,      4, 5))
        # Oreilles pointues
        dr(screen, wd, (sx + 8,  sy - 2, 2, 3))
        dr(screen, wd, (sx + 11, sy - 2, 2, 3))
        # Yeux
        dr(screen, (200, 180, 40), (sx + 9, sy + 1, 1, 1))
        dr(screen, (200, 180, 40), (sx + 11, sy + 1, 1, 1))
        # Museau
        dr(screen, wd, (sx + 10, sy + 3, 2, 1))
        dr(screen, (30, 20, 20), (sx + 11, sy + 3, 1, 1))
        # Queue
        dr(screen, wc, (sx - 1, sy + 3, 3, 2))
        dr(screen, wd, (sx - 2, sy + 2, 2, 2))
        # Pattes
        dr(screen, wc, (sx + 2, sy + 7, 2, 3))
        dr(screen, wc, (sx + 5, sy + 7, 2, 3))
        dr(screen, wc, (sx + 8, sy + 7, 2, 3))

    elif mob.mob_type == MOB_CAT:
        dr = pygame.draw.rect
        cc = (210, 155, 60)    # orange tabby
        cl = (235, 195, 110)   # ventre clair
        cd = (160, 110, 35)    # ombre/rayures
        # Corps
        dr(screen, cc, (sx + 1, sy + 2, 6, 3))
        dr(screen, cl, (sx + 2, sy + 3, 4, 1))
        # Tête
        dr(screen, cc, (sx + 5, sy,     3, 3))
        # Oreilles pointues
        dr(screen, cd, (sx + 5, sy - 1, 1, 2))
        dr(screen, cd, (sx + 7, sy - 1, 1, 2))
        # Yeux
        dr(screen, (100, 200, 80), (sx + 5, sy + 1, 1, 1))
        dr(screen, (100, 200, 80), (sx + 7, sy + 1, 1, 1))
        # Museau
        dr(screen, (220, 170, 170), (sx + 6, sy + 2, 1, 1))
        # Queue relevée
        dr(screen, cc, (sx - 1, sy + 2, 2, 1))
        dr(screen, cc, (sx - 2, sy + 1, 1, 2))
        # Pattes
        dr(screen, cc, (sx + 1, sy + 4, 2, 2))
        dr(screen, cc, (sx + 5, sy + 4, 2, 2))
        # Rayures
        dr(screen, cd, (sx + 2, sy + 2, 1, 1))
        dr(screen, cd, (sx + 4, sy + 2, 1, 1))

    elif mob.mob_type == MOB_GORGON:
        if mob._anchor_x is None:
            return   # pas encore initialisé

        dr     = pygame.draw.rect
        active = (mob.state == "chase")
        ph     = mob._fly_phase
        charge_state = getattr(mob, "_charge_state", "idle")
        # Wind-up : yeux rouges flashants (telegraph d'esquive pour le joueur)
        windup = (charge_state == "windup")
        # Dash : yeux jaunes (charge en cours)
        dashing = (charge_state == "dash")

        # Couleurs
        gc  = ( 12,  42,   8)   # corps sombre
        gs  = ( 28,  75,  18)   # écailles
        gsl = ( 48, 115,  28)   # reflet écailles
        gf  = (155, 210, 120)   # ventre/face
        if windup:
            # flash rouge synchronisé sur ph (~6 Hz)
            flash = (math.sin(ph * 12) > 0)
            ey = (255, 40, 40) if flash else (160, 20, 20)
        elif dashing:
            ey = (255, 220, 60)
        else:
            ey = (0, 245, 100) if active else (15, 140, 55)
        rk  = ( 28,  16,   4)   # racines

        # ── Positions clés en pixels-écran ────────────────────────────────────
        # La tête (mob.x, mob.y) → (sx, sy) via camera
        head_cx = sx + mw // 2
        head_cy = sy + mh // 2

        # Ancre : décalage horizontal par rapport à la tête courante
        anchor_dx_px = int((mob._anchor_x - mob.center_col()) * 16)
        anchor_cx    = head_cx + anchor_dx_px
        # Ancre 20 tiles (320px) sous la tête
        _BODY_PX = 320
        anchor_cy = sy + _BODY_PX

        # ── Corps sinueux (queue → tête, queue dessinée en premier) ──────────
        SEGS = 24
        for i in range(SEGS, 0, -1):
            t   = i / SEGS        # 1 = queue, 0 = tête
            t_h = 1.0 - t         # 0 = queue, 1 = tête

            # Position interpolée (anchor → head)
            bx = int(anchor_cx * t + head_cx * t_h)
            by = int(anchor_cy * t + head_cy * t_h)

            # Ondulation : forte à la tête, quasi-nulle à la queue (ancrée)
            wave = math.sin(ph * 2.8 - t * math.pi * 2.5) * (15 * t_h * t_h)
            bx  += int(wave)

            # Épaisseur : 24px queue → 14px tête
            bw = max(14, int(24 - 10 * t_h))
            bh = max(10, bw - 4)

            # Couleur : gradient sombre queue → légèrement plus clair tête
            r = min(255, 12 + int(18 * t_h))
            g = min(255, 42 + int(45 * t_h))
            b = 8
            dr(screen, (r, g, b), (bx - bw // 2, by - bh // 2, bw, bh))

            # Écailles alternées (bande claire au centre)
            if i % 2 == 1:
                sr = min(255, r + 22)
                sg = min(255, g + 50)
                dr(screen, (sr, sg, b + 10),
                   (bx - bw // 2 + 3, by - bh // 2 + 2, max(5, bw - 6), max(3, bh // 2)))

        # ── Racines / queue ancrée au sol ─────────────────────────────────────
        dr(screen, rk, (anchor_cx - 18, anchor_cy - 7,  36,  9))
        dr(screen, rk, (anchor_cx - 26, anchor_cy - 2,  16,  5))
        dr(screen, rk, (anchor_cx +  10, anchor_cy - 2, 16,  5))
        dr(screen, rk, (anchor_cx -  8, anchor_cy +  2, 18,  4))

        # ── Tête (dessinée en dernier = au-dessus du corps) ───────────────────
        # Corps de tête
        dr(screen, gc,  (sx,      sy,      mw,      mh))
        dr(screen, gs,  (sx + 4,  sy + 3,  mw - 8,  mh - 4))
        # Joues
        dr(screen, (8, 32, 5), (sx + 1,      sy + 2, 4, mh - 2))
        dr(screen, (8, 32, 5), (sx + mw - 5, sy + 2, 4, mh - 2))
        # Face/gueule (haut de la tête, orientée vers le joueur au-dessus)
        dr(screen, gf,  (sx + 5, sy,      mw - 10, 5))
        # Yeux bioluminescents
        dr(screen, ey,  (sx + 2,       sy + 5, 6, 6))
        dr(screen, ey,  (sx + mw - 8,  sy + 5, 6, 6))
        # Pupilles verticales (reptile)
        dr(screen, (0, 0, 0), (sx + 4,       sy + 7, 2, 4))
        dr(screen, (0, 0, 0), (sx + mw - 6,  sy + 7, 2, 4))
        # Crocs (dépassent en haut)
        fang = (215, 225, 190)
        dr(screen, fang, (sx + 7,       sy - 5, 4, 6))
        dr(screen, fang, (sx + mw - 11, sy - 5, 4, 6))
        dr(screen, (170, 180, 150), (sx + 8,       sy - 4, 2, 4))
        dr(screen, (170, 180, 150), (sx + mw - 10, sy - 4, 2, 4))
        # Motif d'écailles sur la tête
        dr(screen, gsl, (sx + 6,       sy + 11, 5, 3))
        dr(screen, gsl, (sx + mw - 11, sy + 11, 5, 3))
        dr(screen, gsl, (sx + 10,      sy + 17, 6, 3))
        # Langue fourchue (clignote en chasse)
        if active:
            tk_c = (200, 25, 25)
            tx   = sx + mw // 2
            dr(screen, tk_c, (tx - 1,             sy - 7, 2, 6))   # tige
            off  = int(math.sin(ph * 10) * 1)
            dr(screen, tk_c, (tx - 4 + off, sy - 10, 2, 4))        # fourche G
            dr(screen, tk_c, (tx + 2 + off, sy - 10, 2, 4))        # fourche D

        # ── Barre de vie (boss) ───────────────────────────────────────────────
        hp_frac = max(0.0, mob.hp / 50.0)
        bar_full = mw + 8
        bar_w    = int(bar_full * hp_frac)
        pygame.draw.rect(screen, (140, 15,  15), (sx - 4, sy - 12, bar_full, 3))
        pygame.draw.rect(screen, ( 30, 200, 80), (sx - 4, sy - 12, bar_w,    3))
        if active:
            pygame.draw.rect(screen, (0, 240, 120), (sx - 4, sy - 12, bar_full, 1))

    # ── Effet brûlure (zombie de surface au lever du soleil) ─────────────────
    if getattr(mob, 'burning', False):
        alpha = int(abs(math.sin(mob._fly_phase * 6)) * 180 + 50)
        burn  = pygame.Surface((mw, mh), pygame.SRCALPHA)
        burn.fill((255, 80, 0, min(230, alpha)))
        screen.blit(burn, (sx, sy))

    # ── Barre de vie temporaire (2s après dégâts) ─────────────────────────────
    if mob._hp_bar_timer > 0 and mob._max_hp > 0:
        hp_frac = max(0.0, mob.hp / mob._max_hp)
        bar_w = max(mw, 12)
        bar_h = 2
        bar_x = int(sx + (mw - bar_w) / 2)
        bar_y = int(sy - 4)
        # Fond sombre
        pygame.draw.rect(screen, (30, 30, 30), (bar_x, bar_y, bar_w, bar_h))
        # Remplissage : vert > 60%, orange > 30%, rouge sinon
        if hp_frac > 0.6:
            color = (40, 200, 40)
        elif hp_frac > 0.3:
            color = (220, 160, 20)
        else:
            color = (200, 30, 30)
        fill_w = max(0, int(bar_w * hp_frac))
        if fill_w > 0:
            pygame.draw.rect(screen, color, (bar_x, bar_y, fill_w, bar_h))
