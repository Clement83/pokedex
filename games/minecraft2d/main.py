"""
Point d'entrée du jeu Minecraft 2D.
"""
import sys
import os
import math

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    TEXT_COLOR, P1_COLOR, P2_COLOR,
    TILE_COLORS, TILE_DIRT, TILE_GRASS, TILE_STONE, TILE_WOOD, TILE_COAL, TILE_AIR,
)

import db as _db
import scene_select
import scene_game

# ── Palette Minecraft ─────────────────────────────────────────────────────────
_MC_GREEN  = ( 90, 180,  30)   # herbe / logo vert
_MC_BROWN  = (101,  67,  33)   # terre
_MC_GRAY   = (128, 128, 128)   # pierre
_MC_COAL   = ( 60,  60,  70)   # charbon
_MC_SKY    = ( 58, 109, 171)   # ciel Minecraft
_MC_YELLOW = (255, 215,   0)   # highlight titre
_MC_SHADOW = ( 60,  40,  20)   # ombre titre
_MC_PANEL  = (  0,   0,   0, 180)

# Liste des blocs du décor de fond (col, row, tile_color)
_SCENERY = [
    # Sol herbe
    *[((i, 14), _MC_GREEN) for i in range(30)],
    *[((i, 15), _MC_BROWN) for i in range(30)],
    *[((i, 16), _MC_BROWN) for i in range(30)],
    *[((i, 17), _MC_GRAY)  for i in range(30)],
    # Arbre gauche
    ((2, 11), _MC_BROWN), ((2, 12), _MC_BROWN), ((2, 13), _MC_BROWN),
    ((1, 10), _MC_GREEN), ((2, 10), _MC_GREEN), ((3, 10), _MC_GREEN),
    ((1, 11), _MC_GREEN), ((3, 11), _MC_GREEN),
    # Arbre droit
    ((26, 11), _MC_BROWN), ((26, 12), _MC_BROWN), ((26, 13), _MC_BROWN),
    ((25, 10), _MC_GREEN), ((26, 10), _MC_GREEN), ((27, 10), _MC_GREEN),
    ((25, 11), _MC_GREEN), ((27, 11), _MC_GREEN),
    # Charbon dans la pierre
    ((5, 17), _MC_COAL),
    ((12, 17), _MC_COAL),
    ((22, 17), _MC_COAL),
]


def _draw_mc_title(screen, font_big, font_shadow, t):
    """Titre style Minecraft : texte jaune avec ombre décalée + léger wiggle."""
    text = "MINECRAFT 2D"
    wiggle = int(math.sin(t * 2.5) * 2)
    x = (SCREEN_WIDTH - font_big.size(text)[0]) // 2
    y = 18 + wiggle
    # Ombre
    shadow = font_shadow.render(text, True, _MC_SHADOW)
    screen.blit(shadow, (x + 3, y + 3))
    # Texte principal
    surf = font_big.render(text, True, _MC_YELLOW)
    screen.blit(surf, (x, y))


def _draw_scenery(screen, ts):
    """Décor pixelisé en bas d'écran."""
    for (col, row), color in _SCENERY:
        pygame.draw.rect(screen, color, (col * ts, row * ts, ts, ts))
        # Grille noire légère
        pygame.draw.rect(screen, (0, 0, 0), (col * ts, row * ts, ts, ts), 1)


def _draw_stickman(screen, bx, by, color, flip=False):
    """Petit bonhomme Minecraft immobile."""
    skin = (255, 210, 160)
    dark = tuple(max(0, v - 55) for v in color)
    d = -1 if flip else 1
    # Tête
    pygame.draw.rect(screen, skin,  (bx,     by,      10, 10))
    pygame.draw.rect(screen, (0,0,0),(bx,     by,      10, 10), 1)
    pygame.draw.rect(screen, (0,0,0),(bx + 2, by + 3,   2,  2))
    pygame.draw.rect(screen, (0,0,0),(bx + 6, by + 3,   2,  2))
    # Corps
    pygame.draw.rect(screen, color,  (bx,     by + 11, 10, 10))
    pygame.draw.rect(screen, (0,0,0),(bx,     by + 11, 10, 10), 1)
    # Jambes
    pygame.draw.rect(screen, dark,   (bx,     by + 22,  4, 10))
    pygame.draw.rect(screen, dark,   (bx + 6, by + 22,  4, 10))
    pygame.draw.rect(screen, (0,0,0),(bx,     by + 22,  4, 10), 1)
    pygame.draw.rect(screen, (0,0,0),(bx + 6, by + 22,  4, 10), 1)


