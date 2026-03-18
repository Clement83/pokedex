"""
Scène de jeu Pong – 2 joueurs.
Retourne 0 si J1 gagne, 1 si J2 gagne, None si on quitte.
"""
import pygame
import math
import random

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    BG_COLOR, PADDLE_J1, PADDLE_J2, BALL_COLOR, NET_COLOR, TEXT_COLOR,
    PADDLE_W, PADDLE_H, PADDLE_SPEED,
    BALL_SIZE, BALL_SPEED_X, BALL_SPEED_Y, BALL_ACCEL, BALL_MAX_SPEED,
    WIN_SCORE, CTRL, AXIS_DEAD,
)

PADDLE_X_J1 = 20
PADDLE_X_J2 = SCREEN_WIDTH - 20 - PADDLE_W


# ── Helpers ───────────────────────────────────────────────────────────────────

def _reset_ball(towards: int):
    """Remet la balle au centre, lancée vers le joueur `towards` (0=J1/gauche, 1=J2/droite)."""
    x = float(SCREEN_WIDTH)  / 2
    y = float(SCREEN_HEIGHT) / 2
    angle = random.uniform(-math.pi / 5, math.pi / 5)
    dx = BALL_SPEED_X * math.cos(angle) * (1 if towards == 1 else -1)
    dy = BALL_SPEED_Y * math.sin(angle) * random.choice([-1, 1])
    return x, y, dx, dy


def _is_held(action: str, keys, joystick=None, btn_held: set = None) -> bool:
    """Retourne True si l'action est active (touche maintenue ou bouton maintenu)."""
    spec = CTRL.get(action, {})

    for k in spec.get('keys', []):
        if keys[k]:
            return True

    if btn_held is not None:
        btn = spec.get('btn')
        if btn is not None and btn in btn_held:
            return True

    if joystick:
        # Hat directionnel
        hat_spec = spec.get('hat')
        if hat_spec:
            try:
                if joystick.get_hat(0) == hat_spec:
                    return True
            except Exception:
                pass
        # Axe analogique
        ax_spec = spec.get('axis')
        if ax_spec:
            ax_id, direction = ax_spec
            try:
                v = joystick.get_axis(ax_id)
                if direction == -1 and v < -AXIS_DEAD:
                    return True
                if direction ==  1 and v >  AXIS_DEAD:
                    return True
            except Exception:
                pass

    return False


# ── Boucle principale ─────────────────────────────────────────────────────────

