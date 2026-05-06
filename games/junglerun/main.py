"""Point d'entrée Jungle Run.

Runner 2 joueurs en split-screen. Saut + double saut, plateformes pourries,
plumes-bouclier, séismes. Survie pure : le dernier en vie gagne.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT

import scene_game
import scene_result


def main():
    pygame.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    pygame.event.pump()
    pygame.event.clear()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Jungle Run – 2 Joueurs")

    while True:
        result = scene_game.run(screen, joysticks)
        if result is None:
            break

        winner, d1, d2 = result
        replay = scene_result.run(screen, winner, d1, d2)
        if not replay:
            break

    pygame.quit()


if __name__ == "__main__":
    main()
