"""
Point d'entrée du jeu Pong.
Boucle : splash → partie → résultat → boucle.
"""
import sys
import os
import math
import collections

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BG_COLOR, PADDLE_J1, PADDLE_J2, TEXT_COLOR

import scene_game
import scene_result


def main():
    pygame.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    pygame.event.pump()   # vider le buffer interne SDL
    pygame.event.clear()  # éliminer tout résidu du launcher

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Pong – 2 Joueurs")

    _show_splash(screen, joysticks)

    while True:
        winner = scene_game.run(screen, joysticks)
        if winner is None:
            break

        replay = scene_result.run(screen, winner, joysticks)
        if not replay:
            break

    pygame.quit()


def _show_splash(screen: pygame.Surface, joysticks):
    """Écran titre Pong : simulation de partie en direct, style arcade rétro."""
    font_title = pygame.font.SysFont("Courier New", 60, bold=True)
    font_score = pygame.font.SysFont("Courier New", 36, bold=True)
    font_sm    = pygame.font.SysFont("Courier New", 11)
    clock      = pygame.time.Clock()

    BORDER  = 14
    PAD_W   = 10
    PAD_H   = 60
    PAD_L_X = 26
    PAD_R_X = SCREEN_WIDTH - 26 - PAD_W

    bx, by   = float(SCREEN_WIDTH // 2), float(SCREEN_HEIGHT // 2)
    bvx, bvy = 220.0, 155.0
    py1, py2 = float(SCREEN_HEIGHT // 2), float(SCREEN_HEIGHT // 2)
    sl, sr   = 0, 0
    trail    = collections.deque(maxlen=14)
    anim     = 0.0

    # Overlay scanlines CRT (créé une seule fois)
    scan_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    for sy in range(0, SCREEN_HEIGHT, 3):
        pygame.draw.line(scan_surf, (0, 0, 0, 28), (0, sy), (SCREEN_WIDTH, sy))

    while True:
        dt   = clock.tick(FPS) / 1000.0
        anim += dt

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type in (pygame.KEYDOWN, pygame.JOYBUTTONDOWN):
                return

        # ── Physique ─────────────────────────────────────────────────────
        bx += bvx * dt
        by += bvy * dt
        trail.appendleft((int(bx), int(by)))

        # Murs haut/bas
        if by < BORDER + 5:
            by = BORDER + 5;   bvy = abs(bvy)
        if by > SCREEN_HEIGHT - BORDER - 5:
            by = SCREEN_HEIGHT - BORDER - 5;   bvy = -abs(bvy)

        # IA raquettes
        ai_spd = 200 * dt
        if   by < py1 - 4: py1 -= ai_spd
        elif by > py1 + 4: py1 += ai_spd
        if   by < py2 - 4: py2 -= ai_spd
        elif by > py2 + 4: py2 += ai_spd
        lo = BORDER + PAD_H // 2
        hi = SCREEN_HEIGHT - BORDER - PAD_H // 2
        py1 = max(lo, min(hi, py1))
        py2 = max(lo, min(hi, py2))

        # Rebond raquette gauche
        if (bvx < 0 and PAD_L_X < bx < PAD_L_X + PAD_W + 6
                and abs(by - py1) < PAD_H // 2):
            bx   = PAD_L_X + PAD_W + 6
            bvx  = abs(bvx) * 1.03
            bvy += (by - py1) * 0.8

        # Rebond raquette droite
        if (bvx > 0 and PAD_R_X - 6 < bx < PAD_R_X + PAD_W
                and abs(by - py2) < PAD_H // 2):
            bx   = PAD_R_X - 6
            bvx  = -abs(bvx) * 1.03
            bvy += (by - py2) * 0.8

        # Vitesse max
        spd = math.hypot(bvx, bvy)
        if spd > 400:
            bvx *= 400 / spd
            bvy *= 400 / spd
        bvy = max(-260.0, min(260.0, bvy))

        # Point marqué
        if bx < -10:
            sr += 1
            bx, by   = float(SCREEN_WIDTH // 2), float(SCREEN_HEIGHT // 2)
            bvx, bvy = 210.0, 140.0 * (1 if sr % 2 == 0 else -1)
            trail.clear()
        if bx > SCREEN_WIDTH + 10:
            sl += 1
            bx, by   = float(SCREEN_WIDTH // 2), float(SCREEN_HEIGHT // 2)
            bvx, bvy = -210.0, 140.0 * (1 if sl % 2 == 0 else -1)
            trail.clear()

        # ── Rendu ─────────────────────────────────────────────────────
        screen.fill(BG_COLOR)

        # Murs haut et bas
        pygame.draw.rect(screen, TEXT_COLOR, (0, 0, SCREEN_WIDTH, BORDER))
        pygame.draw.rect(screen, TEXT_COLOR, (0, SCREEN_HEIGHT - BORDER, SCREEN_WIDTH, BORDER))

        # Filet central
        for ny in range(BORDER, SCREEN_HEIGHT - BORDER, 18):
            pygame.draw.rect(screen, (32, 32, 58), (SCREEN_WIDTH // 2 - 2, ny, 4, 10))

        # Score
        s_l = font_score.render(str(sl), True, PADDLE_J1)
        s_r = font_score.render(str(sr), True, PADDLE_J2)
        screen.blit(s_l, (SCREEN_WIDTH // 4     - s_l.get_width() // 2, BORDER + 4))
        screen.blit(s_r, (3 * SCREEN_WIDTH // 4 - s_r.get_width() // 2, BORDER + 4))

        # Traînée balle (dégradé blanc → fond)
        n = len(trail)
        for i, (ttx, tty) in enumerate(trail):
            f = 1.0 - i / n
            r = max(1, int(5 * f))
            lv = int(8 + 232 * f * f)
            pygame.draw.circle(screen, (lv, lv, lv), (ttx, tty), r)

        # Raquettes
        pygame.draw.rect(screen, PADDLE_J1,
                         (PAD_L_X, int(py1) - PAD_H // 2, PAD_W, PAD_H), border_radius=3)
        pygame.draw.rect(screen, PADDLE_J2,
                         (PAD_R_X, int(py2) - PAD_H // 2, PAD_W, PAD_H), border_radius=3)

        # Balle
        pygame.draw.circle(screen, (240, 240, 240), (int(bx), int(by)), 5)

        # Scanlines CRT
        screen.blit(scan_surf, (0, 0))

        # Titre
        pulse   = 1.0 + 0.025 * math.sin(anim * 3)
        raw     = font_title.render("PONG", True, TEXT_COLOR)
        scaled  = pygame.transform.scale(
            raw, (int(raw.get_width() * pulse), int(raw.get_height() * pulse)))
        titx = SCREEN_WIDTH  // 2 - scaled.get_width()  // 2
        tity = SCREEN_HEIGHT // 2 - scaled.get_height() // 2
        panel = pygame.Surface((scaled.get_width() + 20,
                                 scaled.get_height() + 10), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 155))
        screen.blit(panel,  (titx - 10, tity - 5))
        screen.blit(scaled, (titx,      tity))

        # Clignotant
        if int(anim * 2) % 2 == 0:
            msg = font_sm.render("Appuie sur un bouton pour commencer", True, (100, 100, 145))
            screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2,
                               SCREEN_HEIGHT - BORDER - 18))

        pygame.display.flip()