def _show_splash(screen, joysticks):
    ts = 16   # taille d'un tile décoratif
    font_big    = pygame.font.SysFont("Courier New", 32, bold=True)
    font_shadow = pygame.font.SysFont("Courier New", 32, bold=True)
    font_med    = pygame.font.SysFont("Courier New", 13, bold=True)
    font_sm     = pygame.font.SysFont("Courier New", 11)
    clock       = pygame.time.Clock()
    start       = pygame.time.get_ticks()

    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type in (pygame.KEYDOWN, pygame.JOYBUTTONDOWN):
                return

        t = (pygame.time.get_ticks() - start) / 1000.0
        blink = int(t * 2) % 2 == 0   # clignote à ~2 Hz

        # ── Fond ciel dégradé façon Minecraft ─────────────────────────────
        for y in range(SCREEN_HEIGHT):
            r = int(_MC_SKY[0] + (_MC_SKY[0] * 0.3) * y / SCREEN_HEIGHT)
            g = int(_MC_SKY[1] + (_MC_SKY[1] * 0.1) * y / SCREEN_HEIGHT)
            b = int(_MC_SKY[2] - (_MC_SKY[2] * 0.3) * y / SCREEN_HEIGHT)
            pygame.draw.line(screen, (min(255,r), min(255,g), max(0,b)), (0, y), (SCREEN_WIDTH, y))

        # ── Décor ─────────────────────────────────────────────────────────
        _draw_scenery(screen, ts)

        # ── Petits bonhommes de chaque côté ───────────────────────────────
        _draw_stickman(screen, 60,  14 * ts - 32, P1_COLOR)
        _draw_stickman(screen, SCREEN_WIDTH - 80, 14 * ts - 32, P2_COLOR, flip=True)

        # ── Titre ─────────────────────────────────────────────────────────
        _draw_mc_title(screen, font_big, font_shadow, t)

        # ── Panel noir semi-transparent ───────────────────────────────────
        panel = pygame.Surface((420, 160), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 160))
        screen.blit(panel, ((SCREEN_WIDTH - 420) // 2, 60))

        # ── Contrôles console uniquement ──────────────────────────────────
        cy = 68
        lh = 15   # line height

        header = font_med.render("── CONTROLES ──", True, _MC_YELLOW)
        screen.blit(header, ((SCREEN_WIDTH - header.get_width()) // 2, cy))
        cy += lh + 4

        lines_p1 = [
            ("J1", "Axe gauche / D-pad : se deplacer", P1_COLOR),
            ("J1", "Haut = Saut", P1_COLOR),
            ("J1", "Btn 8  = Miner (maintenu)", P1_COLOR),
            ("J1", "Btn 12 + dirs = Slot  |  + Btn8 = Poser", P1_COLOR),
        ]
        lines_p2 = [
            ("J2", "Axe gauche / ABXY : se deplacer", P2_COLOR),
            ("J2", "Haut = Saut", P2_COLOR),
            ("J2", "Btn 13 = Miner (maintenu)", P2_COLOR),
            ("J2", "Btn 17 + dirs = Slot  |  + Btn13 = Poser", P2_COLOR),
        ]

        col_x = [SCREEN_WIDTH // 2 - 200, SCREEN_WIDTH // 2 + 10]
        for lines, cx in zip([lines_p1, lines_p2], col_x):
            row_y = cy
            for tag, txt, color in lines:
                prefix = font_sm.render(tag + " > ", True, color)
                body   = font_sm.render(txt, True, TEXT_COLOR)
                screen.blit(prefix, (cx, row_y))
                screen.blit(body,   (cx + prefix.get_width(), row_y))
                row_y += lh

        # Séparateur vertical
        mx = SCREEN_WIDTH // 2
        pygame.draw.line(screen, (100, 100, 100), (mx, cy), (mx, cy + lh * 4), 1)

        cy += lh * 4 + 6
        quit_txt = font_sm.render("SELECT + START = Quitter", True, (160, 160, 160))
        screen.blit(quit_txt, ((SCREEN_WIDTH - quit_txt.get_width()) // 2, cy))

        cy += lh + 6
        if blink:
            press = font_med.render(">>> Appuie sur un bouton <<<", True, _MC_YELLOW)
            screen.blit(press, ((SCREEN_WIDTH - press.get_width()) // 2, cy))

        pygame.display.flip()



def main():
    pygame.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    pygame.event.pump()
    pygame.event.clear()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Minecraft 2D – 2 Joueurs")

    _db.init()

    _show_splash(screen, joysticks)

    result = scene_select.run(screen, joysticks)
    if result is not None:
        slot_id, seed = result
        scene_game.run(screen, joysticks, slot_id, seed)

    pygame.quit()


if __name__ == "__main__":
    main()
