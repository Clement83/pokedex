"""
Scène de résultat Bomberman.
Retourne True (rejouer) ou False (quitter).
"""
import pygame
import math
import sys

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    BG_COLOR, TEXT_COLOR, P1_COLOR, P2_COLOR,
    BTN_A, BTN_B, BTN_X, BTN_Y,
)
from quit_combo import QuitCombo

_RESULTS = {
    0: ("Joueur 1 gagne !", P1_COLOR),
    1: ("Joueur 2 gagne !", P2_COLOR),
    2: ("Égalité !", (220, 200, 80)),
}


def run(screen, result, joysticks) -> bool:
    font_xl = pygame.font.SysFont("Arial", 44, bold=True)
    font_md = pygame.font.SysFont("Arial", 16, bold=True)
    font_sm = pygame.font.SysFont("Arial", 12)
    clock   = pygame.time.Clock()

    text, color = _RESULTS.get(result, ("???", TEXT_COLOR))
    quit_combo  = QuitCombo()
    anim        = 0.0

    pygame.event.clear()   # purge les événements résiduels

    while True:
        dt   = clock.tick(FPS) / 1000.0
        anim += dt
        events = pygame.event.get()

        for e in events:
            quit_combo.handle_event(e)
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return True
                if e.key == pygame.K_ESCAPE:
                    return False
            if e.type == pygame.JOYBUTTONDOWN:
                if e.button in (BTN_A, BTN_B, BTN_X, BTN_Y):
                    return True   # n'importe quel bouton ABXY = rejouer

        screen.fill(BG_COLOR)

        # Titre animé
        pulse = 1.0 + 0.04 * math.sin(anim * 4)
        title = font_xl.render(text, True, color)
        ts    = pygame.transform.scale(
            title,
            (int(title.get_width() * pulse), int(title.get_height() * pulse)),
        )
        screen.blit(ts, ((SCREEN_WIDTH - ts.get_width()) // 2, 70))

        # Instructions
        replay = font_md.render("A / B / X / Y  →  Rejouer", True, (200, 200, 220))
        screen.blit(replay, ((SCREEN_WIDTH - replay.get_width()) // 2, 170))
        pygame.draw.rect(
            screen, (200, 200, 220),
            ((SCREEN_WIDTH - replay.get_width()) // 2 - 8, 167,
             replay.get_width() + 16, replay.get_height() + 6),
            2, border_radius=4,
        )

        hint = font_sm.render("SELECT+START  /  Échap  →  Quitter", True, (110, 110, 140))
        screen.blit(hint, ((SCREEN_WIDTH - hint.get_width()) // 2, 220))

        if quit_combo.update_and_draw(screen):
            return False

        pygame.display.flip()
