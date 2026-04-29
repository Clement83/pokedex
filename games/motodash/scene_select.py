import pygame

import config
import levels


class SelectScene:
    def __init__(self, screen, scores_state):
        self.screen = screen
        self.scores_state = scores_state
        self.selected = 0
        self.font_big = pygame.font.SysFont("Arial", 22, bold=True)
        self.font = pygame.font.SysFont("Arial", 14)
        self.font_small = pygame.font.SysFont("Arial", 11)
        self._axis_moved = False
        self.choice = None

    def handle_event(self, event):
        n = len(levels.LEVELS)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.selected = (self.selected - 1) % n
            elif event.key == pygame.K_RIGHT:
                self.selected = (self.selected + 1) % n
            elif event.key in (pygame.K_RETURN, pygame.K_n):
                self.choice = levels.LEVELS[self.selected]["id"]
            elif event.key == pygame.K_ESCAPE:
                self.choice = "quit"
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == config.BTN_THROTTLE:
                self.choice = levels.LEVELS[self.selected]["id"]
            elif event.button == config.BTN_BRAKE:
                self.choice = "quit"
            elif event.button == config.BTN_LEFT:
                self.selected = (self.selected - 1) % n
            elif event.button == config.BTN_RIGHT:
                self.selected = (self.selected + 1) % n
        elif event.type == pygame.JOYHATMOTION:
            x, _ = event.value
            if x < 0:
                self.selected = (self.selected - 1) % n
            elif x > 0:
                self.selected = (self.selected + 1) % n
        elif event.type == pygame.JOYAXISMOTION and event.axis == 0:
            if event.value < -0.7 and not self._axis_moved:
                self.selected = (self.selected - 1) % n
                self._axis_moved = True
            elif event.value > 0.7 and not self._axis_moved:
                self.selected = (self.selected + 1) % n
                self._axis_moved = True
            elif abs(event.value) < 0.3:
                self._axis_moved = False

    def update(self, dt):
        if self.choice:
            return {"choice": self.choice}
        return None

    def render(self):
        self.screen.fill((22, 26, 36))
        w, h = self.screen.get_size()
        title = self.font_big.render("MOTODASH — Sélection du niveau", True, config.TEXT_COLOR)
        self.screen.blit(title, ((w - title.get_width()) // 2, 24))

        n = len(levels.LEVELS)
        tile_w, tile_h = 130, 160
        gap = 16
        total_w = n * tile_w + (n - 1) * gap
        x0 = (w - total_w) // 2
        y0 = 80

        for i, level in enumerate(levels.LEVELS):
            x = x0 + i * (tile_w + gap)
            rect = pygame.Rect(x, y0, tile_w, tile_h)
            sel = i == self.selected
            color = (50, 60, 75) if sel else (35, 40, 50)
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            border_color = (220, 220, 220) if sel else (90, 90, 100)
            pygame.draw.rect(self.screen, border_color, rect, 2 if sel else 1, border_radius=8)

            name = self.font.render(level["name"], True, config.TEXT_COLOR)
            self.screen.blit(name, (x + (tile_w - name.get_width()) // 2, y0 + 14))

            best = self.scores_state.get("best_times", {}).get(level["id"])
            if best:
                mins = int(best["time"] // 60)
                secs = best["time"] - mins * 60
                time_str = f"{mins:02d}:{secs:05.2f}"
                t = self.font.render(time_str, True, (220, 220, 220))
                self.screen.blit(t, (x + (tile_w - t.get_width()) // 2, y0 + 44))
                medal = best.get("medal")
                if medal:
                    mcolor = config.MEDAL_COLORS[medal]
                    pygame.draw.circle(self.screen, mcolor, (x + tile_w // 2, y0 + 90), 18)
            else:
                dash = self.font.render("—", True, (140, 140, 140))
                self.screen.blit(dash, (x + (tile_w - dash.get_width()) // 2, y0 + 60))

            targets = self.font_small.render(
                f"or {level['gold']:.0f}s · arg {level['silver']:.0f}s · br {level['bronze']:.0f}s",
                True, (170, 170, 170),
            )
            self.screen.blit(targets, (x + (tile_w - targets.get_width()) // 2, y0 + tile_h - 20))

        hint = self.font_small.render(
            "←→ choisir · A/Entrée jouer · B/Échap quitter",
            True, (200, 200, 200),
        )
        self.screen.blit(hint, ((w - hint.get_width()) // 2, h - 24))
