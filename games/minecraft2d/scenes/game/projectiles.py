"""
Système de projectiles — flèches tirées à l'arc.

Chaque projectile suit une trajectoire parabolique légère et s'arrête
en heurtant un bloc solide ou un mob.

Types de flèches :
  TILE_ARROW           → dégâts 2, tier 1
  TILE_ARROW_FIRE      → dégâts 5, tier 2
  TILE_ARROW_POISON    → dégâts 2 + poison 4s (1 dmg/s), tier 2
  TILE_ARROW_EXPLOSIVE → dégâts 3 + explosion (zone 2 tiles, casse blocs), tier 3
"""
import math
import pygame

from config import (
    TILE_SIZE, TILE_AIR, TILE_LAVA, TILE_WATER, ROWS,
    TILE_ARROW, TILE_ARROW_FIRE, TILE_ARROW_POISON, TILE_ARROW_EXPLOSIVE,
    TILE_OBSIDIAN, TILE_CHEST, TILE_BREAK_TIME,
    ARROW_TILES, PLAYER_W, PLAYER_H,
)

_ARROW_SPEED   = 7.0    # tuiles/seconde (lent, traversée de monde)
_ARROW_GRAVITY = 0.8    # tuiles/s² (légère courbe)
_ARROW_MAX_AGE = 35.0   # secondes — couvre les ~250 tuiles chargées

# Propriétés par type de flèche : (dégâts, tier, poison_durée, explosif_rayon)
_ARROW_PROPS = {
    TILE_ARROW:            (2, 1, 0.0, 0),
    TILE_ARROW_FIRE:       (5, 2, 0.0, 0),
    TILE_ARROW_POISON:     (2, 2, 4.0, 0),
    TILE_ARROW_EXPLOSIVE:  (3, 3, 0.0, 2),
}

# Couleurs de rendu par type
_ARROW_COLORS = {
    TILE_ARROW:            ((200, 165,  70), (240, 200,  90)),
    TILE_ARROW_FIRE:       ((255, 100,   0), (255, 200,  50)),
    TILE_ARROW_POISON:     (( 80, 200,  50), (140, 255, 100)),
    TILE_ARROW_EXPLOSIVE:  ((255,  50,  50), (255, 150,  80)),
}

# Décalage du centre joueur (utilisé pour centrer le tir sur le joueur)
_HALF_PW = PLAYER_W / TILE_SIZE / 2
_HALF_PH = PLAYER_H / TILE_SIZE / 2

# Blocs indestructibles par explosion
_BLAST_IMMUNE = frozenset((TILE_AIR, TILE_LAVA, TILE_WATER, TILE_OBSIDIAN, TILE_CHEST))


class _Projectile:
    __slots__ = ("x", "y", "vx", "vy", "owner_idx", "damage",
                 "age", "arrow_type", "tier", "poison", "blast_r")

    def __init__(self, x, y, vx, vy, owner_idx, arrow_type):
        self.x          = x
        self.y          = y
        self.vx         = vx
        self.vy         = vy
        self.owner_idx  = owner_idx
        self.age        = 0.0
        self.arrow_type = arrow_type
        dmg, tier, poison, blast_r = _ARROW_PROPS.get(arrow_type, (2, 1, 0.0, 0))
        self.damage  = dmg
        self.tier    = tier
        self.poison  = poison
        self.blast_r = blast_r


