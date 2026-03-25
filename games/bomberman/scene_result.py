"""
Scène de résultat Bomberman – Podium.
Retourne True (rejouer) ou False (quitter).
"""
import pygame
import math
import sys

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    BG_COLOR, TEXT_COLOR, P1_COLOR, P2_COLOR, P3_COLOR, P4_COLOR,
    BTN_A, BTN_B, BTN_X, BTN_Y,
)
from quit_combo import QuitCombo
from scene_game import _draw_player_char

_PLAYER_COLORS = [P1_COLOR, P2_COLOR, P3_COLOR, P4_COLOR]
_PLAYER_LABELS = ['J1', 'J2', 'IA1', 'IA2']

_PODIUM_COLORS = {
    1: (255, 210, 50),    # or
    2: (190, 195, 210),   # argent
    3: (205, 135, 60),    # bronze
    4: (90,  90, 105),    # gris
}

_RANK_SUFFIX = {1: 'er', 2: 'e', 3: 'e', 4: 'e'}


def run(screen, rankings, joysticks) -> bool:
    """
    rankings : liste de listes d'indices joueurs, du 1er au dernier.
               ex. [[2], [0], [1, 3]] → P3 gagne, P1 2e, P2&P4 3e ex-æquo.
    """
    font_xl = pygame.font.SysFont("Arial", 34, bold=True)
    font_lg = pygame.font.SysFont("Arial", 20, bold=True)
    font_md = pygame.font.SysFont("Arial", 13, bold=True)
    font_sm = pygame.font.SysFont("Arial", 11)
    clock   = pygame.time.Clock()
    quit_combo = QuitCombo()
    anim = 0.0

    # Aplatir le classement : [(player_idx, rank), …]
    podium_slots = []
    rank = 1
    for group in rankings:
        for idx in group:
            podium_slots.append((idx, rank))
        rank += len(group)

    pygame.event.clear()

    while True:
        dt   = clock.tick(FPS) / 1000.0
        anim += dt

        for e in pygame.event.get():
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
                    return True

        screen.fill(BG_COLOR)

        # ── Titre ────────────────────────────────────────────────────────────
        pulse = 1.0 + 0.03 * math.sin(anim * 4)
        title = font_xl.render("PODIUM", True, (255, 210, 50))
        ts    = pygame.transform.scale(
            title,
            (int(title.get_width() * pulse), int(title.get_height() * pulse)),
        )
        screen.blit(ts, ((SCREEN_WIDTH - ts.get_width()) // 2, 8))

        # ── Podium ───────────────────────────────────────────────────────────
        _draw_podium(screen, podium_slots, anim, font_lg, font_md, font_sm)

        # ── Instructions ─────────────────────────────────────────────────────
        replay = font_md.render("A / B / X / Y  /  Entree  ->  Rejouer", True, (200, 200, 220))
        screen.blit(replay, ((SCREEN_WIDTH - replay.get_width()) // 2, 277))
        pygame.draw.rect(
            screen, (200, 200, 220),
            ((SCREEN_WIDTH - replay.get_width()) // 2 - 6, 274,
             replay.get_width() + 12, replay.get_height() + 6),
            2, border_radius=4,
        )

        hint = font_sm.render("SELECT+START  /  Echap  ->  Quitter", True, (110, 110, 140))
        screen.blit(hint, ((SCREEN_WIDTH - hint.get_width()) // 2, 302))

        if quit_combo.update_and_draw(screen):
            return False

        pygame.display.flip()


def _draw_podium(surface, podium_slots, anim, font_lg, font_md, font_sm):
    block_w  = 90
    gap      = 6
    total_w  = 4 * block_w + 3 * gap
    start_x  = (SCREEN_WIDTH - total_w) // 2
    bottom_y = 258

    heights = {1: 115, 2: 82, 3: 58, 4: 38}

    # Ordre visuel : 2e, 1er, 3e, 4e (de gauche à droite)
    visual_order = [2, 1, 3, 4]

    # Regrouper par rang
    rank_to_players = {}
    for pidx, rank in podium_slots:
        rank_to_players.setdefault(rank, []).append(pidx)

    for pos_i, rank in enumerate(visual_order):
        x = start_x + pos_i * (block_w + gap)
        h = heights.get(rank, 30)
        y = bottom_y - h
        col = _PODIUM_COLORS.get(rank, (80, 80, 80))

        dark  = tuple(max(0, c - 50) for c in col)
        light = tuple(min(255, c + 50) for c in col)

        # Bloc 3D
        pygame.draw.rect(surface, col, (x, y, block_w, h))
        pygame.draw.rect(surface, light, (x + 1, y + 1, block_w - 2, 5))
        pygame.draw.rect(surface, dark, (x, y + h - 4, block_w, 4))
        pygame.draw.rect(surface, dark, (x, y, block_w, h), 2)

        # Numéro de rang au centre du bloc
        suffix = _RANK_SUFFIX.get(rank, 'e')
        rank_lbl = font_lg.render(f"{rank}{suffix}", True, (30, 30, 45))
        surface.blit(rank_lbl, (x + (block_w - rank_lbl.get_width()) // 2,
                                y + h // 2 - rank_lbl.get_height() // 2 + 5))

        # Joueurs sur ce bloc
        plist = rank_to_players.get(rank, [])
        n = len(plist)
        for j, pidx in enumerate(plist):
            offset = int((j - (n - 1) / 2) * 28)
            cx = x + block_w // 2 + offset
            cy = y - 10

            _draw_player_char(surface, cx, cy, _PLAYER_COLORS[pidx], pidx)

            # Étiquette joueur
            lbl = font_sm.render(_PLAYER_LABELS[pidx], True, _PLAYER_COLORS[pidx])
            surface.blit(lbl, (cx - lbl.get_width() // 2, cy - 30))
