"""
Système de projectiles — flèches tirées à l'arc.

Chaque projectile suit une trajectoire parabolique légère et s'arrête
en heurtant un bloc solide ou un mob.
"""
import math
import pygame

from config import (
    TILE_SIZE, TILE_AIR, TILE_LAVA, TILE_WATER, ROWS,
    TILE_ARROW, PLAYER_W, PLAYER_H,
)

_ARROW_SPEED   = 20.0   # tuiles/seconde
_ARROW_DMG     = 2      # dégâts de base
_ARROW_GRAVITY = 5.0    # tuiles/s² (arc de cercle réaliste)
_ARROW_MAX_AGE = 4.0    # secondes avant disparition automatique

# Décalage du centre joueur (utilisé pour centrer le tir sur le joueur)
_HALF_PW = PLAYER_W / TILE_SIZE / 2
_HALF_PH = PLAYER_H / TILE_SIZE / 2


class _Projectile:
    __slots__ = ("x", "y", "vx", "vy", "owner_idx", "damage", "age")

    def __init__(self, x, y, vx, vy, owner_idx, damage):
        self.x         = x
        self.y         = y
        self.vx        = vx
        self.vy        = vy
        self.owner_idx = owner_idx
        self.damage    = damage
        self.age       = 0.0


class ProjectileManager:
    """Gère toutes les flèches actives sur le terrain."""

    def __init__(self):
        self._pool = []

    def spawn(self, player, dir_x, dir_y):
        """
        Tire une flèche dans la direction (dir_x, dir_y).
        Consomme 1 TILE_ARROW de l'inventaire.
        Retourne True si tirée, False si pas de flèches.
        """
        # Consommer une flèche
        consumed = False
        new_res  = []
        for t, c in player.inventory.resources:
            if t == TILE_ARROW and not consumed:
                c -= 1
                consumed = True
                if c > 0:
                    new_res.append((t, c))
            else:
                new_res.append((t, c))
        if not consumed:
            return False
        player.inventory.resources = new_res

        # Normaliser la direction (jamais vecteur nul)
        mag = math.sqrt(dir_x * dir_x + dir_y * dir_y)
        if mag < 0.01:
            dir_x, mag = 1.0, 1.0
        vx = dir_x / mag * _ARROW_SPEED
        vy = dir_y / mag * _ARROW_SPEED

        # Partir du centre du joueur
        cx = player.x + _HALF_PW
        cy = player.y + _HALF_PH
        self._pool.append(_Projectile(cx, cy, vx, vy, player.idx, _ARROW_DMG))
        return True

    def update(self, dt, world, mob_mgr, loot_notifs, players):
        """Met à jour toutes les flèches ; supprime celles qui ont touché."""
        alive = []
        for p in self._pool:
            p.age += dt
            if p.age > _ARROW_MAX_AGE:
                continue

            # Physique
            p.vy += _ARROW_GRAVITY * dt
            p.x  += p.vx * dt
            p.y  += p.vy * dt

            col = int(p.x)
            row = int(p.y)
            if row < 0 or row >= ROWS:
                continue

            # Collision avec bloc solide
            t = world.get(col, row)
            if t != TILE_AIR and t != TILE_LAVA and t != TILE_WATER:
                continue  # flèche stoppée dans le bloc

            # Collision avec mob : attack_near attend (px, py) = coin supérieur gauche
            # On passe (proj_x - half_pw, proj_y - half_ph) pour que le centre = proj pos
            killed, drops, immune = mob_mgr.attack_near(
                p.x - _HALF_PW, p.y - _HALF_PH, 0.9, p.damage, sword_tier=1
            )
            if immune > 0:
                loot_notifs.append(["⚔ IMMUNE !", 1.2, (255, 60, 60)])
            if killed > 0 or immune > 0:
                owner = next((pl for pl in players if pl.idx == p.owner_idx), None)
                if owner and killed > 0 and drops:
                    from scenes.game.actions import _collect_drops
                    _collect_drops(owner, drops, loot_notifs)
                continue  # flèche consommée sur l'impact

            alive.append(p)
        self._pool = alive

    def draw(self, screen, camera):
        """Dessine chaque flèche comme un petit trait orienté."""
        for p in self._pool:
            sx = int(p.x * TILE_SIZE) - int(camera.x)
            sy = int(p.y * TILE_SIZE) - int(camera.y)
            # Longueur de la flèche : 6 px dans la direction du mouvement
            mag = math.sqrt(p.vx * p.vx + p.vy * p.vy) or 1.0
            nx, ny = p.vx / mag, p.vy / mag
            ex = int(sx - nx * 5)
            ey = int(sy - ny * 5)
            pygame.draw.line(screen, (200, 165, 70), (sx, sy), (ex, ey), 2)
            pygame.draw.circle(screen, (240, 200, 90), (sx, sy), 1)
