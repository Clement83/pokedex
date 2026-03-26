"""Rendu graphique du jeu Pong."""
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    BG_COLOR, PADDLE_J1, PADDLE_J2, BALL_COLOR, NET_COLOR,
    PADDLE_W, PADDLE_H, BALL_SIZE,
)
from engine.ball import PADDLE_X_J1, PADDLE_X_J2


def draw(screen, fonts, paddle_y, scores, ball_x, ball_y, trail, pause_t, flash_who):
    """Dessine une frame complete (fond, filet, raquettes, balle, scores, flash)."""
    font_sc, font_md = fonts
    screen.fill(BG_COLOR)

    # Filet central
    for ny in range(0, SCREEN_HEIGHT, 16):
        pygame.draw.rect(screen, NET_COLOR, (SCREEN_WIDTH // 2 - 2, ny, 4, 8))

    # Raquettes
    pygame.draw.rect(screen, PADDLE_J1,
                     (PADDLE_X_J1, int(paddle_y[0]), PADDLE_W, PADDLE_H),
                     border_radius=3)
    pygame.draw.rect(screen, PADDLE_J2,
                     (PADDLE_X_J2, int(paddle_y[1]), PADDLE_W, PADDLE_H),
                     border_radius=3)

    # Trainee phosphoree
    n = len(trail)
    if n:
        for i, (ttx, tty) in enumerate(trail):
            f = 1.0 - i / n
            r = max(1, int((BALL_SIZE // 2) * f))
            lv = int(8 + 232 * f * f)
            pygame.draw.circle(screen, (lv, lv, lv), (ttx, tty), r)

    # Balle (clignote pendant la pause)
    if pause_t <= 0 or int(pause_t * 8) % 2 == 0:
        pygame.draw.circle(screen, BALL_COLOR,
                           (int(ball_x), int(ball_y)), BALL_SIZE // 2)

    # Scores
    s0 = font_sc.render(str(scores[0]), True, PADDLE_J1)
    s1 = font_sc.render(str(scores[1]), True, PADDLE_J2)
    screen.blit(s0, (SCREEN_WIDTH // 4     - s0.get_width() // 2, 5))
    screen.blit(s1, (3 * SCREEN_WIDTH // 4 - s1.get_width() // 2, 5))

    # Message flash apres un point
    if pause_t > 0 and flash_who >= 0:
        col = (PADDLE_J1, PADDLE_J2)[flash_who]
        msg = font_md.render(f"J{flash_who + 1} marque !", True, col)
        screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2,
                          SCREEN_HEIGHT // 2 - 10))