class ProjectileManager:
    """Gère toutes les flèches actives sur le terrain."""

    def __init__(self):
        self._pool = []

    def spawn(self, player, dir_x, dir_y):
        """
        Tire une flèche dans la direction (dir_x, dir_y).
        Consomme 1 flèche de l'inventaire (spéciale si sélectionnée, sinon normale).
        Retourne True si tirée, False si pas de flèches.
        """
        # Déterminer le type de flèche à utiliser :
        # si la ressource sélectionnée est une flèche, l'utiliser ; sinon chercher TILE_ARROW
        inv = player.inventory
        sel = inv.selected_tile()
        if sel in ARROW_TILES:
            target_tile = sel
        else:
            target_tile = TILE_ARROW  # fallback normal

        # Consommer une flèche du type choisi
        consumed = False
        new_res  = []
        for t, c in inv.resources:
            if t == target_tile and not consumed:
                c -= 1
                consumed = True
                if c > 0:
                    new_res.append((t, c))
            else:
                new_res.append((t, c))
        if not consumed:
            # Pas de ce type → essayer les flèches normales en fallback
            if target_tile != TILE_ARROW:
                target_tile = TILE_ARROW
                new_res = []
                for t, c in inv.resources:
                    if t == TILE_ARROW and not consumed:
                        c -= 1
                        consumed = True
                        if c > 0:
                            new_res.append((t, c))
                    else:
                        new_res.append((t, c))
            if not consumed:
                return False
        inv.resources = new_res

        # Normaliser la direction (jamais vecteur nul)
        mag = math.sqrt(dir_x * dir_x + dir_y * dir_y)
        if mag < 0.01:
            dir_x, mag = 1.0, 1.0
        vx = dir_x / mag * _ARROW_SPEED
        vy = dir_y / mag * _ARROW_SPEED

        # Partir du centre du joueur
        cx = player.x + _HALF_PW
        cy = player.y + _HALF_PH
        self._pool.append(_Projectile(cx, cy, vx, vy, player.idx, target_tile))
        return True

    def update(self, dt, world, mob_mgr, loot_notifs, players, chunks=None, queue_block_fn=None):
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
                # Explosion si flèche explosive
                if p.blast_r > 0:
                    self._explode(p, world, mob_mgr, loot_notifs, players, chunks, queue_block_fn)
                continue  # flèche stoppée dans le bloc

            # Collision avec mob
            killed, drops, immune = mob_mgr.attack_near(
                p.x - _HALF_PW, p.y - _HALF_PH, 0.9, p.damage,
                sword_tier=p.tier, poison=p.poison
            )
            if immune > 0:
                loot_notifs.append(["⚔ IMMUNE !", 1.2, (255, 60, 60)])
            if killed > 0 or immune > 0:
                owner = next((pl for pl in players if pl.idx == p.owner_idx), None)
                if owner and killed > 0 and drops:
                    from scenes.game.actions import _collect_drops
                    _collect_drops(owner, drops, loot_notifs)
                # Explosion sur impact mob
                if p.blast_r > 0:
                    self._explode(p, world, mob_mgr, loot_notifs, players, chunks, queue_block_fn)
                continue  # flèche consommée sur l'impact

            alive.append(p)
        self._pool = alive

    def _explode(self, proj, world, mob_mgr, loot_notifs, players, chunks, queue_block_fn):
        """Déclenche une explosion : casse les blocs et inflige des dégâts de zone."""
        cx, cy = int(proj.x), int(proj.y)
        r = proj.blast_r

        # Casser les blocs dans le rayon
        for dc in range(-r, r + 1):
            for dr in range(-r, r + 1):
                if dc * dc + dr * dr > r * r:
                    continue
                ec, er = cx + dc, cy + dr
                if er < 0 or er >= ROWS:
                    continue
                tile = world.get(ec, er)
                if tile in _BLAST_IMMUNE:
                    continue
                if tile not in TILE_BREAK_TIME:
                    continue
                world.set(ec, er, TILE_AIR)
                if chunks:
                    chunks.update_tile(ec, er, TILE_AIR)
                if queue_block_fn:
                    queue_block_fn(ec, er, TILE_AIR)

        # Dégâts de zone aux mobs (rayon élargi, dégâts = damage, tier 4 pour percer les immunités)
        mob_mgr.attack_near(
            proj.x - _HALF_PW, proj.y - _HALF_PH, float(r + 1),
            proj.damage, sword_tier=4
        )

        # Notification
        loot_notifs.append(["💥 EXPLOSION !", 1.5, (255, 150, 50)])

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
            colors = _ARROW_COLORS.get(p.arrow_type, ((200, 165, 70), (240, 200, 90)))
            pygame.draw.line(screen, colors[0], (sx, sy), (ex, ey), 2)
            pygame.draw.circle(screen, colors[1], (sx, sy), 1)
