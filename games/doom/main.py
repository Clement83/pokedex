"""Point d'entrée du jeu DOOM-like.
Boucle : splash → partie → résultat → boucle.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pygame
import math
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BTN_A, BTN_START

import scene_game
import scene_result


def main():
    pygame.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    pygame.event.pump()
    pygame.event.clear()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("DOOM – Arcade")

    _show_splash(screen, joysticks)

    while True:
        outcome = scene_game.run(screen, joysticks)
        if outcome is None:
            break

        replay = scene_result.run(screen, joysticks, outcome)
        if not replay:
            break

    pygame.quit()


# ── Écran splash ──────────────────────────────────────────────────────────────

def _show_splash(screen: pygame.Surface, joysticks):
    clock    = pygame.time.Clock()
    joy      = joysticks[0] if joysticks else None
    font_xl  = pygame.font.SysFont("Courier New", 72, bold=True)
    font_lg  = pygame.font.SysFont("Courier New", 22, bold=True)
    font_sm  = pygame.font.SysFont("Courier New", 12)

    tick     = 0
    RED      = (200, 30, 30)
    DARK_RED = (120, 15, 15)
    BG       = (8, 5, 5)

    while True:
        clock.tick(FPS)
        tick += 1

        events = pygame.event.get()
        for e in events:
            if e.type == pygame.KEYDOWN and e.key in (
                    pygame.K_SPACE, pygame.K_RETURN):
                return
            if e.type == pygame.JOYBUTTONDOWN and e.button in (BTN_A, BTN_START):
                return

        screen.fill(BG)

        # Titre avec effet de scintillement
        alpha = 255 if (tick // 12) % 3 != 0 else 190
        title = font_xl.render("DOOM", True, RED)
        title.set_alpha(alpha)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2,
                             SCREEN_HEIGHT // 2 - 90))

        sub = font_lg.render("Raycaster Arcade Edition", True, (160, 100, 60))
        screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2,
                          SCREEN_HEIGHT // 2 - 10))

        # Contrôles
        _blit_centered(screen, font_sm, "Joystick / Flèches  :  avancer · tourner",
                       (140, 140, 140), SCREEN_HEIGHT // 2 + 30)
        _blit_centered(screen, font_sm, "R1 / A  :  strafe gauche / tirer",
                       (140, 140, 140), SCREEN_HEIGHT // 2 + 48)
        _blit_centered(screen, font_sm, "SELECT+START  :  quitter",
                       (100, 100, 100), SCREEN_HEIGHT // 2 + 66)

        prompt = "A / ESPACE  –  Lancer"
        blink  = (tick // 20) % 2 == 0
        if blink:
            _blit_centered(screen, font_lg, prompt, (220, 180, 60),
                           SCREEN_HEIGHT - 40)

        pygame.display.flip()


def _blit_centered(screen, font, text, color, y):
    surf = font.render(text, True, color)
    screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, y))


if __name__ == "__main__":
    main()
