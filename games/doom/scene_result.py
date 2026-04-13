"""Écran de résultat (victoire ou mort).

Retourne True pour rejouer, False pour quitter.
"""
import pygame
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BTN_A, BTN_B, BTN_START
from quit_combo import QuitCombo


def run(screen: pygame.Surface, joysticks: list, outcome: str) -> bool:
    """
    outcome : 'win' | 'dead'
    Retourne True pour rejouer, False pour quitter.
    """
    clock  = pygame.time.Clock()
    qc     = QuitCombo()
    joy    = joysticks[0] if joysticks else None

    font_lg = pygame.font.SysFont("Courier New", 52, bold=True)
    font_sm = pygame.font.SysFont("Courier New", 14, bold=True)

    if outcome == 'win':
        title   = "NIVEAU TERMINÉ !"
        t_color = (80, 230, 80)
        sub     = "Tous les ennemis éliminés"
    else:
        title   = "VOUS ÊTES MORT"
        t_color = (230, 60, 50)
        sub     = "Appuyez sur A / ESPACE pour recommencer"

    hint = "A / ESPACE = rejouer    B / ÉCHAP = quitter"

    # ── Fond animé ────────────────────────────────────────────────────────
    BG_COL = (8, 8, 18) if outcome == 'win' else (18, 5, 5)
    tick   = 0

    while True:
        dt     = clock.tick(FPS) / 1000.0
        tick  += 1
        events = pygame.event.get()

        for e in events:
            qc.handle_event(e)
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_SPACE, pygame.K_RETURN):
                    return True
                if e.key == pygame.K_ESCAPE:
                    return False
            if e.type == pygame.JOYBUTTONDOWN:
                if e.button == BTN_A:
                    return True
                if e.button in (BTN_B, BTN_START):
                    return False

        if qc.update_and_draw(screen):
            return False

        screen.fill(BG_COL)

        # Titre (scintillement pour 'dead')
        alpha = 255
        if outcome == 'dead' and (tick // 18) % 2 == 0:
            alpha = 160
        surf = font_lg.render(title, True, t_color)
        surf.set_alpha(alpha)
        screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2,
                           SCREEN_HEIGHT // 2 - 60))

        sub_surf = font_sm.render(sub, True, (180, 180, 180))
        screen.blit(sub_surf, (SCREEN_WIDTH // 2 - sub_surf.get_width() // 2,
                                SCREEN_HEIGHT // 2 + 10))

        hint_surf = font_sm.render(hint, True, (100, 100, 100))
        screen.blit(hint_surf, (SCREEN_WIDTH // 2 - hint_surf.get_width() // 2,
                                 SCREEN_HEIGHT - 30))

        pygame.display.flip()
