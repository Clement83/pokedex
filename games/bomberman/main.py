"""
Point d'entrée du jeu Bomberman.
Boucle : splash → partie → résultat → boucle.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import math
import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BG_COLOR, TEXT_COLOR, P1_COLOR, P2_COLOR

import scene_game
import scene_result


def main():
    pygame.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    pygame.event.pump()
    pygame.event.clear()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Bomberman – 2 Joueurs")

    _show_splash(screen, joysticks)

    while True:
        result = scene_game.run(screen, joysticks)
        if result is None:
            break

        replay = scene_result.run(screen, result, joysticks)
        if not replay:
            break

    pygame.quit()


def _show_splash(screen, joysticks):
    """Écran titre Bomberman : grille en fond avec bombes et explosions animées."""
    clock   = pygame.time.Clock()
    start   = pygame.time.get_ticks()
    font_xl = pygame.font.SysFont("Arial", 54, bold=True)
    font_md = pygame.font.SysFont("Arial", 13, bold=True)
    font_sm = pygame.font.SysFont("Arial", 11)

    TS       = 20                         # taille d'une case de décor
    COLS_BG  = SCREEN_WIDTH  // TS        # 24
    ROWS_BG  = SCREEN_HEIGHT // TS        # 16

    _WALL  = ( 70,  70,  90)
    _BLOCK = (120,  75,  45)
    _FLOOR = ( 35,  35,  50)
    _BOMB  = ( 20,  20,  20)
    _EC    = (255, 230,  80)   # centre explosion
    _EB    = (255, 120,  20)   # branche explosion

    # Bombes sur des cases vides garanties (col impair ou row impair, pas de pilier)
    BOMBS         = [(2, 1), (7, 5), (13, 2), (20, 7), (5, 13), (18, 5), (11, 11)]
    BOMB_CYCLE    = 2.8    # durée mèche (s)
    EXPLO_DUR     = 0.55   # durée explosion (s)
    EXPLO_R       = 3      # portée cases
    FULL_CYCLE    = BOMB_CYCLE + EXPLO_DUR
    # Décalage pour que les bombes s'enchaînent
    bomb_offsets  = {pos: i * FULL_CYCLE / len(BOMBS) for i, pos in enumerate(BOMBS)}

    while True:
        clock.tick(FPS)
        t = (pygame.time.get_ticks() - start) / 1000.0

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type in (pygame.KEYDOWN, pygame.JOYBUTTONDOWN):
                return

        # ── Grille de fond ────────────────────────────────────────────────────
        for row in range(ROWS_BG):
            for col in range(COLS_BG):
                if row == 0 or row == ROWS_BG - 1 or col == 0 or col == COLS_BG - 1:
                    color = _WALL
                elif col % 2 == 0 and row % 2 == 0:
                    color = _WALL
                elif (col + row) % 7 == 0:
                    color = _BLOCK
                else:
                    color = _FLOOR
                pygame.draw.rect(screen, color, (col * TS, row * TS, TS, TS))
                pygame.draw.rect(screen, (0, 0, 0), (col * TS, row * TS, TS, TS), 1)

        # ── Bombes et explosions ──────────────────────────────────────────────
        for (bc, br) in BOMBS:
            timer = (t - bomb_offsets[(bc, br)]) % FULL_CYCLE
            bx = bc * TS + TS // 2
            by = br * TS + TS // 2
            if timer < BOMB_CYCLE:
                ratio = timer / BOMB_CYCLE
                pygame.draw.circle(screen, _BOMB, (bx, by), TS // 2 - 2)
                pygame.draw.circle(screen, (80, 80, 110), (bx, by), TS // 2 - 2, 1)
                # Mèche qui raccourcit
                flen = max(0, int(8 * (1.0 - ratio)))
                if flen:
                    pygame.draw.line(screen, (160, 120, 40),
                                     (bx + 2, by - TS // 2 + 2),
                                     (bx + 2 + flen, by - TS // 2 + 2 - flen), 2)
                # Étincelle en bout de mèche
                if ratio > 0.65:
                    sx = bx + 2 + flen
                    sy = by - TS // 2 + 2 - flen
                    sr = 2 + int(2 * math.sin(t * 18))
                    pygame.draw.circle(screen, (255, 220, 50), (sx, sy), max(1, sr))
            else:
                ef    = (timer - BOMB_CYCLE) / EXPLO_DUR   # 0 → 1
                alpha = 1.0 - ef
                ec    = tuple(int(c * alpha) for c in _EC)
                # Centre
                pygame.draw.rect(screen, ec, (bc * TS, br * TS, TS, TS))
                # Branches avec fondu progressif
                for d in range(1, EXPLO_R + 1):
                    fade      = alpha * (1.0 - d / (EXPLO_R + 1))
                    col_beam  = tuple(int(c * fade) for c in _EB)
                    for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nc, nr = bc + dc * d, br + dr * d
                        if 0 < nc < COLS_BG and 0 < nr < ROWS_BG:
                            pygame.draw.rect(screen, col_beam, (nc * TS, nr * TS, TS, TS))

        # ── Panneau titre ─────────────────────────────────────────────────────
        title  = font_xl.render("BOMBERMAN", True, (255, 200, 50))
        shadow = font_xl.render("BOMBERMAN", True, ( 80,  40,   0))
        tx = (SCREEN_WIDTH  - title.get_width())  // 2
        ty = (SCREEN_HEIGHT - title.get_height()) // 2 - 24
        pad   = 10
        panel = pygame.Surface((title.get_width() + pad * 2,
                                 title.get_height() + pad * 2), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 190))
        screen.blit(panel,  (tx - pad,  ty - pad))
        screen.blit(shadow, (tx + 3,    ty + 3))
        screen.blit(title,  (tx,        ty))

        sub = font_md.render("2 Joueurs", True, TEXT_COLOR)
        screen.blit(sub, ((SCREEN_WIDTH - sub.get_width()) // 2,
                           ty + title.get_height() + 2))

        cy = ty + title.get_height() + 20
        p1 = font_sm.render("J1 : Z/Q/S/D  |  Bombe : E  / Btn 12", True, P1_COLOR)
        p2 = font_sm.render("J2 : O/K/L/M  |  Bombe : P  / Btn 17", True, P2_COLOR)
        screen.blit(p1, ((SCREEN_WIDTH - p1.get_width()) // 2, cy))
        screen.blit(p2, ((SCREEN_WIDTH - p2.get_width()) // 2, cy + 15))

        if int(t * 2) % 2 == 0:
            hint = font_sm.render("Appuie sur un bouton pour jouer", True, (160, 160, 210))
            screen.blit(hint, ((SCREEN_WIDTH - hint.get_width()) // 2, SCREEN_HEIGHT - 18))

        pygame.display.flip()


if __name__ == "__main__":
    main()
