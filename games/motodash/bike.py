import math

import config


class Bike:
    def __init__(self, start_pos):
        self.x, self.y = start_pos
        self.vx = 0.0
        self.vy = 0.0
        self.angle = 0.0
        self.angular_vel = 0.0
        self.on_ground = False
        self.throttle = 0.0
        self.brake = 0.0
        self.lean = 0.0
        self.crashed = False

    def wheel_positions(self):
        cos_a, sin_a = math.cos(self.angle), math.sin(self.angle)
        half = config.WHEELBASE / 2.0
        rear_x  = self.x - cos_a * half
        rear_y  = self.y - sin_a * half
        front_x = self.x + cos_a * half
        front_y = self.y + sin_a * half
        return (rear_x, rear_y), (front_x, front_y)

    def set_inputs(self, throttle, brake, lean):
        self.throttle = 1.0 if throttle else 0.0
        self.brake = 1.0 if brake else 0.0
        self.lean = float(lean)

    def reset_to(self, pos):
        self.x, self.y = pos
        self.vx = self.vy = 0.0
        self.angle = 0.0
        self.angular_vel = 0.0
        self.crashed = False

    def step(self, dt, terrain):
        ax, ay = 0.0, config.GRAVITY

        if self.on_ground and self.throttle > 0:
            cos_a, sin_a = math.cos(self.angle), math.sin(self.angle)
            ax += cos_a * config.THROTTLE_FORCE * self.throttle
            ay += sin_a * config.THROTTLE_FORCE * self.throttle

        # Drag uniquement au sol — en l'air la moto conserve sa vitesse de décollage
        if self.on_ground:
            ax -= self.vx * config.AIR_DRAG
            ay -= self.vy * config.AIR_DRAG

        self.vx += ax * dt
        self.vy += ay * dt

        if self.on_ground and self.brake > 0:
            decel = config.BRAKE_FORCE * dt
            speed = math.hypot(self.vx, self.vy)
            if speed > decel:
                self.vx -= (self.vx / speed) * decel
                self.vy -= (self.vy / speed) * decel
            else:
                self.vx = self.vy = 0.0

        self.angular_vel += self.lean * config.LEAN_TORQUE * dt
        self.angular_vel -= self.angular_vel * config.ANGULAR_DRAG * dt

        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angle += self.angular_vel * dt

        self._resolve_collisions(dt, terrain)

        # Crash uniquement si la moto retombe au sol avec une orientation incorrecte
        # (en l'air, tu peux flipper librement pour faire des saltos).
        if self.on_ground:
            norm = self._normalized_angle()
            if abs(math.degrees(norm)) > config.CRASH_ANGLE_DEG:
                self.crashed = True

    def _normalized_angle(self):
        return (self.angle + math.pi) % (2 * math.pi) - math.pi

    def _resolve_collisions(self, dt, terrain):
        rear, front = self.wheel_positions()
        on_ground_any = False
        # Friction dt-aware : GROUND_FRICTION s'exprime "par frame à 60 FPS"
        friction = config.GROUND_FRICTION ** (60.0 * dt)
        for wheel_pos, sign in ((rear, -1.0), (front, +1.0)):
            wx, wy = wheel_pos
            ground_y = terrain.height_at(wx)
            if ground_y is None:
                continue
            penetration = (wy + config.WHEEL_RADIUS) - ground_y
            if penetration > 0:
                on_ground_any = True
                self.y -= penetration * 0.5
                slope = terrain.slope_at(wx)
                # Contrainte unilatérale : on ne tue la composante perpendiculaire
                # que si la vélocité rentre dans le sol. Sinon la moto décolle
                # naturellement en haut des rampes.
                into = self.vy - slope * self.vx
                if into > 0:
                    inv = 1.0 / (1.0 + slope * slope)
                    self.vx += into * inv * slope
                    self.vy -= into * inv
                self.vx *= friction
                target_angle = math.atan(slope)
                err = self._angle_diff(target_angle, self.angle)
                self.angular_vel += err * 8.0 * dt * sign * 0.5
        self.on_ground = on_ground_any

    @staticmethod
    def _angle_diff(target, current):
        return (target - current + math.pi) % (2 * math.pi) - math.pi
