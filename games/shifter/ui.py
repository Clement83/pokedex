"""
Utilitaires de dessin : sprites véhicules, compte-tours, route.
"""
import pygame
import math
from pathlib import Path

# ── Sprites véhicules ─────────────────────────────────────────────────────────
# Spritesheet vehicle1.png : 2 colonnes × 3 lignes → 6 frames de 768×341 px
# Ordre : row0/col0=Vert, row0/col1=Jaune, row1/col0=Rouge,
#         row1/col1=Blanc, row2/col0=Violet, row2/col1=Bleu

_SPRITE_CACHE: dict = {}
_FW, _FH = 768, 341   # taille d'un frame dans le sheet


def load_vehicle_sprites(target_w: int = 160) -> list:
    """Charge et découpe vehicle1.png. Renvoie liste de 6 surfaces scalées."""
    if target_w in _SPRITE_CACHE:
        return _SPRITE_CACHE[target_w]

    path = Path("asset/sprite/vehicle1.png")
    sheet = pygame.image.load(str(path)).convert_alpha()

    # Supprimer le fond blanc si l'image n'est pas en transparence
    corner = sheet.get_at((0, 0))
    if corner.a == 255 and corner.r > 240 and corner.g > 240 and corner.b > 240:
        sheet.set_colorkey((255, 255, 255))

    scale = target_w / _FW
    th = int(_FH * scale)

    sprites = []
    for row in range(3):
        for col in range(2):
            frame = sheet.subsurface(
                pygame.Rect(col * _FW, row * _FH, _FW, _FH)
            ).copy()
            scaled = pygame.transform.smoothscale(frame, (target_w, th))
            sprites.append(scaled)

    _SPRITE_CACHE[target_w] = sprites
    return sprites


