"""Particules d'ambiance par biome (neige, cendres, braises, papillons).

Pas physiquement liées à la moto — purement décoratives, génératives, légères.
Chaque particule a (x, y, vx, vy, life, kind). Pool fixe pour éviter alloc.
"""

import math
import random
import pygame


class ParticleSystem:
    def __init__(self, biome_name, screen_size, kinds):
        """kinds : liste de types ("snow", "ash", "ember", "butterfly").

        Chaque type a son propre pool et comportement.
        """
        self.biome_name = biome_name
        self.sw, self.sh = screen_size
        self.kinds = kinds
        self._particles = []  # liste de dicts : {kind, x, y, vx, vy, life, max_life}
        self._spawn_acc = {k: 0.0 for k in kinds}
        self._rng = random.Random(0xBEEF + hash(biome_name))

        rates = {
            "snow":      90.0,   # particules / sec
            "ash":       45.0,
            "ember":     35.0,
            "butterfly": 0.5,    # rare
            "dust":      8.0,    # tournoie au sol (canyon, desert)
        }
        self._rates = {k: rates.get(k, 10.0) for k in kinds}

    def update(self, dt, cam_x, cam_y, bike_speed=0.0):
        # Spawn
        for k in self.kinds:
            self._spawn_acc[k] += self._rates[k] * dt
            while self._spawn_acc[k] >= 1.0:
                self._spawn_acc[k] -= 1.0
                self._spawn(k, cam_x, cam_y)

        # Update existing
        alive = []
        for p in self._particles:
            p["life"] -= dt
            if p["life"] <= 0:
                continue
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            kind = p["kind"]
            if kind == "snow":
                # Léger drift latéral (vent)
                p["vx"] += math.sin(p["y"] * 0.05) * 4.0 * dt
            elif kind == "ash":
                p["vx"] += math.sin(p["y"] * 0.04 + p["x"] * 0.02) * 6.0 * dt
            elif kind == "ember":
                # Monte en zigzag
                p["vx"] = math.sin(p["life"] * 4.0) * 18.0
            elif kind == "butterfly":
                p["vy"] = math.sin(p["life"] * 5.0) * 12.0
                p["vx"] = 30.0 + math.cos(p["life"] * 3.0) * 8.0
            elif kind == "dust":
                p["vy"] -= 30.0 * dt  # se dissipe vers le haut
            alive.append(p)
        self._particles = alive

        # Cull off-screen (garde une marge)
        cam_min_x = cam_x - 60
        cam_max_x = cam_x + self.sw + 60
        cam_min_y = cam_y - 60
        cam_max_y = cam_y + self.sh + 60
        self._particles = [
            p for p in self._particles
            if cam_min_x <= p["x"] <= cam_max_x and cam_min_y <= p["y"] <= cam_max_y
        ]

    def _spawn(self, kind, cam_x, cam_y):
        rng = self._rng
        if kind == "snow":
            x = cam_x + rng.uniform(-40, self.sw + 40)
            y = cam_y + rng.uniform(-40, -10)
            self._particles.append({
                "kind": "snow", "x": x, "y": y,
                "vx": rng.uniform(-15, 15), "vy": rng.uniform(40, 75),
                "life": 8.0, "max_life": 8.0, "size": rng.choice([1, 1, 2]),
            })
        elif kind == "ash":
            x = cam_x + rng.uniform(-40, self.sw + 40)
            y = cam_y + rng.uniform(-40, -10)
            self._particles.append({
                "kind": "ash", "x": x, "y": y,
                "vx": rng.uniform(-20, 20), "vy": rng.uniform(20, 45),
                "life": 9.0, "max_life": 9.0, "size": rng.choice([1, 1, 2]),
            })
        elif kind == "ember":
            x = cam_x + rng.uniform(-20, self.sw + 20)
            y = cam_y + self.sh + rng.uniform(-20, 10)
            self._particles.append({
                "kind": "ember", "x": x, "y": y,
                "vx": rng.uniform(-10, 10), "vy": rng.uniform(-90, -55),
                "life": rng.uniform(2.5, 4.0), "max_life": 4.0, "size": 2,
            })
        elif kind == "butterfly":
            x = cam_x + rng.uniform(-20, self.sw + 20)
            y = cam_y + rng.uniform(self.sh * 0.4, self.sh * 0.7)
            self._particles.append({
                "kind": "butterfly", "x": x, "y": y,
                "vx": 30.0, "vy": 0.0,
                "life": 6.0, "max_life": 6.0,
                "color": rng.choice([(245, 200, 80), (220, 100, 180), (240, 240, 240)]),
            })
        elif kind == "dust":
            x = cam_x + rng.uniform(-20, self.sw + 20)
            y = cam_y + self.sh - rng.uniform(20, 60)
            self._particles.append({
                "kind": "dust", "x": x, "y": y,
                "vx": rng.uniform(20, 50), "vy": rng.uniform(-15, 0),
                "life": 2.5, "max_life": 2.5,
            })

    def render(self, surface, cam_x, cam_y):
        for p in self._particles:
            sx = int(p["x"] - cam_x)
            sy = int(p["y"] - cam_y)
            kind = p["kind"]
            t = p["life"] / p["max_life"]
            if kind == "snow":
                a = int(140 + 115 * t)
                col = (245, 250, 255, max(60, min(255, a)))
                self._dot(surface, sx, sy, p.get("size", 1), col)
            elif kind == "ash":
                a = int(60 + 100 * t)
                col = (180, 170, 165, max(40, min(220, a)))
                self._dot(surface, sx, sy, p.get("size", 1), col)
            elif kind == "ember":
                # fade out de jaune → rouge → noir
                if t > 0.6:
                    col = (255, 230, 120)
                elif t > 0.3:
                    col = (255, 140, 50)
                else:
                    col = (180, 50, 20)
                pygame.draw.circle(surface, col, (sx, sy), 2)
            elif kind == "butterfly":
                col = p["color"]
                # Battement d'ailes : ovales
                phase = math.sin(p["life"] * 18.0)
                wing_w = max(1, int(2 + abs(phase) * 2))
                pygame.draw.ellipse(surface, col, (sx - wing_w - 1, sy - 1, wing_w, 3))
                pygame.draw.ellipse(surface, col, (sx + 1, sy - 1, wing_w, 3))
                pygame.draw.line(surface, (40, 40, 40), (sx, sy - 1), (sx, sy + 1), 1)
            elif kind == "dust":
                a = int(180 * t)
                col = (200, 180, 145, max(30, min(180, a)))
                self._dot(surface, sx, sy, 2, col)

    @staticmethod
    def _dot(surface, sx, sy, size, color):
        if len(color) == 4:
            s = pygame.Surface((size * 2 + 1, size * 2 + 1), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (size, size), size)
            surface.blit(s, (sx - size, sy - size))
        else:
            pygame.draw.circle(surface, color, (sx, sy), size)
