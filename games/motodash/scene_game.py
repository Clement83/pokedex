import math
import random
import pygame

import config
from bike import Bike
from terrain import Terrain
from hazards import HazardManager
from particles import ParticleSystem
import scores
import levels


def _build_sky(width, height, biome):
    """Surface de ciel avec dégradé vertical, pré-calculée une fois."""
    sky = pygame.Surface((width, height))
    top = biome["sky_top"]
    bot = biome["sky_bottom"]
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(top[0] + (bot[0] - top[0]) * t)
        g = int(top[1] + (bot[1] - top[1]) * t)
        b = int(top[2] + (bot[2] - top[2]) * t)
        pygame.draw.line(sky, (r, g, b), (0, y), (width, y))
    # Soleil discret en haut à droite
    pygame.draw.circle(sky, biome["sun"], (width - 80, 50), 22)
    pygame.draw.circle(sky, biome["sun_inner"], (width - 80, 50), 16)
    return sky


def _build_clouds(width, height, biome):
    """Surface de nuages flottant dans le ciel, alpha."""
    surf = pygame.Surface((width * 2, height // 2), pygame.SRCALPHA)
    rng = random.Random(42)
    for _ in range(14):
        cx = rng.randint(0, width * 2)
        cy = rng.randint(15, height // 2 - 20)
        for i in range(4):
            ox = rng.randint(-18, 18)
            oy = rng.randint(-6, 6)
            r = rng.randint(10, 18)
            pygame.draw.circle(surf, biome["cloud"], (cx + ox, cy + oy), r)
    return surf


def _build_mountain_band(width, height, color, seed, peakiness=40):
    """Polygone de montagnes répété en boucle horizontale."""
    surf = pygame.Surface((width * 2, height), pygame.SRCALPHA)
    rng = random.Random(seed)
    pts = [(0, height)]
    x = 0
    while x < width * 2:
        x += rng.randint(40, 90)
        y = height - rng.randint(peakiness // 2, peakiness)
        pts.append((x, y))
    pts.append((width * 2, height))
    pygame.draw.polygon(surf, color, pts)
    return surf


class GameScene:
    def __init__(self, screen, level_id):
        self.screen = screen
        self.level = levels.get(level_id)
        self.biome_name = self.level.get("biome", "grass")
        self.biome = config.BIOMES.get(self.biome_name, config.BIOMES["grass"])
        self.biome_fx = config.BIOME_EFFECTS.get(self.biome_name, {"particles": [], "sky_pulse": False, "shake": 0.0})
        self.terrain = Terrain(
            self.level["terrain"],
            self.level["finish_x"],
            self.level["checkpoints"],
            biome=self.biome,
        )
        self.bike = Bike(self.level["start"])
        self.hazards = HazardManager(self.biome_name, self.level.get("hazards", []))
        self.particles = ParticleSystem(
            self.biome_name, screen.get_size(), self.biome_fx["particles"]
        )
        self._shake_phase = 0.0
        self.last_checkpoint = self.level["start"]
        self.passed_checkpoints = set()
        self.elapsed = 0.0
        self.finished = False
        self.crash_timer = 0.0
        # Décompte 3 → 2 → 1 → PARTEZ ! (puis course)
        self.countdown = 3.0
        self.go_hold = 0.0  # temps d'affichage de "PARTEZ !"
        self.cam_x = 0.0
        self.cam_y = 0.0
        self.wheel_spin = 0.0  # angle radians, suit la distance parcourue
        self._last_bike_x = self.bike.x
        sw, sh = screen.get_size()
        self._sky = _build_sky(sw, sh, self.biome)
        self._clouds = _build_clouds(sw, sh, self.biome)
        self._mountain_far = _build_mountain_band(sw, 90, self.biome["mountain_far"], seed=1, peakiness=55)
        self._mountain_mid = _build_mountain_band(sw, 70, self.biome["mountain_mid"], seed=2, peakiness=45)
        self._hill_near    = _build_mountain_band(sw, 55, self.biome["hill_near"], seed=3, peakiness=35)
        self.font = pygame.font.SysFont("Arial", 16, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 12)
        self.input_throttle = False
        self.input_brake = False
        self.input_lean = 0
        self.want_reset = False
        self.want_quit = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.input_throttle = True
            elif event.key == pygame.K_DOWN:
                self.input_brake = True
            elif event.key == pygame.K_LEFT:
                self.input_lean = -1
            elif event.key == pygame.K_RIGHT:
                self.input_lean = 1
            elif event.key == pygame.K_r:
                self.want_reset = True
            elif event.key == pygame.K_ESCAPE:
                self.want_quit = True
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_UP:
                self.input_throttle = False
            elif event.key == pygame.K_DOWN:
                self.input_brake = False
            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.input_lean = 0
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == config.BTN_THROTTLE:
                self.input_throttle = True
            elif event.button == config.BTN_BRAKE:
                self.input_brake = True
            elif event.button == config.BTN_RESET:
                self.want_reset = True
            elif event.button == config.BTN_LEFT:
                self.input_lean = -1
            elif event.button == config.BTN_RIGHT:
                self.input_lean = 1
        elif event.type == pygame.JOYBUTTONUP:
            if event.button == config.BTN_THROTTLE:
                self.input_throttle = False
            elif event.button == config.BTN_BRAKE:
                self.input_brake = False
            elif event.button in (config.BTN_LEFT, config.BTN_RIGHT):
                self.input_lean = 0
        elif event.type == pygame.JOYHATMOTION:
            x, _ = event.value
            if x < 0:
                self.input_lean = -1
            elif x > 0:
                self.input_lean = 1
            else:
                self.input_lean = 0
        elif event.type == pygame.JOYAXISMOTION and event.axis == 0:
            if event.value < -config.AXIS_DEAD:
                self.input_lean = -1
            elif event.value > config.AXIS_DEAD:
                self.input_lean = 1
            elif abs(event.value) < config.AXIS_DEAD * 0.5:
                self.input_lean = 0

    def update(self, dt):
        if self.want_quit:
            return {"quit": True}

        # Pendant le décompte : on bouge la caméra vers la moto mais pas la physique
        if self.countdown > 0:
            self.countdown -= dt
            target_x = self.bike.x - self.screen.get_width() / 2
            target_y = self.bike.y - self.screen.get_height() / 2
            self.cam_x += (target_x - self.cam_x) * min(1.0, 8.0 * dt)
            self.cam_y += (target_y - self.cam_y) * min(1.0, 8.0 * dt)
            self.particles.update(dt, self.cam_x, self.cam_y)
            self._shake_phase += dt
            return None
        if self.go_hold < 0.5:
            self.go_hold += dt

        if self.want_reset:
            self.want_reset = False
            self.bike.reset_to(self.last_checkpoint)

        if self.finished:
            return None

        if self.bike.crashed:
            self.crash_timer += dt
            if self.crash_timer >= 0.6:
                self.bike.reset_to(self.last_checkpoint)
                self.crash_timer = 0.0
        else:
            self.bike.set_inputs(self.input_throttle, self.input_brake, self.input_lean)
            self.bike.step(dt, self.terrain)
            self.hazards.update(self.bike, dt)

        self.elapsed += dt
        self._shake_phase += dt
        self.particles.update(dt, self.cam_x, self.cam_y, math.hypot(self.bike.vx, self.bike.vy))

        # Rotation visuelle des roues : proportionnelle à la distance parcourue
        dx = self.bike.x - self._last_bike_x
        self._last_bike_x = self.bike.x
        self.wheel_spin = (self.wheel_spin + dx / max(1.0, config.WHEEL_RADIUS)) % (2 * math.pi)

        for cp_x in self.terrain.checkpoints:
            if cp_x in self.passed_checkpoints:
                continue
            if self.bike.x >= cp_x:
                self.passed_checkpoints.add(cp_x)
                ground_y = self.terrain.height_at(cp_x) or self.bike.y
                self.last_checkpoint = (cp_x, ground_y - 30)

        if self.bike.x >= self.terrain.finish_x:
            self.finished = True
            medal = scores.medal_for_time(self.level, self.elapsed)
            return {
                "finished": True,
                "level_id": self.level["id"],
                "time": self.elapsed,
                "medal": medal,
            }

        target_x = self.bike.x + max(-80, min(80, self.bike.vx * 0.3)) - self.screen.get_width() / 2
        target_y = self.bike.y - self.screen.get_height() / 2
        self.cam_x += (target_x - self.cam_x) * min(1.0, 8.0 * dt)
        self.cam_y += (target_y - self.cam_y) * min(1.0, 8.0 * dt)

        return None

    def render(self):
        sw, sh = self.screen.get_size()
        # Screen shake : offset caméra (ambiant biome + hazard transitoire).
        # On swap cam_x/cam_y le temps du rendu pour que tous les renderers en bénéficient.
        shake_amp = self.biome_fx["shake"] * 1.5 + self.hazards.shake_intensity * 4.0
        real_cx, real_cy = self.cam_x, self.cam_y
        if shake_amp > 0.05:
            self.cam_x = real_cx + math.sin(self._shake_phase * 47.0) * shake_amp
            self.cam_y = real_cy + math.cos(self._shake_phase * 53.0) * shake_amp

        self._render_background()
        self.terrain.render(self.screen, self.cam_x, self.cam_y)
        self.hazards.render(self.screen, self.cam_x, self.cam_y, (0, 0, sw, sh))
        self._render_bike()
        self.particles.render(self.screen, self.cam_x, self.cam_y)

        # Sky pulse : voile rouge pulsé pour volcano
        if self.biome_fx["sky_pulse"]:
            pulse = 0.5 + 0.5 * math.sin(self._shake_phase * 1.6)
            alpha = int(20 + 35 * pulse)
            overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
            overlay.fill((180, 40, 20, alpha))
            self.screen.blit(overlay, (0, 0))

        self.cam_x, self.cam_y = real_cx, real_cy

        self._render_hud()
        if self.countdown > 0 or self.go_hold < 0.5:
            self._render_countdown()

    def _render_countdown(self):
        sw, sh = self.screen.get_size()
        if self.countdown > 0:
            n = int(math.ceil(self.countdown))
            label = str(n)
            color = (245, 220, 80) if n == 1 else (245, 245, 245)
            frac = self.countdown - (n - 1)  # 1 → 0 dans la seconde
            base_size = 96
        else:
            label = "PARTEZ !"
            color = (110, 235, 110)
            frac = 1.0 - (self.go_hold / 0.5)
            base_size = 56
        scale = 1.6 - frac * 0.6  # 1.6 → 1.0
        alpha = max(60, min(255, int(80 + 175 * frac)))
        size = max(8, int(base_size * scale))
        font = pygame.font.SysFont("Arial", size, bold=True)
        text = font.render(label, True, color)
        shadow = font.render(label, True, (20, 20, 30))
        text.set_alpha(alpha)
        shadow.set_alpha(alpha)
        cx = (sw - text.get_width()) // 2
        cy = (sh - text.get_height()) // 2
        self.screen.blit(shadow, (cx + 3, cy + 3))
        self.screen.blit(text, (cx, cy))

    # ── Background avec parallaxe ───────────────────────────────────────────
    def _render_background(self):
        sw, sh = self.screen.get_size()
        self.screen.blit(self._sky, (0, 0))

        # Nuages : parallaxe très lente
        cw = self._clouds.get_width()
        offset = int(self.cam_x * 0.05) % cw
        self.screen.blit(self._clouds, (-offset, 10))
        self.screen.blit(self._clouds, (cw - offset, 10))

        # Montagnes lointaines (parallaxe 0.15)
        mw = self._mountain_far.get_width()
        offset = int(self.cam_x * 0.15) % mw
        y = sh - 90 - 60
        self.screen.blit(self._mountain_far, (-offset, y))
        self.screen.blit(self._mountain_far, (mw - offset, y))

        # Montagnes mid (parallaxe 0.30)
        mw = self._mountain_mid.get_width()
        offset = int(self.cam_x * 0.30) % mw
        y = sh - 70 - 30
        self.screen.blit(self._mountain_mid, (-offset, y))
        self.screen.blit(self._mountain_mid, (mw - offset, y))

        # Collines proches (parallaxe 0.55)
        mw = self._hill_near.get_width()
        offset = int(self.cam_x * 0.55) % mw
        y = sh - 55 - 5
        self.screen.blit(self._hill_near, (-offset, y))
        self.screen.blit(self._hill_near, (mw - offset, y))

    # ── Moto + pilote ────────────────────────────────────────────────────────
    def _render_bike(self):
        cx = self.bike.x - self.cam_x
        cy = self.bike.y - self.cam_y
        a = self.bike.angle
        cos_a, sin_a = math.cos(a), math.sin(a)
        half = config.WHEELBASE / 2.0
        wheel_r = int(config.WHEEL_RADIUS)

        # Vecteurs locaux (rotés)
        def L(fx, fy):
            """forward, up dans le repère monde (up = perpendiculaire négative en pygame)."""
            wx = cx + cos_a * fx + sin_a * fy
            wy = cy + sin_a * fx - cos_a * fy
            return (wx, wy)

        rear  = L(-half, 0)
        front = L( half, 0)

        # Ombre au sol
        if self.bike.on_ground:
            shadow = pygame.Surface((int(config.WHEELBASE + 18), 7), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, 80), shadow.get_rect())
            sx = int((rear[0] + front[0]) / 2 - shadow.get_width() / 2)
            sy = int(max(rear[1], front[1]) + wheel_r - 1)
            self.screen.blit(shadow, (sx, sy))

        # Suspension : fourche avant (deux tubes parallèles)
        front_top = L(half, 14)
        fork_in   = L(half - 1, 14)
        pygame.draw.line(self.screen, config.BIKE_FORK, front, front_top, 2)
        pygame.draw.line(self.screen, config.BIKE_FRAME_DARK, L(half - 0.5, 4), fork_in, 1)

        # Bras oscillant arrière
        rear_top = L(-half + 4, 7)
        pygame.draw.line(self.screen, config.BIKE_FRAME_DARK, rear, rear_top, 3)

        # Bloc moteur (rectangle sombre central)
        engine_pts = [L(-3, 6), L(6, 6), L(7, 12), L(-2, 13)]
        pygame.draw.polygon(self.screen, (45, 45, 50), engine_pts)
        pygame.draw.polygon(self.screen, (75, 75, 82), engine_pts, 1)
        # Ailettes radiateur
        for k in range(4):
            ax = -2 + k * 2
            pygame.draw.line(self.screen, (90, 90, 95), L(ax, 8), L(ax, 12), 1)

        # Échappement (tuyau qui part du moteur vers l'arrière-haut)
        ex_a = L(-2, 9)
        ex_b = L(-9, 11)
        ex_c = L(-13, 13)
        pygame.draw.line(self.screen, (165, 165, 170), ex_a, ex_b, 3)
        pygame.draw.line(self.screen, (165, 165, 170), ex_b, ex_c, 3)
        pygame.draw.circle(self.screen, (40, 40, 45), (int(ex_c[0]), int(ex_c[1])), 2)

        # Châssis principal : tubes triangulés
        seat_front = L(-3, 14)
        seat_back  = L(-11, 14)
        tank_top   = L(2, 16)
        tank_front = L(7, 14)
        # Réservoir (polygone)
        tank_pts = [seat_front, tank_top, tank_front, L(6, 12), L(-1, 13)]
        pygame.draw.polygon(self.screen, config.BIKE_FRAME, tank_pts)
        pygame.draw.polygon(self.screen, config.BIKE_FRAME_DARK, tank_pts, 1)
        # Highlight sur le réservoir
        pygame.draw.line(self.screen, (235, 110, 100), L(0, 16), L(5, 15.5), 1)

        # Tube haut du cadre (du col de direction au seat)
        pygame.draw.line(self.screen, config.BIKE_FRAME_DARK, front_top, tank_top, 2)
        # Tube descendant (du col vers le moteur)
        pygame.draw.line(self.screen, config.BIKE_FRAME_DARK, L(half - 1, 13), L(5, 8), 2)
        # Tube siège vers bras oscillant
        pygame.draw.line(self.screen, config.BIKE_FRAME_DARK, seat_front, rear_top, 2)

        # Selle (rectangle plat noir)
        seat_pts = [seat_back, seat_front, L(-3, 15), L(-11, 15)]
        pygame.draw.polygon(self.screen, (30, 30, 35), seat_pts)
        # Garde-boue arrière
        fender_pts = [L(-12, 14), L(-15, 14), L(-16, 12), L(-13, 12)]
        pygame.draw.polygon(self.screen, config.BIKE_FRAME_DARK, fender_pts)

        # Plaque numéro avant + phare
        plate_pts = [L(half + 1, 13), L(half + 4, 14), L(half + 4, 17), L(half + 1, 16)]
        pygame.draw.polygon(self.screen, (240, 240, 240), plate_pts)
        pygame.draw.polygon(self.screen, (40, 40, 45), plate_pts, 1)
        # Garde-boue avant
        fb_pts = [L(half - 2, 5), L(half + 4, 7), L(half + 4, 9), L(half - 1, 7)]
        pygame.draw.polygon(self.screen, config.BIKE_FRAME, fb_pts)

        # Guidon
        bar_base = L(half - 0.5, 17)
        bar_grip = L(half + 3, 19)
        pygame.draw.line(self.screen, (40, 40, 45), L(half - 0.5, 14), bar_base, 2)
        pygame.draw.line(self.screen, (40, 40, 45), bar_base, bar_grip, 3)

        # Repose-pied
        peg_pts = [L(0, 4), L(2, 4), L(2, 5), L(0, 5)]
        pygame.draw.polygon(self.screen, (60, 60, 65), peg_pts)

        # Roues
        self._render_wheel(rear,  wheel_r, self.wheel_spin)
        self._render_wheel(front, wheel_r, self.wheel_spin)

        # Pilote
        self._render_rider(L)

    def _render_wheel(self, center, radius, spin):
        x, y = int(center[0]), int(center[1])
        # Pneu épais (cranté)
        pygame.draw.circle(self.screen, config.BIKE_TIRE, (x, y), radius + 1)
        # Crampons (petits points autour du pneu)
        for k in range(8):
            ang = spin * 0.5 + k * (math.pi / 4)
            tx = x + math.cos(ang) * (radius + 1)
            ty = y + math.sin(ang) * (radius + 1)
            pygame.draw.circle(self.screen, (15, 15, 18), (int(tx), int(ty)), 1)
        # Pneu intérieur
        pygame.draw.circle(self.screen, config.BIKE_TIRE, (x, y), radius - 1)
        # Jante (anneau)
        pygame.draw.circle(self.screen, config.BIKE_RIM, (x, y), radius - 2)
        pygame.draw.circle(self.screen, config.BIKE_TIRE, (x, y), radius - 3)
        # Moyeu
        pygame.draw.circle(self.screen, config.BIKE_HUB, (x, y), max(2, radius // 3))
        pygame.draw.circle(self.screen, (50, 50, 55), (x, y), max(1, radius // 5))
        # Rayons (5 rayons qui tournent avec la roue)
        for k in range(5):
            ang = spin + k * (2 * math.pi / 5)
            ex = x + math.cos(ang) * (radius - 3)
            ey = y + math.sin(ang) * (radius - 3)
            pygame.draw.line(self.screen, config.BIKE_RIM, (x, y), (ex, ey), 1)

    def _render_rider(self, L):
        # L(forward, up) → position monde
        # Posture motocross : assis sur selle, torse incliné, bras tendus vers le guidon, jambes pliées
        hip       = L(-4, 15)
        shoulder  = L( 1, 21)
        neck      = L( 3, 23)
        helmet_c  = L( 5, 26)
        elbow     = L( 5, 19)
        hand      = L(10, 19)   # sur le guidon
        knee      = L( 3, 11)
        foot      = L( 1, 5)    # sur le repose-pied

        # Jambes
        pygame.draw.line(self.screen, config.RIDER_SUIT, hip, knee, 5)
        pygame.draw.line(self.screen, config.RIDER_SUIT, knee, foot, 4)
        # Botte
        bx, by = int(foot[0]), int(foot[1])
        pygame.draw.circle(self.screen, (20, 20, 25), (bx, by), 3)
        pygame.draw.circle(self.screen, (20, 20, 25), (bx + 1, by), 2)

        # Torse (avec un peu d'épaisseur via 2 lignes parallèles)
        pygame.draw.line(self.screen, config.RIDER_SUIT, hip, shoulder, 7)
        # Numéro sur le dos (petit highlight)
        chest_mid = ((hip[0] + shoulder[0]) / 2, (hip[1] + shoulder[1]) / 2)
        pygame.draw.circle(self.screen, (235, 235, 240), (int(chest_mid[0]), int(chest_mid[1])), 2)

        # Bras (épaule → coude → main)
        pygame.draw.line(self.screen, config.RIDER_SUIT, shoulder, elbow, 4)
        pygame.draw.line(self.screen, config.RIDER_SUIT, elbow, hand, 3)
        # Gant
        pygame.draw.circle(self.screen, config.RIDER_GLOVE, (int(hand[0]), int(hand[1])), 3)

        # Cou
        pygame.draw.line(self.screen, (60, 60, 70), shoulder, neck, 3)

        # Casque (forme ovale orientée)
        hx, hy = int(helmet_c[0]), int(helmet_c[1])
        a = self.bike.angle
        cos_a, sin_a = math.cos(a), math.sin(a)
        # Casque dessiné comme polygone aplati orienté avec la moto
        # Demi-axes : 5 (forward), 4 (up)
        helmet_pts = []
        for k in range(10):
            t = k / 10 * 2 * math.pi
            lx = math.cos(t) * 5
            ly = math.sin(t) * 4 + 0.5  # légèrement décalé vers le haut
            wx = hx + cos_a * lx + sin_a * ly
            wy = hy + sin_a * lx - cos_a * ly
            helmet_pts.append((wx, wy))
        pygame.draw.polygon(self.screen, config.RIDER_HELMET, helmet_pts)
        pygame.draw.polygon(self.screen, (20, 22, 30), helmet_pts, 1)

        # Visière : rectangle vers l'avant du casque
        v_fwd = 4.5
        v_h = 1.8
        v_off_fwd = 1.5  # devant le centre du casque
        cx_v = hx + cos_a * v_off_fwd
        cy_v = hy + sin_a * v_off_fwd
        v1x, v1y = cos_a * v_fwd / 2, sin_a * v_fwd / 2
        v2x, v2y = sin_a * v_h, -cos_a * v_h
        visor_pts = [
            (cx_v + v1x - v2x, cy_v + v1y - v2y),
            (cx_v + v1x + v2x * 0.5, cy_v + v1y + v2y * 0.5),
            (cx_v - v1x + v2x * 0.5, cy_v - v1y + v2y * 0.5),
            (cx_v - v1x - v2x, cy_v - v1y - v2y),
        ]
        pygame.draw.polygon(self.screen, config.RIDER_VISOR, visor_pts)
        # Reflet sur visière
        ref_pts = [
            (cx_v + v1x * 0.6 - v2x * 0.7, cy_v + v1y * 0.6 - v2y * 0.7),
            (cx_v + v1x * 0.9 - v2x * 0.4, cy_v + v1y * 0.9 - v2y * 0.4),
            (cx_v - v1x * 0.2 + v2x * 0.1, cy_v - v1y * 0.2 + v2y * 0.1),
            (cx_v - v1x * 0.5 - v2x * 0.4, cy_v - v1y * 0.5 - v2y * 0.4),
        ]
        pygame.draw.polygon(self.screen, (180, 220, 240), ref_pts)

    # ── HUD ──────────────────────────────────────────────────────────────────
    def _render_hud(self):
        sw, sh = self.screen.get_size()

        # Cadre chrono en haut à gauche
        mins = int(self.elapsed // 60)
        secs = self.elapsed - mins * 60
        time_str = f"{mins:02d}:{secs:05.2f}"
        surf = self.font.render(time_str, True, config.TEXT_COLOR)
        bg = pygame.Surface((surf.get_width() + 18, surf.get_height() + 10), pygame.SRCALPHA)
        bg.fill(config.HUD_BG)
        pygame.draw.rect(bg, (245, 220, 80), bg.get_rect(), 1, border_radius=4)
        self.screen.blit(bg, (8, 8))
        self.screen.blit(surf, (17, 13))

        # Médaille en cours (couleur du marqueur courant : or > argent > bronze > rien)
        if self.elapsed <= self.level["gold"]:
            cur_color = config.MEDAL_COLORS[config.MEDAL_GOLD]
        elif self.elapsed <= self.level["silver"]:
            cur_color = config.MEDAL_COLORS[config.MEDAL_SILVER]
        elif self.elapsed <= self.level["bronze"]:
            cur_color = config.MEDAL_COLORS[config.MEDAL_BRONZE]
        else:
            cur_color = (110, 110, 110)
        pygame.draw.circle(self.screen, cur_color, (bg.get_width() + 22, 8 + bg.get_height() // 2), 6)

        # Barre de progression sur la longueur du parcours, en haut centrée
        start_x = self.level["start"][0]
        end_x = self.level["finish_x"]
        progress = (self.bike.x - start_x) / max(1.0, end_x - start_x)
        progress = max(0.0, min(1.0, progress))
        bar_w, bar_h = 220, 8
        bar_x = (sw - bar_w) // 2
        bar_y = 14
        bar_bg = pygame.Surface((bar_w + 4, bar_h + 4), pygame.SRCALPHA)
        bar_bg.fill((0, 0, 0, 110))
        self.screen.blit(bar_bg, (bar_x - 2, bar_y - 2))
        pygame.draw.rect(self.screen, (60, 60, 70), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(self.screen, (245, 220, 80), (bar_x, bar_y, int(bar_w * progress), bar_h))
        # Marqueurs checkpoint sur la barre
        for cp_x in self.level["checkpoints"]:
            t = (cp_x - start_x) / max(1.0, end_x - start_x)
            mx = bar_x + int(bar_w * t)
            color = (200, 200, 200) if cp_x in self.passed_checkpoints else (140, 140, 140)
            pygame.draw.line(self.screen, color, (mx, bar_y - 2), (mx, bar_y + bar_h + 2), 1)
        # Drapeau d'arrivée
        pygame.draw.polygon(
            self.screen, (220, 60, 60),
            [(bar_x + bar_w + 2, bar_y - 1),
             (bar_x + bar_w + 8, bar_y + bar_h // 2),
             (bar_x + bar_w + 2, bar_y + bar_h + 1)],
        )

        # Vitesse (km/h fictifs)
        speed = math.hypot(self.bike.vx, self.bike.vy) * 0.12
        speed_surf = self.font_small.render(f"{int(speed)} km/h", True, config.TEXT_COLOR)
        speed_bg = pygame.Surface((speed_surf.get_width() + 12, speed_surf.get_height() + 6), pygame.SRCALPHA)
        speed_bg.fill(config.HUD_BG)
        self.screen.blit(speed_bg, (sw - speed_bg.get_width() - 8, 8))
        self.screen.blit(speed_surf, (sw - speed_surf.get_width() - 14, 11))

        # Crash overlay
        if self.bike.crashed:
            overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
            overlay.fill((180, 20, 20, 60))
            self.screen.blit(overlay, (0, 0))
            msg = self.font.render("CRASH !", True, (255, 230, 230))
            self.screen.blit(msg, ((sw - msg.get_width()) // 2, sh // 2 - 10))

        # Hint discret en bas
        hint = self.font_small.render(
            "↑ accel · ↓ frein · ←→ pencher · R reset · Échap menu",
            True, (235, 235, 235),
        )
        hint_bg = pygame.Surface((hint.get_width() + 12, hint.get_height() + 4), pygame.SRCALPHA)
        hint_bg.fill((0, 0, 0, 100))
        self.screen.blit(hint_bg, ((sw - hint_bg.get_width()) // 2, sh - hint_bg.get_height() - 4))
        self.screen.blit(hint, ((sw - hint.get_width()) // 2, sh - hint.get_height() - 6))
