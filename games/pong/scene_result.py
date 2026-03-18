"""
Scène de résultat Pong.
Affiche le gagnant et propose Rejouer / Quitter.
Retourne True pour rejouer, False pour quitter.
"""
import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    BG_COLOR, PADDLE_J1, PADDLE_J2, TEXT_COLOR,
    CTRL,
)
from quit_combo import QuitCombo


def run(screen, winner: int, joysticks) -> bool:
    clock   = pygame.time.Clock()
    font_xl = pygame.font.SysFont("Arial", 44, bold=True)
    font_md = pygame.font.SysFont("Arial", 16, bold=True)
    font_sm = pygame.font.SysFont("Arial", 11)

    joystick = joysticks[0] if joysticks else None
    btn_held = set()
    quit     = QuitCombo()

    col   = (PADDLE_J1, PADDLE_J2)[winner]
    name  = f"Joueur {winner + 1}"
    anim  = 0.0

    while True:
        dt     = clock.tick(FPS) / 1000.0
        anim  += dt
        events = pygame.event.get()

        for e in events:
            quit.handle_event(e)
            if e.type == pygame.JOYBUTTONDOWN:
                btn_held.add(e.button)
            if e.type == pygame.JOYBUTTONUP:
                btn_held.discard(e.button)

            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_n):
                    return True

            if e.type == pygame.JOYBUTTONDOWN:
                if e.button in (0, 1, 2, 3):   # n'importe quel bouton → rejouer
                    return True

        import math
        screen.fill(BG_COLOR)

        # Titre
        pulse = 1.0 + 0.04 * math.sin(anim * 4)
        title = font_xl.render(f"{name} gagne !", True, col)
        ts = pygame.transform.scale(
            title,
            (int(title.get_width() * pulse), int(title.get_height() * pulse)),
        )
        screen.blit(ts, (SCREEN_WIDTH // 2 - ts.get_width() // 2, 60))

        # Option rejouer
        surf = font_md.render("Rejouer", True, (255, 255, 255))
        screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, SCREEN_HEIGHT // 2 + 40))
        pygame.draw.rect(screen, (255, 255, 255),
                         (SCREEN_WIDTH // 2 - surf.get_width() // 2 - 6,
                          SCREEN_HEIGHT // 2 + 37,
                          surf.get_width() + 12, surf.get_height() + 6),
                         2, border_radius=4)

        if quit.update_and_draw(screen):
            return False  # retour launcher sans rejouer
        pygame.display.flip()
