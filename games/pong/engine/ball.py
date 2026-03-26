"""Physique de la balle : reset, deplacement, collisions."""
import math
import random

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    BALL_SIZE, BALL_SPEED_X, BALL_SPEED_Y, BALL_ACCEL, BALL_MAX_SPEED,
    PADDLE_W, PADDLE_H,
)

PADDLE_X_J1 = 20
PADDLE_X_J2 = SCREEN_WIDTH - 20 - PADDLE_W


def reset(towards):
    """Remet la balle au centre, lancee vers le joueur `towards` (0=gauche, 1=droite)."""
    x = float(SCREEN_WIDTH) / 2
    y = float(SCREEN_HEIGHT) / 2
    angle = random.uniform(-math.pi / 5, math.pi / 5)
    dx = BALL_SPEED_X * math.cos(angle) * (1 if towards == 1 else -1)
    dy = BALL_SPEED_Y * math.sin(angle) * random.choice([-1, 1])
    return x, y, dx, dy


def update(ball_x, ball_y, ball_vx, ball_vy, paddle_y, dt):
    """Deplace la balle, gere rebonds et scoring.

    Retourne (x, y, vx, vy, scorer).
    scorer = None si pas de point, 0 si J1 marque, 1 si J2 marque.
    """
    ball_x += ball_vx * dt
    ball_y += ball_vy * dt
    r = BALL_SIZE // 2

    # Rebond haut / bas
    if ball_y - r <= 0:
        ball_y = r
        ball_vy = abs(ball_vy)
    elif ball_y + r >= SCREEN_HEIGHT:
        ball_y = SCREEN_HEIGHT - r
        ball_vy = -abs(ball_vy)

    # Collision raquette J1
    if ball_vx < 0:
        if (ball_x - r <= PADDLE_X_J1 + PADDLE_W and
                ball_x + r >= PADDLE_X_J1 and
                ball_y + r >= paddle_y[0] and
                ball_y - r <= paddle_y[0] + PADDLE_H):
            rel = (ball_y - (paddle_y[0] + PADDLE_H / 2)) / (PADDLE_H / 2)
            bounce = rel * (math.pi / 3.2)
            spd = min(math.hypot(ball_vx, ball_vy) * BALL_ACCEL, BALL_MAX_SPEED)
            ball_vx = abs(spd * math.cos(bounce))
            ball_vy = spd * math.sin(bounce)
            ball_x = PADDLE_X_J1 + PADDLE_W + r

    # Collision raquette J2
    if ball_vx > 0:
        if (ball_x + r >= PADDLE_X_J2 and
                ball_x - r <= PADDLE_X_J2 + PADDLE_W and
                ball_y + r >= paddle_y[1] and
                ball_y - r <= paddle_y[1] + PADDLE_H):
            rel = (ball_y - (paddle_y[1] + PADDLE_H / 2)) / (PADDLE_H / 2)
            bounce = rel * (math.pi / 3.2)
            spd = min(math.hypot(ball_vx, ball_vy) * BALL_ACCEL, BALL_MAX_SPEED)
            ball_vx = -abs(spd * math.cos(bounce))
            ball_vy = spd * math.sin(bounce)
            ball_x = PADDLE_X_J2 - r

    # Point marque
    scorer = None
    if ball_x < 0:
        scorer = 1
    elif ball_x > SCREEN_WIDTH:
        scorer = 0

    return ball_x, ball_y, ball_vx, ball_vy, scorer
