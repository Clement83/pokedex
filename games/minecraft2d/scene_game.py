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
import sounds as _sounds
import mobs as _mobs
import music_player as _music

# Tuiles qui donnent un bonus de ressources quand cassées (coffres)
_CHEST_LOOT = [TILE_WOOD, TILE_STONE, TILE_BRICK, TILE_COAL, TILE_OBSIDIAN]


# ── Cycle jour / nuit ─────────────────────────────────────────────────────────
#
# _day_time ∈ [0, 1)   0.00 = aube   0.15 = plein jour   0.65 = crépuscule
#                       0.73 = nuit   0.95 = nuit         1.00 = aube (boucle)
#
DAY_CYCLE_DURATION = 300.0   # secondes pour un cycle complet (5 min)

_SKY_KEYFRAMES = [
    (0.00, (220, 130,  80)),   # aube  – orange rosé
    (0.12, (100, 160, 220)),   # jour  – bleu ciel
    (0.62, (100, 160, 220)),   # fin jour
    (0.70, (200,  75,  35)),   # crépuscule orange
    (0.75, ( 30,  15,  55)),   # tombée de nuit
    (0.95, ( 20,  10,  40)),   # nuit profonde
    (1.00, (220, 130,  80)),   # retour aube
]

def _lerp3(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def _sky_color(t):
    for i in range(len(_SKY_KEYFRAMES) - 1):
        t0, c0 = _SKY_KEYFRAMES[i]
        t1, c1 = _SKY_KEYFRAMES[i + 1]
        if t0 <= t <= t1:
            tl = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
            return _lerp3(c0, c1, tl)
    return _SKY_KEYFRAMES[0][1]

def _night_alpha(t):
    """Opacité de l'overlay nuit [0–150]."""
    if   0.70 <= t < 0.75: return int(150 * (t - 0.70) / 0.05)
    elif 0.75 <= t < 0.95: return 150
    elif 0.95 <= t < 1.00: return int(150 * (1.00 - t) / 0.05)
    return 0

def _is_night(t):
    return t >= 0.68

_night_overlay = None   # Surface pré-allouée


def _draw_sky_hud(screen, t, font):
    """Petit indicateur soleil/lune + heure en haut au centre."""
    import math as _m
    cx = SCREEN_WIDTH // 2
    cy = 7
    is_n = _is_night(t)
    if not is_n:
        # Soleil jaune
        pygame.draw.circle(screen, (255, 220,  20), (cx, cy), 5)
        pygame.draw.circle(screen, (255, 255, 120), (cx, cy), 3)
    else:
        # Lune blanche + croissant (cercle sombre décalé)
        pygame.draw.circle(screen, (220, 220, 200), (cx, cy), 5)
        pygame.draw.circle(screen, ( 25,  12,  48), (cx + 2, cy - 1), 4)

class Inventory:
    """
    Inventaire à 5 slots :
      slot 0 – outil       : Main, Pioche, Canon, Épée (si trouvée)
      slot 1 – ressources  : blocs récoltés (liste dynamique)
      slot 2 – tête        : liste de casques trouvés [(slot, mat), ...]
      slot 3 – corps       : liste de plastrons trouvés
      slot 4 – pieds       : liste de bottes trouvées

    Contrôles (MODIFIER tenu) :
      ← / →  → naviguer entre les slots 0-4
      ↑ / ↓  → changer l'item actif du slot courant
    """
    SLOT_TOOL  = 0
    SLOT_RES   = 1
    SLOT_HEAD  = 2
    SLOT_BODY  = 3
    SLOT_FEET  = 4
    NUM_SLOTS  = 5

    EQUIP_SLOT_MAP = {SLOT_HEAD: EQUIP_HEAD, SLOT_BODY: EQUIP_BODY,
                      SLOT_FEET: EQUIP_FEET}

    def __init__(self):
        self.active_slot  = 0           # slot mis en évidence
        self.tool         = TOOL_HAND
        self.resources    = []          # [(tile, count), ...]
        self.resource_idx = 0
        self.swords     = []    # matériaux d'épées trouvées [MAT_WOOD, MAT_IRON, ...]
        self.sword_idx  = 0     # index de l'épée active
        self.pickaxes   = []    # matériaux de pioches trouvées
        self.pickaxe_idx = 0    # index de la pioche active
        # équipements : listes de (equip_slot, material)
        self.equip = {
            EQUIP_HEAD:  [],   # ex. [(EQUIP_HEAD, MAT_WOOD), (EQUIP_HEAD, MAT_IRON)]
            EQUIP_BODY:  [],
            EQUIP_FEET:  [],
        }
        self.equip_idx = {EQUIP_HEAD: 0, EQUIP_BODY: 0, EQUIP_FEET: 0}

    @property
    def sword_mat(self):
        """Matériau de l'épée active, ou None."""
        return self.swords[self.sword_idx] if self.swords else None

    @property
    def pickaxe_mat(self):
        """Matériau de la pioche active, ou None (pioche par défaut)."""
        return self.pickaxes[self.pickaxe_idx] if self.pickaxes else None

    # ── Équipement porté ──────────────────────────────────────────────────────
    def worn_equip(self, equip_slot):
        """Retourne (equip_slot, material) actuellement porté ou None."""
        lst = self.equip[equip_slot]
        if not lst:
            return None
        return lst[self.equip_idx[equip_slot]]

    # ── Ajouter un équipement au bon slot ─────────────────────────────────────
    def add_equip(self, item):
        """item = (equip_slot, material)."""
        eslot, mat = item
        if eslot == EQUIP_SWORD:
            if mat not in self.swords:
                self.swords.append(mat)
        elif eslot == EQUIP_PICKAXE:
            if mat not in self.pickaxes:
                self.pickaxes.append(mat)
        else:
            if item not in self.equip[eslot]:
                self.equip[eslot].append(item)

    # ── Retirer l'équipement actif d'un slot (drop) ───────────────────────────
    def drop_equip(self, equip_slot):
        lst = self.equip[equip_slot]
        if not lst:
            return None
        idx  = self.equip_idx[equip_slot]
        item = lst.pop(idx)
        self.equip_idx[equip_slot] = max(0, min(idx, len(lst) - 1))
        return item

    # ── Tuile à poser (pistolet) ──────────────────────────────────────────────
    def selected_tile(self):
        if not self.resources:
            return TILE_AIR
        tile, count = self.resources[self.resource_idx]
        return tile if count > 0 else TILE_AIR

    # ── Ajouter une ressource ─────────────────────────────────────────────────
    def add(self, tile):
        for i, (t, c) in enumerate(self.resources):
            if t == tile:
                self.resources[i] = (t, c + 1)
                return
        self.resources.append((tile, 1))

    # ── Consommer une ressource ───────────────────────────────────────────────
    def consume(self):
        if not self.resources:
            return
        t, c = self.resources[self.resource_idx]
        if c <= 0:
            return
        if c == 1:
            self.resources.pop(self.resource_idx)
            self.resource_idx = max(0, min(self.resource_idx, len(self.resources) - 1))
        else:
            self.resources[self.resource_idx] = (t, c - 1)

    # ── Navigation ←/→ entre slots ───────────────────────────────────────────
    def slot_next(self):
        self.active_slot = (self.active_slot + 1) % self.NUM_SLOTS

    def slot_prev(self):
        self.active_slot = (self.active_slot - 1) % self.NUM_SLOTS

    # ── Navigation ↑/↓ dans le slot actif ────────────────────────────────────
    def _tool_items(self):
        """Liste plate des items du slot outil."""
        # Pioche : sans matériau si aucune trouvée, sinon tuples (TOOL_PICKAXE, mat)
        if self.pickaxes:
            items = [TOOL_HAND] + [(TOOL_PICKAXE, m) for m in self.pickaxes] + [TOOL_PLACER]
        else:
            items = [TOOL_HAND, TOOL_PICKAXE, TOOL_PLACER]
        for mat in self.swords:
            items.append((TOOL_SWORD, mat))
        items.append(TOOL_FLAG)   # drapeau : toujours disponible
        return items

    def _active_tool_idx(self):
        items = self._tool_items()
        if self.tool == TOOL_SWORD and self.swords:
            target = (TOOL_SWORD, self.swords[self.sword_idx])
        elif self.tool == TOOL_PICKAXE and self.pickaxes:
            target = (TOOL_PICKAXE, self.pickaxes[self.pickaxe_idx])
        else:
            target = self.tool
        try:
            return items.index(target)
        except ValueError:
            return 0

    def _apply_tool_item(self, item):
        if isinstance(item, tuple):
            if item[0] == TOOL_SWORD:
                self.tool = TOOL_SWORD
                self.sword_idx = self.swords.index(item[1])
            elif item[0] == TOOL_PICKAXE:
                self.tool = TOOL_PICKAXE
                self.pickaxe_idx = self.pickaxes.index(item[1])
        else:
            self.tool = item

    def item_next(self):
        s = self.active_slot
        if s == self.SLOT_TOOL:
            items = self._tool_items()
            self._apply_tool_item(items[(self._active_tool_idx() + 1) % len(items)])
        elif s == self.SLOT_RES and len(self.resources) > 1:
            self.resource_idx = (self.resource_idx + 1) % len(self.resources)
        elif s in self.EQUIP_SLOT_MAP:
            eslot = self.EQUIP_SLOT_MAP[s]
            lst   = self.equip[eslot]
            if len(lst) > 1:
                self.equip_idx[eslot] = (self.equip_idx[eslot] + 1) % len(lst)

    def item_prev(self):
        s = self.active_slot
        if s == self.SLOT_TOOL:
            items = self._tool_items()
            self._apply_tool_item(items[(self._active_tool_idx() - 1) % len(items)])
        elif s == self.SLOT_RES and len(self.resources) > 1:
            self.resource_idx = (self.resource_idx - 1) % len(self.resources)
        elif s in self.EQUIP_SLOT_MAP:
            eslot = self.EQUIP_SLOT_MAP[s]
            lst   = self.equip[eslot]
            if len(lst) > 1:
                self.equip_idx[eslot] = (self.equip_idx[eslot] - 1) % len(lst)


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
        self.max_hp  = 6         # 3 cœurs = 6 demi-cœurs
        self.hp      = 6
        self._dmg_flash = 0.0    # durée restante du flash rouge (s)

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
        try:
            if joy.get_button(J1_BTN_UP):    return  0, -1
            if joy.get_button(J1_BTN_DOWN):  return  0,  1
            if joy.get_button(J1_BTN_LEFT):  return -1,  0
            if joy.get_button(J1_BTN_RIGHT): return  1,  0
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
        # Boutons YXBA uniquement (même manette que J1, joystick réservé à J1)
        # Accumulation des deux axes pour permettre les diagonales
        try:
            pressed = {b for b in range(joy.get_numbuttons()) if joy.get_button(b)}
            dx = dy = 0
            if BTN_B in pressed: dx =  1   # B = droite
            if BTN_Y in pressed: dx = -1   # Y = gauche
            if BTN_X in pressed: dy = -1   # X = haut / saut
            if BTN_A in pressed: dy =  1   # A = bas
            if dx != 0 or dy != 0:
                return dx, dy
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

def _get_cursor(player, dx, dy, world=None):
    """
    Retourne (col, row) du bloc visé à partir de la direction courante.
    En horizontal sans direction verticale :
      - cible en priorité le bloc au niveau des pieds (bas du corps)
      - si ce bloc est de l'air, remonte d'une rangée (niveau tête)
    """
    pw = PLAYER_W / TILE_SIZE
    ph = PLAYER_H / TILE_SIZE
    if dx == 0 and dy == 0:
        dx = 1   # défaut : regarde à droite

    # Horizontal : tuile collée au bord gauche ou droit du joueur
    if dx > 0:
        col = int(player.x + pw - 0.01) + 1
    elif dx < 0:
        col = int(player.x) - 1
    else:
        col = int(player.x + pw / 2)

    # Vertical
    if dy > 0:
        row = int(player.y + ph - 0.01) + 1   # 1 case sous le bas du joueur
    elif dy < 0:
        row = int(player.y) - 1               # 1 case au-dessus de la tête
    else:
        # Mouvement horizontal pur : pieds d'abord, puis tête si pieds = air
        feet_row = int(player.y + ph - 0.01)
        if world is None or world.get(col, feet_row) != TILE_AIR:
            row = feet_row
        else:
            row = feet_row - 1   # remonte au niveau de la tête

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
                x = dc * ts
                y = row * ts
                if tile == TILE_CHEST:
                    _draw_chest_tile(surf, x, y)
                else:
                    color = TILE_COLORS[tile]
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

# Coffre pixel-art 16×16 ──────────────────────────────────────────────────────
_C_BK  = ( 30,  15,   5)   # contour sombre
_C_GD  = (215, 165,   5)   # or (cadre / bande)
_C_BR  = (115,  65,  20)   # brun corps
_C_WH  = (220, 205, 175)   # reflet clair


def _draw_chest_tile(surf, x, y):
    """Dessine un coffre pixel-art sur la surface surf à (x, y), taille 16×16."""
    dr = surf.fill   # alias raccourci

    # ── Fond brun ───────────────────────────────────────────────────────
    dr(_C_BR,  (x,     y,     16, 16))

    # ── Cadre or 1 px intérieur + contour noir ───────────────────────────
    pygame.draw.rect(surf, _C_BK, (x,   y,   16, 16), 1)
    pygame.draw.rect(surf, _C_GD, (x+1, y+1, 14, 14), 1)

    # ── Bande horizontale séparant couvercle et corps (y+6, 1px) ────────
    dr(_C_GD,  (x+1,  y+6,  14,  1))

    # ── Serrure centrée sur la bande : 3×3 px ────────────────────────────
    lx = x + 7   # centre horizontal
    dr(_C_BK,  (lx,   y+5,   3,   3))   # fond sombre
    dr(_C_GD,  (lx,   y+5,   3,   1))   # haut de la serrure (=bande or)
    dr(_C_WH,  (lx+1, y+6,   1,   1))   # reflet centre

    # ── Reflets couvercle (haut-gauche) ──────────────────────────────────
    dr(_C_WH,  (x+3,  y+2,   4,   1))
    dr(_C_WH,  (x+3,  y+3,   1,   2))

    # ── Reflets corps (haut-gauche du corps) ─────────────────────────────
    dr(_C_WH,  (x+3,  y+8,   4,   1))
    dr(_C_WH,  (x+3,  y+9,   1,   2))

    # ── Pieds (deux petits blocs or en bas) ──────────────────────────────
    dr(_C_GD,  (x+2,  y+14,  2,   1))
    dr(_C_GD,  (x+12, y+14,  2,   1))

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
    dc = tuple(max(0, v - 55) for v in c)

    inv = player.inventory

    # ── Équipements portés ────────────────────────────────────────────────────
    head_item  = inv.worn_equip(EQUIP_HEAD)
    body_item  = inv.worn_equip(EQUIP_BODY)
    feet_item  = inv.worn_equip(EQUIP_FEET)
    head_color = MAT_COLORS[head_item[1]] if head_item else None
    body_color = MAT_COLORS[body_item[1]] if body_item else None
    feet_color = MAT_COLORS[feet_item[1]] if feet_item else None

    # ── Tête (10×10) – au-dessus de la hitbox ─────────────────────────────
    hx, hy = px, py - 10
    pygame.draw.rect(screen, _SKIN,  (hx,     hy,     10, 10))
    pygame.draw.rect(screen, _DARK,  (hx,     hy,     10, 10), 1)
    # Yeux
    pygame.draw.rect(screen, _BLACK, (hx + 2, hy + 3,  2,  2))
    pygame.draw.rect(screen, _BLACK, (hx + 6, hy + 3,  2,  2))
    # Bouche
    pygame.draw.rect(screen, _DARK,  (hx + 3, hy + 7,  4,  1))
    # Casque : bande colorée sur le haut de la tête
    if head_color:
        pygame.draw.rect(screen, head_color, (hx,     hy,     10,  3))
        pygame.draw.rect(screen, head_color, (hx - 1, hy,      1, 10))
        pygame.draw.rect(screen, head_color, (hx + 10,hy,      1, 10))
        pygame.draw.rect(screen, _DARK,      (hx,     hy,     10,  3), 1)

    # ── Corps (10×10) – première moitié de la hitbox ──────────────────────
    bx, by = px, py
    body_c = body_color if body_color else c
    pygame.draw.rect(screen, body_c,  (bx,     by,     10, 10))
    pygame.draw.rect(screen, _DARK,   (bx,     by,     10, 10), 1)
    # Détail boutons sur le plastron
    detail_c = dc if not body_color else tuple(max(0, v - 40) for v in body_color)
    pygame.draw.rect(screen, detail_c, (bx + 3, by + 3,  2,  2))
    pygame.draw.rect(screen, detail_c, (bx + 6, by + 3,  2,  2))
    # Ligne centrale plastron
    if body_color:
        pygame.draw.rect(screen, _DARK, (bx + 4, by + 1,  2,  8))

    # ── Jambes (4×10 chacune) – deuxième moitié de la hitbox ─────────────
    lx, ly = px, py + 10
    leg_c = feet_color if feet_color else dc
    pygame.draw.rect(screen, leg_c,  (lx,     ly, 4, 10))
    pygame.draw.rect(screen, leg_c,  (lx + 6, ly, 4, 10))
    pygame.draw.rect(screen, _DARK,  (lx,     ly, 4, 10), 1)
    pygame.draw.rect(screen, _DARK,  (lx + 6, ly, 4, 10), 1)
    # Semelle bottes
    if feet_color:
        pygame.draw.rect(screen, _DARK, (lx,     ly + 8, 4, 2))
        pygame.draw.rect(screen, _DARK, (lx + 6, ly + 8, 4, 2))

    # ── Outil en main (droite du corps) ───────────────────────────────────
    tool = inv.tool
    R    = pygame.draw.rect
    tx   = px + 11   # juste à droite du corps
    ty   = py +  2   # hauteur épaule
    if tool == TOOL_PICKAXE:
        _ph_steel = {MAT_WOOD: (155, 100, 42), MAT_IRON: (195, 198, 215), MAT_GOLD: (255, 200, 0)}
        _ph_dstl  = {MAT_WOOD: (100,  62, 20), MAT_IRON: ( 95,  98, 120), MAT_GOLD: (190, 145, 0)}
        pm    = inv.pickaxe_mat
        HNDL  = (155, 100, 42)
        STEEL = _ph_steel.get(pm, (195, 198, 215))
        DSTL  = _ph_dstl.get(pm,  ( 95,  98, 120))
        # manche
        R(screen, HNDL,  (tx + 0, ty + 5, 2, 3))
        R(screen, HNDL,  (tx + 2, ty + 3, 2, 2))
        # corps tête
        R(screen, STEEL, (tx + 3, ty + 1, 4, 3))
        R(screen, DSTL,  (tx + 3, ty + 1, 4, 3), 1)
        # pointe haute
        R(screen, STEEL, (tx + 6, ty + 0, 2, 2))
        R(screen, DSTL,  (tx + 7, ty + 0, 1, 2))
        # pointe basse
        R(screen, STEEL, (tx + 6, ty + 3, 2, 2))
        R(screen, DSTL,  (tx + 7, ty + 4, 1, 1))
    elif tool == TOOL_PLACER:
        METAL = (140, 140, 158)
        DARK  = ( 75,  75,  92)
        SHINE = (215, 215, 230)
        # corps
        R(screen, METAL, (tx + 0, ty + 2, 6, 3))
        R(screen, SHINE, (tx + 0, ty + 2, 6, 1))
        # canon
        R(screen, METAL, (tx + 6, ty + 3, 3, 2))
        R(screen, DARK,  (tx + 6, ty + 3, 3, 1))
        # poignée
        R(screen, DARK,  (tx + 1, ty + 5, 3, 3))
        R(screen, METAL, (tx + 1, ty + 5, 2, 2))
        # détente
        R(screen, DARK,  (tx + 4, ty + 4, 1, 1))
    elif tool == TOOL_SWORD:
        _sword_blade = {MAT_WOOD: (170, 120, 50), MAT_IRON: (205, 208, 220), MAT_GOLD: (240, 195, 20)}
        BLADE = _sword_blade.get(inv.sword_mat, (205, 208, 220))
        SHINE = (245, 248, 255)
        DARK  = ( 80,  90, 115)
        GUARD = (200, 162,  30)
        GRIP  = (120,  72,  28)
        # poignée
        R(screen, GRIP,  (tx + 0, ty + 6, 2, 2))
        # garde
        R(screen, GUARD, (tx + 0, ty + 4, 4, 2))
        # lame diagonale
        R(screen, BLADE, (tx + 2, ty + 3, 2, 2))
        R(screen, BLADE, (tx + 4, ty + 1, 2, 2))
        R(screen, BLADE, (tx + 6, ty + 0, 2, 2))
        R(screen, SHINE, (tx + 2, ty + 3, 1, 1))
        R(screen, SHINE, (tx + 4, ty + 1, 1, 1))
        R(screen, SHINE, (tx + 6, ty + 0, 1, 1))
        R(screen, DARK,  (tx + 3, ty + 4, 1, 1))
        R(screen, DARK,  (tx + 5, ty + 2, 1, 1))
    elif tool == TOOL_FLAG:
        POLE = (160, 130, 80)
        fc   = player.color
        # hampe
        R(screen, POLE, (tx + 1, ty + 2, 2, 6))
        # drapeau triangle
        R(screen, fc,   (tx + 3, ty + 2, 5, 2))
        R(screen, fc,   (tx + 3, ty + 4, 3, 1))
        # pointe
        R(screen, (220, 200, 120), (tx + 1, ty + 0, 2, 2))

    # ── Étiquette J1 / J2 ─────────────────────────────────────────────────
    label = font.render("J" + str(player.idx + 1), True, (255, 255, 255))
    lw = label.get_width()
    pygame.draw.rect(screen, (0, 0, 0), (px + (10 - lw) // 2 - 1, hy - 9, lw + 2, 9))
    screen.blit(label, (px + (10 - lw) // 2, hy - 9))


_CURSOR_SURF = None   # Surface pré-allouée, créée au premier appel

def _draw_compass(surf, cam, me, other, surf_w, color):
    """Boussole (top-right) dont l'aiguille pointe vers l'autre joueur."""
    import math as _math
    R   = 12          # rayon du cadran
    cx  = surf_w - R - 6
    cy  = R + 6

    # Fond semi-transparent
    bg  = pygame.Surface((R*2+2, R*2+2), pygame.SRCALPHA)
    pygame.draw.circle(bg, (0, 0, 0, 110), (R+1, R+1), R+1)
    surf.blit(bg, (cx - R - 1, cy - R - 1))

    # Cercle du cadran
    pygame.draw.circle(surf, (50, 50, 50),  (cx, cy), R)
    pygame.draw.circle(surf, (180, 180, 180), (cx, cy), R, 1)

    # Angle vers l'autre joueur (en pixels monde)
    dx = (other.px() + PLAYER_W / 2) - (me.px() + PLAYER_W / 2)
    dy = (other.py() + PLAYER_H / 2) - (me.py() + PLAYER_H / 2)
    angle = _math.atan2(dy, dx)   # 0 = droite, sens horaire vers le bas

    needle = R - 3
    tip_x  = int(cx + _math.cos(angle) * needle)
    tip_y  = int(cy + _math.sin(angle) * needle)
    tail_x = int(cx - _math.cos(angle) * (needle // 2))
    tail_y = int(cy - _math.sin(angle) * (needle // 2))

    # Aiguille : pointe colorée (vers l'autre joueur) + queue grise
    pygame.draw.line(surf, (80, 80, 80), (tail_x, tail_y), (cx, cy), 2)
    pygame.draw.line(surf, color,        (cx, cy), (tip_x, tip_y), 2)
    pygame.draw.circle(surf, color, (tip_x, tip_y), 2)
    # Point central
    pygame.draw.circle(surf, (220, 220, 220), (cx, cy), 2)


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


# ── Coeurs de vie ─────────────────────────────────────────────────────────────
# Masque d'un coeur 6×5 px : liste de (dx, dy)
_HEART_MASK = [
    (1, 0), (2, 0), (4, 0), (5, 0),
    (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1),
    (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2),
    (1, 3), (2, 3), (3, 3), (4, 3),
    (2, 4), (3, 4),
]
_HEART_W     = 6    # largeur d'un cœur en px
_HEART_GAP   = 3    # espace entre cœurs
_HEART_FULL  = (220,  50,  50)
_HEART_EMPTY = ( 70,  20,  20)
_HEART_SHINE = (255, 140, 140)


def _draw_hearts(surf, hp, max_hp, x, y):
    """Dessine max_hp//2 cœurs. hp et max_hp sont en demi-cœurs."""
    n = max_hp // 2
    R = pygame.draw.rect
    for i in range(n):
        hx = x + i * (_HEART_W + _HEART_GAP)
        for dx, dy in _HEART_MASK:
            half   = 0 if dx < 3 else 1
            filled = hp > i * 2 + half
            R(surf, _HEART_FULL if filled else _HEART_EMPTY, (hx + dx, y + dy, 1, 1))
        if hp > i * 2:
            R(surf, _HEART_SHINE, (hx + 1, y + 1, 1, 1))


def _draw_flag_in_world(screen, flag_x, flag_y, color, camera):
    """Dessine un drapeau posé dans le monde (hampe 3px × 14px + triangle)."""
    px = int(flag_x * TILE_SIZE)
    py = int(flag_y * TILE_SIZE)
    sx, sy = camera.world_to_screen(px, py - 14)   # sommet de la hampe
    R    = pygame.draw.rect
    POLE = (160, 130, 80)
    R(screen, POLE,  (sx,     sy,     2, 14))        # hampe
    R(screen, color, (sx + 2, sy,     7, 3))         # drapeau haut
    R(screen, color, (sx + 2, sy + 3, 5, 2))         # drapeau milieu
    R(screen, color, (sx + 2, sy + 5, 3, 2))         # drapeau bas
    R(screen, (220, 200, 120), (sx, sy - 2, 2, 2))   # pointe dorée


_HOTBAR_SLOT_W = 28   # largeur d'un slot (px) — réduit pour loger 5 slots
_HOTBAR_SLOT_H = 22   # hauteur d'un slot (px)
_HOTBAR_PAD    = 3    # espace entre les slots
_HOTBAR_TOTAL  = _HOTBAR_SLOT_W * 5 + _HOTBAR_PAD * 4

# Icônes pixel-art pour les outils et équipements

def _draw_tool_icon(screen, tool, sx, sy, sw, sh, mat=None):
    """Icône pixel-art de l'outil centrée dans le slot (sw×sh)."""
    R = pygame.draw.rect

    if tool == TOOL_HAND:
        # ── Main – 16×12 ─────────────────────────────────────────────────────
        skin = (235, 186, 135)
        shad = (175, 125, 80)
        ox = sx + (sw - 16) // 2
        oy = sy + (sh - 12) // 2
        # Doigts (index, majeur, annulaire, auriculaire)
        R(screen, skin, (ox + 0,  oy + 0, 2, 6))
        R(screen, skin, (ox + 3,  oy + 0, 2, 8))
        R(screen, skin, (ox + 6,  oy + 1, 2, 7))
        R(screen, skin, (ox + 9,  oy + 2, 2, 6))
        # Paume
        R(screen, skin, (ox + 0,  oy + 7, 12, 5))
        R(screen, shad, (ox + 0,  oy + 11, 12, 1))
        # Pouce
        R(screen, skin, (ox + 11, oy + 8,  4, 3))
        R(screen, shad, (ox + 11, oy + 11, 4, 1))
        # Ombres jointures
        R(screen, shad, (ox + 2,  oy + 6, 1, 1))
        R(screen, shad, (ox + 5,  oy + 7, 1, 1))
        R(screen, shad, (ox + 8,  oy + 7, 1, 1))

    elif tool == TOOL_PICKAXE:
        # ── Pioche – 14×14 (classique diagonale) ────────────────────────────
        _mat_steel = {MAT_WOOD: (155, 100,  42), MAT_IRON: (195, 198, 215), MAT_GOLD: (255, 200,   0)}
        _mat_dstl  = {MAT_WOOD: (100,  62,  20), MAT_IRON: ( 95,  98, 120), MAT_GOLD: (190, 145,   0)}
        _mat_shine = {MAT_WOOD: (200, 145,  80), MAT_IRON: (235, 238, 248), MAT_GOLD: (255, 230,  80)}
        HNDL  = (155, 100,  42)   # bois manche
        HSHAD = (100,  62,  20)   # ombre manche
        STEEL = _mat_steel.get(mat, (195, 198, 215))
        DSTL  = _mat_dstl.get(mat,  ( 95,  98, 120))
        SHINE = _mat_shine.get(mat, (235, 238, 248))
        ox = sx + (sw - 14) // 2
        oy = sy + (sh - 14) // 2
        # Manche (bas-gauche → milieu, 4 segments)
        R(screen, HNDL,  (ox + 0, oy + 11, 2, 3))
        R(screen, HNDL,  (ox + 2, oy +  9, 2, 2))
        R(screen, HSHAD, (ox + 1, oy + 12, 1, 2))  # ombre
        R(screen, HNDL,  (ox + 4, oy +  7, 2, 2))
        R(screen, HSHAD, (ox + 5, oy +  8, 1, 1))
        R(screen, HNDL,  (ox + 6, oy +  5, 2, 2))
        # Corps de la tête (3×3)
        R(screen, STEEL, (ox + 5, oy +  3, 5, 4))
        R(screen, DSTL,  (ox + 5, oy +  3, 5, 4), 1)  # contour
        R(screen, SHINE, (ox + 6, oy +  4, 2, 1))      # reflet
        # Pointe haute → haut-droite
        R(screen, STEEL, (ox +  9, oy +  0, 3, 3))
        R(screen, SHINE, (ox +  9, oy +  0, 3, 1))
        R(screen, DSTL,  (ox + 11, oy +  0, 1, 3))
        R(screen, DSTL,  (ox +  9, oy +  2, 3, 1))
        # Pointe basse → bas-droite
        R(screen, STEEL, (ox +  9, oy +  7, 3, 3))
        R(screen, DSTL,  (ox + 11, oy +  7, 1, 3))
        R(screen, DSTL,  (ox +  9, oy +  9, 3, 1))

    elif tool == TOOL_PLACER:
        # ── Pistolet à cube – 16×12 ──────────────────────────────────────────
        METAL = (140, 140, 158)
        DARK  = ( 75,  75,  92)
        SHINE = (215, 215, 230)
        CUBE  = (200, 140,  50)   # couleur coffre / cube
        CHIGH = (230, 175,  70)   # highlight cube
        ox = sx + (sw - 16) // 2
        oy = sy + (sh - 12) // 2
        # Corps du pistolet
        R(screen, METAL, (ox + 0, oy + 3, 10, 5))  # corps
        R(screen, SHINE, (ox + 1, oy + 3,  8, 1))  # reflet haut
        # Canon
        R(screen, METAL, (ox + 10, oy + 4, 4, 3))  # canon
        R(screen, DARK,  (ox + 10, oy + 4, 4, 1))  # ombre haut canon
        # Poignée
        R(screen, DARK,  (ox + 2,  oy + 8, 4, 4))  # poignée
        R(screen, METAL, (ox + 2,  oy + 8, 3, 3))  # face avant poignée
        # Détente
        R(screen, DARK,  (ox + 5,  oy + 7, 2, 1))
        # Cube éjecté au bout du canon
        R(screen, CUBE,  (ox + 13, oy + 2, 3, 4))  # cube
        R(screen, CHIGH, (ox + 13, oy + 2, 3, 1))  # highlight haut
        R(screen, CHIGH, (ox + 13, oy + 2, 1, 4))  # highlight gauche
        R(screen, DARK,  (ox + 15, oy + 4, 1, 2))  # ombre bas-droite

    elif tool == TOOL_SWORD:
        # ── Épée – 14×14 (lame diagonale haut-droite) ───────────────────────
        _blade_cols = {MAT_WOOD: (170, 120, 50), MAT_IRON: (205, 208, 220), MAT_GOLD: (240, 195, 20)}
        BLADE = _blade_cols.get(mat, (205, 208, 220))
        SHINE = (245, 248, 255)
        DARK  = ( 80,  90, 115)
        GUARD = (200, 162,  30)   # garde or
        GRIP  = (120,  72,  28)   # poignée bois
        ox = sx + (sw - 14) // 2
        oy = sy + (sh - 14) // 2
        # Poignée (bas-gauche)
        R(screen, GRIP,  (ox +  0, oy + 12, 2, 2))
        R(screen, GRIP,  (ox +  2, oy + 10, 2, 2))
        # Garde (croix)
        R(screen, GUARD, (ox +  1, oy +  8, 6, 2))
        R(screen, (230, 185, 50), (ox + 1, oy + 8, 6, 1))  # reflet garde
        # Lame diagonale
        R(screen, BLADE, (ox +  4, oy +  7, 2, 2))
        R(screen, BLADE, (ox +  6, oy +  5, 2, 2))
        R(screen, BLADE, (ox +  8, oy +  3, 2, 2))
        R(screen, BLADE, (ox + 10, oy +  1, 2, 2))
        R(screen, BLADE, (ox + 12, oy +  0, 2, 2))  # pointe
        # Reflet (bord haut de chaque segment)
        R(screen, SHINE, (ox +  4, oy +  7, 1, 1))
        R(screen, SHINE, (ox +  6, oy +  5, 1, 1))
        R(screen, SHINE, (ox +  8, oy +  3, 1, 1))
        R(screen, SHINE, (ox + 10, oy +  1, 1, 1))
        # Ombre (bord bas)
        R(screen, DARK,  (ox +  5, oy +  8, 1, 1))
        R(screen, DARK,  (ox +  7, oy +  6, 1, 1))
        R(screen, DARK,  (ox +  9, oy +  4, 1, 1))
        R(screen, DARK,  (ox + 11, oy +  2, 1, 1))

    elif tool == TOOL_FLAG:
        # ── Drapeau – hampe + triangle de drapeau ─────────────────────────
        fc = mat if mat else (255, 80, 80)   # couleur passée = couleur joueur
        POLE = (160, 130, 80)   # bois de hampe
        ox = sx + (sw - 10) // 2
        oy = sy + (sh - 14) // 2
        # Hampe verticale
        R(screen, POLE, (ox + 1, oy + 3, 2, 11))
        # Drapeau (triangle approximé avec 3 rectangles décroissants)
        R(screen, fc, (ox + 3, oy + 3,  7, 2))
        R(screen, fc, (ox + 3, oy + 5,  5, 2))
        R(screen, fc, (ox + 3, oy + 7,  3, 2))
        # Pointe de la hampe
        R(screen, (220, 200, 120), (ox + 1, oy + 1, 2, 2))


def _draw_equip_icon(screen, eslot, mat_color, sx, sy, sw, sh):
    """Icône pixel-art de l'équipement centrée dans le slot (sw×sh)."""
    c    = mat_color if mat_color else (80, 80, 80)
    dark = (max(0, c[0]-70), max(0, c[1]-70), max(0, c[2]-70))
    R    = pygame.draw.rect

    if eslot == EQUIP_HEAD:
        # Casque — icône 16×9 centrée
        ox = sx + (sw - 16) // 2
        oy = sy + (sh - 9)  // 2
        R(screen, c, (ox+3, oy,   10, 1))   # arc du dôme
        R(screen, c, (ox+1, oy+1, 14, 1))
        R(screen, c, (ox,   oy+2, 16, 1))
        R(screen, c, (ox,   oy+3, 16, 3))   # corps
        R(screen, (15,15,15), (ox+4, oy+3, 8, 3))  # visière sombre
        R(screen, c, (ox,    oy+6, 5, 3))   # jugulaire gauche
        R(screen, c, (ox+11, oy+6, 5, 3))   # jugulaire droite

    elif eslot == EQUIP_BODY:
        # Plastron — icône 16×12 centrée
        ox = sx + (sw - 16) // 2
        oy = sy + (sh - 12) // 2
        R(screen, c, (ox,   oy,    16,  2))  # épaulettes
        R(screen, (15,15,15), (ox+5, oy, 6, 2))  # encolure
        R(screen, c, (ox+1, oy+2,  14, 10))  # corps
        R(screen, dark, (ox+7, oy+3,  2,  8))  # couture centrale
        R(screen, dark, (ox+3, oy+5,  2,  2))  # rivet gauche
        R(screen, dark, (ox+11,oy+5,  2,  2))  # rivet droit

    elif eslot == EQUIP_FEET:
        # Bottes — deux L miroir, icône 14×7 centrée
        ox = sx + (sw - 14) // 2
        oy = sy + (sh - 7)  // 2
        R(screen, c, (ox,    oy,   5, 5))   # tige gauche
        R(screen, c, (ox,    oy+5, 7, 2))   # semelle gauche
        R(screen, c, (ox+9,  oy,   5, 5))   # tige droite
        R(screen, c, (ox+7,  oy+5, 7, 2))   # semelle droite

    elif eslot == EQUIP_SWORD:
        # Épée — lame diagonale + garde, icône 12×14 centrée
        ox = sx + (sw - 12) // 2
        oy = sy + (sh - 14) // 2
        SILVER = (200, 200, 210)
        GOLD_H = (220, 180, 40)
        blade  = SILVER if not mat_color else c
        handle = GOLD_H if not mat_color else dark
        # Lame (colonne centrale)
        R(screen, blade,  (ox + 5, oy,     2, 10))  # lame verticale
        R(screen, blade,  (ox + 4, oy + 1, 4,  1))  # évasement 1
        R(screen, blade,  (ox + 3, oy + 2, 6,  1))  # évasement 2
        # Reflet sur la lame
        R(screen, (240, 240, 245), (ox + 5, oy + 1, 1, 7))
        # Garde
        R(screen, handle, (ox,     oy + 10, 12, 2))
        # Poignée
        R(screen, (100, 65, 35),  (ox + 5, oy + 12, 2, 2))


def _draw_hotbar(screen, inventory, x_offset, color, font):
    """Dessine la hotbar : [outil][ressources][tête][corps][pieds][épée]."""
    sw, sh, pad = _HOTBAR_SLOT_W, _HOTBAR_SLOT_H, _HOTBAR_PAD
    y = HOTBAR_Y

    slot_configs = [
        (Inventory.SLOT_TOOL,  "Outil"),
        (Inventory.SLOT_RES,   "Sac"),
        (Inventory.SLOT_HEAD,  "Tête"),
        (Inventory.SLOT_BODY,  "Corps"),
        (Inventory.SLOT_FEET,  "Pieds"),
    ]

    for i, (slot_id, _) in enumerate(slot_configs):
        sx  = x_offset + i * (sw + pad)
        act = (inventory.active_slot == slot_id)
        bg  = (120, 100, 20) if act else (55, 55, 55)
        pygame.draw.rect(screen, bg,    (sx, y, sw, sh))
        pygame.draw.rect(screen, color, (sx, y, sw, sh), 2 if act else 1)

        if slot_id == Inventory.SLOT_TOOL:
            _tool_mat = (inventory.sword_mat   if inventory.tool == TOOL_SWORD   else
                         inventory.pickaxe_mat if inventory.tool == TOOL_PICKAXE else
                         color                 if inventory.tool == TOOL_FLAG     else None)
            _draw_tool_icon(screen, inventory.tool, sx, y, sw, sh, mat=_tool_mat)
            # Compteur si plusieurs items dans le slot outil
            items = inventory._tool_items()
            if len(items) > 1:
                tidx  = inventory._active_tool_idx()
                idx_s = font.render(f"{tidx+1}/{len(items)}", True, (180, 180, 180))
                screen.blit(idx_s, (sx + 1, y + sh - idx_s.get_height()))

        elif slot_id == Inventory.SLOT_RES:
            if inventory.resources:
                tile, count = inventory.resources[inventory.resource_idx]
                pygame.draw.rect(screen, TILE_COLORS[tile],
                                 (sx + 3, y + 3, sh - 6, sh - 6))
                cnt_s = font.render(str(count), True, (255, 255, 255))
                screen.blit(cnt_s, (sx + sw - cnt_s.get_width() - 1,
                                     y + sh - cnt_s.get_height()))
                if len(inventory.resources) > 1:
                    idx_s = font.render(
                        f"{inventory.resource_idx+1}/{len(inventory.resources)}",
                        True, (180, 180, 180))
                    screen.blit(idx_s, (sx + 1, y + sh - idx_s.get_height()))
            else:
                none_s = font.render("—", True, (100, 100, 100))
                screen.blit(none_s, (sx + (sw - none_s.get_width()) // 2,
                                      y + (sh - none_s.get_height()) // 2))

        else:
            # Slots équipement — icônes pixel-art
            eslot  = Inventory.EQUIP_SLOT_MAP[slot_id]
            item   = inventory.worn_equip(eslot)
            mat_c  = MAT_COLORS[item[1]] if item else None
            _draw_equip_icon(screen, eslot, mat_c, sx, y, sw, sh)
            # Compteur si plusieurs pièces du même slot
            if item:
                lst = inventory.equip[eslot]
                if len(lst) > 1:
                    cnt_s = font.render(str(len(lst)), True, (255, 255, 255))
                    screen.blit(cnt_s, (sx + sw - cnt_s.get_width() - 1,
                                         y + sh - cnt_s.get_height()))

    # ── Nom de l'item actif affiché sous la hotbar ────────────────────────────
    s = inventory.active_slot
    if s == Inventory.SLOT_TOOL:
        if inventory.tool == TOOL_SWORD:
            mat_name = MAT_NAMES.get(inventory.sword_mat, "") if inventory.sword_mat is not None else ""
            name = "Épée " + mat_name if mat_name else "Épée"
        else:
            name = TOOL_NAMES.get(inventory.tool, "")
    elif s == Inventory.SLOT_RES and inventory.resources:
        name = TILE_NAMES.get(inventory.resources[inventory.resource_idx][0], "?")
    elif s in Inventory.EQUIP_SLOT_MAP:
        eslot = Inventory.EQUIP_SLOT_MAP[s]
        item  = inventory.worn_equip(eslot)
        name  = EQUIP_NAMES.get(item, "—") if item else "—"
    else:
        name = ""
    if name:
        name_s = font.render(name, True, color)
        screen.blit(name_s, (x_offset, y + sh + 2))


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
    _saved_players = _db.load_players(world_id)

    chunks = ChunkCache(world)

    # Cycle jour/nuit
    _day_time = [0.12]   # on démarre en plein jour

    # ── Batch SQLite ──────────────────────────────────────────────────────
    _pending_saves  = {}   # {(col, row): tile}  – mods non encore flushées
    _last_flush     = [0.0]
    _FLUSH_INTERVAL = 2.0   # secondes

    def _queue_block(col, row, tile):
        _pending_saves[(col, row)] = tile

    def _flush_all():
        if _pending_saves:
            _db.save_blocks_batch(world_id, [(c, r, t) for (c, r), t in _pending_saves.items()])
            _pending_saves.clear()
        for p in players:
            _db.save_player(world_id, p.idx, p.x, p.y, p.inventory, flag=flag_positions[p.idx])

    # alias court utilisé par les blocs de code existants
    def _flush_blocks():
        _flush_all()


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

    flag_positions = [None, None]      # position de respawn de chaque joueur (x, y en tuiles)

    # ── Restaurer la dernière position / inventaire sauvegardés ──────────
    for p in players:
        sv = _saved_players.get(p.idx)
        if sv:
            p.x = sv["x"]
            p.y = sv["y"]
            p.inventory.tool      = sv["tool"]
            p.inventory.resources = [tuple(r) for r in sv["resources"]]
            p.inventory.swords       = sv.get("swords", [])
            p.inventory.sword_idx    = sv.get("sword_idx", 0)
            p.inventory.pickaxes     = sv.get("pickaxes", [])
            p.inventory.pickaxe_idx  = sv.get("pickaxe_idx", 0)
            p.inventory.equip        = {
                k: [tuple(e) for e in v] for k, v in sv["equip"].items()
            }
            # Corriger les index si la liste a rétréci
            for eslot, lst in p.inventory.equip.items():
                p.inventory.equip_idx[eslot] = min(
                    p.inventory.equip_idx.get(eslot, 0), max(0, len(lst) - 1)
                )
            _eject_from_blocks(p, world)
            # Restaurer la position du drapeau
            if sv.get("flag") is not None:
                flag_positions[p.idx] = sv["flag"]

    # Caméra partagée – centrée sur J1 au départ
    HALF_W = SCREEN_WIDTH // 2
    shared_cam = Camera()

    # ── Mobs ──────────────────────────────────────────────────────────────
    mob_mgr    = _mobs.MobManager(world)
    _mob_spawn_cd = [0.0]   # cooldown avant prochain scan de spawn
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
    # Une seule manette : J1 = joystick/hat, J2 = boutons YXBA sur la même manette
    joy2 = joy1

    # Mapping joueur → (joystick, btn_mine, btn_mine2, btn_mod, get_dir_fn, kb_mine, kb_mod)
    player_controls = [
        (joy1, J1_BTN_MINE, -1,            J1_BTN_MODIFIER, _get_dir_p1, KB_J1_MINE, KB_J1_MODIFIER),
        (joy2, J2_BTN_MINE, J2_BTN_MINE2,  J2_BTN_MODIFIER, _get_dir_p2, KB_J2_MINE, KB_J2_MODIFIER),
    ]

    # État inter-frames
    p_dirs      = [(0, 0), (0, 0)]   # dernière direction connue (pour le curseur)
    break_infos = [None, None]        # (col, row, progress) en cours de cassage
    prev_mine   = [False, False]      # état précédent du bouton mine
    prev_dx     = [0, 0]              # pour détecter l'edge gauche/droite en mode modifier
    prev_dy     = [0, 0]              # pour détecter l'edge haut/bas en mode modifier
    mine_tick_cd = [0.0, 0.0]         # throttle du son de minage (s)
    loot_notifs   = []   # [[texte, temps_restant, couleur], ...]

    while True:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)

        # ── Cycle jour/nuit ───────────────────────────────────────────────
        _day_time[0] = (_day_time[0] + dt / DAY_CYCLE_DURATION) % 1.0
        _sky_c   = _sky_color(_day_time[0])
        is_night = _is_night(_day_time[0])

        _last_flush[0] += dt
        if _last_flush[0] >= _FLUSH_INTERVAL:
            _flush_all()
            _last_flush[0] = 0.0
        mine_tick_cd[0] = max(0.0, mine_tick_cd[0] - dt)
        mine_tick_cd[1] = max(0.0, mine_tick_cd[1] - dt)

        events = pygame.event.get()
        keys   = pygame.key.get_pressed()

        for e in events:
            if e.type == pygame.QUIT:
                _flush_blocks()
                return None
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                _flush_blocks()
                return True
            if e.type == pygame.KEYDOWN and e.key == pygame.K_p:
                _sounds.toggle_mute()
                _music.toggle_mute()
            quit_combo.handle_event(e)

        # ── Mise à jour physique et contrôles ─────────────────────────────
        for i, player in enumerate(players):
            joy, btn_mine, btn_mine2, btn_mod, get_dir, kb_mine, kb_mod = player_controls[i]

            dx, dy = get_dir(keys, joy)
            cur_mine = _joy_btn(joy, btn_mine) or _joy_btn(joy, btn_mine2) or bool(keys[kb_mine])
            cur_mod  = _joy_btn(joy, btn_mod)  or bool(keys[kb_mod])

            # ── Mode MODIFIER : navigation inventaire ─────────────────────────
            if cur_mod:
                # ←/→ : changer de slot actif (outil ↔ ressources)
                if dx ==  1 and prev_dx[i] !=  1:
                    player.inventory.slot_next()
                    _sounds.inv_change()
                elif dx == -1 and prev_dx[i] != -1:
                    player.inventory.slot_prev()
                    _sounds.inv_change()
                # ↑/↓ : changer d'outil (slot 0) ou de ressource (slot 1)
                if dy == -1 and prev_dy[i] != -1:
                    player.inventory.item_prev()
                    _sounds.inv_change()
                elif dy ==  1 and prev_dy[i] !=  1:
                    player.inventory.item_next()
                    _sounds.inv_change()
                # Bloquer le déplacement horizontal
                player.vx = 0.0
            else:
                player.vx = dx * WALK_SPEED

            if dx != 0 or dy != 0:
                p_dirs[i] = (dx, dy)
            prev_dx[i] = dx
            prev_dy[i] = dy

            # ── Escalade de mur (appuyer haut contre n'importe quel bloc) ────
            player.on_wall = _touching_wall(player, world)
            climbing = dy < 0 and player.on_wall and not player.on_ground and not cur_mod

            if climbing:
                # Annule la gravité, monte à vitesse constante
                player.vy = -CLIMB_SPEED
            else:
                # Saut (direction haut, disabled si modifier tenu)
                if dy < 0 and player.on_ground and not cur_mod:
                    player.vy = JUMP_VEL
                    _sounds.jump()

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
            cur_col, cur_row = _get_cursor(player, cdx, cdy, world)
            cur_row = max(0, min(ROWS - 1, cur_row))
            in_reach = _in_reach(player, cur_col, cur_row)

            # ─ Mode ÉPÉE : attaque sans condition de portée (zone autour du joueur)
            if player.inventory.tool == TOOL_SWORD and player._action_cd <= 0:
                if cur_mine and not prev_mine[i] and not cur_mod:
                    dmg = (player.inventory.sword_mat or 0) + 1
                    killed = mob_mgr.attack_near(player.x, player.y, REACH_RADIUS, dmg)
                    if killed > 0:
                        player.hp = player.max_hp   # tuer un mob = vie pleine
                    player._action_cd = 0.35
                    _sounds.sword_hit()

            # ─ Mode DRAPEAU : pose le drapeau sur le joueur (appui unique)
            if player.inventory.tool == TOOL_FLAG and player._action_cd <= 0:
                if cur_mine and not prev_mine[i] and not cur_mod:
                    flag_positions[i] = (player.x, player.y)
                    player._action_cd = 0.4
                    loot_notifs.append(["Drapeau J" + str(i + 1) + " placé !", 2.0, player.color])
                    _sounds.flag_place()

            if in_reach and player._action_cd <= 0 and player.inventory.tool != TOOL_SWORD:
                tile_at = world.get(cur_col, cur_row)

                if cur_mine and not prev_mine[i] and not cur_mod:
                    # ─ MINE appui unique + outil Canon → POSER un bloc ─────────
                    if (player.inventory.tool == TOOL_PLACER
                            and tile_at == TILE_AIR):
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
                                for p in players:
                                    _eject_from_blocks(p, world)
                                player.inventory.consume()
                                player._action_cd = 0.2
                                _queue_block(cur_col, cur_row, selected)
                                _sounds.place()

                elif cur_mine and not cur_mod:
                    # ─ MINE seul (maintenu) ───────────────────────────────
                    if tile_at == TILE_CHEST and player.inventory.tool == TOOL_HAND:
                        # ── Coffre × Outil Main → loote l'équipement ─────
                        if break_infos[i] and break_infos[i][:2] == (cur_col, cur_row):
                            player._break_time += dt
                            progress = min(player._break_time / 0.6, 1.0)
                            break_infos[i] = (cur_col, cur_row, progress)
                            if player._break_time >= 0.6:
                                item = world.chest_loot()
                                player.inventory.add_equip(item)
                                loot_notifs.append([EQUIP_NAMES.get(item, "?"), 2.5, player.color])
                                world.set(cur_col, cur_row, TILE_AIR)
                                chunks.invalidate(cur_col)
                                break_infos[i] = None
                                player._break_time = 0.0
                                player._action_cd  = 0.3
                                _queue_block(cur_col, cur_row, TILE_AIR)
                                _sounds.chest_open()
                        else:
                            player._break_time = 0.0
                            break_infos[i] = (cur_col, cur_row, 0.0)

                    elif tile_at != TILE_AIR and tile_at != TILE_CHEST \
                            and player.inventory.tool == TOOL_PICKAXE:
                        # ── Minage normal (Pioche uniquement) ─────────────
                        if break_infos[i] and break_infos[i][:2] == (cur_col, cur_row):
                            player._break_time += dt
                            req_time = TILE_BREAK_TIME.get(tile_at, 0.5)
                            progress = min(player._break_time / req_time, 1.0)
                            break_infos[i] = (cur_col, cur_row, progress)
                            # Son de frappe throttlé (toutes les ~0.15 s)
                            if mine_tick_cd[i] <= 0.0:
                                _sounds.mine_tick()
                                mine_tick_cd[i] = 0.15
                            if player._break_time >= req_time:
                                # Alerte le Golem si c'était un bloc de cabane
                                if world._cabin_tile(cur_col, cur_row) != TILE_AIR:
                                    mob_mgr.trigger_cabin_break(cur_col)
                                player.inventory.add(tile_at)
                                world.set(cur_col, cur_row, TILE_AIR)
                                chunks.invalidate(cur_col)
                                break_infos[i] = None
                                player._break_time = 0.0
                                player._action_cd  = 0.1
                                _queue_block(cur_col, cur_row, TILE_AIR)
                                _sounds.mine_done()
                                mine_tick_cd[i] = 0.0
                        else:
                            player._break_time = 0.0
                            break_infos[i] = (cur_col, cur_row, 0.0)
                    else:
                        break_infos[i]   = None
                        player._break_time = 0.0
                else:
                    break_infos[i]   = None
                    player._break_time = 0.0
            else:
                if not cur_mine:
                    break_infos[i] = None
                    player._break_time = 0.0

            prev_mine[i] = cur_mine

        # ── Tick dmg flash ────────────────────────────────────────────────
        for player in players:
            player._dmg_flash = max(0.0, player._dmg_flash - dt)

        # ── Respawn si un joueur tombe hors du monde ou meurt ─────────────
        for i, player in enumerate(players):
            dead = player.hp <= 0 or player.y * TILE_SIZE > ROWS * TILE_SIZE + 64
            if dead:
                player.hp = player.max_hp
                fp = flag_positions[i]
                if fp:
                    player.x, player.y = fp
                else:
                    col = mid - 3 if i == 0 else mid + 3
                    player.x = spawn_x(col)
                    player.y = spawn_y(col)
                player.vx = 0.0
                player.vy = 0.0
                _eject_from_blocks(player, world)

        # ── Mobs : spawn périodique + update ──────────────────────────────
        _mob_spawn_cd[0] -= dt
        if _mob_spawn_cd[0] <= 0:
            centers = list({int(p.x) for p in players})
            mob_mgr.spawn_around(centers, is_night)
            _mob_spawn_cd[0] = 3.0
        mob_mgr.update(dt, players, world)

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
        screen.fill(_sky_c)

        if is_split:
            for i, (surf, cam) in enumerate(zip(split_surfs, split_cams)):
                surf.fill(_sky_c)
                chunks.preload_around(cam.x, HALF_W)
                _draw_world(surf, chunks, cam, break_infos[i])

                # Curseurs des deux joueurs dans chaque vue (pas avec l'épée)
                for j, player in enumerate(players):
                    if player.inventory.tool == TOOL_SWORD:
                        continue
                    cdx, cdy = p_dirs[j]
                    cur_col, cur_row = _get_cursor(player, cdx, cdy, world)
                    cur_row = max(0, min(ROWS - 1, cur_row))
                    if _in_reach(player, cur_col, cur_row):
                        _draw_cursor(surf, player, cur_col, cur_row, cam)

                # Drapeaux de respawn
                for fi, fp in enumerate(flag_positions):
                    if fp:
                        _draw_flag_in_world(surf, fp[0], fp[1], players[fi].color, cam)

                # Mobs puis joueurs (joueurs par-dessus)
                mob_mgr.draw(surf, cam)
                for player in players:
                    _draw_player(surf, player, cam, font_sm)

                # Hotbar du joueur propriétaire de cette vue (nom inclus dans _draw_hotbar)
                player_i = players[i]
                _draw_hotbar(surf, player_i.inventory, 4, player_i.color, font_sm)

                # Coeurs de vie (à droite de la hotbar)
                _draw_hearts(surf, player_i.hp, player_i.max_hp,
                             4 + _HOTBAR_TOTAL + 4,
                             HOTBAR_Y + (_HOTBAR_SLOT_H - 5) // 2 + 1)

                # Flash de dégâts (overlay rouge)
                if player_i._dmg_flash > 0:
                    _alpha = int(140 * player_i._dmg_flash / 0.4)
                    _dmg_surf = pygame.Surface((HALF_W, SCREEN_HEIGHT), pygame.SRCALPHA)
                    _dmg_surf.fill((200, 0, 0, min(140, _alpha)))
                    surf.blit(_dmg_surf, (0, 0))

                # Boussole vers l'autre joueur (top-right)
                other = players[1 - i]
                _draw_compass(surf, cam, players[i], other, HALF_W, other.color)

            # Séparateur vertical central
            pygame.draw.line(screen, (200, 200, 200), (HALF_W, 0), (HALF_W, SCREEN_HEIGHT), 2)

            # Seed sur la moitié droite
            seed_lbl = font_sm.render("seed:" + str(world_seed), True, (180, 180, 180))
            split_surfs[1].blit(seed_lbl, (HALF_W - seed_lbl.get_width() - 4, SCREEN_HEIGHT - seed_lbl.get_height() - 2))

        else:
            chunks.preload_around(shared_cam.x, SCREEN_WIDTH)
            _draw_world(screen, chunks, shared_cam, break_infos[0] or break_infos[1])

            for i, player in enumerate(players):
                if player.inventory.tool == TOOL_SWORD:
                    continue
                cdx, cdy = p_dirs[i]
                cur_col, cur_row = _get_cursor(player, cdx, cdy, world)
                cur_row = max(0, min(ROWS - 1, cur_row))
                if _in_reach(player, cur_col, cur_row):
                    _draw_cursor(screen, player, cur_col, cur_row, shared_cam)

            mob_mgr.draw(screen, shared_cam)
            # Drapeaux de respawn
            for fi, fp in enumerate(flag_positions):
                if fp:
                    _draw_flag_in_world(screen, fp[0], fp[1], players[fi].color, shared_cam)
            for i, player in enumerate(players):
                _draw_player(screen, player, shared_cam, font_sm)

            # Hotbar J1 à gauche, J2 à droite (nom inclus dans _draw_hotbar)
            _draw_hotbar(screen, players[0].inventory, 4, P1_COLOR, font_sm)
            _draw_hotbar(screen, players[1].inventory,
                         SCREEN_WIDTH - _HOTBAR_TOTAL - 4, P2_COLOR, font_sm)

            # Coeurs de vie J1 (à droite de sa hotbar) et J2 (à gauche de sa hotbar)
            _hearts_y = HOTBAR_Y + (_HOTBAR_SLOT_H - 5) // 2 + 1
            _hearts_w  = players[0].max_hp // 2 * (_HEART_W + _HEART_GAP) - _HEART_GAP
            _draw_hearts(screen, players[0].hp, players[0].max_hp,
                         4 + _HOTBAR_TOTAL + 4, _hearts_y)
            _draw_hearts(screen, players[1].hp, players[1].max_hp,
                         SCREEN_WIDTH - _HOTBAR_TOTAL - 4 - 4 - _hearts_w, _hearts_y)

            # Flash de dégâts (overlay rouge par joueur — même vue)
            for _pi, _pp in enumerate(players):
                if _pp._dmg_flash > 0:
                    _alpha = int(140 * _pp._dmg_flash / 0.4)
                    _dmg_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                    _dmg_surf.fill((200, 0, 0, min(140, _alpha)))
                    screen.blit(_dmg_surf, (0, 0))

            seed_lbl = font_sm.render("seed: " + str(world_seed), True, (180, 180, 180))
            screen.blit(seed_lbl, (SCREEN_WIDTH - seed_lbl.get_width() - 4, SCREEN_HEIGHT - seed_lbl.get_height() - 2))

        # ── Overlay nuit ──────────────────────────────────────────────────
        _na = _night_alpha(_day_time[0])
        if _na > 0:
            global _night_overlay
            if _night_overlay is None:
                _night_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            _night_overlay.fill((10, 5, 30, _na))
            screen.blit(_night_overlay, (0, 0))
        _draw_sky_hud(screen, _day_time[0], font_sm)

        # Overlay SELECT+START (dessiné sur l'écran complet, au-dessus de tout)
        if quit_combo.update_and_draw(screen):
            _flush_blocks()
            return True

        # Indicateur mute (PC uniquement, coin bas-centre)
        if _sounds.is_muted():
            mute_lbl = font_sm.render("[MUTE] P", True, (255, 80, 80))
            screen.blit(mute_lbl, (SCREEN_WIDTH // 2 - mute_lbl.get_width() // 2,
                                   SCREEN_HEIGHT - mute_lbl.get_height() - 2))

        # ── Notifications loot coffre ─────────────────────────────────────
        _ni = 0
        while _ni < len(loot_notifs):
            loot_notifs[_ni][1] -= dt
            if loot_notifs[_ni][1] <= 0:
                loot_notifs.pop(_ni)
            else:
                _ni += 1
        if loot_notifs:
            _ntxt, _ntime, _ncol = loot_notifs[-1]
            _nalpha = 255 if _ntime > 0.6 else int(_ntime / 0.6 * 255)
            _nlbl   = font_med.render("Obtenu : " + _ntxt + " !", True, (255, 220, 60))
            _nlbl.set_alpha(_nalpha)
            _nlw, _nlh = _nlbl.get_size()
            _npad = 6
            _nbg  = pygame.Surface((_nlw + _npad * 2, _nlh + _npad * 2), pygame.SRCALPHA)
            _nbg.fill((0, 0, 0, int(_nalpha * 0.7)))
            _nnx = SCREEN_WIDTH  // 2 - (_nlw + _npad * 2) // 2
            _nny = SCREEN_HEIGHT // 3
            screen.blit(_nbg, (_nnx, _nny))
            screen.blit(_nlbl, (_nnx + _npad, _nny + _npad))

        pygame.display.flip()
