"""
Scene de jeu Pong - 2 joueurs.
Retourne 0 si J1 gagne, 1 si J2 gagne, None si on quitte.
"""
import pygame
import random
import collections

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    PADDLE_H, PADDLE_SPEED, WIN_SCORE,
)
from quit_combo import QuitCombo
from engine.input import is_held
from engine.ball import reset as reset_ball, update as update_ball
from engine.renderer import draw


def run(screen, joysticks):
    clock   = pygame.time.Clock()
    font_sc = pygame.font.SysFont("Arial", 42, bold=True)
    font_md = pygame.font.SysFont("Arial", 14, bold=True)
    fonts   = (font_sc, font_md)

    joystick = joysticks[0] if joysticks else None

    paddle_y = [float(SCREEN_HEIGHT // 2 - PADDLE_H // 2)] * 2
    scores   = [0, 0]
    btn_held = set()
    quit     = QuitCombo()

    ball_x, ball_y, ball_vx, ball_vy = reset_ball(random.randint(0, 1))
    trail = collections.deque(maxlen=14)

    PAUSE_DUR = 0.85
    pause_t   = 0.0
    flash_who = -1

    while True:
        dt     = clock.tick(FPS) / 1000.0
        events = pygame.event.get()

        for e in events:
            quit.handle_event(e)
            if e.type == pygame.JOYBUTTONDOWN:
                btn_held.add(e.button)
            if e.type == pygame.JOYBUTTONUP:
                btn_held.discard(e.button)

        keys = pygame.key.get_pressed()

        # Mouvement raquettes
        if is_held('up_j1',   keys, joystick):
            paddle_y[0] -= PADDLE_SPEED * dt
        if is_held('down_j1', keys, joystick):
            paddle_y[0] += PADDLE_SPEED * dt
        if is_held('up_j2',   keys, None, btn_held):
            paddle_y[1] -= PADDLE_SPEED * dt
        if is_held('down_j2', keys, None, btn_held):
            paddle_y[1] += PADDLE_SPEED * dt

        for i in range(2):
            paddle_y[i] = max(0.0, min(float(SCREEN_HEIGHT - PADDLE_H), paddle_y[i]))

        # Physique balle (gelee pendant la pause)
        if pause_t > 0:
            pause_t -= dt
        else:
            ball_x, ball_y, ball_vx, ball_vy, scorer = update_ball(
                ball_x, ball_y, ball_vx, ball_vy, paddle_y, dt)

            if scorer is not None:
                scores[scorer] += 1
                flash_who = scorer
                if scores[scorer] >= WIN_SCORE:
                    return scorer
                ball_x, ball_y, ball_vx, ball_vy = reset_ball(
                    0 if scorer == 1 else 1)
                trail.clear()
                pause_t = PAUSE_DUR
            else:
                trail.appendleft((int(ball_x), int(ball_y)))

        # Dessin
        draw(screen, fonts, paddle_y, scores, ball_x, ball_y,
             trail, pause_t, flash_who)

        if quit.update_and_draw(screen):
            return None
        pygame.display.flip()
