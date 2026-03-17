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
    MID_COUNT = 4

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


# ── Constantes internes cockpit ───────────────────────────────────────────────
_H_W = 240   # largeur d'un panel (= PW dans scene_race)
_H_H = 62    # hauteur de la bande HUD
_SP  = 200   # SHIFT_PERF RPM
_SG  = 500   # SHIFT_GOOD RPM


def _hud_bg(surf: pygame.Surface, ox: int, tint=(0, 0, 0, 195)):
    """Fond semi-transparent de la bande HUD."""
    bg = pygame.Surface((_H_W, _H_H), pygame.SRCALPHA)
    bg.fill(tint)
    surf.blit(bg, (ox, 0))


def _arc_gauge(surf, cx, cy, r, rpm, max_rpm, opt_rpm, accent_col,
               arc_start=225, arc_sweep=270, band_w=8, steps=32):
    """Arc compte-tours + aiguille, sans texte. Réutilisé par plusieurs styles."""
    r_out, r_in = r, r - band_w

    def t_ang(v):
        return arc_start - max(0.0, min(1.0, v / max_rpm)) * arc_sweep

    def pt(deg, radius):
        rad = math.radians(deg)
        return (int(cx + radius * math.cos(rad)), int(cy - radius * math.sin(rad)))

    def band(color, v0, v1, ra, rb, n=steps):
        a0, a1 = t_ang(v0), t_ang(v1)
        for i in range(n):
            t1, t2 = i / n, (i + 1) / n
            d1 = a0 + (a1 - a0) * t1
            d2 = a0 + (a1 - a0) * t2
            pygame.draw.polygon(surf, color,
                                [pt(d1, ra), pt(d1, rb), pt(d2, rb), pt(d2, ra)])

    band((28, 28, 34), 0, max_rpm, r_in, r_out)
    red_start = opt_rpm + _SG
    band((148, 20, 20), red_start, max_rpm, r_in, r_out)
    band((158, 138, 0), opt_rpm - _SG, opt_rpm - _SP, r_in, r_out)
    band((158, 138, 0), opt_rpm + _SP, red_start, r_in, r_out)
    band((0, 168, 54), opt_rpm - _SP, opt_rpm + _SP, r_in, r_out)

    for k in range(0, int(max_rpm) + 1, int(max_rpm // 6)):
        deg = t_ang(k)
        pygame.draw.line(surf, (85, 85, 105), pt(deg, r_in - 1), pt(deg, r_out + 1), 1)

    ndeg = t_ang(rpm)
    pygame.draw.line(surf, (255, 255, 255), pt(ndeg, int(r * 0.28)), pt(ndeg, int(r * 0.88)), 2)
    pygame.draw.circle(surf, (255, 255, 255), pt(ndeg, int(r * 0.88)), 2)
    _draw_thin_arc(surf, accent_col, cx, cy, r + 2, arc_start, arc_start - arc_sweep, 1)


# ── Styles de cockpit ─────────────────────────────────────────────────────────

def _cockpit_sport(surf, ox, car, pid, font_sm, font_md, p_col):
    """Classic 270° arc + vitesse digitale intégrée. Style tuner JDM."""
    _hud_bg(surf, ox, (0, 10, 2, 205))
    cx, cy, r = ox + 120, 40, 27
    _arc_gauge(surf, cx, cy, r, car.rpm, car.max_rpm, car.opt_rpm, p_col)

    spd_s = font_md.render(str(int(car.speed)), True, (240, 240, 240))
    surf.blit(spd_s, (cx - spd_s.get_width() // 2, cy - spd_s.get_height() // 2 + 1))
    kph_s = font_sm.render("km/h", True, (95, 95, 95))
    surf.blit(kph_s, (cx - kph_s.get_width() // 2, cy + 9))

    g_s = font_md.render(str(car.gear), True, p_col)
    surf.blit(g_s, (cx - g_s.get_width() // 2, cy - r - 2))

    surf.blit(font_sm.render(f"J{pid + 1}", True, p_col), (ox + 4, 3))
    surf.blit(font_sm.render(f"{int(car.position)}m", True, (120, 120, 155)), (ox + 4, 15))
    t_s = font_sm.render(f"{car.race_time:.2f}s", True, (165, 165, 195))
    surf.blit(t_s, (ox + _H_W - t_s.get_width() - 4, 3))


def _cockpit_rally(surf, ox, car, pid, font_sm, font_md, p_col):
    """Barre de 14 LEDs séquentielles + affichage digital. Style rally/F1."""
    _hud_bg(surf, ox, (12, 10, 0, 205))

    n, led_r, spacing = 14, 4, 13
    bar_x0  = ox + (_H_W - (n - 1) * spacing) // 2
    rpm_pct = min(1.0, car.rpm / car.max_rpm)
    for i in range(n):
        lx  = bar_x0 + i * spacing
        lit = rpm_pct >= i / n
        if i < 6:
            on_c, off_c = (35, 215, 55), (9, 45, 12)
        elif i < 10:
            on_c, off_c = (218, 195, 0), (48, 42, 0)
        else:
            on_c, off_c = (238, 35, 35), (52, 8, 8)
        col = on_c if lit else off_c
        pygame.draw.circle(surf, col, (lx, 10), led_r)
        if lit:
            glow = pygame.Surface((led_r * 4, led_r * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*on_c, 50), (led_r * 2, led_r * 2), led_r * 2)
            surf.blit(glow, (lx - led_r * 2, 10 - led_r * 2))

    g_s = font_md.render(str(car.gear), True, p_col)
    surf.blit(g_s,  (ox + 20, 30))
    surf.blit(g_s,  (ox + 21, 30))  # pseudo-gras
    surf.blit(font_sm.render("GEAR", True, (75, 70, 30)), (ox + 16, 48))

    spd_s = font_md.render(str(int(car.speed)), True, (245, 242, 215))
    surf.blit(spd_s, (ox + 120 - spd_s.get_width() // 2, 28))
    kph_s = font_sm.render("km/h", True, (95, 90, 45))
    surf.blit(kph_s, (ox + 120 - kph_s.get_width() // 2, 46))

    surf.blit(font_sm.render(f"J{pid + 1}", True, p_col), (ox + 4, 3))
    t_s = font_sm.render(f"{car.race_time:.2f}s", True, (165, 165, 195))
    surf.blit(t_s, (ox + _H_W - t_s.get_width() - 4, 3))
    d_s = font_sm.render(f"{int(car.position)}m", True, (105, 100, 60))
    surf.blit(d_s, (ox + _H_W - d_s.get_width() - 4, 15))


def _cockpit_digital(surf, ox, car, pid, font_sm, font_md, p_col):
    """Affichage LCD pur : barre RPM + grands chiffres. Style tablette de bord."""
    _hud_bg(surf, ox, (2, 2, 8, 212))

    bx, by, bw, bh = ox + 4, 6, _H_W - 8, 7
    rpm_pct  = min(1.0, car.rpm / car.max_rpm)
    filled_w = int(bw * rpm_pct)
    pygame.draw.rect(surf, (18, 18, 28), (bx, by, bw, bh), border_radius=3)
    if filled_w > 0:
        diff = abs(car.rpm - car.opt_rpm)
        if car.rpm >= car.max_rpm:
            bar_col = (228, 28, 28)
        elif diff <= _SP:
            bar_col = (35, 215, 55)
        elif diff <= _SG:
            bar_col = (215, 190, 0)
        else:
            bar_col = (55, 135, 220)
        pygame.draw.rect(surf, bar_col, (bx, by, filled_w, bh), border_radius=3)
    opt_x = bx + int(bw * car.opt_rpm / car.max_rpm)
    pygame.draw.line(surf, (195, 195, 195), (opt_x, by - 1), (opt_x, by + bh + 1), 1)

    rk_s = font_sm.render(f"{car.rpm / 1000:.1f}k", True, (135, 135, 165))
    surf.blit(rk_s, (ox + _H_W - rk_s.get_width() - 6, by - 1))

    surf.blit(font_sm.render(f"J{pid + 1}", True, p_col), (ox + 4, by - 1))
    surf.blit(font_md.render(str(car.gear), True, p_col), (ox + 4, 20))
    surf.blit(font_sm.render("GEAR", True, (55, 55, 78)), (ox + 4, 37))

    spd_s = font_md.render(str(int(car.speed)), True, (215, 228, 255))
    surf.blit(spd_s, (ox + 95 - spd_s.get_width() // 2, 22))
    surf.blit(font_sm.render("km/h", True, (82, 95, 128)), (ox + 95 - 14, 40))

    t_s = font_sm.render(f"{car.race_time:.2f}s", True, (165, 165, 198))
    d_s = font_sm.render(f"{int(car.position)}m", True, (105, 105, 138))
    surf.blit(t_s, (ox + _H_W - t_s.get_width() - 4, 20))
    surf.blit(d_s, (ox + _H_W - d_s.get_width() - 4, 35))


def _cockpit_retro(surf, ox, car, pid, font_sm, font_md, p_col):
    """Deux jauges analogiques côte à côte. Style européen rétro."""
    _hud_bg(surf, ox, (8, 4, 0, 210))

    cx_rpm, cx_spd, cy, r = ox + 68, ox + 172, 41, 22
    _arc_gauge(surf, cx_rpm, cy, r, car.rpm, car.max_rpm, car.opt_rpm,
               (210, 115, 18), arc_start=220, arc_sweep=260, band_w=6)
    _arc_gauge(surf, cx_spd, cy, r, car.speed, 220.0, 176.0,
               (195, 195, 195), arc_start=220, arc_sweep=260, band_w=6)

    rpm_s = font_sm.render(f"{car.rpm / 1000:.1f}k", True, (238, 195, 115))
    spd_s = font_sm.render(str(int(car.speed)),       True, (235, 228, 195))
    surf.blit(rpm_s, (cx_rpm - rpm_s.get_width() // 2, cy - rpm_s.get_height() // 2 + 1))
    surf.blit(spd_s, (cx_spd - spd_s.get_width() // 2, cy - spd_s.get_height() // 2 + 1))

    surf.blit(font_sm.render("RPM",  True, (125, 75, 18)),   (cx_rpm - 12, 57))
    surf.blit(font_sm.render("km/h", True, (105, 105, 105)), (cx_spd - 14, 57))

    g_s = font_md.render(str(car.gear), True, p_col)
    surf.blit(g_s, (ox + 120 - g_s.get_width() // 2, cy - g_s.get_height() // 2))

    surf.blit(font_sm.render(f"J{pid + 1}", True, p_col), (ox + 4, 3))
    t_s = font_sm.render(f"{car.race_time:.2f}s", True, (155, 135, 95))
    surf.blit(t_s, (ox + _H_W - t_s.get_width() - 4, 3))


def _cockpit_race(surf, ox, car, pid, font_sm, font_md, p_col):
    """6 LEDs de shift en haut + arc gauche + vitesse droite. Style course."""
    _hud_bg(surf, ox, (10, 0, 14, 210))

    thresholds = [car.opt_rpm - _SG + i * (2 * _SG / 5) for i in range(6)]
    for i, thresh in enumerate(thresholds):
        lx  = ox + 88 + i * 13
        lit = car.rpm >= thresh
        if i < 3:
            on_c, off_c = (28, 215, 55), (7, 38, 11)
        elif i < 5:
            on_c, off_c = (228, 195, 0), (43, 38, 0)
        else:
            on_c, off_c = (238, 28, 28), (48, 7, 7)
        col = on_c if lit else off_c
        pygame.draw.circle(surf, col, (lx, 8), 5)
        if lit:
            glow = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*on_c, 55), (10, 10), 10)
            surf.blit(glow, (lx - 10, -2))

    cx, cy, r = ox + 82, 43, 25
    _arc_gauge(surf, cx, cy, r, car.rpm, car.max_rpm, car.opt_rpm, p_col)
    g_s = font_md.render(str(car.gear), True, p_col)
    surf.blit(g_s, (cx - g_s.get_width() // 2, cy - g_s.get_height() // 2))

    spd_s = font_md.render(str(int(car.speed)), True, (242, 242, 242))
    kph_s = font_sm.render("km/h", True, (115, 75, 135))
    surf.blit(spd_s, (ox + 185 - spd_s.get_width() // 2, 30))
    surf.blit(kph_s, (ox + 185 - kph_s.get_width() // 2, 47))

    surf.blit(font_sm.render(f"J{pid + 1}", True, p_col), (ox + 4, 3))
    d_s = font_sm.render(f"{int(car.position)}m", True, (115, 75, 145))
    surf.blit(d_s, (ox + 4, 15))
    t_s = font_sm.render(f"{car.race_time:.2f}s", True, (165, 125, 188))
    surf.blit(t_s, (ox + _H_W - t_s.get_width() - 4, 3))


def _cockpit_street(surf, ox, car, pid, font_sm, font_md, p_col):
    """Demi-cercle (180°) en bas de la bande. Style JDM street moderne."""
    _hud_bg(surf, ox, (0, 4, 14, 208))

    cx, cy, r = ox + 120, _H_H - 8, 38
    r_in, r_out = r - 9, r

    def t_ang(v):
        return 180 - max(0.0, min(1.0, v / car.max_rpm)) * 180

    def pt(deg, radius):
        rad = math.radians(deg)
        return (int(cx + radius * math.cos(rad)), int(cy - radius * math.sin(rad)))

    def band(color, v0, v1, ra, rb, n=30):
        a0, a1 = t_ang(v0), t_ang(v1)
        for i in range(n):
            t1, t2 = i / n, (i + 1) / n
            d1 = a0 + (a1 - a0) * t1
            d2 = a0 + (a1 - a0) * t2
            pygame.draw.polygon(surf, color,
                                [pt(d1, ra), pt(d1, rb), pt(d2, rb), pt(d2, ra)])

    band((25, 25, 35), 0, car.max_rpm, r_in, r_out)
    red_s = car.opt_rpm + _SG
    band((138, 18, 18), red_s, car.max_rpm, r_in, r_out)
    band((158, 138, 0), car.opt_rpm - _SG, car.opt_rpm - _SP, r_in, r_out)
    band((158, 138, 0), car.opt_rpm + _SP, red_s, r_in, r_out)
    band((0, 158, 50), car.opt_rpm - _SP, car.opt_rpm + _SP, r_in, r_out)

    for k in range(0, int(car.max_rpm) + 1, int(car.max_rpm // 6)):
        pygame.draw.line(surf, (80, 80, 100), pt(t_ang(k), r_in - 1), pt(t_ang(k), r_out + 1), 1)

    ndeg = t_ang(car.rpm)
    pygame.draw.line(surf, (255, 255, 255), pt(ndeg, int(r * 0.18)), pt(ndeg, int(r * 0.86)), 2)
    pygame.draw.circle(surf, (255, 255, 255), pt(ndeg, int(r * 0.86)), 2)
    _draw_thin_arc(surf, p_col, cx, cy, r + 2, 180, 0, 1)

    spd_s = font_md.render(str(int(car.speed)), True, (228, 238, 255))
    surf.blit(spd_s, (cx - spd_s.get_width() // 2, cy - r + 2))
    surf.blit(font_sm.render("km/h", True, (75, 98, 138)), (cx - 14, cy - r + 18))

    g_s = font_md.render(str(car.gear), True, p_col)
    surf.blit(g_s, (cx - 38 - g_s.get_width() // 2, cy - r + 6))

    surf.blit(font_sm.render(f"J{pid + 1}", True, p_col), (ox + 4, 3))
    t_s = font_sm.render(f"{car.race_time:.2f}s", True, (135, 158, 198))
    surf.blit(t_s, (ox + _H_W - t_s.get_width() - 4, 3))
    dist_s = font_sm.render(f"{int(car.position)}m", True, (75, 98, 138))
    surf.blit(dist_s, (ox + 4, 50))


def _cockpit_ghost(surf, ox, car, pid, font_sm, font_md, p_col):
    """Compte-tours grand arc (demi-lune) gauche + compteur vitesse cercle droit. Style White Ghost."""
    _hud_bg(surf, ox, (3, 4, 10, 218))

    # ── Compte-tours (grand arc, centre sous la bande HUD) ───────────────────
    tcx, tcy, tr = ox + 62, _H_H + 20, 68
    tbw = 10            # épaisseur de la couronne
    a_s, a_e = 172, 22  # angles départ/fin de l'arc
    a_sw = a_s - a_e    # sweep = 150°

    def tA(v):
        return a_s - max(0.0, min(1.0, v / car.max_rpm)) * a_sw

    def tP(deg, r_):
        rad = math.radians(deg)
        return (int(tcx + r_ * math.cos(rad)), int(tcy - r_ * math.sin(rad)))

    def tBand(col, v0, v1, n=36):
        a0, a1 = tA(v0), tA(v1)
        for i in range(n):
            d1 = a0 + (a1 - a0) * i / n
            d2 = a0 + (a1 - a0) * (i + 1) / n
            pygame.draw.polygon(surf, col,
                                [tP(d1, tr - tbw), tP(d1, tr),
                                 tP(d2, tr),        tP(d2, tr - tbw)])

    tBand((22, 22, 30), 0, car.max_rpm)
    red_s = car.opt_rpm + _SG
    tBand((148, 20, 20), red_s, car.max_rpm)
    tBand((158, 138, 0), car.opt_rpm - _SG, car.opt_rpm - _SP)
    tBand((158, 138, 0), car.opt_rpm + _SP, red_s)
    tBand((0, 168, 54),  car.opt_rpm - _SP, car.opt_rpm + _SP)

    for k in range(0, int(car.max_rpm) + 1, int(car.max_rpm // 7)):
        deg = tA(k)
        pygame.draw.line(surf, (80, 80, 105), tP(deg, tr - tbw - 1), tP(deg, tr + 1), 1)

    ndeg = tA(car.rpm)
    pygame.draw.line(surf, (255, 255, 255), tP(ndeg, int(tr * 0.25)), tP(ndeg, int(tr * 0.90)), 2)
    pygame.draw.circle(surf, (255, 255, 255), tP(ndeg, int(tr * 0.90)), 2)
    _draw_thin_arc(surf, p_col, tcx, tcy, tr + 2, a_s, a_e, 1)

    rpm_s = font_sm.render(f"{car.rpm / 1000:.1f}k", True, (135, 135, 168))
    surf.blit(rpm_s, (ox + 5, 50))

    # ── Compteur de vitesse (cercle à droite) ─────────────────────────────────
    scx, scy, sr = ox + 183, 31, 26
    sbw = 6
    ss, ssw = 225, 210  # arc start, sweep

    def sA(v):
        return ss - max(0.0, min(1.0, v / 220.0)) * ssw

    def sP(deg, r_):
        rad = math.radians(deg)
        return (int(scx + r_ * math.cos(rad)), int(scy - r_ * math.sin(rad)))

    def sBand(col, v0, v1, n=28):
        a0, a1 = sA(v0), sA(v1)
        for i in range(n):
            d1 = a0 + (a1 - a0) * i / n
            d2 = a0 + (a1 - a0) * (i + 1) / n
            pygame.draw.polygon(surf, col,
                                [sP(d1, sr - sbw), sP(d1, sr),
                                 sP(d2, sr),        sP(d2, sr - sbw)])

    sBand((22, 22, 30), 0, 220)
    pygame.draw.circle(surf, (14, 14, 22), (scx, scy), sr - sbw - 1)

    for k in range(0, 241, 40):
        deg = sA(k)
        pygame.draw.line(surf, (72, 72, 95), sP(deg, sr - sbw - 1), sP(deg, sr + 1), 1)

    sdeg = sA(car.speed)
    pygame.draw.line(surf, (228, 232, 255), sP(sdeg, int(sr * 0.22)), sP(sdeg, int(sr * 0.88)), 2)
    pygame.draw.circle(surf, (228, 232, 255), sP(sdeg, int(sr * 0.88)), 2)
    pygame.draw.circle(surf, (185, 190, 215), (scx, scy), 3)
    _draw_thin_arc(surf, p_col, scx, scy, sr + 1, ss, ss - ssw, 1)

    spd_s = font_md.render(str(int(car.speed)), True, (215, 228, 255))
    surf.blit(spd_s, (scx - spd_s.get_width() // 2, scy - spd_s.get_height() // 2 + 1))
    kph_s = font_sm.render("km/h", True, (70, 80, 118))
    surf.blit(kph_s, (scx - kph_s.get_width() // 2, scy + 9))

    # ── Rapport de boîte + infos ──────────────────────────────────────────────
    g_s = font_md.render(str(car.gear), True, p_col)
    surf.blit(g_s, (ox + 138 - g_s.get_width() // 2, 20))
    surf.blit(font_sm.render("GEAR", True, (55, 55, 82)), (ox + 125, 37))

    surf.blit(font_sm.render(f"J{pid + 1}", True, p_col), (ox + 4, 3))
    t_s = font_sm.render(f"{car.race_time:.2f}s", True, (158, 162, 198))
    d_s = font_sm.render(f"{int(car.position)}m",  True, (98, 102, 138))
    surf.blit(t_s, (ox + _H_W - t_s.get_width() - 4, 3))
    surf.blit(d_s, (ox + _H_W - d_s.get_width() - 4, 15))


_COCKPIT_FUNCS = {
    "sport":   _cockpit_sport,
    "rally":   _cockpit_rally,
    "digital": _cockpit_digital,
    "retro":   _cockpit_retro,
    "race":    _cockpit_race,
    "street":  _cockpit_street,
    "ghost":   _cockpit_ghost,
}


def draw_cockpit(surf: pygame.Surface, ox: int, car, player_id: int,
                 font_sm, font_md, player_color):
    """Dessine la bande HUD complète selon le style de cockpit de la voiture."""
    hud_type = car.data.get("hud", "sport")
    _COCKPIT_FUNCS.get(hud_type, _cockpit_sport)(
        surf, ox, car, player_id, font_sm, font_md, player_color
    )


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
