import pygame
import os
import socket
from pathlib import Path


# Couleurs
BG_COLOR = (18, 18, 18)
TILE_COLOR = (38, 38, 38)
TILE_SELECTED_COLOR = (60, 60, 60)
BORDER_COLOR = (190, 190, 190)
BORDER_UNAVAILABLE = (65, 65, 65)
TEXT_COLOR = (240, 240, 240)
SUBTITLE_COLOR = (145, 145, 145)
UNAVAILABLE_COLOR = (38, 38, 38)
PLACEHOLDER_COLOR = (48, 48, 48)
PLACEHOLDER_TEXT_COLOR = (95, 95, 95)
HEADER_COLOR = (220, 220, 220)

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
        self.bg_images = self._load_bg_images()
        self._axis_moved = False
        # Carousel : position actuelle du scroll (pixels), interpolée vers la cible
        self._scroll_x = 0.0  # démarre centré sur le 1er jeu
        self._ip = self._get_ip()

    @staticmethod
    def _get_ip() -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "no network"

    def update(self, dt: float):
        """Anime le scroll du carousel vers la tuile sélectionnée."""
        step = TILE_W + TILE_GAP
        target = self.selected * step
        self._scroll_x += (target - self._scroll_x) * min(1.0, 14.0 * dt)

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

    def _load_bg_images(self):
        """Charge une version plein-écran de chaque cover pour le fond."""
        sw, sh = self.screen.get_size()
        bgs = []
        for game in self.games:
            bg = None
            img_path = game.get("image")
            if img_path and os.path.exists(img_path):
                try:
                    raw = pygame.image.load(img_path).convert()
                    bg = self._cover_crop(raw, sw, sh)
                except Exception:
                    pass
            bgs.append(bg)
        return bgs

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
            x, y = event.value
            # Gauche ou haut → jeu précédent ; droite ou bas → jeu suivant
            if x == -1 or y == 1:
                self.selected = (self.selected - 1) % len(self.games)
            elif x == 1 or y == -1:
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
            if event.button in (0, 1):  # A ou B → lancer le jeu
                if self.is_available(self.games[self.selected]):
                    return self.selected
            elif event.button in (10, 8, 7):  # LEFT / UP / L → jeu précédent
                self.selected = (self.selected - 1) % len(self.games)
            elif event.button in (11, 9, 5):  # RIGHT / DOWN / R → jeu suivant
                self.selected = (self.selected + 1) % len(self.games)

        return None

    def render(self):
        w, h = self.screen.get_size()

        # ── Fond : cover du jeu sélectionné ───────────────────────────────────
        bg = self.bg_images[self.selected]
        if bg:
            self.screen.blit(bg, (0, 0))
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 175))
            self.screen.blit(overlay, (0, 0))
        else:
            self.screen.fill(BG_COLOR)

        # ── En-tête : nom du jeu sélectionné ──────────────────────────────────
        game = self.games[self.selected]
        header_text = game["title"] if self.is_available(game) else f"{game['title']}  (bientôt)"
        header_surf = self.font_header.render(header_text, True, HEADER_COLOR)
        pygame.draw.line(self.screen, (70, 70, 70), (0, HEADER_H), (w, HEADER_H), 1)
        self.screen.blit(header_surf, ((w - header_surf.get_width()) // 2, (HEADER_H - header_surf.get_height()) // 2))

        # ── Carousel ───────────────────────────────────────────────────────────
        step   = TILE_W + TILE_GAP
        tile_y = HEADER_H + (h - HEADER_H - TILE_H) // 2
        # La tuile sélectionnée est centrée horizontalement
        center_x = w // 2 - TILE_W // 2

        # Zone de clip : toute la zone sous le header (cache les débordements)
        clip_rect = pygame.Rect(0, HEADER_H, w, h - HEADER_H)
        self.screen.set_clip(clip_rect)

        for i, g in enumerate(self.games):
            x = center_x + i * step - int(self._scroll_x)

            # Ne pas dessiner les tuiles trop loin hors-écran
            if x + TILE_W < -10 or x > w + 10:
                continue

            selected  = i == self.selected
            available = self.is_available(g)

            # Fond de la tuile (semi-transparent)
            tile_surf = pygame.Surface((TILE_W, TILE_H), pygame.SRCALPHA)
            if available:
                alpha = 200 if selected else 160
                rgb   = (65, 65, 65) if selected else (38, 38, 38)
            else:
                alpha = 130
                rgb   = (30, 30, 30)
            pygame.draw.rect(tile_surf, (*rgb, alpha), tile_surf.get_rect(), border_radius=12)
            tile_rect = pygame.Rect(x, tile_y, TILE_W, TILE_H)
            self.screen.blit(tile_surf, tile_rect)

            # Bordure
            border_color = BORDER_COLOR if selected else (BORDER_UNAVAILABLE if not available else (75, 75, 75))
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
            title_surf  = self.font_tile.render(g["title"], True, title_color)
            title_x = x + (TILE_W - title_surf.get_width()) // 2
            title_y = tile_y + TILE_H - 26 + (26 - title_surf.get_height()) // 2
            self.screen.blit(title_surf, (title_x, title_y))

        self.screen.set_clip(None)

        # ── Dégradés bords gauche/droite (effet profondeur carousel) ──────────
        FADE_W = 48
        for side in ('left', 'right'):
            fade = pygame.Surface((FADE_W, h - HEADER_H), pygame.SRCALPHA)
            for px in range(FADE_W):
                t     = px / FADE_W
                alpha = int(160 * (1.0 - t)) if side == 'left' else int(160 * t)
                pygame.draw.line(fade, (0, 0, 0, alpha),
                                 (px if side == 'left' else FADE_W - 1 - px, 0),
                                 (px if side == 'left' else FADE_W - 1 - px, h - HEADER_H))
            self.screen.blit(fade, (0 if side == 'left' else w - FADE_W, HEADER_H))

        # ── Flèches indicatrices ──────────────────────────────────────────────
        arrow_font = pygame.font.SysFont("Arial", 20, bold=True)
        arrow_y    = HEADER_H + (h - HEADER_H) // 2 - 10
        if self.selected > 0:
            a = arrow_font.render("◄", True, (180, 180, 180))
            self.screen.blit(a, (6, arrow_y))
        if self.selected < len(self.games) - 1:
            a = arrow_font.render("►", True, (180, 180, 180))
            self.screen.blit(a, (w - a.get_width() - 6, arrow_y))

        # ── Indicateurs de position (points) ──────────────────────────────────
        n = len(self.games)
        if n > 1:
            dot_r   = 3
            dot_gap = 10
            dots_w  = n * (dot_r * 2) + (n - 1) * (dot_gap - dot_r * 2)
            dot_y   = h - 18
            dot_x0  = (w - dots_w) // 2
            for i in range(n):
                cx = dot_x0 + i * dot_gap
                col = (200, 200, 200) if i == self.selected else (60, 60, 60)
                pygame.draw.circle(self.screen, col, (cx, dot_y), dot_r)

        # ── Indication de navigation ───────────────────────────────────────────
        hint_font = pygame.font.SysFont("Arial", 11)
        hint = hint_font.render("◄ ► naviguer    A/Entrée sélectionner    B/Échap quitter", True, (100, 100, 100))
        self.screen.blit(hint, ((w - hint.get_width()) // 2, h - hint.get_height() - 4))

        # ── IP en bas à gauche (discret) ────────────────────────────────────
        ip_surf = hint_font.render(self._ip, True, (55, 55, 55))
        self.screen.blit(ip_surf, (4, h - ip_surf.get_height() - 4))