def run(screen, joysticks):
    clock   = pygame.time.Clock()
    font_sc = pygame.font.SysFont("Arial", 42, bold=True)
    font_md = pygame.font.SysFont("Arial", 14, bold=True)
    font_sm = pygame.font.SysFont("Arial", 11)

    joystick = joysticks[0] if joysticks else None

    paddle_y   = [float(SCREEN_HEIGHT // 2 - PADDLE_H // 2)] * 2
    scores     = [0, 0]
    btn_held   = set()

    ball_x, ball_y, ball_vx, ball_vy = _reset_ball(random.randint(0, 1))

    PAUSE_DUR  = 0.85   # secondes de pause après un point
    pause_t    = 0.0
    flash_who  = -1

    while True:
        dt     = clock.tick(FPS) / 1000.0
        events = pygame.event.get()

        for e in events:
            if e.type == pygame.JOYBUTTONDOWN:
                btn_held.add(e.button)
            if e.type == pygame.JOYBUTTONUP:
                btn_held.discard(e.button)

        keys = pygame.key.get_pressed()

        # ── Mouvement raquettes ───────────────────────────────────────────────
        if _is_held('up_j1',   keys, joystick):
            paddle_y[0] -= PADDLE_SPEED * dt
        if _is_held('down_j1', keys, joystick):
            paddle_y[0] += PADDLE_SPEED * dt

        if _is_held('up_j2',   keys, None, btn_held):
            paddle_y[1] -= PADDLE_SPEED * dt
        if _is_held('down_j2', keys, None, btn_held):
            paddle_y[1] += PADDLE_SPEED * dt

        for i in range(2):
            paddle_y[i] = max(0.0, min(float(SCREEN_HEIGHT - PADDLE_H), paddle_y[i]))

        # ── Physique balle (gelée pendant la pause) ───────────────────────────
        if pause_t > 0:
            pause_t -= dt
        else:
            ball_x += ball_vx * dt
            ball_y += ball_vy * dt

            r = BALL_SIZE // 2

            # Rebond haut / bas
            if ball_y - r <= 0:
                ball_y  =  r
                ball_vy =  abs(ball_vy)
            elif ball_y + r >= SCREEN_HEIGHT:
                ball_y  =  SCREEN_HEIGHT - r
                ball_vy = -abs(ball_vy)

            # ─ Collision raquette J1 (balle va vers la gauche) ───────────────
            if ball_vx < 0:
                if (ball_x - r <= PADDLE_X_J1 + PADDLE_W and
                        ball_x + r >= PADDLE_X_J1 and
                        ball_y + r >= paddle_y[0] and
                        ball_y - r <= paddle_y[0] + PADDLE_H):
                    rel    = (ball_y - (paddle_y[0] + PADDLE_H / 2)) / (PADDLE_H / 2)
                    bounce = rel * (math.pi / 3.2)
                    spd    = min(math.hypot(ball_vx, ball_vy) * BALL_ACCEL, BALL_MAX_SPEED)
                    ball_vx =  abs(spd * math.cos(bounce))
                    ball_vy =      spd * math.sin(bounce)
                    ball_x  = PADDLE_X_J1 + PADDLE_W + r

            # ─ Collision raquette J2 (balle va vers la droite) ───────────────
            if ball_vx > 0:
                if (ball_x + r >= PADDLE_X_J2 and
                        ball_x - r <= PADDLE_X_J2 + PADDLE_W and
                        ball_y + r >= paddle_y[1] and
                        ball_y - r <= paddle_y[1] + PADDLE_H):
                    rel    = (ball_y - (paddle_y[1] + PADDLE_H / 2)) / (PADDLE_H / 2)
                    bounce = rel * (math.pi / 3.2)
                    spd    = min(math.hypot(ball_vx, ball_vy) * BALL_ACCEL, BALL_MAX_SPEED)
                    ball_vx = -abs(spd * math.cos(bounce))
                    ball_vy =      spd * math.sin(bounce)
                    ball_x  = PADDLE_X_J2 - r

            # ─ Point marqué ──────────────────────────────────────────────────
            if ball_x < 0:
                scores[1] += 1
                flash_who = 1
                if scores[1] >= WIN_SCORE:
                    return 1
                ball_x, ball_y, ball_vx, ball_vy = _reset_ball(0)
                pause_t = PAUSE_DUR

            elif ball_x > SCREEN_WIDTH:
                scores[0] += 1
                flash_who = 0
                if scores[0] >= WIN_SCORE:
                    return 0
                ball_x, ball_y, ball_vx, ball_vy = _reset_ball(1)
                pause_t = PAUSE_DUR

        # ── Dessin ────────────────────────────────────────────────────────────
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

        # Balle (clignote pendant la pause)
        if pause_t <= 0 or int(pause_t * 8) % 2 == 0:
            pygame.draw.circle(screen, BALL_COLOR,
                               (int(ball_x), int(ball_y)), BALL_SIZE // 2)

        # Scores
        s0 = font_sc.render(str(scores[0]), True, PADDLE_J1)
        s1 = font_sc.render(str(scores[1]), True, PADDLE_J2)
        screen.blit(s0, (SCREEN_WIDTH // 4     - s0.get_width() // 2, 5))
        screen.blit(s1, (3 * SCREEN_WIDTH // 4 - s1.get_width() // 2, 5))

        # Message flash après un point
        if pause_t > 0 and flash_who >= 0:
            col = (PADDLE_J1, PADDLE_J2)[flash_who]
            msg = font_md.render(f"J{flash_who + 1} marque !", True, col)
            screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2,
                              SCREEN_HEIGHT // 2 - 10))

        # Aide contrôles (discret, en bas)
        pygame.display.flip()
