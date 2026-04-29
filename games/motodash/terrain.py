import bisect
import math
import random
import pygame

import config


class Terrain:
    def __init__(self, points, finish_x, checkpoints, biome=None):
        self.points = list(points)
        self.xs = [p[0] for p in self.points]
        self.finish_x = finish_x
        self.checkpoints = list(checkpoints)
        self.biome = biome or config.BIOMES["grass"]
        # Décorations pré-calculées : tufs d'herbe + cailloux
        rng = random.Random(hash(tuple(self.xs)) & 0xFFFFFFFF)
        self._grass_tufts = []
        if self.xs:
            x_min, x_max = self.xs[0], self.xs[-1]
            x = x_min
            while x < x_max:
                x += rng.randint(8, 28)
                self._grass_tufts.append((x, rng.randint(3, 6), rng.choice([-1, 1])))
        self._stones = []
        if self.xs:
            x = self.xs[0]
            x_max = self.xs[-1]
            while x < x_max:
                x += rng.randint(80, 200)
                self._stones.append((x, rng.randint(2, 5)))

    def _segment_at(self, x):
        if x < self.xs[0] or x > self.xs[-1]:
            return None
        i = bisect.bisect_right(self.xs, x) - 1
        if i < 0:
            i = 0
        if i + 1 >= len(self.points):
            return None
        x1, y1 = self.points[i]
        x2, y2 = self.points[i + 1]
        return x1, y1, x2, y2

    def height_at(self, x):
        seg = self._segment_at(x)
        if seg is None:
            return None
        x1, y1, x2, y2 = seg
        if x2 == x1:
            return y1
        t = (x - x1) / (x2 - x1)
        return y1 + t * (y2 - y1)

    def slope_at(self, x):
        seg = self._segment_at(x)
        if seg is None:
            return 0.0
        x1, y1, x2, y2 = seg
        if x2 == x1:
            return 0.0
        return (y2 - y1) / (x2 - x1)

    def render(self, surface, cam_x, cam_y):
        sw, sh = surface.get_size()
        x_min = cam_x - 50
        x_max = cam_x + sw + 50
        screen_pts = []
        for px, py in self.points:
            if px > x_max:
                screen_pts.append((px - cam_x, py - cam_y))
                break
            if px < x_min and screen_pts:
                continue
            screen_pts.append((px - cam_x, py - cam_y))

        if len(screen_pts) < 2:
            return

        # Couche terre (polygone plein, descend hors écran)
        fill = list(screen_pts) + [(screen_pts[-1][0], sh + 40), (screen_pts[0][0], sh + 40)]
        pygame.draw.polygon(surface, self.biome["dirt"], fill)

        # Bandes horizontales sombres pour donner de la profondeur à la terre
        for band_y_offset in (18, 38, 60):
            dark_pts = []
            for sp in screen_pts:
                dark_pts.append((sp[0], sp[1] + band_y_offset))
            band_fill = (
                list(dark_pts)
                + [(dark_pts[-1][0], sh + 40), (dark_pts[0][0], sh + 40)]
            )
            pygame.draw.polygon(surface, self.biome["dirt_dark"], band_fill)

        # Bande herbe (polygone fin sur les premiers ~5 px sous la surface)
        grass_pts = list(screen_pts) + [(screen_pts[i][0], screen_pts[i][1] + 5) for i in range(len(screen_pts) - 1, -1, -1)]
        pygame.draw.polygon(surface, self.biome["grass_dark"], grass_pts)
        # Surcouche herbe claire (surface uniquement)
        pygame.draw.lines(surface, self.biome["grass"], False, screen_pts, 2)

        # Tufs d'herbe sur la surface
        for tx, th, _ in self._grass_tufts:
            if tx < x_min or tx > x_max:
                continue
            ty = self.height_at(tx)
            if ty is None:
                continue
            sx = tx - cam_x
            sy = ty - cam_y
            pygame.draw.line(surface, self.biome["grass"], (sx, sy), (sx - 1, sy - th), 1)
            pygame.draw.line(surface, self.biome["grass"], (sx, sy), (sx + 1, sy - th + 1), 1)
            pygame.draw.line(surface, self.biome["grass_dark"], (sx + 1, sy), (sx + 2, sy - th), 1)

        # Cailloux
        for stx, sr in self._stones:
            if stx < x_min or stx > x_max:
                continue
            sty = self.height_at(stx)
            if sty is None:
                continue
            sx = stx - cam_x
            sy = sty - cam_y
            pygame.draw.circle(surface, self.biome["stone"], (int(sx), int(sy - sr // 2)), sr)
            pygame.draw.circle(surface, self.biome["stone_light"], (int(sx - 1), int(sy - sr // 2 - 1)), max(1, sr // 2))

        # Checkpoints (petits poteaux jaunes avec drapeaux)
        for cp_x in self.checkpoints:
            cx = cp_x - cam_x
            if -10 <= cx <= sw + 10:
                cy_ground = self.height_at(cp_x)
                if cy_ground is not None:
                    top = cy_ground - cam_y - 28
                    bot = cy_ground - cam_y
                    pygame.draw.line(surface, (90, 90, 95), (cx, bot), (cx, top), 2)
                    pygame.draw.polygon(
                        surface, (245, 220, 80),
                        [(cx, top), (cx + 12, top + 4), (cx, top + 8)],
                    )

        # Drapeau d'arrivée (à carreaux)
        fx = self.finish_x - cam_x
        if -20 <= fx <= sw + 20:
            fy_ground = self.height_at(self.finish_x)
            if fy_ground is not None:
                top = fy_ground - cam_y - 60
                bot = fy_ground - cam_y
                # Mât
                pygame.draw.line(surface, (235, 235, 235), (fx, bot), (fx, top), 2)
                # Drapeau à carreaux 4x3
                flag_w, flag_h = 24, 14
                cell = flag_w // 4
                for row in range(3):
                    for col in range(4):
                        color = (235, 235, 235) if (row + col) % 2 == 0 else (30, 30, 30)
                        pygame.draw.rect(
                            surface, color,
                            (fx + col * cell, top + row * (flag_h // 3), cell, flag_h // 3 + 1),
                        )
