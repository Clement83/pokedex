"""
Point d'entrée du jeu Bomberman.
Boucle : splash → partie → résultat → boucle.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

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
    font_xl = pygame.font.SysFont("Arial", 52, bold=True)
    font_md = pygame.font.SysFont("Arial", 16)
    font_sm = pygame.font.SysFont("Arial", 12)
    clock   = pygame.time.Clock()

    while True:
        clock.tick(FPS)
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type in (pygame.KEYDOWN, pygame.JOYBUTTONDOWN):
                return

        screen.fill(BG_COLOR)

        title = font_xl.render("BOMBERMAN", True, (255, 200, 50))
        screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 70))

        sub = font_md.render("2 Joueurs", True, TEXT_COLOR)
        screen.blit(sub, ((SCREEN_WIDTH - sub.get_width()) // 2, 140))

        hint = font_sm.render("Appuie sur un bouton pour jouer", True, (140, 140, 180))
        screen.blit(hint, ((SCREEN_WIDTH - hint.get_width()) // 2, 175))

        p1 = font_sm.render("J1 : Z/Q/S/D  |  Bombe : E      |  Manette : D-pad / btn 12", True, (255, 130, 130))
        p2 = font_sm.render("J2 : O/K/L/M  |  Bombe : P      |  Manette : X/B/Y/A / btn 17", True, (130, 190, 255))
        screen.blit(p1, ((SCREEN_WIDTH - p1.get_width()) // 2, 225))
        screen.blit(p2, ((SCREEN_WIDTH - p2.get_width()) // 2, 248))

        pygame.display.flip()


if __name__ == "__main__":
    main()
