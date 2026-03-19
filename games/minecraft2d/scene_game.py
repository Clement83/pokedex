"""
Scène de jeu principale Minecraft 2D.
Retourne None (quitter) ou True (retour sélection).
"""
import pygame
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from config import *
from world import generate
from quit_combo import QuitCombo
import db as _db


# ── Inventaire ────────────────────────────────────────────────────────────────

class Inventory:
    """5 slots, chacun contient (type_tuile, quantité)."""

    DEFAULT_ITEMS = [
        (TILE_DIRT,  20),
        (TILE_STONE, 10),
        (TILE_WOOD,  10),
        (TILE_SAND,   5),
        (TILE_AIR,    0),   # slot vide
    ]

    def __init__(self):
        self.slots = list(self.DEFAULT_ITEMS)   # [(tile, count), ...]
        self.active = 0

    def selected_tile(self):
        t, c = self.slots[self.active]
        return t if c > 0 else TILE_AIR

    def add(self, tile):
        # Cherche un slot existant du même type
        for i, (t, c) in enumerate(self.slots):
            if t == tile:
                self.slots[i] = (t, c + 1)
                return
        # Cherche un slot vide
        for i, (t, c) in enumerate(self.slots):
            if t == TILE_AIR or c == 0:
                self.slots[i] = (tile, 1)
                return
        # Plus de place : on empile dans le slot actif quand même
        t, c = self.slots[self.active]
        self.slots[self.active] = (t, c + 1)

    def consume(self):
        t, c = self.slots[self.active]
        if c > 0:
            self.slots[self.active] = (t, c - 1)

    def slot_next(self):
        self.active = (self.active + 1) % INVENTORY_SLOTS

    def slot_prev(self):
        self.active = (self.active - 1) % INVENTORY_SLOTS


# ── Joueur ────────────────────────────────────────────────────────────────────

class Player:
    def __init__(self, x, y, color, idx):
        self.x     = float(x)   # position en tuiles (virgule flottante)
        self.y     = float(y)
        self.vx    = 0.0
        self.vy    = 0.0
        self.on_ground = False
        self.on_wall   = False   # collé contre un mur (escalade possible)
        self.color = color
        self.idx   = idx
        self.inventory = Inventory()
        self._action_cd  = 0.0   # cooldown après place/break
        self._break_time = 0.0   # temps accumulé sur le bloc en cours

    # position pixel du coin supérieur gauche
    def px(self): return int(self.x * TILE_SIZE)
    def py(self): return int(self.y * TILE_SIZE)

    # centre en tuiles
    def col(self): return int(self.x + PLAYER_W / TILE_SIZE / 2)
    def row(self): return int(self.y + PLAYER_H / TILE_SIZE / 2)


# ── Utilitaires de collision ───────────────────────────────────────────────────

def _solid(grid, col, row):
    if col < 0 or col >= COLS or row < 0 or row >= ROWS:
        return True
    return grid[row][col] != TILE_AIR


def _move_x(player, grid, dx):
    """Déplace horizontalement avec collision par colonnes."""
    player.x += dx
    pw = PLAYER_W / TILE_SIZE

    left  = int(player.x)
    right = int(player.x + pw - 0.01)
    rows  = _player_rows(player)

    if dx > 0:
        for r in rows:
            if _solid(grid, right, r):
                player.x = right - pw
                player.vx = 0
                break
    elif dx < 0:
        for r in rows:
            if _solid(grid, left, r):
                player.x = left + 1
                player.vx = 0
                break


def _move_y(player, grid, dy):
    """Déplace verticalement avec collision par lignes."""
    player.y += dy
    ph = PLAYER_H / TILE_SIZE

    top    = int(player.y)
    bottom = int(player.y + ph - 0.01)
    cols   = _player_cols(player)

    if dy > 0:
        player.on_ground = False
        for c in cols:
            if _solid(grid, c, bottom):
                player.y = bottom - ph
                player.vy = 0
                player.on_ground = True
                break
    elif dy < 0:
        for c in cols:
            if _solid(grid, c, top):
                player.y = top + 1
                player.vy = 0
                break


