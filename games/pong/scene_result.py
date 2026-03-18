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


def run(screen, winner: int, joysticks) -> bool:
    clock   = pygame.time.Clock()
    font_xl = pygame.font.SysFont("Arial", 44, bold=True)
    font_md = pygame.font.SysFont("Arial", 16, bold=True)
    font_sm = pygame.font.SysFont("Arial", 11)

    joystick = joysticks[0] if joysticks else None
    btn_held = set()

    col   = (PADDLE_J1, PADDLE_J2)[winner]
    name  = f"Joueur {winner + 1}"
    anim  = 0.0
    sel   = 0   # 0 = Rejouer, 1 = Quitter
    options = ["Rejouer", "Quitter"]

    while True:
        dt     = clock.tick(FPS) / 1000.0
        anim  += dt
        events = pygame.event.get()

        for e in events:
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.JOYBUTTONDOWN:
                btn_held.add(e.button)
            if e.type == pygame.JOYBUTTONUP:
                btn_held.discard(e.button)

            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_LEFT, pygame.K_RIGHT,
                             pygame.K_x, pygame.K_b):
                    sel = 1 - sel
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return sel == 0
                elif e.key == pygame.K_ESCAPE:
                    return False

            if e.type == pygame.JOYHATMOTION:
                if e.value[0] != 0:
                    sel = 1 - sel

            if e.type == pygame.JOYBUTTONDOWN:
                if e.button == 0:   # A → confirmer
                    return sel == 0
                if e.button in (2, 1):  # X / B → changer sélection
                    sel = 1 - sel

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

        # Options
        for i, label in enumerate(options):
            c = (255, 255, 255) if i == sel else (80, 80, 100)
            surf = font_md.render(label, True, c)
            x = SCREEN_WIDTH // 4 + i * SCREEN_WIDTH // 2
            y = SCREEN_HEIGHT // 2 + 40
            screen.blit(surf, (x - surf.get_width() // 2, y))
            if i == sel:
                pygame.draw.rect(screen, c,
                                 (x - surf.get_width() // 2 - 6, y - 3,
                                  surf.get_width() + 12, surf.get_height() + 6),
                                 2, border_radius=4)

        hint = font_sm.render("◄► Sélection   A/Entrée Confirmer", True, (60, 60, 80))
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2,
                           SCREEN_HEIGHT - 16))

        pygame.display.flip()
