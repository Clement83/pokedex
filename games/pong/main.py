"""
Point d'entrée du jeu Pong.
Boucle : splash → partie → résultat → boucle.
"""
import sys
import os
import math

sys.path.insert(0, os.path.dirname(__file__))

import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BG_COLOR, PADDLE_J1, PADDLE_J2, TEXT_COLOR

import scene_game
import scene_result


def main():
    pygame.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Pong – 2 Joueurs")

    _show_splash(screen, joysticks)

    while True:
        winner = scene_game.run(screen, joysticks)
        if winner is None:
            break

        replay = scene_result.run(screen, winner, joysticks)
        if not replay:
            break

    pygame.quit()


def _show_splash(screen: pygame.Surface, joysticks):
    font_xl = pygame.font.SysFont("Arial", 52, bold=True)
    font_md = pygame.font.SysFont("Arial", 14, bold=True)
    font_sm = pygame.font.SysFont("Arial", 11)
    clock   = pygame.time.Clock()

    anim = 0.0
    while True:
        dt     = clock.tick(60) / 1000.0
        anim  += dt
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type in (pygame.KEYDOWN, pygame.JOYBUTTONDOWN):
                return

        screen.fill(BG_COLOR)

        # Filet décoratif
        for ny in range(0, SCREEN_HEIGHT, 16):
            pygame.draw.rect(screen, (20, 20, 40),
                             (SCREEN_WIDTH // 2 - 2, ny, 4, 8))

        # Raquettes décoratives animées
        offset_j1 = 20 + int(15 * math.sin(anim * 1.8))
        offset_j2 = 20 + int(15 * math.sin(anim * 1.8 + math.pi))
        pygame.draw.rect(screen, PADDLE_J1,
                         (24, SCREEN_HEIGHT // 2 - 30 + offset_j1, 10, 60),
                         border_radius=3)
        pygame.draw.rect(screen, PADDLE_J2,
                         (SCREEN_WIDTH - 34, SCREEN_HEIGHT // 2 - 30 + offset_j2, 10, 60),
                         border_radius=3)

        # Balle qui rebondit
        bx = SCREEN_WIDTH  // 2 + int((SCREEN_WIDTH  // 2 - 40) * math.sin(anim * 2.5))
        by = SCREEN_HEIGHT // 2 + int((SCREEN_HEIGHT // 2 - 20) * math.sin(anim * 3.1))
        pygame.draw.circle(screen, (240, 240, 240), (bx, by), 5)

        # Titre
        pulse = 1.0 + 0.04 * math.sin(anim * 3)
        title = font_xl.render("PONG", True, TEXT_COLOR)
        ts = pygame.transform.scale(
            title,
            (int(title.get_width() * pulse), int(title.get_height() * pulse)),
        )
        screen.blit(ts, (SCREEN_WIDTH // 2 - ts.get_width() // 2, 50))

        sub = font_md.render("2 Joueurs", True, (140, 140, 180))
        screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 120))

        ctrl1 = font_sm.render("J1 : ↑ ↓  (flèches)", True, PADDLE_J1)
        ctrl2 = font_sm.render("J2 : N (haut)   M (bas)   /   A / B", True, PADDLE_J2)
        screen.blit(ctrl1, (SCREEN_WIDTH // 2 - ctrl1.get_width() // 2, 155))
        screen.blit(ctrl2, (SCREEN_WIDTH // 2 - ctrl2.get_width() // 2, 169))

        if int(anim * 2) % 2 == 0:
            msg = font_sm.render("Appuie sur un bouton pour commencer", True, (100, 100, 140))
            screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, 240))

        pygame.display.flip()
