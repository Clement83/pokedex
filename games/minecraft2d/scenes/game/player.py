"""
Classe Player et utilitaires de collision / physique du joueur.
"""
from config import (
    TILE_SIZE, PLAYER_W, PLAYER_H, ROWS,
    GRAVITY, MAX_FALL_SPEED, JUMP_VEL, WALK_SPEED, CLIMB_SPEED,
    REACH_RADIUS, TILE_AIR,
)
from scenes.game.inventory import Inventory


# ── Classe Player ─────────────────────────────────────────────────────────────

class Player:
    def __init__(self, x, y, color, idx):
        self.x     = float(x)    # position en tuiles (float)
        self.y     = float(y)
        self.vx    = 0.0
        self.vy    = 0.0
        self.on_ground = False
        self.on_wall   = False
        self.color = color
        self.idx   = idx
        self.inventory    = Inventory()
        self._action_cd   = 0.0
        self._break_time  = 0.0
        self.max_hp = 6
        self.hp     = 6
        self._dmg_flash = 0.0    # durée restante du flash rouge (s)

    def px(self):
        return int(self.x * TILE_SIZE)

    def py(self):
        return int(self.y * TILE_SIZE)

    def col(self):
        return int(self.x + PLAYER_W / TILE_SIZE / 2)

    def row(self):
        return int(self.y + PLAYER_H / TILE_SIZE / 2)


# ── Helpers collision ────────────────────────────────────────────────────────

def solid(world, col, row):
    if row < 0 or row >= ROWS:
        return True
    return world.get(col, row) != TILE_AIR


def player_cols(p):
    pw = PLAYER_W / TILE_SIZE
    return list(range(int(p.x), int(p.x + pw - 0.01) + 1))


def player_rows(p):
    ph = PLAYER_H / TILE_SIZE
    return list(range(int(p.y), int(p.y + ph - 0.01) + 1))


def move_x(player, world, dx):
    player.x += dx
    pw    = PLAYER_W / TILE_SIZE
    left  = int(player.x)
    right = int(player.x + pw - 0.01)
    rows  = player_rows(player)
    if dx > 0:
        for r in rows:
            if solid(world, right, r):
                player.x  = right - pw
                player.vx = 0
                break
    elif dx < 0:
        for r in rows:
            if solid(world, left, r):
                player.x  = left + 1
                player.vx = 0
                break


def move_y(player, world, dy):
    player.y += dy
    ph     = PLAYER_H / TILE_SIZE
    top    = int(player.y)
    bottom = int(player.y + ph - 0.01)
    cols   = player_cols(player)
    if dy > 0:
        player.on_ground = False
        for c in cols:
            if solid(world, c, bottom):
                player.y = bottom - ph
                player.vy = 0
                player.on_ground = True
                break
    elif dy < 0:
        for c in cols:
            if solid(world, c, top):
                player.y = top + 1
                player.vy = 0
                break


def touching_wall(player, world):
    pw    = PLAYER_W / TILE_SIZE
    left  = int(player.x) - 1
    right = int(player.x + pw - 0.01) + 1
    for r in player_rows(player):
        if solid(world, left, r) or solid(world, right, r):
            return True
    return False


def in_reach(player, col, row):
    pcol = player.x + PLAYER_W / TILE_SIZE / 2
    prow = player.y + PLAYER_H / TILE_SIZE / 2
    dist = ((col - pcol) ** 2 + (row - prow) ** 2) ** 0.5
    return dist <= REACH_RADIUS


def eject_from_blocks(player, world):
    """Éjecte le joueur vers le haut hors de tout bloc solide."""
    ph   = PLAYER_H / TILE_SIZE
    pw   = PLAYER_W / TILE_SIZE
    for _ in range(ROWS):
        top    = int(player.y)
        bottom = int(player.y + ph - 0.01)
        cols   = list(range(int(player.x), int(player.x + pw - 0.01) + 1))
        if not any(solid(world, c, r) for r in range(top, bottom + 1) for c in cols):
            break
        player.y -= 1.0
    player.vy = min(player.vy, 0.0)