def _player_cols(p):
    pw = PLAYER_W / TILE_SIZE
    return list(range(int(p.x), int(p.x + pw - 0.01) + 1))


def _player_rows(p):
    ph = PLAYER_H / TILE_SIZE
    return list(range(int(p.y), int(p.y + ph - 0.01) + 1))


def _touching_wall(player, grid):
    """Vrai si le joueur touche un bloc solide directement à gauche ou à droite."""
    pw = PLAYER_W / TILE_SIZE
    left  = int(player.x) - 1
    right = int(player.x + pw - 0.01) + 1
    rows  = _player_rows(player)
    for r in rows:
        if _solid(grid, left, r) or _solid(grid, right, r):
            return True
    return False


def _in_reach(player, col, row):
    """Vérifie que (col, row) est dans REACH_RADIUS autour du joueur."""
    pcol = player.x + PLAYER_W / TILE_SIZE / 2
    prow = player.y + PLAYER_H / TILE_SIZE / 2
    dist = ((col - pcol) ** 2 + (row - prow) ** 2) ** 0.5
    return dist <= REACH_RADIUS


# ── Lecture des contrôles ─────────────────────────────────────────────────────

def _get_dir_p1(keys, joy):
    if joy:
        try:
            ax = joy.get_axis(0)
            ay = joy.get_axis(1)
            if ax < -AXIS_DEAD: return -1, 0
            if ax >  AXIS_DEAD: return  1, 0
            if ay < -AXIS_DEAD: return  0, -1
            if ay >  AXIS_DEAD: return  0,  1
        except Exception:
            pass
        try:
            hx, hy = joy.get_hat(0)
            if hx != 0 or hy != 0:
                return hx, -hy
        except Exception:
            pass
    dx = dy = 0
    if keys[KB_J1_RIGHT]: dx =  1
    elif keys[KB_J1_LEFT]: dx = -1
    if keys[KB_J1_UP]: dy = -1
    elif keys[KB_J1_DOWN]: dy = 1
    return dx, dy


def _get_dir_p2(keys, joy):
    if joy:
        try:
            ax = joy.get_axis(0) if joy.get_numaxes() > 0 else 0
            ay = joy.get_axis(1) if joy.get_numaxes() > 1 else 0
            if ax < -AXIS_DEAD: return -1, 0
            if ax >  AXIS_DEAD: return  1, 0
            if ay < -AXIS_DEAD: return  0, -1
            if ay >  AXIS_DEAD: return  0,  1
        except Exception:
            pass
        # Boutons ABXY en fallback
        try:
            pressed = {b for b in range(joy.get_numbuttons()) if joy.get_button(b)}
            if BTN_X in pressed: return  1, 0
            if BTN_Y in pressed: return -1, 0
            if BTN_A in pressed: return  0, -1
            if BTN_B in pressed: return  0,  1
        except Exception:
            pass
    dx = dy = 0
    if keys[KB_J2_RIGHT]: dx =  1
    elif keys[KB_J2_LEFT]: dx = -1
    if keys[KB_J2_UP]: dy = -1
    elif keys[KB_J2_DOWN]: dy = 1
    return dx, dy


def _joy_btn(joy, btn):
    try:
        return bool(joy and joy.get_button(btn))
    except Exception:
        return False


# ── Caméra ────────────────────────────────────────────────────────────────────

