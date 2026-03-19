"""
Scène de jeu principale Minecraft 2D.
Retourne None (quitter) ou True (retour sélection).
"""
import pygame
import sys
import os
from collections import OrderedDict

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

def _solid(world, col, row):
    if row < 0 or row >= ROWS:
        return True
    return world.get(col, row) != TILE_AIR


def _move_x(player, world, dx):
    """Déplace horizontalement avec collision par colonnes."""
    player.x += dx
    pw = PLAYER_W / TILE_SIZE

    left  = int(player.x)
    right = int(player.x + pw - 0.01)
    rows  = _player_rows(player)

    if dx > 0:
        for r in rows:
            if _solid(world, right, r):
                player.x = right - pw
                player.vx = 0
                break
    elif dx < 0:
        for r in rows:
            if _solid(world, left, r):
                player.x = left + 1
                player.vx = 0
                break


def _move_y(player, world, dy):
    """Déplace verticalement avec collision par lignes."""
    player.y += dy
    ph = PLAYER_H / TILE_SIZE

    top    = int(player.y)
    bottom = int(player.y + ph - 0.01)
    cols   = _player_cols(player)

    if dy > 0:
        player.on_ground = False
        for c in cols:
            if _solid(world, c, bottom):
                player.y = bottom - ph
                player.vy = 0
                player.on_ground = True
                break
    elif dy < 0:
        for c in cols:
            if _solid(world, c, top):
                player.y = top + 1
                player.vy = 0
                break


def _player_cols(p):
    pw = PLAYER_W / TILE_SIZE
    return list(range(int(p.x), int(p.x + pw - 0.01) + 1))


def _player_rows(p):
    ph = PLAYER_H / TILE_SIZE
    return list(range(int(p.y), int(p.y + ph - 0.01) + 1))


def _touching_wall(player, world):
    """Vrai si le joueur touche un bloc solide directement à gauche ou à droite."""
    pw = PLAYER_W / TILE_SIZE
    left  = int(player.x) - 1
    right = int(player.x + pw - 0.01) + 1
    rows  = _player_rows(player)
    for r in rows:
        if _solid(world, left, r) or _solid(world, right, r):
            return True
    return False


def _in_reach(player, col, row):
    """Vérifie que (col, row) est dans REACH_RADIUS autour du joueur."""
    pcol = player.x + PLAYER_W / TILE_SIZE / 2
    prow = player.y + PLAYER_H / TILE_SIZE / 2
    dist = ((col - pcol) ** 2 + (row - prow) ** 2) ** 0.5
    return dist <= REACH_RADIUS