def draw_car_sprite(surf: pygame.Surface, cx: int, cy: int, sprite: pygame.Surface):
    """Blit sprite centré en (cx, cy)."""
    surf.blit(sprite, (cx - sprite.get_width() // 2,
                        cy - sprite.get_height() // 2))


# ── Voiture procédurale (fallback) ────────────────────────────────────────────

def draw_car(surf: pygame.Surface, cx: int, cy: int, body_color, scale: float = 1.0):
    """
    Dessine une voiture style tuner vue de profil (gauche).
    cx, cy = centre de la voiture (roues incluses).
    """
    bw = int(88 * scale)   # largeur de la carrosserie
    bh = int(22 * scale)   # hauteur de la carrosserie (bas)
    rh = int(18 * scale)   # hauteur du toit
    rw = int(52 * scale)   # largeur du toit
    wr = int(10 * scale)   # rayon des roues

    # ── Corps (bas) ───────────────────────────────────────────────────────────
    body_y = cy - wr + 2
    body_rect = pygame.Rect(cx - bw // 2, body_y - bh, bw, bh)
    pygame.draw.rect(surf, body_color, body_rect, border_radius=4)

    # Pare-chocs (légèrement plus clairs)
    bump_col = _brighten(body_color, 40)
    pygame.draw.rect(surf, bump_col, (cx - bw // 2, body_y - bh, 8, bh), border_radius=3)
    pygame.draw.rect(surf, bump_col, (cx + bw // 2 - 8, body_y - bh, 8, bh), border_radius=3)

    # ── Toit / habitacle ──────────────────────────────────────────────────────
    roof_x = cx - rw // 2 - 4
    roof_y = body_y - bh - rh + 4
    roof_color = _darken(body_color, 30)
    pygame.draw.rect(surf, roof_color, (roof_x, roof_y, rw, rh), border_radius=5)

    # Vitres
    win_col = (120, 195, 240)
    win_w   = int(rw * 0.42)
    win_h   = int(rh * 0.65)
    # Vitre avant
    pygame.draw.rect(surf, win_col, (roof_x + rw - win_w - 4, roof_y + 3, win_w, win_h), border_radius=2)
    # Vitre arrière
    pygame.draw.rect(surf, win_col, (roof_x + 4, roof_y + 3, win_w, win_h), border_radius=2)

    # ── Roues ─────────────────────────────────────────────────────────────────
    front_x = cx + bw // 2 - int(14 * scale)
    rear_x  = cx - bw // 2 + int(14 * scale)
    wheel_y = cy

    for wx in (front_x, rear_x):
        pygame.draw.circle(surf, (18, 18, 18),  (wx, wheel_y), wr)
        pygame.draw.circle(surf, (130, 130, 140), (wx, wheel_y), wr - 4)
        pygame.draw.circle(surf, (18, 18, 18),  (wx, wheel_y), 4)

    # Phares (petits points jaunes)
    light_col = (255, 235, 120)
    pygame.draw.circle(surf, light_col, (cx + bw // 2 - 3, body_y - bh + 5), 3)


# ── Décor / route scrollante ──────────────────────────────────────────────────

_BG_CACHE: dict = {}


def _load_bg_strip(panel_w: int, panel_h: int) -> list:
    """
    Charge les 3 images de fond et les scale à panel_h de hauteur.
    Retourne la liste de surfaces dans l'ordre : [start, mid, end].
    La largeur de chaque image est proportionnellement conservée.
    """
    key = (panel_w, panel_h)
    if key in _BG_CACHE:
        return _BG_CACHE[key]

    base = Path("asset/sprite")
    names = ["start-back.jpg", "mid-back.jpg", "end-back.jpg"]
    surfs = []
    for name in names:
        img = pygame.image.load(str(base / name)).convert()
        iw, ih = img.get_size()
        scaled_w = max(panel_w, int(iw * panel_h / ih))
        surfs.append(pygame.transform.smoothscale(img, (scaled_w, panel_h)))

    _BG_CACHE[key] = surfs
    return surfs


class TrackBackground:
    """
    Fond de course scrollant basé sur les images start/mid/end.
    La séquence est : start → mid (répété) → end sur 400 m.
    Le scroll est piloté par la distance parcourue (px/m calculés depuis la
    largeur totale des images ramenée à RACE_DISTANCE mètres).
    """

    # Nombre de segments mid intercalés entre start et end
    MID_COUNT = 8

    def __init__(self, panel_w: int, panel_h: int):
        self.pw = panel_w
        self.ph = panel_h

        surfs = _load_bg_strip(panel_w, panel_h)
        self._start = surfs[0]
        self._mid   = surfs[1]
        self._end   = surfs[2]

        # Largeurs individuelles
        self._sw = self._start.get_width()
        self._mw = self._mid.get_width()
        self._ew = self._end.get_width()

        # Largeur totale de la bande
        self._total_w = self._sw + self._mw * self.MID_COUNT + self._ew

        # Pixels parcourus (mis à jour depuis update())
        self._scroll_px = 0.0

        # Echelle pixels/mètre (pour placer la voiture adverse)
        from config import RACE_DISTANCE
        self._px_per_meter = self._total_w / RACE_DISTANCE

    def update(self, position_m: float):
        """Scroll piloté par la position sur la course (0..RACE_DISTANCE)."""
        from config import RACE_DISTANCE
        max_scroll = max(0, self._total_w - self.pw)
        t = max(0.0, min(1.0, position_m / RACE_DISTANCE))
        self._scroll_px = t * max_scroll

    def draw(self, surf: pygame.Surface, ox: int, oy: int):
        """Dessine le fond dans le panel (ox, oy)."""
        scroll = int(self._scroll_px)

        # On construit la séquence de segments [(surface, x_in_strip)]
        segments = []
        x_cursor = 0
        segments.append((self._start, x_cursor))
        x_cursor += self._sw
        for _ in range(self.MID_COUNT):
            segments.append((self._mid, x_cursor))
            x_cursor += self._mw
        segments.append((self._end, x_cursor))

        # Clamp : on ne dépasse pas la fin
        max_scroll = max(0, self._total_w - self.pw)
        scroll = min(scroll, max_scroll)

        for img, img_x in segments:
            # position de l'image sur le panel après scroll
            dest_x = ox + img_x - scroll
            iw = img.get_width()
            # culling : skip si hors champ
            if dest_x + iw <= ox or dest_x >= ox + self.pw:
                continue
            surf.blit(img, (dest_x, oy))

        # Clip au panel pour ne pas déborder
        # (pygame blit se charge de clipper tout seul sur la surface)

    @property
    def car_y(self) -> int:
        """Y (dans le panel) où poser la voiture (bas de la route)."""
        return int(self.ph * 0.92)

    @property
    def px_per_meter(self) -> float:
        """Pixels de background correspondant à 1 mètre de course."""
        return self._px_per_meter


# ── Compte-tours ──────────────────────────────────────────────────────────────

def draw_smoke(
    surf: pygame.Surface,
    car_cx: int,
    car_top_y: int,
    intensity: float,
):
    """
    Dessine des volutes de fumée au-dessus de la voiture.
    intensity : 0..1 (0 = pas de fumée, 1 = fumée maximale)
    """
    import random
    rng = random.Random(int(pygame.time.get_ticks() / 80))  # graine temps → animation

    n_puffs   = max(1, int(intensity * 6))
    base_alpha = int(intensity * 140)

    for i in range(n_puffs):
        offset_x = rng.randint(-10, 10)
        offset_y = rng.randint(0, int(25 * intensity))
        radius   = rng.randint(5, max(5, int(12 * intensity) + 4))
        alpha    = max(30, base_alpha - i * 18)

        smoke_col = (180, 180, 180) if not (i % 3 == 0 and intensity > 0.6) else (100, 80, 60)

        puff = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(puff, (*smoke_col, alpha), (radius, radius), radius)
        surf.blit(puff, (car_cx - radius + offset_x,
                          car_top_y - radius - offset_y - 8))


def draw_tachometer(
    surf: pygame.Surface,
    cx: int, cy: int,
    radius: int,
    rpm: float,
    max_rpm: float,
    opt_rpm: float,
    gear: int,
    font_small,
    font_med,
    player_color,
):
    """
    Arc de compte-tours style NFS avec barre de LEDs et anneau de zone.
    cx, cy = centre (peut être sous le bas de l'écran pour effet d'immersion).
    Arc visible de ~225° à ~-45° (270° de balayage, sens math CCW).
    """
    ARC_START  = 225
    ARC_END    = -45
    ARC_SWEEP  = 270

    SHIFT_PERF = 200
    SHIFT_GOOD = 500

    # ── Zone courante ─────────────────────────────────────────────────────────
    diff = abs(rpm - opt_rpm)
    if diff <= SHIFT_PERF:
        zone      = 'PERFECT'
        zone_col  = (40, 240, 80)
    elif diff <= SHIFT_GOOD:
        zone      = 'GOOD'
        zone_col  = (240, 200, 0)
    else:
        zone      = 'BAD'
        zone_col  = (220, 40, 40)

    def rpm_angle(r):
        t = max(0.0, min(1.0, r / max_rpm))
        return ARC_START - t * ARC_SWEEP

    def arc_pt(deg, r):
        rad = math.radians(deg)
        return (int(cx + r * math.cos(rad)), int(cy - r * math.sin(rad)))

    def draw_arc_band(color, rpm_lo, rpm_hi, r_in, r_out, steps=40):
        a0 = rpm_angle(rpm_lo)
        a1 = rpm_angle(rpm_hi)
        for i in range(steps):
            t1 = i / steps
            t2 = (i + 1) / steps
            d1 = a0 + (a1 - a0) * t1
            d2 = a0 + (a1 - a0) * t2
            p1 = arc_pt(d1, r_in);  p2 = arc_pt(d1, r_out)
            p3 = arc_pt(d2, r_out); p4 = arc_pt(d2, r_in)
            pygame.draw.polygon(surf, color, [p1, p2, p3, p4])

    r1 = radius - 10
    r2 = radius

    # ── Fond arc ──────────────────────────────────────────────────────────────
    draw_arc_band((30, 30, 35), 0, max_rpm, r1, r2)

    # ── Zones colorées de l'arc ───────────────────────────────────────────────
    red_start = opt_rpm + SHIFT_GOOD
    draw_arc_band((160, 25, 25), red_start, max_rpm, r1, r2)
    draw_arc_band((170, 150, 0),
                  opt_rpm - SHIFT_GOOD, opt_rpm - SHIFT_PERF, r1, r2)
    draw_arc_band((170, 150, 0),
                  opt_rpm + SHIFT_PERF, red_start, r1, r2)
    draw_arc_band((0, 180, 60),
                  opt_rpm - SHIFT_PERF, opt_rpm + SHIFT_PERF, r1, r2)

    # ── Anneau intérieur : couleur de la zone courante ────────────────────────
    ring_r1 = r1 - 4
    ring_r2 = r1 - 1
    draw_arc_band(zone_col, 0, max_rpm, ring_r1, ring_r2)

    # ── Aiguille ──────────────────────────────────────────────────────────────
    needle_deg  = rpm_angle(rpm)
    needle_end  = arc_pt(needle_deg, int(radius * 0.9))
    needle_base = arc_pt(needle_deg, int(radius * 0.3))
    pygame.draw.line(surf, (255, 255, 255), needle_base, needle_end, 2)
    pygame.draw.circle(surf, (255, 255, 255), needle_end, 2)

    # ── Marques de graduation ─────────────────────────────────────────────────
    for k_rpm in range(0, int(max_rpm) + 1, int(max_rpm // 8)):
        deg   = rpm_angle(k_rpm)
        p_in  = arc_pt(deg, int(radius * 0.65))
        p_out = arc_pt(deg, radius + 1)
        pygame.draw.line(surf, (110, 110, 130), p_in, p_out, 1)

    # ── Texte central : rapport + RPM ─────────────────────────────────────────
    gear_surf = font_med.render(str(gear), True, zone_col)
    surf.blit(gear_surf, (cx - gear_surf.get_width() // 2,
                           cy - gear_surf.get_height() // 2 - 8))

    rpm_k    = round(rpm / 1000, 1)
    rpm_surf = font_small.render(f"{rpm_k}k", True, (160, 160, 185))
    surf.blit(rpm_surf, (cx - rpm_surf.get_width() // 2, cy + 5))

    # ── Bordure extérieure couleur joueur ─────────────────────────────────────
    _draw_thin_arc(surf, player_color, cx, cy, radius + 3, ARC_START, ARC_END, 1)


def _draw_thin_arc(surf, color, cx, cy, r, a_start, a_end, width, steps=80):
    pts = []
    for i in range(steps + 1):
        t   = i / steps
        deg = a_start + (a_end - a_start) * t
        rad = math.radians(deg)
        pts.append((cx + r * math.cos(rad), cy - r * math.sin(rad)))
    if len(pts) > 1:
        pygame.draw.lines(surf, color, False, [(int(x), int(y)) for x, y in pts], width)


# ── Feux de départ ─────────────────────────────────────────────────────────────

class StartLights:
    """Feux de départ au centre de l'écran ( rouge → orange → vert )."""
    PHASES = [
        (3.0, 'red'),
        (1.0, 'orange'),
        (0.0, 'green'),
    ]

    def __init__(self, screen_w, screen_h):
        self.sw      = screen_w
        self.sh      = screen_h
        self.timer   = sum(d for d, _ in self.PHASES)
        self.phase   = 'waiting'   # 'red' | 'orange' | 'green' | 'done'
        self.done    = False
        self._phase_timer = 0.0
        self._go_flash    = 0.0

    def start(self):
        self.phase        = 'red'
        self._phase_timer = self.PHASES[0][0]

    def update(self, dt):
        if self.phase == 'waiting' or self.done:
            return
        self._phase_timer -= dt
        if self._phase_timer <= 0:
            if self.phase == 'red':
                self.phase        = 'orange'
                self._phase_timer = self.PHASES[1][0]
            elif self.phase == 'orange':
                self.phase        = 'green'
                self._phase_timer = 1.2
                self._go_flash    = 1.2
            elif self.phase == 'green':
                self.done = True

    def draw(self, surf):
        if self.done:
            return
        lx = self.sw // 2
        ly = 36
        r  = 14
        gap = 34

        colors_off = {'red': (60, 10, 10), 'orange': (55, 40, 10), 'green': (10, 55, 10)}
        colors_on  = {'red': (255, 40, 40), 'orange': (255, 165, 0), 'green': (40, 240, 80)}

        lights = ['red', 'orange', 'green']
        for i, name in enumerate(lights):
            x = lx + (i - 1) * gap
            on = (
                (self.phase == 'red'    and name == 'red') or
                (self.phase == 'orange' and name in ('red', 'orange')) or
                (self.phase == 'green'  and name == 'green')
            )
            col = colors_on[name] if on else colors_off[name]
            pygame.draw.circle(surf, col,        (x, ly), r)
            pygame.draw.circle(surf, (200,200,200),(x, ly), r, 2)

        if self.phase == 'green' and self._go_flash > 0:
            self._go_flash -= 0.02
            go_font = pygame.font.SysFont("Arial", 28, bold=True)
            t = go_font.render("GO!", True, (80, 255, 80))
            surf.blit(t, (lx - t.get_width() // 2, ly + r + 6))

    @property
    def race_started(self) -> bool:
        return self.phase == 'green'


# ── Helpers couleurs ──────────────────────────────────────────────────────────

def _brighten(color, amount):
    return tuple(min(255, c + amount) for c in color)

def _darken(color, amount):
    return tuple(max(0, c - amount) for c in color)