class Camera:
    """Caméra centrée sur un point donné, en pixels."""
    def __init__(self, view_w=SCREEN_WIDTH, view_h=SCREEN_HEIGHT):
        self.x = 0.0   # coin supérieur gauche (pixels)
        self.y = 0.0
        self.view_w = view_w
        self.view_h = view_h

    def follow(self, target_px, target_py, dt):
        cx = target_px - self.view_w // 2
        cy = target_py - self.view_h // 2
        # Clamp au monde
        max_x = COLS * TILE_SIZE - self.view_w
        max_y = ROWS * TILE_SIZE - self.view_h
        cx = max(0, min(cx, max_x))
        cy = max(0, min(cy, max_y))
        # Interpolation douce
        self.x += (cx - self.x) * min(1.0, 8.0 * dt)
        self.y += (cy - self.y) * min(1.0, 8.0 * dt)

    def world_to_screen(self, wx_px, wy_px):
        return int(wx_px - self.x), int(wy_px - self.y)

    def screen_to_tile(self, sx, sy):
        wx = sx + self.x
        wy = sy + self.y
        return int(wx // TILE_SIZE), int(wy // TILE_SIZE)

    def visible_tile_range(self):
        c0 = max(0, int(self.x // TILE_SIZE))
        r0 = max(0, int(self.y // TILE_SIZE))
        c1 = min(COLS, c0 + self.view_w // TILE_SIZE + 2)
        r1 = min(ROWS, r0 + self.view_h // TILE_SIZE + 2)
        return c0, r0, c1, r1


# ── Curseur de la cible (bloc visé) ───────────────────────────────────────────

def _get_cursor(player, dx, dy):
    """
    Retourne (col, row) du bloc visé à partir de la direction courante.
    Si pas de direction, cible le bloc juste devant.
    """
    pcol = player.x + PLAYER_W / TILE_SIZE / 2
    prow = player.y + PLAYER_H / TILE_SIZE / 2
    if dx == 0 and dy == 0:
        dx = 1   # défaut : regarde à droite
    return int(pcol + dx * 1.5), int(prow + dy * 1.5)


# ── Dessin ────────────────────────────────────────────────────────────────────

def _draw_world(screen, grid, camera, break_info):
    """Dessine uniquement les tuiles visibles (optimization clé)."""
    c0, r0, c1, r1 = camera.visible_tile_range()
    ts = TILE_SIZE

    for row in range(r0, r1):
        for col in range(c0, c1):
            tile = grid[row][col]
            color = TILE_COLORS[tile]
            sx, sy = camera.world_to_screen(col * ts, row * ts)
            pygame.draw.rect(screen, color, (sx, sy, ts, ts))
            if tile != TILE_AIR:
                # Bordure légère pour donner du relief
                pygame.draw.rect(screen, (0, 0, 0, 50), (sx, sy, ts, ts), 1)

    # Barre de cassage
    if break_info:
        col, row, progress = break_info
        sx, sy = camera.world_to_screen(col * ts, row * ts)
        pygame.draw.rect(screen, (0, 0, 0), (sx, sy + ts - 3, ts, 3))
        pygame.draw.rect(screen, BREAK_BAR_COLOR, (sx, sy + ts - 3, int(ts * progress), 3))


# Couleurs du bonhomme
_SKIN   = (255, 210, 160)   # peau
_BLACK  = (  0,   0,   0)
_DARK   = ( 40,  40,  40)   # contour

def _draw_player(screen, player, camera, font):
    px, py = camera.world_to_screen(player.px(), player.py())
    c  = player.color
    # version foncée de la couleur pour les jambes / ombre
    dc = tuple(max(0, v - 55) for v in c)

    # ── Tête (10×10) – au-dessus de la hitbox ─────────────────────────────
    hx, hy = px, py - 10
    pygame.draw.rect(screen, _SKIN,  (hx,     hy,     10, 10))
    pygame.draw.rect(screen, _DARK,  (hx,     hy,     10, 10), 1)
    # Yeux
    pygame.draw.rect(screen, _BLACK, (hx + 2, hy + 3,  2,  2))
    pygame.draw.rect(screen, _BLACK, (hx + 6, hy + 3,  2,  2))
    # Bouche
    pygame.draw.rect(screen, _DARK,  (hx + 3, hy + 7,  4,  1))

    # ── Corps (10×10) – première moitié de la hitbox ──────────────────────
    bx, by = px, py
    pygame.draw.rect(screen, c,    (bx,     by,     10, 10))
    pygame.draw.rect(screen, _DARK,(bx,     by,     10, 10), 1)
    # Boutons / détail
    pygame.draw.rect(screen, dc,   (bx + 3, by + 3,  2,  2))
    pygame.draw.rect(screen, dc,   (bx + 6, by + 3,  2,  2))

    # ── Jambes (4×10 chacune) – deuxième moitié de la hitbox ─────────────
    lx, ly = px, py + 10
    pygame.draw.rect(screen, dc,   (lx,         ly, 4, 10))
    pygame.draw.rect(screen, dc,   (lx + 6,     ly, 4, 10))
    pygame.draw.rect(screen, _DARK,(lx,         ly, 4, 10), 1)
    pygame.draw.rect(screen, _DARK,(lx + 6,     ly, 4, 10), 1)

    # ── Étiquette J1 / J2 ─────────────────────────────────────────────────
    label = font.render("J" + str(player.idx + 1), True, (255, 255, 255))
    lw = label.get_width()
    # fond sombre pour lisibilité
    pygame.draw.rect(screen, (0, 0, 0), (px + (10 - lw) // 2 - 1, hy - 9, lw + 2, 9))
    screen.blit(label, (px + (10 - lw) // 2, hy - 9))


def _draw_cursor(screen, player, col, row, camera):
    sx, sy = camera.world_to_screen(col * TILE_SIZE, row * TILE_SIZE)
    ts = TILE_SIZE
    # Cadre jaune clignotant
    t = pygame.time.get_ticks()
    alpha = 128 + int(127 * abs((t % 600) / 300 - 1))
    s = pygame.Surface((ts, ts), pygame.SRCALPHA)
    s.fill((255, 255, 0, alpha))
    screen.blit(s, (sx, sy))


def _draw_hotbar(screen, inventory, x_offset, color, font):
    """Dessine la hotbar d'un joueur."""
    slot_size = 22
    pad = 3
    total_w = INVENTORY_SLOTS * (slot_size + pad) - pad
    y = HOTBAR_Y

    for i, (tile, count) in enumerate(inventory.slots):
        sx = x_offset + i * (slot_size + pad)
        # Fond
        bg = (60, 60, 60) if i != inventory.active else (180, 160, 20)
        pygame.draw.rect(screen, bg, (sx, y, slot_size, slot_size))
        pygame.draw.rect(screen, color, (sx, y, slot_size, slot_size), 2 if i == inventory.active else 1)

        if tile != TILE_AIR and count > 0:
            tc = TILE_COLORS[tile]
            pygame.draw.rect(screen, tc, (sx + 3, y + 3, slot_size - 6, slot_size - 6))
            cnt_label = font.render(str(count), True, (255, 255, 255))
            screen.blit(cnt_label, (sx + slot_size - cnt_label.get_width() - 1, y + slot_size - cnt_label.get_height()))


# ── Scène principale ──────────────────────────────────────────────────────────

def run(screen, joysticks, world_id, seed):
    """
    Lance la partie.
    world_id : int  1-4  (slot SQLite)
    seed     : int       (seed de génération)
    Retourne True (retour menu) ou None (quitter).
    """
    clock     = pygame.time.Clock()
    quit_combo = QuitCombo()
    font_sm   = pygame.font.SysFont("Arial", 9)
    font_med  = pygame.font.SysFont("Arial", 11, bold=True)

    grid, surface, world_seed = generate(seed)

    # ── Appliquer les modifications sauvegardées ────────────────────────
    saved_blocks = _db.load_blocks(world_id)
    for (col, row), tile in saved_blocks.items():
        if 0 <= row < ROWS and 0 <= col < COLS:
            grid[row][col] = tile
    # Accumulateur de changements à sauvegarder en batch


    # Spawn J1 et J2 côte à côte au centre du monde
    def spawn_x(col): return col - PLAYER_W / TILE_SIZE / 2
    def spawn_y(col): return surface[col] - PLAYER_H / TILE_SIZE - 1

    mid = COLS // 2
    p1_col = mid - 3
    p2_col = mid + 3
    players = [
        Player(spawn_x(p1_col), spawn_y(p1_col), P1_COLOR, 0),
        Player(spawn_x(p2_col), spawn_y(p2_col), P2_COLOR, 1),
    ]

    # Caméra partagée – centrée sur J1 au départ
    HALF_W = SCREEN_WIDTH // 2
    shared_cam = Camera()
    spawn_mid_px = (players[0].px() + players[1].px()) // 2
    spawn_mid_py = (players[0].py() + players[1].py()) // 2
    max_cx = COLS * TILE_SIZE - SCREEN_WIDTH
    max_cy = ROWS * TILE_SIZE - SCREEN_HEIGHT
    shared_cam.x = max(0, min(spawn_mid_px - SCREEN_WIDTH  // 2, max_cx))
    shared_cam.y = max(0, min(spawn_mid_py - SCREEN_HEIGHT // 2, max_cy))

    # ── Split-screen ──────────────────────────────────────────────────────
    split_cams  = [Camera(view_w=HALF_W), Camera(view_w=HALF_W)]
    split_surfs = [
        screen.subsurface(pygame.Rect(0,      0, HALF_W, SCREEN_HEIGHT)),
        screen.subsurface(pygame.Rect(HALF_W, 0, HALF_W, SCREEN_HEIGHT)),
    ]
    SPLIT_DIST   = int(SCREEN_WIDTH * 0.60)   # entrer en split (~288 px)
    UNSPLIT_DIST = int(SCREEN_WIDTH * 0.45)   # revenir en commun (~216 px)
    is_split     = False
    for sc in split_cams:
        sc.x, sc.y = shared_cam.x, shared_cam.y

    joy1 = joysticks[0] if len(joysticks) > 0 else None
    joy2 = joysticks[1] if len(joysticks) > 1 else None

    # Mapping joueur → (joystick, btn_mine, btn_mod, get_dir_fn, kb_mine, kb_mod)
    player_controls = [
        (joy1, J1_BTN_MINE, J1_BTN_MODIFIER, _get_dir_p1, KB_J1_MINE, KB_J1_MODIFIER),
        (joy2, J2_BTN_MINE, J2_BTN_MODIFIER, _get_dir_p2, KB_J2_MINE, KB_J2_MODIFIER),
    ]

    # État inter-frames
    p_dirs      = [(0, 0), (0, 0)]   # dernière direction connue (pour le curseur)
    break_infos = [None, None]        # (col, row, progress) en cours de cassage
    prev_mine   = [False, False]      # état précédent du bouton mine
    prev_dx     = [0, 0]              # pour détecter l'edge gauche/droite en mode modifier

    while True:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        events = pygame.event.get()
        keys   = pygame.key.get_pressed()

        for e in events:
            if e.type == pygame.QUIT:
                return None
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return True
            quit_combo.handle_event(e)

        # ── Mise à jour physique et contrôles ─────────────────────────────
        for i, player in enumerate(players):
            joy, btn_mine, btn_mod, get_dir, kb_mine, kb_mod = player_controls[i]

            dx, dy = get_dir(keys, joy)
            cur_mine = _joy_btn(joy, btn_mine) or bool(keys[kb_mine])
            cur_mod  = _joy_btn(joy, btn_mod)  or bool(keys[kb_mod])

            # ── Mode MODIFIER : tenu + dirs = slot, tenu + MINE = poser ───
            if cur_mod:
                # Navigation inventaire (edge gauche/droite)
                if dx ==  1 and prev_dx[i] !=  1:
                    player.inventory.slot_next()
                elif dx == -1 and prev_dx[i] != -1:
                    player.inventory.slot_prev()
                # Bloquer le déplacement horizontal
                player.vx = 0.0
            else:
                player.vx = dx * WALK_SPEED

            if dx != 0 or dy != 0:
                p_dirs[i] = (dx, dy)
            prev_dx[i] = dx

            # ── Escalade de mur (appuyer haut contre n'importe quel bloc) ────
            player.on_wall = _touching_wall(player, grid)
            climbing = dy < 0 and player.on_wall and not player.on_ground

            if climbing:
                # Annule la gravité, monte à vitesse constante
                player.vy = -CLIMB_SPEED
            else:
                # Saut (direction haut, toujours actif)
                if dy < 0 and player.on_ground:
                    player.vy = JUMP_VEL

                # Gravité
                player.vy = min(player.vy + GRAVITY * dt, MAX_FALL_SPEED)

            # Collisions
            player.on_ground = False
            _move_x(player, grid, player.vx * dt)
            _move_y(player, grid, player.vy * dt)

            if player._action_cd > 0:
                player._action_cd -= dt

            # Curseur cible
            cdx, cdy = p_dirs[i]
            cur_col, cur_row = _get_cursor(player, cdx, cdy)
            cur_col = max(0, min(COLS - 1, cur_col))
            cur_row = max(0, min(ROWS - 1, cur_row))
            in_reach = _in_reach(player, cur_col, cur_row)

            if in_reach and player._action_cd <= 0:
                tile_at = grid[cur_row][cur_col]

                if cur_mod and cur_mine and not prev_mine[i]:
                    # ─ MODIFIER + MINE (edge) = POSER un bloc ────────────
                    if tile_at == TILE_AIR:
                        selected = player.inventory.selected_tile()
                        if selected != TILE_AIR:
                            occupied = any(
                                int(p.x + PLAYER_W / TILE_SIZE / 2) == cur_col and
                                int(p.y + PLAYER_H / TILE_SIZE / 2) == cur_row
                                for p in players
                            )
                            if not occupied:
                                grid[cur_row][cur_col] = selected
                                player.inventory.consume()
                                player._action_cd = 0.2
                                _db.save_block(world_id, cur_col, cur_row, selected)

                elif cur_mine and not cur_mod and tile_at != TILE_AIR:
                    # ─ MINE seul (maintenu) = MINER ──────────────────────
                    if break_infos[i] and break_infos[i][:2] == (cur_col, cur_row):
                        player._break_time += dt
                        req_time = TILE_BREAK_TIME.get(tile_at, 0.5)
                        progress = min(player._break_time / req_time, 1.0)
                        break_infos[i] = (cur_col, cur_row, progress)
                        if player._break_time >= req_time:
                            player.inventory.add(tile_at)
                            grid[cur_row][cur_col] = TILE_AIR
                            break_infos[i] = None
                            player._break_time = 0.0
                            player._action_cd = 0.1
                            _db.save_block(world_id, cur_col, cur_row, TILE_AIR)
                    else:
                        player._break_time = 0.0
                        break_infos[i] = (cur_col, cur_row, 0.0)
                else:
                    break_infos[i] = None
                    player._break_time = 0.0
            else:
                if not cur_mine:
                    break_infos[i] = None
                    player._break_time = 0.0

            prev_mine[i] = cur_mine

        # ── Caméra ─────────────────────────────────────────────────────────
        player_dist = abs(players[0].px() - players[1].px())
        if not is_split and player_dist >= SPLIT_DIST:
            is_split = True
            # Snap immédiat sur chaque joueur pour éviter un saut visuel
            for i, cam in enumerate(split_cams):
                cam.x = max(0, min(players[i].px() - HALF_W       // 2, COLS * TILE_SIZE - HALF_W))
                cam.y = max(0, min(players[i].py() - SCREEN_HEIGHT // 2, ROWS * TILE_SIZE - SCREEN_HEIGHT))
        elif is_split and player_dist <= UNSPLIT_DIST:
            is_split = False
            # Snap shared_cam sur le milieu actuel
            mx = (players[0].px() + players[1].px()) // 2
            my = (players[0].py() + players[1].py()) // 2
            shared_cam.x = max(0, min(mx - SCREEN_WIDTH  // 2, COLS * TILE_SIZE - SCREEN_WIDTH))
            shared_cam.y = max(0, min(my - SCREEN_HEIGHT // 2, ROWS * TILE_SIZE - SCREEN_HEIGHT))

        if is_split:
            for i, cam in enumerate(split_cams):
                cam.follow(players[i].px(), players[i].py(), dt)
        else:
            mid_px = (players[0].px() + players[1].px()) // 2
            mid_py = (players[0].py() + players[1].py()) // 2
            shared_cam.follow(mid_px, mid_py, dt)

        # ── Rendu ──────────────────────────────────────────────────────────
        screen.fill(BG_SKY)

        if is_split:
            slot_size = 22
            pad = 3
            total_w = INVENTORY_SLOTS * (slot_size + pad) - pad

            for i, (surf, cam) in enumerate(zip(split_surfs, split_cams)):
                surf.fill(BG_SKY)
                _draw_world(surf, grid, cam, break_infos[i])

                # Curseurs des deux joueurs dans chaque vue
                for j, player in enumerate(players):
                    cdx, cdy = p_dirs[j]
                    cur_col, cur_row = _get_cursor(player, cdx, cdy)
                    cur_col = max(0, min(COLS - 1, cur_col))
                    cur_row = max(0, min(ROWS - 1, cur_row))
                    if _in_reach(player, cur_col, cur_row):
                        _draw_cursor(surf, player, cur_col, cur_row, cam)

                # Les deux joueurs visibles dans chaque moitié
                for player in players:
                    _draw_player(surf, player, cam, font_sm)

                # Hotbar du joueur propriétaire de cette vue
                player_i = players[i]
                _draw_hotbar(surf, player_i.inventory, 4, player_i.color, font_sm)
                tile = player_i.inventory.selected_tile()
                name = TILE_NAMES.get(tile, "?") if tile != TILE_AIR else "—"
                surf.blit(font_sm.render(name, True, player_i.color), (4, HOTBAR_Y + 24))

            # Séparateur vertical central
            pygame.draw.line(screen, (200, 200, 200), (HALF_W, 0), (HALF_W, SCREEN_HEIGHT), 2)

            # Seed sur la moitié droite
            seed_lbl = font_sm.render("seed:" + str(world_seed), True, (180, 180, 180))
            split_surfs[1].blit(seed_lbl, (HALF_W - seed_lbl.get_width() - 4, SCREEN_HEIGHT - seed_lbl.get_height() - 2))

        else:
            _draw_world(screen, grid, shared_cam, break_infos[0] or break_infos[1])

            for i, player in enumerate(players):
                cdx, cdy = p_dirs[i]
                cur_col, cur_row = _get_cursor(player, cdx, cdy)
                cur_col = max(0, min(COLS - 1, cur_col))
                cur_row = max(0, min(ROWS - 1, cur_row))
                if _in_reach(player, cur_col, cur_row):
                    _draw_cursor(screen, player, cur_col, cur_row, shared_cam)

            for i, player in enumerate(players):
                _draw_player(screen, player, shared_cam, font_sm)

            slot_size = 22
            pad = 3
            total_w = INVENTORY_SLOTS * (slot_size + pad) - pad
            _draw_hotbar(screen, players[0].inventory, 4, P1_COLOR, font_sm)
            _draw_hotbar(screen, players[1].inventory, SCREEN_WIDTH - total_w - 4, P2_COLOR, font_sm)

            for i, (player, cx) in enumerate(zip(players, [4, SCREEN_WIDTH // 2])):
                tile = player.inventory.selected_tile()
                name = TILE_NAMES.get(tile, "?") if tile != TILE_AIR else "—"
                label = font_sm.render(name, True, player.color)
                screen.blit(label, (cx + i * 50, HOTBAR_Y + 24))

            seed_lbl = font_sm.render("seed: " + str(world_seed), True, (180, 180, 180))
            screen.blit(seed_lbl, (SCREEN_WIDTH - seed_lbl.get_width() - 4, SCREEN_HEIGHT - seed_lbl.get_height() - 2))

        # Overlay SELECT+START (dessiné sur l'écran complet, au-dessus de tout)
        if quit_combo.update_and_draw(screen):
            return True

        pygame.display.flip()
