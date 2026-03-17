import pygame
import os
from pathlib import Path


# Couleurs
BG_COLOR = (12, 12, 28)
TILE_COLOR = (28, 28, 55)
TILE_SELECTED_COLOR = (45, 45, 90)
BORDER_COLOR = (110, 110, 255)
BORDER_UNAVAILABLE = (60, 60, 80)
TEXT_COLOR = (240, 240, 255)
SUBTITLE_COLOR = (160, 160, 200)
UNAVAILABLE_COLOR = (45, 45, 55)
PLACEHOLDER_COLOR = (35, 35, 60)
PLACEHOLDER_TEXT_COLOR = (90, 90, 120)
HEADER_COLOR = (200, 200, 255)

TILE_W = 155
TILE_H = 210
TILE_GAP = 24
IMG_W = 135
IMG_H = 148
HEADER_H = 36


class Launcher:
    def __init__(self, screen, games, base_dir):
        self.screen = screen
        self.games = games
        self.base_dir = Path(base_dir)
        self.selected = 0
        self.font_header = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_tile = pygame.font.SysFont("Arial", 13, bold=True)
        self.font_placeholder = pygame.font.SysFont("Arial", 36, bold=True)
        self.images = self._load_images()
        self._axis_moved = False

    def _load_images(self):
        images = []
        for game in self.games:
            img = None
            img_path = game.get("image")
            if img_path and os.path.exists(img_path):
                try:
                    raw = pygame.image.load(img_path).convert()
                    img = self._cover_crop(raw, IMG_W, IMG_H)
                except Exception:
                    pass
            images.append(img)
        return images

    @staticmethod
    def _cover_crop(surf: pygame.Surface, tw: int, th: int) -> pygame.Surface:
        """Redimensionne + crop centré (style CSS cover) sans déformer."""
        sw, sh = surf.get_size()
        scale = max(tw / sw, th / sh)
        nw = int(sw * scale)
        nh = int(sh * scale)
        scaled = pygame.transform.smoothscale(surf, (nw, nh))
        cx = (nw - tw) // 2
        cy = (nh - th) // 2
        cropped = pygame.Surface((tw, th))
        cropped.blit(scaled, (0, 0), pygame.Rect(cx, cy, tw, th))
        return cropped

    def is_available(self, game):
        path = game.get("path")
        entry = game.get("entry", "main")
        return bool(path and os.path.exists(os.path.join(path, entry + ".py")))

    def handle_event(self, event):
        """Retourne l'index du jeu sélectionné si confirmé, sinon None."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.selected = (self.selected - 1) % len(self.games)
            elif event.key == pygame.K_RIGHT:
                self.selected = (self.selected + 1) % len(self.games)
            elif event.key in (pygame.K_RETURN, pygame.K_n):
                if self.is_available(self.games[self.selected]):
                    return self.selected
            elif event.key == pygame.K_ESCAPE:
                return -1  # quitter le launcher

        if event.type == pygame.JOYHATMOTION:
            x, _ = event.value
            if x == -1:
                self.selected = (self.selected - 1) % len(self.games)
            elif x == 1:
                self.selected = (self.selected + 1) % len(self.games)

        if event.type == pygame.JOYAXISMOTION:
            if event.axis == 0:
                if event.value < -0.7 and not self._axis_moved:
                    self.selected = (self.selected - 1) % len(self.games)
                    self._axis_moved = True
                elif event.value > 0.7 and not self._axis_moved:
                    self.selected = (self.selected + 1) % len(self.games)
                    self._axis_moved = True
                elif abs(event.value) < 0.3:
                    self._axis_moved = False

        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:  # A / Confirmer
                if self.is_available(self.games[self.selected]):
                    return self.selected
            elif event.button == 1:  # B / Quitter
                return -1

        return None

    def render(self):
        w, h = self.screen.get_size()
        self.screen.fill(BG_COLOR)

        # ── En-tête : nom du jeu sélectionné ──────────────────────────────────
        game = self.games[self.selected]
        header_text = game["title"] if self.is_available(game) else f"{game['title']}  (bientôt)"
        header_surf = self.font_header.render(header_text, True, HEADER_COLOR)
        pygame.draw.line(self.screen, (50, 50, 100), (0, HEADER_H), (w, HEADER_H), 1)
        self.screen.blit(header_surf, ((w - header_surf.get_width()) // 2, (HEADER_H - header_surf.get_height()) // 2))

        # ── Tuiles ─────────────────────────────────────────────────────────────
        n = len(self.games)
        total_w = n * TILE_W + (n - 1) * TILE_GAP
        start_x = (w - total_w) // 2
        tile_y = HEADER_H + (h - HEADER_H - TILE_H) // 2

        for i, g in enumerate(self.games):
            x = start_x + i * (TILE_W + TILE_GAP)
            selected = i == self.selected
            available = self.is_available(g)

            # Fond de la tuile
            tile_color = (TILE_SELECTED_COLOR if selected else TILE_COLOR) if available else UNAVAILABLE_COLOR
            tile_rect = pygame.Rect(x, tile_y, TILE_W, TILE_H)
            pygame.draw.rect(self.screen, tile_color, tile_rect, border_radius=12)

            # Bordure
            border_color = BORDER_COLOR if selected else (BORDER_UNAVAILABLE if not available else (55, 55, 88))
            border_w = 3 if selected else 1
            pygame.draw.rect(self.screen, border_color, tile_rect, border_w, border_radius=12)

            # Image ou placeholder
            img_x = x + (TILE_W - IMG_W) // 2
            img_y = tile_y + 8
            if self.images[i]:
                self.screen.blit(self.images[i], (img_x, img_y))
            else:
                ph_rect = pygame.Rect(img_x, img_y, IMG_W, IMG_H)
                pygame.draw.rect(self.screen, PLACEHOLDER_COLOR, ph_rect, border_radius=8)
                q = self.font_placeholder.render("?", True, PLACEHOLDER_TEXT_COLOR)
                self.screen.blit(q, (img_x + (IMG_W - q.get_width()) // 2,
                                     img_y + (IMG_H - q.get_height()) // 2))

            # Titre de la tuile
            title_color = TEXT_COLOR if available else SUBTITLE_COLOR
            title_surf = self.font_tile.render(g["title"], True, title_color)
            title_x = x + (TILE_W - title_surf.get_width()) // 2
            title_y = tile_y + TILE_H - 26 + (26 - title_surf.get_height()) // 2
            self.screen.blit(title_surf, (title_x, title_y))

        # ── Indication de navigation ───────────────────────────────────────────
        hint_font = pygame.font.SysFont("Arial", 11)
        hint = hint_font.render("◄ ► naviguer    A/Entrée sélectionner    B/Échap quitter", True, (70, 70, 110))
        self.screen.blit(hint, ((w - hint.get_width()) // 2, h - hint.get_height() - 4))
