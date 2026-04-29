import bisect
import pygame

import config


class Terrain:
    def __init__(self, points, finish_x, checkpoints):
        self.points = list(points)
        self.xs = [p[0] for p in self.points]
        self.finish_x = finish_x
        self.checkpoints = list(checkpoints)

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

        fill = list(screen_pts) + [(screen_pts[-1][0], sh + 40), (screen_pts[0][0], sh + 40)]
        pygame.draw.polygon(surface, config.TERRAIN_COLOR, fill)
        pygame.draw.lines(surface, config.TERRAIN_LINE, False, screen_pts, 2)

        # Drapeau d'arrivée
        fx = self.finish_x - cam_x
        if -20 <= fx <= sw + 20:
            fy_ground = self.height_at(self.finish_x)
            if fy_ground is not None:
                top = fy_ground - cam_y - 50
                bot = fy_ground - cam_y
                pygame.draw.line(surface, (240, 240, 240), (fx, bot), (fx, top), 2)
                pygame.draw.polygon(
                    surface, (220, 60, 60),
                    [(fx, top), (fx + 18, top + 6), (fx, top + 12)],
                )

        # Checkpoints (petits poteaux jaunes)
        for cp_x in self.checkpoints:
            cx = cp_x - cam_x
            if -10 <= cx <= sw + 10:
                cy_ground = self.height_at(cp_x)
                if cy_ground is not None:
                    top = cy_ground - cam_y - 24
                    bot = cy_ground - cam_y
                    pygame.draw.line(surface, (245, 220, 80), (cx, bot), (cx, top), 2)
