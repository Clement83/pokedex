"""
Écran de sélection des voitures (split 2 joueurs).
Retourne (idx_car_j1, idx_car_j2) ou None si on quitte.
"""
import pygame
import math
import types
from config import CARS, PLAYER_COLORS, CTRL, SCREEN_WIDTH, SCREEN_HEIGHT, AXIS_DEAD
from ui import load_car_sprite, draw_car_sprite, draw_cockpit

# ── Palettes UI ───────────────────────────────────────────────────────────────
BG_TOP    = (8,   8,  20)
BG_BOT    = (16, 16, 38)
PANEL_BG  = (14, 14, 32)
SEP_COL   = (60, 60, 100)
TEXT_W    = (230, 230, 255)
TEXT_DIM  = (110, 110, 150)
READY_COL = (40,  220, 80)

# ── Catégories de véhicules ───────────────────────────────────────────────────
TIERS = [
    {"name": "STREET LEVEL",    "tag": "Tuners & Rookies",   "col": (60, 200, 80)},
    {"name": "QUARTER MILE",    "tag": "Import Legends",     "col": (255, 160, 20)},
    {"name": "BUILT NOT BOUGHT","tag": "No Mercy Builds",    "col": (220, 40,  40)},
]
CARS_PER_TIER = 6   # chaque sheet a exactement 6 voitures


# ── Détection d'événements (just-pressed) ─────────────────────────────────────

class ActionDetector:
    """Traduit les événements pygame en actions logiques pour un joueur."""

    def __init__(self):
        self._axis_moved = {0: False, 1: False}

    def check(self, events, action_key: str) -> bool:
        spec = CTRL[action_key]
        keys_just = {e.key for e in events if e.type == pygame.KEYDOWN}
        hats_just = {(e.value[0], e.value[1]) for e in events if e.type == pygame.JOYHATMOTION}
        btns_just = {e.button for e in events if e.type == pygame.JOYBUTTONDOWN}

        for k in spec.get('keys', []):
            if k in keys_just:
                return True

        hat = spec.get('hat')
        if hat and hat in hats_just:
            return True

        btn = spec.get('btn')
        if btn is not None and btn in btns_just:
            return True

        return False

    def check_axis(self, events, action_key: str) -> bool:
        """Détection just-moved pour un axe joystick (avec deadzone)."""
        spec = CTRL.get(action_key, {})
        ax_spec = spec.get('axis')
        if ax_spec is None:
            return False
        ax_id, direction = ax_spec
        for e in events:
            if e.type == pygame.JOYAXISMOTION and e.axis == ax_id:
                val = e.value
                if direction == -1 and val < -AXIS_DEAD:
                    return True
                if direction == 1 and val > AXIS_DEAD:
                    return True
        return False


# ── Dessin d'un volet joueur ───────────────────────────────────────────────────

