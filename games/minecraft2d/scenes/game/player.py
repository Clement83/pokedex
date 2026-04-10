"""
Classe Player et utilitaires de collision / physique du joueur.
"""
from config import (
    TILE_SIZE, PLAYER_W, PLAYER_H, ROWS,
    GRAVITY, MAX_FALL_SPEED, JUMP_VEL, WALK_SPEED, CLIMB_SPEED,
    REACH_RADIUS, TILE_AIR, TILE_ICE, TILE_LAVA, TILE_WATER, TILE_PORTAL,
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
        self.dark_color = tuple(max(0, v - 55) for v in color)
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
    t = world.get(col, row)
    return t != TILE_AIR and t != TILE_LAVA and t != TILE_WATER and t != TILE_PORTAL


def in_lava(player, world):
    """Retourne True si le joueur touche de la lave."""
    for c in player_cols(player):
        for r in player_rows(player):
            if world.get(c, r) == TILE_LAVA:
                return True
    return False


def in_water(player, world):
    """Retourne True si le joueur touche de l'eau."""
    for c in player_cols(player):
        for r in player_rows(player):
            if world.get(c, r) == TILE_WATER:
                return True
    return False


def in_portal(player, world):
    """Retourne True si le joueur touche un portail actif."""
    for c in player_cols(player):
        for r in player_rows(player):
            if world.get(c, r) == TILE_PORTAL:
                return True
    return False


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


def on_ice(player, world):
    """Retourne True si le joueur est debout sur de la glace."""
    if not player.on_ground:
        return False
    ph = PLAYER_H / TILE_SIZE
    foot_row = int(player.y + ph - 0.01) + 1
    for c in player_cols(player):
        if world.get(c, foot_row) == TILE_ICE:
            return True
    return False


def armor_bonuses(player):
    """Retourne (bonus_hp, bonus_dmg, bonus_speed) des armures améliorées portées."""
    from config import EQUIP_HEAD, EQUIP_BODY, EQUIP_FEET, VITAL_TILES, FORCE_TILES, SWIFT_TILES
    hp = dmg = 0
    spd = 0.0
    head = player.inventory.worn_tile(EQUIP_HEAD)
    if head in VITAL_TILES:
        hp += 2
    body = player.inventory.worn_tile(EQUIP_BODY)
    if body in FORCE_TILES:
        dmg += 1
    feet = player.inventory.worn_tile(EQUIP_FEET)
    if feet in SWIFT_TILES:
        spd += 1.5
    return hp, dmg, spd


# Alias pour compatibilité
crystal_bonuses = armor_bonuses


def effective_max_hp(player):
    """Max HP effectif = base + bonus casque amélioré."""
    return player.max_hp + armor_bonuses(player)[0]


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
