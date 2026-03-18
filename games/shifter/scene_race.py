"""
Scène de course – split-screen 2 joueurs côte à côte.
Retourne la liste de résultats triés ou None si on quitte.
"""
import pygame
import math
from config import (
    CARS, PLAYER_COLORS, CTRL, AXIS_DEAD,
    SCREEN_WIDTH, SCREEN_HEIGHT, RACE_DISTANCE,
    OVERHEAT_TIME, OVERHEAT_WARN_TIME,
)
from car import Car
from ui import TrackBackground, StartLights, draw_car_sprite, load_car_sprite, draw_cockpit, draw_smoke

# ── Constantes de mise en page ────────────────────────────────────────────────
PW = SCREEN_WIDTH // 2   # largeur d'un volet : 240px
PH = SCREEN_HEIGHT        # hauteur : 320px
HUD_H            = 62    # hauteur de la bande HUD en haut
TACHO_R          = 30    # rayon du compte-tours
HUD_TACHO_CY     = 33    # centre Y du tacho dans le HUD
CAR_BASE_X       = PW // 3   # X fixe de la voiture joueur dans son panel
VISUAL_PX_PER_M  = 4    # pixels de décalage X par mètre d'écart entre les autos

BG_RACE = (10, 10, 25)


# ── Détecteur d'événements (réutilisé depuis scene_select) ───────────────────

def _just_pressed(events, action_key: str) -> bool:
    spec = CTRL[action_key]
    keys = {e.key for e in events if e.type == pygame.KEYDOWN}
    btns = {e.button for e in events if e.type == pygame.JOYBUTTONDOWN}
    hats = {(e.value[0], e.value[1]) for e in events if e.type == pygame.JOYHATMOTION}

    for k in spec.get('keys', []):
        if k in keys:
            return True
    btn = spec.get('btn')
    if btn is not None and btn in btns:
        return True
    hat = spec.get('hat')
    if hat and hat in hats:
        return True
    return False


def _axis_just(events, action_key: str) -> bool:
    spec = CTRL.get(action_key, {})
    ax_spec = spec.get('axis')
    if ax_spec is None:
        return False
    ax_id, direction = ax_spec
    for e in events:
        if e.type == pygame.JOYAXISMOTION and e.axis == ax_id:
            if direction == -1 and e.value < -AXIS_DEAD:
                return True
            if direction == 1 and e.value > AXIS_DEAD:
                return True
    return False


# ── Dessin d'un volet ─────────────────────────────────────────────────────────

