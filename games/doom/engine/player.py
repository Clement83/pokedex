"""Joueur : position, direction, déplacement, collisions."""
import math
from config import (
    PLAYER_SPEED, ROTATE_SPEED, CAM_PLANE, PLAYER_HP,
    STARTING_AMMO, FIRE_COOLDOWN,
)

_MARGIN = 0.28   # rayon de collision du joueur (en cases)


class Player:
    __slots__ = (
        'x', 'y', 'angle', 'dx', 'dy', 'px', 'py',
        'hp', 'ammo', 'fire_timer', 'hurt_timer', 'dead',
    )

    def __init__(self, x: float, y: float, angle: float = 0.0):
        self.x = x
        self.y = y
        self.angle = angle
        self.hp    = PLAYER_HP
        self.ammo  = STARTING_AMMO
        self.fire_timer = 0.0
        self.hurt_timer = 0.0
        self.dead  = False
        self._refresh_dir()

    # ── Vecteurs de direction ─────────────────────────────────────────────

    def _refresh_dir(self):
        self.dx =  math.cos(self.angle)
        self.dy =  math.sin(self.angle)
        # Plan caméra perpendiculaire à la direction ((-dy, dx) * CAM_PLANE)
        self.px = -self.dy * CAM_PLANE
        self.py =  self.dx * CAM_PLANE

    # ── Mise à jour ───────────────────────────────────────────────────────

    def update(self, grid, dt: float, fwd: float, side: float, turn: float):
        """
        fwd  ∈ [-1, 1]  → avancer / reculer
        side ∈ [-1, 1]  → strafe droite (>0) / gauche (<0)
        turn ∈ [-1, 1]  → rotation droite (>0) / gauche (<0)
        """
        # Rotation
        self.angle += turn * ROTATE_SPEED * dt
        self._refresh_dir()

        MAP_H, MAP_W = grid.shape

        # Avancer / reculer
        if abs(fwd) > 0.001:
            nx = self.x + self.dx * fwd * PLAYER_SPEED * dt
            ny = self.y + self.dy * fwd * PLAYER_SPEED * dt
            self._try_move(grid, nx, ny, MAP_W, MAP_H)

        # Strafe  (perpendiculaire à la direction : vecteur (-dy, dx))
        if abs(side) > 0.001:
            nx = self.x + (-self.dy) * side * PLAYER_SPEED * dt
            ny = self.y +   self.dx  * side * PLAYER_SPEED * dt
            self._try_move(grid, nx, ny, MAP_W, MAP_H)

        # Timers
        if self.fire_timer > 0:
            self.fire_timer -= dt
        if self.hurt_timer > 0:
            self.hurt_timer -= dt

    def _try_move(self, grid, nx: float, ny: float, MAP_W: int, MAP_H: int):
        """Déplacement séparé X/Y pour éviter de coller dans les coins."""
        M = _MARGIN
        nx = max(M + 0.01, min(MAP_W - M - 0.01, nx))
        ny = max(M + 0.01, min(MAP_H - M - 0.01, ny))

        # Mouvement X
        if (grid[int(self.y - M), int(nx)] == 0 and
                grid[int(self.y + M), int(nx)] == 0):
            self.x = nx

        # Mouvement Y
        if (grid[int(ny - M), int(self.x)] == 0 and
                grid[int(ny + M), int(self.x)] == 0):
            self.y = ny

    # ── Actions ───────────────────────────────────────────────────────────

    def try_fire(self) -> bool:
        """Retourne True si le tir est possible (munitions + cooldown)."""
        if self.fire_timer <= 0 and self.ammo > 0:
            self.fire_timer = FIRE_COOLDOWN
            self.ammo -= 1
            return True
        return False

    def take_damage(self, dmg: int):
        self.hp = max(0, self.hp - dmg)
        self.hurt_timer = 0.3
        if self.hp <= 0:
            self.dead = True