def draw_panel(
    surf: pygame.Surface,
    px: int, pw: int,
    car_idx: int,
    player_id: int,
    is_ready: bool,
    font_sm, font_md, font_lg,
    anim_t: float,
):
    PH        = SCREEN_HEIGHT
    car_data  = CARS[car_idx]
    p_col     = PLAYER_COLORS[player_id]
    tier_idx  = car_idx // CARS_PER_TIER
    tier      = TIERS[tier_idx]
    t_col     = tier["col"]
    car_in_tier = car_idx % CARS_PER_TIER

    # Fond dégradé léger
    panel_surf = pygame.Surface((pw, PH), pygame.SRCALPHA)
    for y in range(PH):
        t   = y / PH
        col = (
            int(PANEL_BG[0] + t * 6),
            int(PANEL_BG[1] + t * 6),
            int(PANEL_BG[2] + t * 10),
            255,
        )
        pygame.draw.line(panel_surf, col, (0, y), (pw, y))

    # Bordure colorée du côté joueur
    border_w = 3
    if player_id == 0:
        pygame.draw.rect(panel_surf, p_col, (0, 0, border_w, PH))
    else:
        pygame.draw.rect(panel_surf, p_col, (pw - border_w, 0, border_w, PH))

    # ── Header ───────────────────────────────────────────────────────────────
    header = font_md.render(f"JOUEUR {player_id + 1}", True, p_col)
    panel_surf.blit(header, (pw // 2 - header.get_width() // 2, 8))

    # ── Prévisualisation cockpit ──────────────────────────────────────────────
    s = car_data["stats"]
    preview_car = types.SimpleNamespace(
        rpm=s["optRPM"] * (0.5 + 0.3 * math.sin(anim_t * 1.2)),
        speed=80.0 + 50.0 * abs(math.sin(anim_t * 0.7)),
        gear=3,
        position=0.0,
        race_time=0.0,
        max_rpm=s["maxRPM"],
        opt_rpm=s["optRPM"],
        data=car_data,
    )
    cockpit_preview = pygame.Surface((pw, 66), pygame.SRCALPHA)
    draw_cockpit(cockpit_preview, 0, preview_car, player_id, font_sm, font_md, p_col)
    panel_surf.blit(cockpit_preview, (0, 26))

    # ── Voiture (dessin au centre) ────────────────────────────────────────────
    car_cx = pw // 2
    car_cy = 130
    bob = int(math.sin(anim_t * 2.5) * 2)
    sprite = load_car_sprite(car_data["sprite"], 170)
    draw_car_sprite(panel_surf, car_cx, car_cy + bob, sprite)

    # Reflet sol (ombre sous la voiture)
    ref_col = car_data["col"]
    sprite_bottom = car_cy + bob + sprite.get_height() // 2
    for i in range(6):
        alpha = 70 - i * 12
        ref_surf = pygame.Surface((sprite.get_width() - 20, 3), pygame.SRCALPHA)
        ref_surf.fill((*ref_col, alpha))
        panel_surf.blit(ref_surf, (car_cx - ref_surf.get_width() // 2, sprite_bottom + i * 3))

    # ── Infos voiture ─────────────────────────────────────────────────────────
    name_surf = font_md.render(car_data["name"], True, TEXT_W)
    panel_surf.blit(name_surf, (pw // 2 - name_surf.get_width() // 2, 168))

    cat_surf = font_sm.render(car_data["cat"], True, p_col)
    panel_surf.blit(cat_surf, (pw // 2 - cat_surf.get_width() // 2, 184))

    desc_surf = font_sm.render(car_data["desc"], True, TEXT_DIM)
    panel_surf.blit(desc_surf, (pw // 2 - desc_surf.get_width() // 2, 196))

    # ── Stats compactes ───────────────────────────────────────────────────────
    s = car_data["stats"]
    lines = [
        (f"{s['power']} ch",   "PUISSANCE"),
        (f"{s['gears']} v.",   "VITESSES"),
        (f"{s['maxRPM']//1000:.0f}k RPM", "MAX"),
    ]
    col_x = [14, pw // 2 - 22, pw - 74]
    for i, (val, lbl) in enumerate(lines):
        vx = col_x[i]
        v_surf = font_sm.render(val, True, TEXT_W)
        l_surf = font_sm.render(lbl, True, TEXT_DIM)
        panel_surf.blit(v_surf, (vx, 214))
        panel_surf.blit(l_surf, (vx, 226))

    # ── Flèches navigation ────────────────────────────────────────────────────
    if player_id == 0:
        hints = "← → voiture   ↑ Prêt"
    else:
        hints = "Y X voiture   A Prêt"
    h_surf = font_sm.render(hints, True, TEXT_DIM)
    panel_surf.blit(h_surf, (pw // 2 - h_surf.get_width() // 2, 240))

    # ── Bannière tier ─────────────────────────────────────────────────────────
    tier_bg = pygame.Surface((pw, 20), pygame.SRCALPHA)
    tier_bg.fill((*t_col, 40))
    panel_surf.blit(tier_bg, (0, 254))
    pygame.draw.line(panel_surf, t_col, (0, 254), (pw, 254), 1)
    tier_name_surf = font_sm.render(tier["name"], True, t_col)
    panel_surf.blit(tier_name_surf, (pw // 2 - tier_name_surf.get_width() // 2, 257))

    # ── Indicateur PRÊT ou dots ────────────────────────────────────────────────
    if is_ready:
        ready_surf = font_lg.render("PRÊT!", True, READY_COL)
        rb = pygame.Rect(
            pw // 2 - ready_surf.get_width() // 2 - 8,
            279,
            ready_surf.get_width() + 16,
            ready_surf.get_height() + 6,
        )
        pygame.draw.rect(panel_surf, (10, 50, 20), rb, border_radius=6)
        pygame.draw.rect(panel_surf, READY_COL,    rb, 2, border_radius=6)
        panel_surf.blit(ready_surf, (rb.x + 8, rb.y + 3))
    else:
        # 6 dots pour la position dans le tier courant
        dot_r   = 4
        dot_gap = 10
        total_w = CARS_PER_TIER * (dot_r * 2) + (CARS_PER_TIER - 1) * dot_gap
        start_x = pw // 2 - total_w // 2
        for i in range(CARS_PER_TIER):
            col = p_col if i == car_in_tier else (55, 55, 80)
            pygame.draw.circle(panel_surf, col,
                               (start_x + i * (dot_r * 2 + dot_gap) + dot_r, 290), dot_r)

    surf.blit(panel_surf, (px, 0))


# ── Boucle principale ─────────────────────────────────────────────────────────

def run(screen: pygame.Surface, joysticks: list) -> tuple | None:
    """
    Retourne (car_idx_j1, car_idx_j2) quand les 2 joueurs sont prêts,
    ou None si on quitte.
    """
    clock  = pygame.time.Clock()
    PW     = SCREEN_WIDTH // 2    # largeur d'un volet (240px)

    font_sm = pygame.font.SysFont("Arial", 11, bold=True)
    font_md = pygame.font.SysFont("Arial", 14, bold=True)
    font_lg = pygame.font.SysFont("Arial", 18, bold=True)

    # préchargement des sprites dans le cache
    for car in CARS:
        load_car_sprite(car["sprite"], 170)
    car_sel = [0, 0]
    ready   = [False, False]
    det     = ActionDetector()
    anim_t  = 0.0

    running = True
    while running:
        dt     = clock.tick(60) / 1000.0
        anim_t += dt
        events = pygame.event.get()

        for e in events:
            if e.type == pygame.QUIT:
                return None
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return None

        if not ready[0]:
            if det.check(events, 'sel_prev_j1') or det.check_axis(events, 'sel_prev_j1'):
                car_sel[0] = (car_sel[0] - 1) % len(CARS)
            if det.check(events, 'sel_next_j1') or det.check_axis(events, 'sel_next_j1'):
                car_sel[0] = (car_sel[0] + 1) % len(CARS)
            if det.check(events, 'sel_conf_j1') or det.check_axis(events, 'sel_conf_j1'):
                ready[0] = True
        else:
            if det.check(events, 'sel_prev_j1') or det.check(events, 'sel_next_j1'):
                ready[0] = False

        if not ready[1]:
            if det.check(events, 'sel_prev_j2'):
                car_sel[1] = (car_sel[1] - 1) % len(CARS)
            if det.check(events, 'sel_next_j2'):
                car_sel[1] = (car_sel[1] + 1) % len(CARS)
            if det.check(events, 'sel_conf_j2'):
                ready[1] = True
        else:
            if det.check(events, 'sel_prev_j2') or det.check(events, 'sel_next_j2'):
                ready[1] = False

        # Les 2 prêts → on lance !
        if ready[0] and ready[1]:
            return (car_sel[0], car_sel[1])

        # ── Rendu ─────────────────────────────────────────────────────────────
        for y in range(SCREEN_HEIGHT):
            t   = y / SCREEN_HEIGHT
            col = tuple(int(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * t) for i in range(3))
            pygame.draw.line(screen, col, (0, y), (SCREEN_WIDTH, y))

        draw_panel(screen, 0,  PW, car_sel[0], 0, ready[0], font_sm, font_md, font_lg, anim_t)
        draw_panel(screen, PW, PW, car_sel[1], 1, ready[1], font_sm, font_md, font_lg, anim_t)

        # Séparateur central
        pygame.draw.line(screen, SEP_COL, (PW, 0), (PW, SCREEN_HEIGHT), 2)

        pygame.display.flip()
