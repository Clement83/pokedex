"""Entités ennemies : IA simple (idle → chase → attack → dead)."""
import math
from config import (
    ENEMY_HP, ENEMY_DAMAGE, ENEMY_SPEED,
    ENEMY_SIGHT_RANGE, ENEMY_ATTACK_RANGE, ENEMY_SHOOT_COOLDOWN,
)


class Enemy:
    IDLE   = 0
    CHASE  = 1
    ATTACK = 2
    DEAD   = 3

    __slots__ = ('x', 'y', 'hp', 'state', 'attack_timer', 'dead')

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.hp           = ENEMY_HP
        self.state        = self.IDLE
        self.attack_timer = 0.0
        self.dead         = False

    # ── Mise à jour ───────────────────────────────────────────────────────

    def update(self, grid, player, dt: float):
        if self.dead:
            return

        dx   = player.x - self.x
        dy   = player.y - self.y
        dist = math.hypot(dx, dy)

        # Passage IDLE → CHASE : vue dégagée + portée
        if self.state == self.IDLE:
            if dist < ENEMY_SIGHT_RANGE and self._has_los(grid, player):
                self.state = self.CHASE

        elif self.state == self.CHASE:
            if dist < ENEMY_ATTACK_RANGE:
                self.state = self.ATTACK
                self.attack_timer = 0.0
            else:
                # Déplacement simple vers le joueur (pas de pathfinding)
                self._move_toward(grid, player, dx, dy, dist, dt)
                # Perd de vue si trop loin
                if dist > ENEMY_SIGHT_RANGE * 1.5:
                    self.state = self.IDLE

        elif self.state == self.ATTACK:
            self.attack_timer += dt
            if dist > ENEMY_ATTACK_RANGE * 1.8:
                self.state = self.CHASE
            elif self.attack_timer >= ENEMY_SHOOT_COOLDOWN:
                player.take_damage(ENEMY_DAMAGE)
                self.attack_timer = 0.0

    # ── Déplacement ───────────────────────────────────────────────────────

    def _move_toward(self, grid, player, dx, dy, dist, dt: float):
        if dist < 0.001:
            return
        MAP_H, MAP_W = grid.shape
        M  = 0.28
        spd = ENEMY_SPEED * dt
        ndx = dx / dist * spd
        ndy = dy / dist * spd

        nx, ny = self.x + ndx, self.y + ndy
        nx = max(M, min(MAP_W - 1 - M, nx))
        ny = max(M, min(MAP_H - 1 - M, ny))

        if grid[int(self.y), int(nx)] == 0:
            self.x = nx
        if grid[int(ny), int(self.x)] == 0:
            self.y = ny

    # ── Ligne de vue (DDA rapide) ─────────────────────────────────────────

    def _has_los(self, grid, player) -> bool:
        """True si aucun mur non nul ne bloque la ligne enemy → player."""
        ox, oy = self.x, self.y
        edx    = player.x - ox
        edy    = player.y - oy
        steps  = max(int(math.hypot(edx, edy) * 3), 1)
        for i in range(1, steps):
            t = i / steps
            cx = int(ox + edx * t)
            cy = int(oy + edy * t)
            MAP_H, MAP_W = grid.shape
            if not (0 <= cx < MAP_W and 0 <= cy < MAP_H):
                return False
            if grid[cy, cx] != 0:
                return False
        return True

    # ── Dommages ──────────────────────────────────────────────────────────

    def take_damage(self, dmg: int):
        self.hp = max(0, self.hp - dmg)
        if self.hp <= 0:
            self.dead  = True
            self.state = self.DEAD

    # ── Détection de tir joueur ───────────────────────────────────────────

    def is_hit_by_shot(self, player, z_buf) -> bool:
        """
        Vérifie si l'ennemi est touché par le tir centré du joueur
        (colonne milieu de l'écran).
        """
        from config import RENDER_W, RENDER_H, N_RAYS
        from config import CAM_PLANE

        dx   = self.x - player.x
        dy   = self.y - player.y
        det  = player.dx * player.py - player.dy * player.px
        ty   = (-player.dy * dx + player.dx * dy) / det

        if ty <= 0.05:
            return False

        tx      = (player.py * dx - player.px * dy) / det
        sc_x    = int(RENDER_W / 2 * (1.0 + tx / ty))
        sp_half = abs(int(RENDER_H / ty)) // 2

        # Doit être au centre de l'écran ±crosshair_px et pas derrière un mur
        cx_pix  = RENDER_W // 2
        if abs(sc_x - cx_pix) > max(sp_half // 2, 4):
            return False

        col = min(max(sc_x, 0), N_RAYS - 1)
        return ty < z_buf[col]
