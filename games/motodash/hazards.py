"""Hazards par biome : kill zones (lave, rivière, lave, crevasse, sables mouvants),
obstacles (cactus, rondins, rochers), zones de slow (boue), patches glacés,
updrafts, geysers, et chutes de pierres/braises périodiques.

Le manager applique les effets sur la moto à chaque tick et fournit le rendu.
Tout est piloté par data : chaque hazard est un dict {kind, ...params}.
"""

import math
import random
import pygame


def _rect_contains(rect, x, y):
    rx, ry, rw, rh = rect
    return rx <= x <= rx + rw and ry <= y <= ry + rh


class HazardManager:
    def __init__(self, biome, hazard_specs):
        self.biome = biome
        self.specs = list(hazard_specs)
        self.elapsed = 0.0
        self.kill_floor_y = None
        self.shake_intensity = 0.0  # 0..1, ajouté au shake ambiant
        # Spawn d'objets dynamiques (rocks, embers)
        self._spawned = []  # liste de {kind, x, y, vy, life, hit}
        for s in self.specs:
            if s["kind"] == "kill_floor":
                self.kill_floor_y = s["y"]

    def update(self, bike, dt):
        self.elapsed += dt
        self.shake_intensity = max(0.0, self.shake_intensity - dt * 2.0)
        if bike.crashed:
            self._tick_spawned(dt)
            return

        # Kill floor (fond de canyon, sous niveau de jeu)
        if self.kill_floor_y is not None and bike.y > self.kill_floor_y:
            bike.crashed = True
            self.shake_intensity = 1.0
            self._tick_spawned(dt)
            return

        for s in self.specs:
            self._apply_effect(s, bike, dt)

        self._tick_spawned(dt, bike)

    def _apply_effect(self, s, bike, dt):
        kind = s["kind"]
        if kind == "kill_zone":
            if _rect_contains(s["rect"], bike.x, bike.y):
                bike.crashed = True
                self.shake_intensity = 1.0
        elif kind == "obstacle":
            ox, oy, ow, oh = s["rect"]
            wheels = bike.wheel_positions()
            for (wx, wy) in wheels:
                if ox <= wx <= ox + ow and oy <= wy + 8 <= oy + oh:
                    speed = math.hypot(bike.vx, bike.vy)
                    if speed > 110.0 or s.get("subkind") == "rock":
                        bike.crashed = True
                        self.shake_intensity = 0.7
                    else:
                        bike.vx *= 0.35
                    return
        elif kind == "slow_zone":
            if _rect_contains(s["rect"], bike.x, bike.y + 8):
                # Multiplicateur dt-aware (compense la friction par-frame)
                mult = s.get("mult", 0.7)
                k = mult ** (60.0 * dt)
                bike.vx *= k
        elif kind == "ice_patch":
            ox, oy, ow, oh = s["rect"]
            wheels = bike.wheel_positions()
            for (wx, wy) in wheels:
                if ox <= wx <= ox + ow and oy <= wy + 8 <= oy + oh + 4:
                    # Annule la friction de cette frame en boostant légèrement la vitesse
                    bike.vx *= 1.005
                    return
        elif kind == "updraft":
            if _rect_contains(s["rect"], bike.x, bike.y):
                force = s.get("force", 220.0)
                bike.vy -= force * dt
        elif kind == "falling_rock":
            self._update_falling_rock(s, bike, dt)
        elif kind == "geyser":
            self._update_geyser(s, bike, dt)

    def _update_falling_rock(self, s, bike, dt):
        x = s["x"]
        period = s.get("period", 3.0)
        phase = s.get("phase", 0.0)
        life = s.get("fall_duration", 1.6)
        t = (self.elapsed - phase) % period
        # Mémoire latente : on "spawne" un rock chaque cycle ; tracé via t directement
        if 0.0 <= t <= life:
            top_y = s.get("top_y", 80.0)
            ground_y = s.get("ground_y", 260.0)
            rock_y = top_y + (ground_y - top_y) * (t / life)
            # Hit si proche
            if abs(bike.x - x) < 14 and abs(bike.y - rock_y) < 14:
                if not s.get("_hit_cycle") == int((self.elapsed - phase) // period):
                    s["_hit_cycle"] = int((self.elapsed - phase) // period)
                    bike.vx *= 0.4
                    bike.vy = max(bike.vy, 80.0)
                    self.shake_intensity = max(self.shake_intensity, 0.5)

    def _update_geyser(self, s, bike, dt):
        x = s["x"]
        period = s.get("period", 4.0)
        phase = s.get("phase", 0.0)
        active_dur = s.get("active_duration", 0.9)
        t = (self.elapsed - phase) % period
        if t <= active_dur:
            ground_y = s.get("ground_y", 240.0)
            top_y = ground_y - s.get("height", 120.0)
            if abs(bike.x - x) < 22 and top_y <= bike.y <= ground_y + 10:
                force = s.get("force", 700.0)
                bike.vy -= force * dt
                self.shake_intensity = max(self.shake_intensity, 0.25)

    def _tick_spawned(self, dt, bike=None):
        # Pas utilisé pour l'instant : tout est calculé via t modulo période
        pass

    # ── Rendu ────────────────────────────────────────────────────────────────
    def render(self, surface, cam_x, cam_y, view_rect):
        x_min = view_rect[0] + cam_x - 20
        x_max = view_rect[0] + view_rect[2] + cam_x + 20
        for s in self.specs:
            self._render_hazard(surface, s, cam_x, cam_y, x_min, x_max)

    def _render_hazard(self, surface, s, cam_x, cam_y, x_min, x_max):
        kind = s["kind"]
        if kind == "kill_zone":
            self._render_kill_zone(surface, s, cam_x, cam_y, x_min, x_max)
        elif kind == "obstacle":
            self._render_obstacle(surface, s, cam_x, cam_y, x_min, x_max)
        elif kind == "slow_zone":
            self._render_slow_zone(surface, s, cam_x, cam_y, x_min, x_max)
        elif kind == "ice_patch":
            self._render_ice_patch(surface, s, cam_x, cam_y, x_min, x_max)
        elif kind == "updraft":
            self._render_updraft(surface, s, cam_x, cam_y, x_min, x_max)
        elif kind == "falling_rock":
            self._render_falling_rock(surface, s, cam_x, cam_y, x_min, x_max)
        elif kind == "geyser":
            self._render_geyser(surface, s, cam_x, cam_y, x_min, x_max)

    def _render_kill_zone(self, surface, s, cam_x, cam_y, x_min, x_max):
        rx, ry, rw, rh = s["rect"]
        if rx + rw < x_min or rx > x_max:
            return
        sub = s.get("subkind", "lava")
        sx = int(rx - cam_x)
        sy = int(ry - cam_y)
        rect = pygame.Rect(sx, sy, int(rw), int(rh))

        if sub == "lava":
            pygame.draw.rect(surface, (220, 70, 25), rect)
            # Bulles animées (vagues sinusoïdales)
            for k in range(int(rw // 18)):
                bx = sx + 6 + k * 18 + int(math.sin(self.elapsed * 2.5 + k) * 3)
                by = sy + 4 + int(math.cos(self.elapsed * 3.0 + k * 0.7) * 2)
                pygame.draw.circle(surface, (255, 200, 100), (bx, by), 3)
                pygame.draw.circle(surface, (255, 240, 180), (bx, by - 1), 1)
            # Bordure plus sombre en bas
            pygame.draw.line(surface, (90, 25, 10), (sx, sy + rh - 1), (sx + rw, sy + rh - 1), 2)
        elif sub == "river":
            # Eau bleue avec ondulations
            pygame.draw.rect(surface, (45, 95, 165), rect)
            for k in range(int(rw // 12)):
                wx = sx + k * 12
                wy = sy + 4 + int(math.sin(self.elapsed * 2.0 + k * 0.4) * 2)
                pygame.draw.line(surface, (130, 180, 230), (wx, wy), (wx + 8, wy), 1)
            pygame.draw.line(surface, (200, 220, 240), (sx, sy + 1), (sx + rw, sy + 1), 1)
        elif sub == "crevasse":
            pygame.draw.rect(surface, (40, 60, 90), rect)
            # Lèvres de glace claires en haut
            pygame.draw.line(surface, (220, 235, 245), (sx, sy), (sx + rw, sy), 2)
            # Stries sombres
            for k in range(int(rh // 6)):
                ty = sy + 4 + k * 6
                pygame.draw.line(surface, (20, 35, 60), (sx + 3, ty), (sx + rw - 3, ty), 1)
        elif sub == "quicksand":
            pygame.draw.rect(surface, (190, 155, 95), rect)
            # Spirales (cercles concentriques)
            cx_s = sx + rw // 2
            cy_s = sy + rh // 2
            phase = self.elapsed * 0.8
            for k in range(3):
                r = max(2, int((rh / 2) - (k * 4) - (phase * 6) % 12))
                if r > 1:
                    pygame.draw.ellipse(
                        surface, (140, 110, 65),
                        pygame.Rect(cx_s - r * 2, cy_s - r // 2, r * 4, r), 1,
                    )
        else:
            pygame.draw.rect(surface, (180, 30, 30), rect)

    def _render_obstacle(self, surface, s, cam_x, cam_y, x_min, x_max):
        ox, oy, ow, oh = s["rect"]
        if ox + ow < x_min or ox > x_max:
            return
        sub = s.get("subkind", "log")
        sx = int(ox - cam_x)
        sy = int(oy - cam_y)
        if sub == "log":
            # Rondin brun horizontal
            pygame.draw.rect(surface, (105, 70, 40), (sx, sy, ow, oh), border_radius=3)
            pygame.draw.line(surface, (150, 105, 65), (sx + 2, sy + 2), (sx + ow - 3, sy + 2), 1)
            # Anneaux
            for k in range(int(ow // 6)):
                pygame.draw.line(surface, (75, 50, 28),
                                 (sx + 4 + k * 6, sy + 1),
                                 (sx + 4 + k * 6, sy + oh - 1), 1)
        elif sub == "cactus":
            # Cactus vert avec deux bras
            base_x = sx + ow // 2
            pygame.draw.rect(surface, (60, 110, 65), (base_x - 3, sy, 6, oh))
            pygame.draw.rect(surface, (90, 140, 90), (base_x - 2, sy, 1, oh - 2))
            # Bras gauche
            pygame.draw.rect(surface, (60, 110, 65), (base_x - 8, sy + oh // 2, 5, 3))
            pygame.draw.rect(surface, (60, 110, 65), (base_x - 8, sy + oh // 2 - 5, 3, 5))
            # Bras droit
            pygame.draw.rect(surface, (60, 110, 65), (base_x + 3, sy + oh // 3, 5, 3))
            pygame.draw.rect(surface, (60, 110, 65), (base_x + 5, sy + oh // 3 - 5, 3, 5))
            # Épines
            for k in range(0, oh, 3):
                pygame.draw.line(surface, (220, 220, 180),
                                 (base_x - 3, sy + k), (base_x - 5, sy + k), 1)
                pygame.draw.line(surface, (220, 220, 180),
                                 (base_x + 3, sy + k + 1), (base_x + 5, sy + k + 1), 1)
        elif sub == "rock":
            # Caillou gris saillant (mort si touché)
            pygame.draw.polygon(surface, (90, 85, 80), [
                (sx, sy + oh), (sx + 3, sy + 2), (sx + ow // 2, sy),
                (sx + ow - 2, sy + 4), (sx + ow, sy + oh),
            ])
            pygame.draw.polygon(surface, (130, 125, 120), [
                (sx + 4, sy + oh - 2), (sx + 5, sy + 4), (sx + ow // 2, sy + 2),
                (sx + ow - 4, sy + 6),
            ])

    def _render_slow_zone(self, surface, s, cam_x, cam_y, x_min, x_max):
        rx, ry, rw, rh = s["rect"]
        if rx + rw < x_min or rx > x_max:
            return
        sx = int(rx - cam_x)
        sy = int(ry - cam_y)
        # Boue : marron foncé avec taches
        pygame.draw.rect(surface, (75, 50, 30), (sx, sy, int(rw), int(rh)), border_radius=2)
        rng = random.Random(int(rx) * 7 + int(ry))
        for _ in range(int(rw // 8)):
            tx = sx + rng.randint(2, max(3, int(rw) - 3))
            ty = sy + rng.randint(1, max(2, int(rh) - 2))
            pygame.draw.circle(surface, (50, 35, 20), (tx, ty), 2)
        # Reflet
        pygame.draw.line(surface, (130, 95, 65), (sx + 2, sy + 1), (sx + int(rw) - 3, sy + 1), 1)

    def _render_ice_patch(self, surface, s, cam_x, cam_y, x_min, x_max):
        rx, ry, rw, rh = s["rect"]
        if rx + rw < x_min or rx > x_max:
            return
        sx = int(rx - cam_x)
        sy = int(ry - cam_y)
        # Plaque bleu glacé brillante
        ice = pygame.Surface((int(rw), int(rh)), pygame.SRCALPHA)
        pygame.draw.rect(ice, (190, 230, 250, 200), ice.get_rect(), border_radius=2)
        # Reflet diagonal
        for k in range(0, int(rw), 4):
            pygame.draw.line(ice, (245, 250, 255, 220), (k, 0), (k + 6, int(rh)), 1)
        surface.blit(ice, (sx, sy))
        pygame.draw.rect(surface, (140, 190, 220), (sx, sy, int(rw), int(rh)), 1, border_radius=2)

    def _render_updraft(self, surface, s, cam_x, cam_y, x_min, x_max):
        rx, ry, rw, rh = s["rect"]
        if rx + rw < x_min or rx > x_max:
            return
        sx = int(rx - cam_x)
        sy = int(ry - cam_y)
        # Particules d'air qui montent (verticales)
        layer = pygame.Surface((int(rw), int(rh)), pygame.SRCALPHA)
        for k in range(int(rw // 8)):
            px = k * 8 + 4
            py = (int(self.elapsed * 80 + k * 17)) % int(rh)
            pygame.draw.line(layer, (220, 230, 240, 90), (px, py), (px, py - 6), 1)
            pygame.draw.line(layer, (255, 255, 255, 60), (px + 1, py - 2), (px + 1, py - 5), 1)
        surface.blit(layer, (sx, sy))

    def _render_falling_rock(self, surface, s, cam_x, cam_y, x_min, x_max):
        x = s["x"]
        if x < x_min - 30 or x > x_max + 30:
            return
        period = s.get("period", 3.0)
        phase = s.get("phase", 0.0)
        life = s.get("fall_duration", 1.6)
        t = (self.elapsed - phase) % period
        if t > life:
            # Effet d'impact (avant le respawn)
            return
        top_y = s.get("top_y", 80.0)
        ground_y = s.get("ground_y", 260.0)
        rock_y = top_y + (ground_y - top_y) * (t / life)
        sx = int(x - cam_x)
        sy = int(rock_y - cam_y)
        pygame.draw.circle(surface, (90, 70, 60), (sx, sy), 5)
        pygame.draw.circle(surface, (130, 110, 95), (sx - 1, sy - 1), 2)

    def _render_geyser(self, surface, s, cam_x, cam_y, x_min, x_max):
        x = s["x"]
        if x < x_min - 30 or x > x_max + 30:
            return
        period = s.get("period", 4.0)
        phase = s.get("phase", 0.0)
        active_dur = s.get("active_duration", 0.9)
        t = (self.elapsed - phase) % period
        sx = int(x - cam_x)
        ground_y = s.get("ground_y", 240.0)
        gy = int(ground_y - cam_y)
        # Toujours dessiner la base (fissure)
        pygame.draw.line(surface, (200, 80, 30), (sx - 6, gy), (sx + 6, gy), 2)
        pygame.draw.circle(surface, (60, 35, 25), (sx, gy), 5)
        if t <= active_dur:
            # Colonne de feu/vapeur
            ratio = t / active_dur
            height_active = int(s.get("height", 120.0) * (1.0 - abs(ratio - 0.5) * 1.4))
            if height_active > 0:
                top = gy - height_active
                for layer_h in (height_active, max(2, height_active * 2 // 3), max(1, height_active // 3)):
                    color = (
                        (255, 220, 90) if layer_h == height_active else
                        ((255, 140, 40) if layer_h == max(2, height_active * 2 // 3) else (200, 60, 20))
                    )
                    poly_w = 6 if layer_h == height_active else (10 if layer_h == max(2, height_active * 2 // 3) else 14)
                    pygame.draw.polygon(surface, color, [
                        (sx - poly_w, gy),
                        (sx, gy - layer_h),
                        (sx + poly_w, gy),
                    ])