def _draw_panel(
    surf: pygame.Surface,
    ox: int,              # décalage X du volet
    car: Car,
    track: TrackBackground,
    player_id: int,
    font_sm, font_md,
    shift_flash: dict,    # {'text': str, 'timer': float, 'color': tuple}
    finish_order: list,   # liste des player_id ayant fini, ordre d'arrivée
    opponent_car: Car,
):
    p_col   = PLAYER_COLORS[player_id]
    opp_col = PLAYER_COLORS[1 - player_id]

    # ── Clip strict au panel (évite le débordement du fond dans l'autre volet) ─
    surf.set_clip(pygame.Rect(ox, 0, PW, PH))

    # ── Décor / route ─────────────────────────────────────────────────────────
    track.draw(surf, ox, 0)

    # ── Positions des voitures ───────────────────────────────────────────────
    # Le joueur est fixé dans le panel ; l'adversaire se déplace selon l'écart.
    car_y = track.car_y
    delta_m   = opponent_car.position - car.position

    player_x  = ox + CAR_BASE_X
    player_cy = car_y + 28                            # voie droite (plus proche, plus bas)
    player_sprite = load_car_sprite(car.data["sprite"], 140)
    player_blit_y = player_cy - player_sprite.get_height() // 2

    opp_x     = ox + CAR_BASE_X + int(delta_m * VISUAL_PX_PER_M)
    opp_cy    = car_y                                 # voie gauche (plus loin)
    opp_sprite = load_car_sprite(opponent_car.data["sprite"], 140)
    opp_blit_y = opp_cy - opp_sprite.get_height() // 2

    # Ordre de rendu : adversaire toujours en arrière-plan, joueur toujours au premier plan
    if ox - opp_sprite.get_width() < opp_x < ox + PW + opp_sprite.get_width():
        pygame.draw.rect(surf, opp_col,
                         (opp_x - 8, opp_blit_y - opp_sprite.get_height() // 2 - 10, 16, 5),
                         border_radius=2)
        draw_car_sprite(surf, opp_x, opp_blit_y, opp_sprite)
    draw_car_sprite(surf, player_x, player_blit_y, player_sprite)

    # ── Cockpit HUD (style propre à la voiture) ────────────────────────────────
    draw_cockpit(surf, ox, car, player_id, font_sm, font_md, p_col)

    # ── Barre de progression (bas du HUD) ─────────────────────────────────────
    prog_y   = HUD_H - 8
    prog_h   = 5
    prog_pct = min(1.0, car.position / RACE_DISTANCE)
    pygame.draw.rect(surf, (35, 35, 55), (ox, prog_y, PW, prog_h))
    pygame.draw.rect(surf, p_col,        (ox, prog_y, int(PW * prog_pct), prog_h))

    # Indicateur de position adverse sur la barre
    opp_pct   = min(1.0, opponent_car.position / RACE_DISTANCE)
    opp_bar_x = ox + int(PW * opp_pct)
    pygame.draw.circle(surf, opp_col, (opp_bar_x, prog_y + 2), 4)
    pygame.draw.circle(surf, (255, 255, 255), (opp_bar_x, prog_y + 2), 4, 1)

    # ── Flash qualité de shift ────────────────────────────────────────────────
    if shift_flash['timer'] > 0:
        alpha = min(255, int(shift_flash['timer'] * 600))
        fsurf = font_md.render(shift_flash['text'], True, shift_flash['color'])
        fsurf.set_alpha(alpha)
        surf.blit(fsurf, (ox + PW // 2 - fsurf.get_width() // 2, HUD_H + 8))
    # ── Fumée moteur ──────────────────────────────────────────────
    if car.smoke_intensity > 0.05:
        draw_smoke(surf, player_x, player_blit_y, car.smoke_intensity)

    # ── Alerte surchauffe ───────────────────────────────────────
    overheat_warn = (not car.is_overheating
                     and car.overheat_timer >= OVERHEAT_TIME - OVERHEAT_WARN_TIME)
    if car.is_overheating or overheat_warn:
        if car.is_overheating:
            warn_text  = "SURCHAUFFE!"
            warn_color = (255, 80, 0)
        else:
            warn_text  = "TEMP. CRITIQUE"
            warn_color = (255, 200, 0)
        warn_surf = font_md.render(warn_text, True, warn_color)
        warn_y    = HUD_H + (28 if shift_flash['timer'] > 0 else 8)
        surf.blit(warn_surf, (ox + PW // 2 - warn_surf.get_width() // 2, warn_y))
    # ── Arrivée ───────────────────────────────────────────────────────────────
    if car.has_finished:
        pos = finish_order.index(player_id) + 1 if player_id in finish_order else '?'
        pos_labels = {1: ("1er", (255, 215, 0)), 2: ("2e", (200, 200, 200))}
        lbl, lcol  = pos_labels.get(pos, (str(pos), (200, 200, 200)))
        win_surf   = font_md.render(f"ARRIVÉ! {lbl}", True, lcol)
        wb = pygame.Rect(
            ox + PW // 2 - win_surf.get_width() // 2 - 6,
            HUD_H + 20, win_surf.get_width() + 12, win_surf.get_height() + 6,
        )
        pygame.draw.rect(surf, (0, 0, 0), wb, border_radius=5)
        pygame.draw.rect(surf, lcol,      wb, 2, border_radius=5)
        surf.blit(win_surf, (wb.x + 6, wb.y + 3))

    # ── Hint contrôles (bas gauche) ───────────────────────────────────────────
    hint  = "↑↓ Rapports" if player_id == 0 else "A/B Rapports"
    h_srf = font_sm.render(hint, True, (60, 60, 90))
    surf.blit(h_srf, (ox + 4, PH - 13))

    # ── Restaurer le clip ─────────────────────────────────────────────────────
    surf.set_clip(None)


# ── Boucle principale ─────────────────────────────────────────────────────────

def run(screen: pygame.Surface, joysticks: list, car_indices: tuple, environment: str = "tokio1") -> list | None:
    """
    Retourne le classement [{'player_id', 'car', 'time', 'rank'}]
    ou None si on quitte.
    """
    clock = pygame.time.Clock()

    # ── Polices ───────────────────────────────────────────────────────────────
    font_sm = pygame.font.SysFont("Arial", 11, bold=True)
    font_md = pygame.font.SysFont("Arial", 14, bold=True)

    # ── Voitures ──────────────────────────────────────────────────────────────
    cars = [Car(CARS[idx]) for idx in car_indices]
    # ── Sprites véhicules (préchargement dans le cache) ─────────────────────────
    for c in cars:
        load_car_sprite(c.data["sprite"], 140)
    # ── Décors ────────────────────────────────────────────────────────────────
    tracks = [TrackBackground(PW, PH, environment) for _ in range(2)]

    # ── Feux de départ ────────────────────────────────────────────────────────
    lights = StartLights(SCREEN_WIDTH, SCREEN_HEIGHT)
    lights.start()

    # ── État ──────────────────────────────────────────────────────────────────
    race_started  = False
    finish_order  = []          # player_id dans l'ordre d'arrivée
    post_timer    = 0.0         # temps d'attente après que les 2 ont fini
    POST_WAIT     = 3.0

    shift_flash = [
        {'text': '', 'timer': 0.0, 'color': (255, 255, 255)},
        {'text': '', 'timer': 0.0, 'color': (255, 255, 255)},
    ]
    FLASH_COLORS = {
        'PERFECT': (40, 240, 80),
        'GOOD':    (240, 200, 0),
        'BAD':     (240, 60,  60),
    }

    # ── Boucle ────────────────────────────────────────────────────────────────
    running = True
    while running:
        dt     = min(clock.tick(60) / 1000.0, 0.05)
        events = pygame.event.get()

        for e in events:
            if e.type == pygame.QUIT:
                return None
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return None

        # ── Feux ──────────────────────────────────────────────────────────────
        lights.update(dt)
        if lights.race_started and not race_started:
            race_started = True
            for c in cars:
                c.start()

        # ── Inputs ────────────────────────────────────────────────────────────
        if race_started:
            # Joueur 1
            if _just_pressed(events, 'race_up_j1') or _axis_just(events, 'race_up_j1'):
                old_q = cars[0].shift_quality
                cars[0].shift_up()
                nq = cars[0].shift_quality
                if nq and nq != old_q:
                    shift_flash[0] = {'text': nq, 'timer': 0.6, 'color': FLASH_COLORS[nq]}

            if _just_pressed(events, 'race_down_j1') or _axis_just(events, 'race_down_j1'):
                cars[0].shift_down()

            # Joueur 2
            if _just_pressed(events, 'race_up_j2'):
                old_q = cars[1].shift_quality
                cars[1].shift_up()
                nq = cars[1].shift_quality
                if nq and nq != old_q:
                    shift_flash[1] = {'text': nq, 'timer': 0.6, 'color': FLASH_COLORS[nq]}

            if _just_pressed(events, 'race_down_j2'):
                cars[1].shift_down()

        # ── Physique ──────────────────────────────────────────────────────────
        for i, c in enumerate(cars):
            c.update(dt)
            tracks[i].update(c.position)
            if shift_flash[i]['timer'] > 0:
                shift_flash[i]['timer'] -= dt
            if c.has_finished and (i not in finish_order):
                finish_order.append(i)

        # Temps d'attente post-arrivée
        if len(finish_order) == 2:
            post_timer += dt
            if post_timer >= POST_WAIT:
                running = False

        # ── Rendu ─────────────────────────────────────────────────────────────
        screen.fill(BG_RACE)

        for i in range(2):
            _draw_panel(
                screen, i * PW,
                cars[i], tracks[i],
                i, font_sm, font_md,
                shift_flash[i],
                finish_order,
                cars[1 - i],
            )

        # Séparateur central
        pygame.draw.line(screen, (50, 50, 80), (PW, 0), (PW, PH), 2)

        # Feux de départ (au-dessus de tout)
        lights.draw(screen)

        pygame.display.flip()

    # ── Construction du résultat ──────────────────────────────────────────────
    # Classer les joueurs : d'abord ceux qui ont fini (par ordre d'arrivée),
    # puis les autres par position décroissante.
    finished     = [(pid, cars[pid]) for pid in finish_order]
    not_finished = sorted(
        [(i, cars[i]) for i in range(2) if i not in finish_order],
        key=lambda x: x[1].position, reverse=True,
    )
    ordered = finished + not_finished

    results = []
    for rank, (pid, c) in enumerate(ordered, start=1):
        results.append({
            'player_id': pid,
            'car':       c,
            'rank':      rank,
        })
    return results
