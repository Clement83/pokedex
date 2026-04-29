import pygame

import config
import levels


TILE_W = 150
TILE_H = 200
TILE_GAP = 20
HEADER_H = 32
FADE_W = 40


class SelectScene:
    def __init__(self, screen, scores_state):
        self.screen = screen
        self.scores_state = scores_state
        self.selected = 0
        self.font_big = pygame.font.SysFont("Arial", 16, bold=True)
        self.font = pygame.font.SysFont("Arial", 12, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 10)
        self.font_arrow = pygame.font.SysFont("Arial", 22, bold=True)
        self._axis_x = False
        self.choice = None
        self._scroll_x = 0.0

    def _move(self, dx):
        n = len(levels.LEVELS)
        if n == 0:
            return
        self.selected = (self.selected + dx) % n

    def _is_unlocked(self, index):
        if index <= 0:
            return True
        prev = levels.LEVELS[index - 1]
        best = self.scores_state.get("best_times", {}).get(prev["id"])
        return bool(best and best.get("medal"))

    def _try_select(self):
        if self._is_unlocked(self.selected):
            self.choice = levels.LEVELS[self.selected]["id"]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self._move(-1)
            elif event.key == pygame.K_RIGHT:
                self._move(1)
            elif event.key in (pygame.K_RETURN, pygame.K_n):
                self._try_select()
            elif event.key == pygame.K_ESCAPE:
                self.choice = "quit"
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == config.BTN_THROTTLE:
                self._try_select()
            elif event.button == config.BTN_BRAKE:
                self.choice = "quit"
            elif event.button == config.BTN_LEFT:
                self._move(-1)
            elif event.button == config.BTN_RIGHT:
                self._move(1)
        elif event.type == pygame.JOYHATMOTION:
            x, y = event.value
            if x < 0 or y > 0:
                self._move(-1)
            elif x > 0 or y < 0:
                self._move(1)
        elif event.type == pygame.JOYAXISMOTION:
            if event.axis == 0:
                if event.value < -0.7 and not self._axis_x:
                    self._move(-1); self._axis_x = True
                elif event.value > 0.7 and not self._axis_x:
                    self._move(1); self._axis_x = True
                elif abs(event.value) < 0.3:
                    self._axis_x = False

    def update(self, dt):
        step = TILE_W + TILE_GAP
        target = self.selected * step
        self._scroll_x += (target - self._scroll_x) * min(1.0, 14.0 * dt)
        if self.choice:
            return {"choice": self.choice}
        return None

    def _draw_tile(self, level, x, y, selected, locked):
        rect = pygame.Rect(x, y, TILE_W, TILE_H)
        biome_key = level.get("biome", "grass")
        biome = config.BIOMES.get(biome_key, config.BIOMES["grass"])

        # Fond de tuile (semi-transparent)
        tile_surf = pygame.Surface((TILE_W, TILE_H), pygame.SRCALPHA)
        if locked:
            alpha = 200 if selected else 150
            rgb = (28, 30, 38)
        else:
            alpha = 220 if selected else 170
            rgb = (60, 70, 85) if selected else (35, 40, 50)
        pygame.draw.rect(tile_surf, (*rgb, alpha), tile_surf.get_rect(), border_radius=10)
        self.screen.blit(tile_surf, rect)

        # Bordure
        if locked:
            border_color = (180, 150, 60) if selected else (70, 65, 50)
        else:
            border_color = (220, 220, 220) if selected else (90, 90, 100)
        pygame.draw.rect(self.screen, border_color, rect, 2 if selected else 1, border_radius=10)

        # Aperçu du biome (bandeau de ciel + sol stylisé)
        preview_h = 60
        preview_rect = pygame.Rect(x + 6, y + 6, TILE_W - 12, preview_h)
        sky_surf = pygame.Surface((preview_rect.width, preview_rect.height))
        top = biome["sky_top"]
        bot = biome["sky_bottom"]
        for py in range(preview_rect.height):
            t = py / max(1, preview_rect.height - 1)
            r = int(top[0] + (bot[0] - top[0]) * t)
            g = int(top[1] + (bot[1] - top[1]) * t)
            b = int(top[2] + (bot[2] - top[2]) * t)
            pygame.draw.line(sky_surf, (r, g, b), (0, py), (preview_rect.width, py))
        # Soleil
        pygame.draw.circle(sky_surf, biome["sun"], (preview_rect.width - 18, 14), 7)
        pygame.draw.circle(sky_surf, biome["sun_inner"], (preview_rect.width - 18, 14), 4)
        # Montagnes
        mh = preview_rect.height
        pygame.draw.polygon(
            sky_surf, biome["mountain_far"],
            [(0, mh - 18), (30, mh - 32), (55, mh - 22), (80, mh - 30), (preview_rect.width, mh - 18), (preview_rect.width, mh), (0, mh)],
        )
        # Sol (herbe / sable)
        pygame.draw.rect(
            sky_surf, biome["dirt"],
            (0, mh - 14, preview_rect.width, 14),
        )
        pygame.draw.rect(
            sky_surf, biome["grass"],
            (0, mh - 14, preview_rect.width, 3),
        )
        self.screen.blit(sky_surf, preview_rect)
        pygame.draw.rect(self.screen, (20, 20, 20), preview_rect, 1, border_radius=2)

        # Nom du niveau
        name = self.font.render(level["name"], True, config.TEXT_COLOR)
        self.screen.blit(name, (x + (TILE_W - name.get_width()) // 2, y + 72))

        # Meilleur temps + médaille
        best = self.scores_state.get("best_times", {}).get(level["id"])
        if best:
            mins = int(best["time"] // 60)
            secs = best["time"] - mins * 60
            time_str = f"{mins:02d}:{secs:05.2f}"
            t = self.font.render(time_str, True, (220, 220, 220))
            self.screen.blit(t, (x + (TILE_W - t.get_width()) // 2, y + 92))
            medal = best.get("medal")
            if medal:
                mcolor = config.MEDAL_COLORS[medal]
                pygame.draw.circle(self.screen, mcolor, (x + TILE_W // 2, y + 130), 14)
                pygame.draw.circle(self.screen, (30, 30, 30), (x + TILE_W // 2, y + 130), 14, 1)
        else:
            dash = self.font.render("—", True, (140, 140, 140))
            self.screen.blit(dash, (x + (TILE_W - dash.get_width()) // 2, y + 118))

        # Temps cibles
        gold_s = self.font_small.render(f"or  {level['gold']:.1f}s", True, config.MEDAL_COLORS[config.MEDAL_GOLD])
        silv_s = self.font_small.render(f"arg {level['silver']:.1f}s", True, config.MEDAL_COLORS[config.MEDAL_SILVER])
        bron_s = self.font_small.render(f"br  {level['bronze']:.1f}s", True, config.MEDAL_COLORS[config.MEDAL_BRONZE])
        self.screen.blit(gold_s, (x + (TILE_W - gold_s.get_width()) // 2, y + TILE_H - 42))
        self.screen.blit(silv_s, (x + (TILE_W - silv_s.get_width()) // 2, y + TILE_H - 30))
        self.screen.blit(bron_s, (x + (TILE_W - bron_s.get_width()) // 2, y + TILE_H - 18))

        if locked:
            # Voile sombre
            veil = pygame.Surface((TILE_W, TILE_H), pygame.SRCALPHA)
            veil.fill((0, 0, 0, 165))
            pygame.draw.rect(veil, (0, 0, 0, 0), veil.get_rect(), border_radius=10)
            mask = pygame.Surface((TILE_W, TILE_H), pygame.SRCALPHA)
            pygame.draw.rect(mask, (0, 0, 0, 165), mask.get_rect(), border_radius=10)
            self.screen.blit(mask, rect)
            # Cadenas dessiné (anse + corps)
            cx = x + TILE_W // 2
            cy = y + TILE_H // 2
            color = (220, 200, 110) if selected else (180, 165, 95)
            pygame.draw.arc(
                self.screen, color,
                pygame.Rect(cx - 11, cy - 22, 22, 22), 3.14, 6.28, 3,
            )
            body = pygame.Rect(cx - 14, cy - 6, 28, 22)
            pygame.draw.rect(self.screen, color, body, border_radius=3)
            pygame.draw.rect(self.screen, (40, 35, 15), body, 1, border_radius=3)
            pygame.draw.circle(self.screen, (40, 35, 15), (cx, cy + 4), 2)
            # Texte
            unlock_msg = self.font_small.render(
                "Médaille requise au précédent",
                True, (220, 200, 110),
            )
            self.screen.blit(
                unlock_msg,
                (x + (TILE_W - unlock_msg.get_width()) // 2, cy + 22),
            )

    def render(self):
        self.screen.fill((22, 26, 36))
        w, h = self.screen.get_size()

        # En-tête
        title = self.font_big.render("MOTODASH — Sélection du niveau", True, config.TEXT_COLOR)
        self.screen.blit(title, ((w - title.get_width()) // 2, 8))
        pygame.draw.line(self.screen, (70, 70, 70), (0, HEADER_H), (w, HEADER_H), 1)

        n = len(levels.LEVELS)
        if n == 0:
            return

        # Carousel : tuile sélectionnée centrée horizontalement
        step = TILE_W + TILE_GAP
        center_x = w // 2 - TILE_W // 2
        tile_y = HEADER_H + (h - HEADER_H - TILE_H) // 2 - 8

        # Clip sous le header
        clip_rect = pygame.Rect(0, HEADER_H, w, h - HEADER_H)
        self.screen.set_clip(clip_rect)

        for i, level in enumerate(levels.LEVELS):
            x = center_x + i * step - int(self._scroll_x)
            if x + TILE_W < -10 or x > w + 10:
                continue
            self._draw_tile(level, x, tile_y, i == self.selected, not self._is_unlocked(i))

        self.screen.set_clip(None)

        # Dégradés bords gauche/droite
        for side in ('left', 'right'):
            fade = pygame.Surface((FADE_W, h - HEADER_H), pygame.SRCALPHA)
            for px in range(FADE_W):
                t = px / FADE_W
                alpha = int(160 * (1.0 - t)) if side == 'left' else int(160 * t)
                col_x = px if side == 'left' else FADE_W - 1 - px
                pygame.draw.line(fade, (0, 0, 0, alpha), (col_x, 0), (col_x, h - HEADER_H))
            self.screen.blit(fade, (0 if side == 'left' else w - FADE_W, HEADER_H))

        # Flèches
        arrow_y = HEADER_H + (h - HEADER_H) // 2 - 12
        if self.selected > 0:
            a = self.font_arrow.render("◄", True, (180, 180, 180))
            self.screen.blit(a, (6, arrow_y))
        if self.selected < n - 1:
            a = self.font_arrow.render("►", True, (180, 180, 180))
            self.screen.blit(a, (w - a.get_width() - 6, arrow_y))

        # Points de position
        if n > 1:
            dot_r = 3
            dot_gap = 10
            dots_w = n * (dot_r * 2) + (n - 1) * (dot_gap - dot_r * 2)
            dot_y = h - 22
            dot_x0 = (w - dots_w) // 2
            for i in range(n):
                cx = dot_x0 + i * dot_gap
                col = (220, 220, 220) if i == self.selected else (70, 70, 80)
                pygame.draw.circle(self.screen, col, (cx, dot_y), dot_r)

        hint = self.font_small.render(
            "◄ ► naviguer · A/Entrée jouer · B/Échap quitter",
            True, (160, 160, 160),
        )
        self.screen.blit(hint, ((w - hint.get_width()) // 2, h - 12))
