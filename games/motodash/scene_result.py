import pygame

import config


class ResultScene:
    def __init__(self, screen, level, time_seconds, medal, is_new_best):
        self.screen = screen
        self.level = level
        self.time = time_seconds
        self.medal = medal
        self.is_new_best = is_new_best
        self.font_big = pygame.font.SysFont("Arial", 28, bold=True)
        self.font = pygame.font.SysFont("Arial", 16)
        self.font_small = pygame.font.SysFont("Arial", 12)
        self.choice = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_r):
                self.choice = "retry"
            elif event.key == pygame.K_ESCAPE:
                self.choice = "menu"
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == config.BTN_THROTTLE:
                self.choice = "retry"
            elif event.button == config.BTN_BRAKE:
                self.choice = "menu"

    def update(self, dt):
        if self.choice:
            return {"choice": self.choice}
        return None

    def render(self):
        self.screen.fill((20, 25, 35))
        w, h = self.screen.get_size()

        title = self.font_big.render(self.level["name"], True, config.TEXT_COLOR)
        self.screen.blit(title, ((w - title.get_width()) // 2, 30))

        mins = int(self.time // 60)
        secs = self.time - mins * 60
        time_str = f"{mins:02d}:{secs:05.2f}"
        time_surf = self.font_big.render(time_str, True, config.TEXT_COLOR)
        self.screen.blit(time_surf, ((w - time_surf.get_width()) // 2, 80))

        if self.medal:
            color = config.MEDAL_COLORS[self.medal]
            label = self.medal.upper()
            medal_surf = self.font_big.render(label, True, color)
            self.screen.blit(medal_surf, ((w - medal_surf.get_width()) // 2, 130))
            pygame.draw.circle(self.screen, color, (w // 2, 200), 24)
        else:
            label = self.font.render("Pas de médaille", True, (180, 180, 180))
            self.screen.blit(label, ((w - label.get_width()) // 2, 140))

        if self.is_new_best:
            best = self.font.render("Nouveau meilleur temps !", True, (120, 255, 140))
            self.screen.blit(best, ((w - best.get_width()) // 2, 230))

        hint = self.font_small.render(
            "Entrée/A : recommencer    Échap/B : menu",
            True, (200, 200, 200),
        )
        self.screen.blit(hint, ((w - hint.get_width()) // 2, h - 24))
