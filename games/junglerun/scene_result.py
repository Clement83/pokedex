"""Scène de fin de partie : annonce le gagnant + propose rejouer."""
import math
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    PLAYER_J1, PLAYER_J2, TEXT_COLOR,
    J1_DPAD_BTNS, J2_FACE_BTNS, J1_KEYS, J2_KEYS,
)
from quit_combo import QuitCombo


def run(screen, winner: int, dist1: int, dist2: int) -> bool:
    """Affiche le gagnant. Retourne True pour rejouer, False pour quitter."""
    clock = pygame.time.Clock()
    font_xl = pygame.font.SysFont("Arial", 42, bold=True)
    font_md = pygame.font.SysFont("Arial", 16, bold=True)
    font_sm = pygame.font.SysFont("Arial", 12)

    quit_combo = QuitCombo()
    anim = 0.0

    if winner == 0:
        title, color = "Joueur 1 gagne !", PLAYER_J1
    elif winner == 1:
        title, color = "Joueur 2 gagne !", PLAYER_J2
    else:
        title, color = "Égalité !", TEXT_COLOR

    while True:
        dt = clock.tick(FPS) / 1000.0
        anim += dt

        for e in pygame.event.get():
            quit_combo.handle_event(e)
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.KEYDOWN and e.key in (
                    pygame.K_RETURN, pygame.K_SPACE, *J1_KEYS, *J2_KEYS):
                return True
            if e.type == pygame.JOYBUTTONDOWN and e.button in (
                    *J1_DPAD_BTNS, *J2_FACE_BTNS):
                return True

        screen.fill((22, 30, 25))

        # Titre pulsé.
        pulse = 1.0 + 0.04 * math.sin(anim * 4)
        raw = font_xl.render(title, True, color)
        scaled = pygame.transform.scale(
            raw, (int(raw.get_width() * pulse), int(raw.get_height() * pulse)))
        screen.blit(scaled, (SCREEN_WIDTH // 2 - scaled.get_width() // 2, 56))

        # Distances finales.
        d1 = font_md.render(f"J1 : {dist1} m", True, PLAYER_J1)
        d2 = font_md.render(f"J2 : {dist2} m", True, PLAYER_J2)
        screen.blit(d1, (SCREEN_WIDTH // 2 - d1.get_width() // 2, 145))
        screen.blit(d2, (SCREEN_WIDTH // 2 - d2.get_width() // 2, 170))

        # Replay.
        if int(anim * 2) % 2 == 0:
            msg = font_sm.render("Appuyez sur n'importe quel bouton pour rejouer", True, (200, 200, 200))
            screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, 235))

        if quit_combo.update_and_draw(screen):
            return False
        pygame.display.flip()