def _eject_from_blocks(player, world):
    """
    Si le joueur chevauche un bloc solide, l'éjecte vers le haut case par case
    jusqu'à trouver un espace libre sur PLAYER_H tuiles.
    Appelé au spawn et après qu'un bloc soit posé.
    """
    ph    = PLAYER_H / TILE_SIZE
    pw    = PLAYER_W / TILE_SIZE
    max_up = ROWS   # sécurité anti-boucle infinie
    for _ in range(max_up):
        top    = int(player.y)
        bottom = int(player.y + ph - 0.01)
        cols   = list(range(int(player.x), int(player.x + pw - 0.01) + 1))
        overlap = any(_solid(world, c, r) for r in range(top, bottom + 1) for c in cols)
        if not overlap:
            break
        player.y -= 1.0
    player.vy = min(player.vy, 0.0)   # annule la vitesse vers le bas


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
            if BTN_A in pressed: return  1, 0
            if BTN_Y in pressed: return -1, 0
            if BTN_X in pressed: return  0, -1
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
        # Clamp vertical uniquement (monde infini horizontalement)
        max_y = ROWS * TILE_SIZE - self.view_h
        cx = max(0, cx)
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
        c0 = int(self.x // TILE_SIZE)
        r0 = max(0, int(self.y // TILE_SIZE))
        c1 = c0 + self.view_w // TILE_SIZE + 2
        r1 = min(ROWS, r0 + self.view_h // TILE_SIZE + 2)
        return c0, r0, c1, r1


# ── Curseur de la cible (bloc visé) ───────────────────────────────────────────

def _get_cursor(player, dx, dy):
    """
    Retourne (col, row) du bloc visé à partir de la direction courante.
    Cible toujours la tuile immédiatement adjacente au bord du joueur (max 1 case).
    Si pas de direction, cible le bloc juste à droite.
    """
    pw = PLAYER_W / TILE_SIZE
    ph = PLAYER_H / TILE_SIZE
    if dx == 0 and dy == 0:
        dx = 1   # défaut : regarde à droite

    # Horizontal : tuile collée au bord gauche ou droit du joueur
    if dx > 0:
        col = int(player.x + pw - 0.01) + 1   # 1 case à droite du bord droit
    elif dx < 0:
        col = int(player.x) - 1               # 1 case à gauche du bord gauche
    else:
        col = int(player.x + pw / 2)          # colonne centrale

    # Vertical : tuile collée au bord haut ou bas du joueur
    if dy > 0:
        row = int(player.y + ph - 0.01) + 1   # 1 case sous le bas du joueur
    elif dy < 0:
        row = int(player.y) - 1               # 1 case au-dessus de la tête
    else:
        row = int(player.y + ph / 2)          # rangée centrale

    return col, row


# ── Cache de chunks ──────────────────────────────────────────────────────────
#
# Principe : chaque chunk est une Surface pré-rendue (CHUNK_W × CHUNK_H px).
# Par frame : 2-3 Surface.blit() au lieu de ~600 draw.rect() Python.
# Invalidation ponctuelle quand un joueur mine ou pose un bloc.

CHUNK_COLS = 30                          # colonnes par chunk = 1 écran
_CHUNK_W   = CHUNK_COLS * TILE_SIZE      # 480 px
_CHUNK_H   = ROWS       * TILE_SIZE      # 960 px


class ChunkCache:
    _MAX_CHUNKS = 8   # ~8 × 480×960 px = ~30 MB VRAM max

    def __init__(self, world):
        self._world = world
        self._cache = OrderedDict()   # LRU : clé → Surface

    def _build(self, cx):
        surf = pygame.Surface((_CHUNK_W, _CHUNK_H))
        ts   = TILE_SIZE
        col0 = cx * CHUNK_COLS
        for row in range(ROWS):
            for dc in range(CHUNK_COLS):
                col   = col0 + dc
                tile  = self._world.get(col, row)
                color = TILE_COLORS[tile]
                x = dc * ts
                y = row * ts
                surf.fill(color, (x, y, ts, ts))
                if tile != TILE_AIR:
                    pygame.draw.rect(surf, (0, 0, 0), (x, y, ts, ts), 1)
        # Éviction LRU si cache plein
        if len(self._cache) >= self._MAX_CHUNKS:
            self._cache.popitem(last=False)
        self._cache[cx] = surf
        return surf

    def get(self, cx):
        if cx in self._cache:
            self._cache.move_to_end(cx)   # marquer comme récemment utilisé
            return self._cache[cx]
        return self._build(cx)

    def invalidate(self, col):
        """Invalide le chunk contenant la colonne col."""
        self._cache.pop(col // CHUNK_COLS, None)

    def preload_around(self, cam_x, view_w):
        """Pré-rend les chunks visibles + 1 d'avance de chaque côté."""
        cx0 = int(cam_x)          // _CHUNK_W - 1
        cx1 = (int(cam_x) + view_w) // _CHUNK_W + 1
        for cx in range(cx0, cx1 + 1):
            if cx not in self._cache:
                self._build(cx)


# ── Dessin ────────────────────────────────────────────────────────────────────

def _draw_world(screen, chunks, camera, break_info):
    """Rendu via cache de chunks : 2-3 blit() par frame."""
    w      = screen.get_width()
    ts     = TILE_SIZE
    cam_x  = int(camera.x)
    cam_y  = max(0, min(int(camera.y), _CHUNK_H - SCREEN_HEIGHT))

    cx0 = cam_x // _CHUNK_W
    cx1 = (cam_x + w - 1) // _CHUNK_W

    for cx in range(cx0, cx1 + 1):
        surf   = chunks.get(cx)
        dest_x = cx * _CHUNK_W - cam_x
        screen.blit(surf, (dest_x, 0), (0, cam_y, _CHUNK_W, SCREEN_HEIGHT))

    # Barre de cassage (dessinée par-dessus, pas dans le cache)
    if break_info:
        col, row, progress = break_info
        sx, sy = camera.world_to_screen(col * ts, row * ts)
        pygame.draw.rect(screen, (0, 0, 0),        (sx, sy + ts - 3, ts, 3))
        pygame.draw.rect(screen, BREAK_BAR_COLOR,  (sx, sy + ts - 3, int(ts * progress), 3))


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


_CURSOR_SURF = None   # Surface pré-allouée, créée au premier appel

def _draw_cursor(screen, player, col, row, camera):
    global _CURSOR_SURF
    sx, sy = camera.world_to_screen(col * TILE_SIZE, row * TILE_SIZE)
    ts = TILE_SIZE
    if _CURSOR_SURF is None:
        _CURSOR_SURF = pygame.Surface((ts, ts))
        _CURSOR_SURF.fill((255, 255, 0))
    t = pygame.time.get_ticks()
    alpha = 128 + int(127 * abs((t % 600) / 300 - 1))
    _CURSOR_SURF.set_alpha(alpha)
    screen.blit(_CURSOR_SURF, (sx, sy))


_hotbar_label_cache = {}   # {(count, color): Surface}

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
            key = (count, color)
            cnt_label = _hotbar_label_cache.get(key)
            if cnt_label is None:
                cnt_label = font.render(str(count), True, (255, 255, 255))
                _hotbar_label_cache[key] = cnt_label
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

    world      = generate(seed)
    world_seed = world.seed
    world.mods.update(_db.load_blocks(world_id))

    chunks = ChunkCache(world)

    # ── Batch SQLite ──────────────────────────────────────────────────────
    _pending_saves  = {}   # {(col, row): tile}  – mods non encore flushées
    _last_flush     = [0.0]
    _FLUSH_INTERVAL = 2.0   # secondes

    def _queue_block(col, row, tile):
        _pending_saves[(col, row)] = tile

    def _flush_blocks():
        if _pending_saves:
            _db.save_blocks_batch(world_id, [(c, r, t) for (c, r), t in _pending_saves.items()])
            _pending_saves.clear()


    # Spawn J1 et J2 côte à côte au centre du monde
    def spawn_x(col): return col - PLAYER_W / TILE_SIZE / 2
    def spawn_y(col): return world.surface_at(col) - PLAYER_H / TILE_SIZE - 1

    mid = 1_000_000   # spawn loin dans les positifs : pas de limite atteignable
    p1_col = mid - 3
    p2_col = mid + 3
    players = [
        Player(spawn_x(p1_col), spawn_y(p1_col), P1_COLOR, 0),
        Player(spawn_x(p2_col), spawn_y(p2_col), P2_COLOR, 1),
    ]
    # S'assurer qu'aucun joueur ne spawn dans un bloc (arbre, terrain irrégulier…)
    for p in players:
        _eject_from_blocks(p, world)

    # Caméra partagée – centrée sur J1 au départ
    HALF_W = SCREEN_WIDTH // 2
    shared_cam = Camera()
    spawn_mid_px = (players[0].px() + players[1].px()) // 2
    spawn_mid_py = (players[0].py() + players[1].py()) // 2
    max_cy = ROWS * TILE_SIZE - SCREEN_HEIGHT
    shared_cam.x = max(0, spawn_mid_px - SCREEN_WIDTH  // 2)
    shared_cam.y = max(0, min(spawn_mid_py - SCREEN_HEIGHT // 2, max_cy))

    # Pré-charger les chunks autour du spawn (3 au minimum)
    chunks.preload_around(shared_cam.x, SCREEN_WIDTH)

    # ── Split-screen ──────────────────────────────────────────────────────
    split_cams  = [Camera(view_w=HALF_W), Camera(view_w=HALF_W)]
    split_surfs = [
        screen.subsurface(pygame.Rect(0,      0, HALF_W, SCREEN_HEIGHT)),
        screen.subsurface(pygame.Rect(HALF_W, 0, HALF_W, SCREEN_HEIGHT)),
    ]
    SPLIT_DIST   = int(SCREEN_HEIGHT * 0.55)   # entrer en split (~176 px) – valide pour X et Y
    UNSPLIT_DIST = int(SCREEN_HEIGHT * 0.40)   # revenir en commun (~128 px)
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
        _last_flush[0] += dt
        if _last_flush[0] >= _FLUSH_INTERVAL:
            _flush_blocks()
            _last_flush[0] = 0.0

        events = pygame.event.get()
        keys   = pygame.key.get_pressed()

        for e in events:
            if e.type == pygame.QUIT:
                _flush_blocks()
                return None
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                _flush_blocks()
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
            player.on_wall = _touching_wall(player, world)
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
            _move_x(player, world, player.vx * dt)
            _move_y(player, world, player.vy * dt)

            if player._action_cd > 0:
                player._action_cd -= dt

            # Curseur cible
            cdx, cdy = p_dirs[i]
            cur_col, cur_row = _get_cursor(player, cdx, cdy)
            cur_row = max(0, min(ROWS - 1, cur_row))
            in_reach = _in_reach(player, cur_col, cur_row)

            if in_reach and player._action_cd <= 0:
                tile_at = world.get(cur_col, cur_row)

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
                                world.set(cur_col, cur_row, selected)
                                chunks.invalidate(cur_col)
                                # Éjecter un joueur si le bloc a été posé sur lui
                                for p in players:
                                    _eject_from_blocks(p, world)
                                player.inventory.consume()
                                player._action_cd = 0.2
                                _queue_block(cur_col, cur_row, selected)

                elif cur_mine and not cur_mod and tile_at != TILE_AIR:
                    # ─ MINE seul (maintenu) = MINER ──────────────────────
                    if break_infos[i] and break_infos[i][:2] == (cur_col, cur_row):
                        player._break_time += dt
                        req_time = TILE_BREAK_TIME.get(tile_at, 0.5)
                        progress = min(player._break_time / req_time, 1.0)
                        break_infos[i] = (cur_col, cur_row, progress)
                        if player._break_time >= req_time:
                            player.inventory.add(tile_at)
                            world.set(cur_col, cur_row, TILE_AIR)
                            chunks.invalidate(cur_col)
                            break_infos[i] = None
                            player._break_time = 0.0
                            player._action_cd = 0.1
                            _queue_block(cur_col, cur_row, TILE_AIR)
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
        dx_dist = abs(players[0].px() - players[1].px())
        dy_dist = abs(players[0].py() - players[1].py())
        player_dist = max(dx_dist, dy_dist)   # split si trop loin en X OU en Y
        if not is_split and player_dist >= SPLIT_DIST:
            is_split = True
            # Snap immédiat sur chaque joueur pour éviter un saut visuel
            for i, cam in enumerate(split_cams):
                cam.x = max(0, players[i].px() - HALF_W       // 2)
                cam.y = max(0, min(players[i].py() - SCREEN_HEIGHT // 2, ROWS * TILE_SIZE - SCREEN_HEIGHT))
        elif is_split and player_dist <= UNSPLIT_DIST:
            is_split = False
            # Snap shared_cam sur le milieu actuel
            mx = (players[0].px() + players[1].px()) // 2
            my = (players[0].py() + players[1].py()) // 2
            shared_cam.x = max(0, mx - SCREEN_WIDTH  // 2)
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
                chunks.preload_around(cam.x, HALF_W)
                _draw_world(surf, chunks, cam, break_infos[i])

                # Curseurs des deux joueurs dans chaque vue
                for j, player in enumerate(players):
                    cdx, cdy = p_dirs[j]
                    cur_col, cur_row = _get_cursor(player, cdx, cdy)
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
            chunks.preload_around(shared_cam.x, SCREEN_WIDTH)
            _draw_world(screen, chunks, shared_cam, break_infos[0] or break_infos[1])

            for i, player in enumerate(players):
                cdx, cdy = p_dirs[i]
                cur_col, cur_row = _get_cursor(player, cdx, cdy)
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
            _flush_blocks()
            return True

        pygame.display.flip()
