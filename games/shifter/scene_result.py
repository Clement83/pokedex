"""
Écran de résultats après la course.
Retourne True (rejouer) ou False (quitter).
"""
import pygame
from config import PLAYER_COLORS, CTRL, SCREEN_WIDTH, SCREEN_HEIGHT
from ui import load_vehicle_sprites

BG_COL   = (8,  8,  20)
GOLD     = (255, 215,  0)
SILVER   = (192, 192, 192)
BRONZE   = (180, 100,  20)
TEXT_W   = (230, 230, 255)
TEXT_DIM = (120, 120, 160)
NEON     = (80,  200, 255)


def _podium_color(rank: int):
    return [GOLD, SILVER, BRONZE][rank - 1] if rank <= 3 else (150, 150, 170)


def run(screen: pygame.Surface, results: list) -> bool:
    """
    results = [{'player_id', 'car', 'rank'}, ...]  triés par rang croissant.
    Retourne True pour rejouer, False pour quitter.
    """
    clock   = pygame.time.Clock()
    font_sm = pygame.font.SysFont("Arial", 11, bold=True)
    font_md = pygame.font.SysFont("Arial", 14, bold=True)
    font_lg = pygame.font.SysFont("Arial", 20, bold=True)
    font_xl = pygame.font.SysFont("Arial", 28, bold=True)

    winner = results[0]
    p_col  = PLAYER_COLORS[winner['player_id']]
    anim_t = 0.0
    winner_sprites = load_vehicle_sprites(220)

    while True:
        dt     = clock.tick(60) / 1000.0
        anim_t += dt
        events = pygame.event.get()

        for e in events:
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return False
                if e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_n, pygame.K_UP):
                    return True
            if e.type == pygame.JOYBUTTONDOWN:
                if e.button in (0, 2):   # A ou X → rejouer
                    return True
                if e.button in (1, 3):   # B ou Y → quitter
                    return False

        # ── Rendu ─────────────────────────────────────────────────────────────
        screen.fill(BG_COL)

        # Fond dégradé subtil
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            col = (int(8 + t * 12), int(8 + t * 10), int(20 + t * 20))
            pygame.draw.line(screen, col, (0, y), (SCREEN_WIDTH, y))

        # ── Titre ─────────────────────────────────────────────────────────────
        pygame.draw.rect(screen, (18, 18, 45),
                         pygame.Rect(0, 0, SCREEN_WIDTH, 36))
        pygame.draw.line(screen, NEON, (0, 36), (SCREEN_WIDTH, 36), 1)
        title = font_lg.render("RÉSULTATS", True, NEON)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 8))

        # ── Vainqueur (texte) ─────────────────────────────────────────────────
        import math
        scale_pulse = 1.0 + 0.04 * math.sin(anim_t * 4)
        w_text = f"🏆  J{winner['player_id']+1}  {winner['car'].name}  GAGNE !"
        w_surf = font_xl.render(w_text, True, p_col)
        ws = pygame.transform.scale(w_surf,
            (int(w_surf.get_width() * scale_pulse),
             int(w_surf.get_height() * scale_pulse)))
        screen.blit(ws, (SCREEN_WIDTH // 2 - ws.get_width() // 2, 44))

        # ── Sprite voiture gagnante ───────────────────────────────────────────
        w_sprite = winner_sprites[winner['car'].data['sprite_frame']]
        sprite_x = SCREEN_WIDTH // 2 - w_sprite.get_width() // 2
        sprite_y = 78
        screen.blit(w_sprite, (sprite_x, sprite_y))
        pygame.draw.line(screen, p_col,
                         (sprite_x + 10, sprite_y + w_sprite.get_height() - 2),
                         (sprite_x + w_sprite.get_width() - 10, sprite_y + w_sprite.get_height() - 2), 2)

        # ── Tableau ───────────────────────────────────────────────────────────
        row_h   = 38
        table_y = sprite_y + w_sprite.get_height() + 6
        labels = ["POS", "JOUEUR", "VOITURE", "TEMPS", "VIT.MAX", "PERF./BON/RAT"]
        col_x  = [6, 38, 88, 188, 250, 310]

        # Header tableau
        for i, lbl in enumerate(labels):
            ls = font_sm.render(lbl, True, (90, 90, 130))
            screen.blit(ls, (col_x[i], table_y))
        table_y += 14

        pygame.draw.line(screen, (50, 50, 80),
                         (0, table_y), (SCREEN_WIDTH, table_y), 1)
        table_y += 2

        for res in results:
            rank  = res['rank']
            pid   = res['player_id']
            c     = res['car']
            p_c   = PLAYER_COLORS[pid]
            r_col = _podium_color(rank)

            row_rect = pygame.Rect(0, table_y, SCREEN_WIDTH, row_h - 2)
            pygame.draw.rect(screen, (16, 16, 36), row_rect, border_radius=4)
            if rank == 1:
                pygame.draw.rect(screen, (50, 40, 0), row_rect, border_radius=4)
            pygame.draw.rect(screen, (30, 30, 60), row_rect, 1, border_radius=4)

            medals = {1: "🥇", 2: "🥈"}
            pos_txt = medals.get(rank, str(rank))
            pos_s = font_md.render(pos_txt, True, r_col)
            screen.blit(pos_s, (col_x[0], table_y + (row_h - 2 - pos_s.get_height()) // 2))

            jname = font_md.render(f"J{pid+1}", True, p_c)
            screen.blit(jname, (col_x[1], table_y + (row_h - 2 - jname.get_height()) // 2))

            car_s = font_sm.render(c.name, True, TEXT_W)
            screen.blit(car_s, (col_x[2], table_y + 2))
            cat_s = font_sm.render(c.data["cat"], True, TEXT_DIM)
            screen.blit(cat_s, (col_x[2], table_y + 14))

            t_s = font_md.render(f"{c.race_time:.3f}s", True, TEXT_W)
            screen.blit(t_s, (col_x[3], table_y + (row_h - 2 - t_s.get_height()) // 2))

            v_s = font_md.render(f"{int(c.best_speed)}", True, NEON)
            screen.blit(v_s, (col_x[4], table_y + (row_h - 2 - v_s.get_height()) // 2))

            shifts = f"✓{c.perfect_shifts} /{c.good_shifts} ✗{c.bad_shifts}"
            sh_s  = font_sm.render(shifts, True, TEXT_DIM)
            screen.blit(sh_s, (col_x[5], table_y + (row_h - 2 - sh_s.get_height()) // 2))

            table_y += row_h

        # ── Boutons de fin ────────────────────────────────────────────────────
        hint_y = SCREEN_HEIGHT - 22
        pygame.draw.line(screen, (30, 30, 60), (0, hint_y - 4), (SCREEN_WIDTH, hint_y - 4), 1)

        replay = font_sm.render("A / Entrée : Rejouer", True, (80, 200, 255))
        quit_  = font_sm.render("B / Echap  : Quitter", True, (180, 80, 80))
        screen.blit(replay, (SCREEN_WIDTH // 4 - replay.get_width() // 2, hint_y))
        screen.blit(quit_,  (3 * SCREEN_WIDTH // 4 - quit_.get_width() // 2, hint_y))

        pygame.display.flip()
