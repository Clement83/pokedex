"""
Physique voiture – portage fidèle du Car.js du POC Phaser.
"""
from config import (
    AIR_RES, ROLL_RES,
    SHIFT_PERF, SHIFT_GOOD, SHIFT_MULT, SHIFT_BONUS_DUR,
    RACE_DISTANCE,
)


class Car:
    def __init__(self, data: dict):
        s = data["stats"]
        self.data         = data
        self.name         = data["name"]
        self.color        = data["col"]
        self.max_power    = s["power"]
        self.weight       = s["weight"]
        self.max_gears    = s["gears"]
        self.max_rpm      = s["maxRPM"]
        self.opt_rpm      = s["optRPM"]
        self.shift_time   = s["shiftT"]
        self.curve        = data["curve"]
        self.ratios       = data["ratios"]

        # État dynamique
        self.rpm          = 1000.0
        self.speed        = 0.0    # km/h
        self.gear         = 1
        self.position     = 0.0   # mètres
        self.race_time    = 0.0   # secondes

        self.is_shifting      = False
        self.shift_cooldown   = 0.0
        self.shift_bonus      = 1.0
        self.shift_bonus_timer = 0.0
        self.shift_quality    = None  # 'PERFECT' | 'GOOD' | 'BAD' | None

        self.has_started  = False
        self.has_finished = False
        self.best_speed   = 0.0

        # Stats de course
        self.perfect_shifts = 0
        self.good_shifts    = 0
        self.bad_shifts     = 0

    # ── Courbe de puissance ────────────────────────────────────────────────────
    def power_at_rpm(self, rpm: float) -> float:
        rpm = max(1000.0, min(self.max_rpm, rpm))
        c = self.curve
        for i in range(len(c) - 1):
            r1, p1 = c[i]
            r2, p2 = c[i + 1]
            if r1 <= rpm <= r2:
                t = (rpm - r1) / (r2 - r1)
                return p1 + (p2 - p1) * t
        return c[-1][1]

    def calc_rpm(self, speed: float, gear: int) -> float:
        if speed < 1:
            return 1000.0
        # Constante abaissée (25 au lieu de 40) : chaque vitesse couvre
        # une plage de speed plus large → moins de shifts à spammer
        rpm = speed * self.ratios[gear - 1] * 25.0
        return max(1000.0, min(rpm, self.max_rpm + 500))

    # ── Changements de vitesse ─────────────────────────────────────────────────
    def shift_up(self):
        if self.gear < self.max_gears and not self.is_shifting:
            self.is_shifting = True
            old_rpm = self.rpm
            self.gear += 1
            self.rpm *= 0.7
            self._eval_shift(old_rpm)
            self.shift_cooldown = self.shift_time

    def shift_down(self):
        if self.gear > 1 and not self.is_shifting:
            self.is_shifting = True
            self.gear -= 1
            self.rpm = min(self.rpm * 1.4, self.max_rpm)
            self.shift_cooldown = self.shift_time

    def _eval_shift(self, rpm_before: float):
        diff = abs(rpm_before - self.opt_rpm)
        if diff <= SHIFT_PERF:
            q = 'PERFECT'
            self.perfect_shifts += 1
        elif diff <= SHIFT_GOOD:
            q = 'GOOD'
            self.good_shifts += 1
        else:
            q = 'BAD'
            self.bad_shifts += 1
        self.shift_quality     = q
        self.shift_bonus       = SHIFT_MULT[q]
        self.shift_bonus_timer = SHIFT_BONUS_DUR

    # ── Mise à jour physique ───────────────────────────────────────────────────
    def update(self, dt: float):
        if not self.has_started or self.has_finished:
            return

        # Cooldown de changement de vitesse
        if self.is_shifting:
            self.shift_cooldown -= dt
            if self.shift_cooldown <= 0:
                self.is_shifting    = False
                self.shift_cooldown = 0.0

        # Timer du bonus de shift
        if self.shift_bonus_timer > 0:
            self.shift_bonus_timer -= dt
            if self.shift_bonus_timer <= 0:
                self.shift_bonus   = 1.0
                self.shift_quality = None

        # ── Physique (identique au Car.js) ────────────────────────────────────
        power_hp = self.power_at_rpm(self.rpm) * self.shift_bonus
        power_w  = power_hp * 745.7
        vel_ms   = self.speed / 3.6

        wheel_force = power_w / vel_ms if vel_ms > 0.1 else power_w * 10.0
        accel       = wheel_force / self.weight

        air_drag     = AIR_RES  * self.speed ** 2
        rolling_drag = ROLL_RES * self.weight * 9.81
        total_drag   = (air_drag + rolling_drag) / self.weight
        net_accel    = accel - total_drag

        if self.is_shifting:
            net_accel *= 0.3
        if self.rpm >= self.max_rpm:
            net_accel *= 0.2

        self.speed = max(0.0, self.speed + net_accel * dt * 3.6)
        self.rpm   = self.calc_rpm(self.speed, self.gear)

        self.position  += (self.speed / 3.6) * dt
        self.race_time += dt

        if self.speed > self.best_speed:
            self.best_speed = self.speed

        if self.position >= RACE_DISTANCE:
            self.position    = RACE_DISTANCE
            self.has_finished = True

    def start(self):
        self.has_started = True

    def reset(self):
        self.__init__(self.data)
