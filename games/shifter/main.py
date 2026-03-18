"""
Point d'entrée du jeu Shifter.
Lance : sélection → course → résultats → boucle.
"""
import sys
import os

# S'assurer que le dossier courant est dans sys.path
sys.path.insert(0, os.path.dirname(__file__))

import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS

import scene_select
import scene_race
import scene_result


def main():
    pygame.init()
    pygame.joystick.init()
    pygame.event.clear()  # vider les événements résiduels du launcher
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Shifter – Drag Race 2J")

    # ── Écran d'accueil ───────────────────────────────────────────────────────
    _show_splash(screen)

    # ── Boucle principale ─────────────────────────────────────────────────────
    while True:
        # Sélection des voitures
        result = scene_select.run(screen, joysticks)
        if result is None:
            break

        car_indices = result  # (idx_j1, idx_j2)

        # Course
        race_results = scene_race.run(screen, joysticks, car_indices)
        if race_results is None:
            break

        # Résultats
        replay = scene_result.run(screen, race_results)
        if not replay:
            break

    pygame.quit()


def _show_splash(screen: pygame.Surface):
    """Petit écran de titre avant la sélection."""
    font_xl = pygame.font.SysFont("Arial", 42, bold=True)
    font_md = pygame.font.SysFont("Arial", 14, bold=True)
    font_sm = pygame.font.SysFont("Arial", 11)
    clock   = pygame.time.Clock()

    start = pygame.time.get_ticks()
    anim  = 0.0
    while True:
        dt     = clock.tick(60) / 1000.0
        anim  += dt
        events = pygame.event.get()
        for e in events:
            if e.type in (pygame.KEYDOWN, pygame.JOYBUTTONDOWN):
                return   # n'importe quelle touche → continuer

        # fond
        import math
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(10 + t * 8)
            g = int(8  + t * 6)
            b = int(25 + t * 20)
            pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Titre avec légère pulsation
        pulse = 1.0 + 0.05 * math.sin(anim * 3)
        title = font_xl.render("SHIFTER", True, (80, 200, 255))
        ts = pygame.transform.scale(title,
            (int(title.get_width() * pulse), int(title.get_height() * pulse)))
        screen.blit(ts, (SCREEN_WIDTH // 2 - ts.get_width() // 2, 70))

        sub = font_md.render("Drag Race 2 Joueurs", True, (160, 160, 220))
        screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 148))

        # Contrôles
        ctrl1 = font_sm.render("J1 : Croix directionnelle", True, (255, 100, 100))
        ctrl2 = font_sm.render("J2 : Boutons A B X Y",      True, (100, 180, 255))
        screen.blit(ctrl1, (SCREEN_WIDTH // 2 - ctrl1.get_width() // 2, 185))
        screen.blit(ctrl2, (SCREEN_WIDTH // 2 - ctrl2.get_width() // 2, 199))

        # Clignottement "Appuie sur un bouton"
        if int(anim * 2) % 2 == 0:
            msg = font_sm.render("Appuie sur un bouton pour commencer", True, (150, 150, 200))
            screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, 240))

        # Transition automatique après 8 s
        if pygame.time.get_ticks() - start > 8000:
            return

        pygame.display.flip()


if __name__ == "__main__":
    main()
