import math
import pygame

import config
from bike import Bike
from terrain import Terrain
import scores
import levels


class GameScene:
    def __init__(self, screen, level_id):
        self.screen = screen
        self.level = levels.get(level_id)
        self.terrain = Terrain(
            self.level["terrain"],
            self.level["finish_x"],
            self.level["checkpoints"],
        )
        self.bike = Bike(self.level["start"])
        self.last_checkpoint = self.level["start"]
        self.passed_checkpoints = set()
        self.elapsed = 0.0
        self.finished = False
        self.crash_timer = 0.0
        self.cam_x = 0.0
        self.cam_y = 0.0
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

        self.elapsed += dt

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
        self.screen.fill(config.BG_COLOR)
        self.terrain.render(self.screen, self.cam_x, self.cam_y)
        self._render_bike()
        self._render_hud()

    def _render_bike(self):
        cx = self.bike.x - self.cam_x
        cy = self.bike.y - self.cam_y
        cos_a, sin_a = math.cos(self.bike.angle), math.sin(self.bike.angle)
        half = config.WHEELBASE / 2.0
        rear  = (cx - cos_a * half, cy - sin_a * half)
        front = (cx + cos_a * half, cy + sin_a * half)
        pygame.draw.line(self.screen, config.BIKE_BODY, rear, front, 5)
        pygame.draw.circle(self.screen, config.BIKE_WHEEL, (int(rear[0]),  int(rear[1])),  int(config.WHEEL_RADIUS))
        pygame.draw.circle(self.screen, config.BIKE_WHEEL, (int(front[0]), int(front[1])), int(config.WHEEL_RADIUS))
        head_x = cx - sin_a * 14
        head_y = cy - cos_a * 14
        pygame.draw.circle(self.screen, config.BIKE_RIDER, (int(head_x), int(head_y)), 4)

    def _render_hud(self):
        mins = int(self.elapsed // 60)
        secs = self.elapsed - mins * 60
        time_str = f"{mins:02d}:{secs:05.2f}"
        surf = self.font.render(time_str, True, config.TEXT_COLOR)
        bg = pygame.Surface((surf.get_width() + 16, surf.get_height() + 8), pygame.SRCALPHA)
        bg.fill(config.HUD_BG)
        self.screen.blit(bg, (8, 8))
        self.screen.blit(surf, (16, 12))
        if self.bike.crashed:
            msg = self.font.render("CRASH ! reset...", True, (255, 80, 80))
            self.screen.blit(msg, ((self.screen.get_width() - msg.get_width()) // 2, 60))
        hint = self.font_small.render(
            "↑ accel · ↓ frein · ←→ pencher · R reset · Échap menu",
            True, (220, 220, 220),
        )
        self.screen.blit(hint, ((self.screen.get_width() - hint.get_width()) // 2,
                                self.screen.get_height() - hint.get_height() - 6))
