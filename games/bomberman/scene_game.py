"""
Scène de jeu Bomberman – 2 joueurs humains + 2 IA.
Retourne un classement (liste de listes d'indices joueur, du 1er au dernier)
ou None (quitter).
"""
import pygame
import random
import math
import collections

from config import *
from quit_combo import QuitCombo
import sound_manager

_PLAYER_LABELS = ['J1', 'J2', 'IA1', 'IA2']
_PLAYER_COLORS = [P1_COLOR, P2_COLOR, P3_COLOR, P4_COLOR]


# ── Génération de la grille ───────────────────────────────────────────────────

# Cases toujours libres autour des 4 spawns (coins)
_SPAWN_SAFE = {
    (1, 1), (2, 1), (1, 2),
    (COLS - 2, ROWS - 2), (COLS - 3, ROWS - 2), (COLS - 2, ROWS - 3),
    (COLS - 2, 1), (COLS - 3, 1), (COLS - 2, 2),
    (1, ROWS - 2), (2, ROWS - 2), (1, ROWS - 3),
}


def _base_grid():
    grid = [[EMPTY] * COLS for _ in range(ROWS)]
    for c in range(COLS):
        grid[0][c] = grid[ROWS - 1][c] = WALL
    for r in range(ROWS):
        grid[r][0] = grid[r][COLS - 1] = WALL
    return grid


def _scatter_blocks(grid, density):
    for r in range(1, ROWS - 1):
        for c in range(1, COLS - 1):
            if grid[r][c] == EMPTY and (c, r) not in _SPAWN_SAFE:
                if random.random() < density:
                    grid[r][c] = BLOCK
    return grid


def _make_classic():
    """Classique : piliers fixes aux positions paires + 55 % de blocs."""
    grid = _base_grid()
    for r in range(2, ROWS - 1, 2):
        for c in range(2, COLS - 1, 2):
            grid[r][c] = WALL
    return _scatter_blocks(grid, 0.55), 'classic'


def _make_labyrinth():
    """Labyrinthe : piliers fixes + 75 % de blocs, terrain très serré."""
    grid = _base_grid()
    for r in range(2, ROWS - 1, 2):
        for c in range(2, COLS - 1, 2):
            grid[r][c] = WALL
    return _scatter_blocks(grid, 0.75), 'labyrinth'


def _make_arena():
    """Arène : anneau de piliers intérieur style colisée + piliers centraux."""
    grid = _base_grid()
    # Anneau haut et bas (r=2 et r=6)
    for c in range(3, COLS - 2, 2):
        if (c, 2) not in _SPAWN_SAFE:
            grid[2][c] = WALL
        if (c, ROWS - 3) not in _SPAWN_SAFE:
            grid[ROWS - 3][c] = WALL
    # Piliers latéraux gauche et droite (c=3 et c=11)
    for r in range(3, ROWS - 2, 2):
        if (3, r) not in _SPAWN_SAFE:
            grid[r][3] = WALL
        if (COLS - 4, r) not in _SPAWN_SAFE:
            grid[r][COLS - 4] = WALL
    # Piliers centraux en îlot
    for r in (3, 5):
        for c in (6, 8):
            grid[r][c] = WALL
    return _scatter_blocks(grid, 0.28), 'arena'


def _make_tunnels():
    """
    3 couloirs horizontaux séparés par des murs avec ouvertures décalées.
    Couloir haut (r=1-2), couloir milieu (r=4), couloir bas (r=6-7).
    Les ouvertures obligent à zigzaguer d'un couloir à l'autre.
    """
    grid = _base_grid()
    # Mur r=3 : ouvertures près des coins et au centre
    gaps_r3 = {2, 7, 12}
    # Mur r=5 : ouvertures décalées pour forcer le zigzag
    gaps_r5 = {3, 8, 13}
    for c in range(1, COLS - 1):
        if c not in gaps_r3:
            grid[3][c] = WALL
        if c not in gaps_r5:
            grid[5][c] = WALL
    # Quelques piliers dans les couloirs haut et bas
    for c in range(2, COLS - 1, 2):
        if (c, 2) not in _SPAWN_SAFE:
            grid[2][c] = WALL
        if (c, 6) not in _SPAWN_SAFE:
            grid[6][c] = WALL
    return _scatter_blocks(grid, 0.40), 'tunnels'


def _make_cross():
    """
    Grande croix indestructible divisant la carte en 4 quadrants.
    Passages d'1 case près des spawns pour maintenir l'accessibilité.
    """
    grid = _base_grid()
    # Barre verticale (c=7) : 1 passage en haut (r=2) et 1 en bas (r=6)
    gaps_v = {2, 6}
    for r in range(1, ROWS - 1):
        if r not in gaps_v:
            grid[r][7] = WALL
    # Barre horizontale (r=4) : 1 passage à gauche (c=2) et 1 à droite (c=12)
    gaps_h = {2, 12}
    for c in range(1, COLS - 1):
        if c not in gaps_h and c != 7:
            grid[4][c] = WALL
    return _scatter_blocks(grid, 0.45), 'cross'


_LAYOUTS = [_make_classic, _make_labyrinth, _make_arena, _make_tunnels, _make_cross]


def _make_grid():
    grid, _ = random.choice(_LAYOUTS)()
    theme = random.choice(list(_THEME_PALETTE.keys()))
    return grid, theme


# ── Entités ────────────────────────────────────────────────────────────────────

class Player:
    def __init__(self, col, row, color):
        self.col           = col
        self.row           = row
        self.color         = color
        self.alive         = True
        self.move_cd       = 0.0
        self.bomb_cd       = 0.0
        self.active_bombs  = 0
        self.max_bombs     = 1
        self.bomb_range    = BOMB_RANGE
        self.move_cooldown = MOVE_COOLDOWN


class Bomb:
    def __init__(self, col, row, owner_idx, bomb_range=BOMB_RANGE):
        self.col       = col
        self.row       = row
        self.timer     = BOMB_TIMER
        self.range     = bomb_range
        self.owner     = owner_idx
        self.next_tick = 0.40


class Explosion:
    def __init__(self, cells):
        self.cells = cells
        self.timer = EXPLOSION_DUR


class Bonus:
    def __init__(self, col, row, bonus_type):
        self.col  = col
        self.row  = row
        self.type = bonus_type


# ── Helpers de contrôle (joueurs humains) ───────────────────────────────────

def _get_p1_dir(keys, joystick):
    if joystick:
        try:
            ax = joystick.get_axis(0)
            ay = joystick.get_axis(1)
            if ax < -AXIS_DEAD: return -1,  0
            if ax >  AXIS_DEAD: return  1,  0
            if ay < -AXIS_DEAD: return  0, -1
            if ay >  AXIS_DEAD: return  0,  1
        except Exception:
            pass
        try:
            hx, hy = joystick.get_hat(0)
            if hx != 0 or hy != 0:
                return hx, -hy
        except Exception:
            pass
    if keys[pygame.K_z]:  return  0, -1
    if keys[pygame.K_s]:  return  0,  1
    if keys[pygame.K_q]:  return -1,  0
    if keys[pygame.K_d]:  return  1,  0
    return None


def _get_p2_dir(keys, p2_btns):
    if BTN_B in p2_btns: return  1,  0
    if BTN_A in p2_btns: return  0,  1
    if BTN_Y in p2_btns: return -1,  0
    if BTN_X in p2_btns: return  0, -1
    if keys[pygame.K_o]:  return  0, -1
    if keys[pygame.K_l]:  return  0,  1
    if keys[pygame.K_k]:  return -1,  0
    if keys[pygame.K_m]:  return  1,  0
    return None


def _is_blocked(col, row, grid, players, bombs, exclude_player=-1):
    if not (0 <= col < COLS and 0 <= row < ROWS):
        return True
    if grid[row][col] != EMPTY:
        return True
    for i, p in enumerate(players):
        if i != exclude_player and p.alive and p.col == col and p.row == row:
            return True
    for b in bombs:
        if b.col == col and b.row == row:
            return True
    return False


# ── Logique d'explosion ────────────────────────────────────────────────────────

def _compute_explosion(col, row, bomb_range, grid, bombs):
    cells   = {(col, row)}
    destroy = set()
    chain   = []

    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        for dist in range(1, bomb_range + 1):
            nc, nr = col + dx * dist, row + dy * dist
            if not (0 <= nc < COLS and 0 <= nr < ROWS):
                break
            if grid[nr][nc] == WALL:
                break
            cells.add((nc, nr))
            for b in bombs:
                if b.col == nc and b.row == nr:
                    chain.append(b)
            if grid[nr][nc] == BLOCK:
                destroy.add((nc, nr))
                break

    return cells, destroy, chain


def _process_explosions(to_explode, bombs, grid, players, explosions):
    processed     = set()
    queue         = list(to_explode)
    all_destroyed = set()

    while queue:
        b = queue.pop(0)
        if id(b) in processed:
            continue
        processed.add(id(b))

        cells, destroy, chain = _compute_explosion(b.col, b.row, b.range, grid, bombs)
        explosions.append(Explosion(cells))

        if 0 <= b.owner < len(players):
            players[b.owner].active_bombs = max(0, players[b.owner].active_bombs - 1)

        for dc, dr in destroy:
            grid[dr][dc] = EMPTY
            all_destroyed.add((dc, dr))

        for cb in chain:
            if id(cb) not in processed:
                queue.append(cb)

    return [b for b in bombs if id(b) not in processed], all_destroyed


def _apply_bonus(player, bonus_type):
    if bonus_type == BONUS_BOMB:
        player.max_bombs = min(BONUS_MAX_BOMBS, player.max_bombs + 1)
    elif bonus_type == BONUS_RANGE:
        player.bomb_range = min(BONUS_MAX_RANGE, player.bomb_range + 1)
    elif bonus_type == BONUS_SPEED:
        player.move_cooldown = max(BONUS_MIN_CD, player.move_cooldown - BONUS_SPEED_GAIN)


# ── Intelligence artificielle ──────────────────────────────────────────────────

_DIRS = ((0, -1), (1, 0), (0, 1), (-1, 0))

# États de la machine à états de l'IA
_AI_SEEK      = 'SEEK'       # cherche un bloc à casser, s'en approche, pose la bombe
_AI_FLEE      = 'FLEE'       # fuit après avoir posé une bombe (peut traverser les blasts)
_AI_WAIT_SAFE = 'WAIT_SAFE'  # en zone safe, attend que le danger disparaisse


class AIState:
    def __init__(self):
        self.state = _AI_SEEK
        self.pause = random.uniform(0.5, 1.5)  # petite pause initiale


def _danger_cells(bombs, explosions, grid, max_timer=999.0):
    """Cellules dangereuses. max_timer filtre les bombes par timer restant."""
    cells = set()
    for ex in explosions:
        cells |= ex.cells
    for b in bombs:
        if b.timer < max_timer:
            blast, _, _ = _compute_explosion(b.col, b.row, b.range, grid, [])
            cells |= blast
    return cells


def _bfs_path(start, targets, grid, players, bombs, pidx, danger=None,
              max_dist=999, ignore_bombs=False):
    """BFS : retourne la liste de cases du chemin (start exclu) vers targets, ou []."""
    sc, sr = start
    if (sc, sr) in targets:
        return []
    queue  = collections.deque([(sc, sr)])
    parent = {(sc, sr): None}
    dist   = {(sc, sr): 0}
    found  = None
    while queue:
        c, r = queue.popleft()
        if dist[(c, r)] >= max_dist:
            continue
        for dx, dy in _DIRS:
            nc, nr = c + dx, r + dy
            if (nc, nr) in parent:
                continue
            if not (0 <= nc < COLS and 0 <= nr < ROWS):
                continue
            if grid[nr][nc] != EMPTY:
                continue
            blocked = False
            for i, p2 in enumerate(players):
                if i != pidx and p2.alive and p2.col == nc and p2.row == nr:
                    blocked = True
                    break
            if blocked:
                continue
            if not ignore_bombs:
                if any(b.col == nc and b.row == nr for b in bombs):
                    continue
            if danger and (nc, nr) in danger:
                continue
            parent[(nc, nr)] = (c, r)
            dist[(nc, nr)]   = dist[(c, r)] + 1
            if (nc, nr) in targets:
                found = (nc, nr)
                break
            queue.append((nc, nr))
        if found:
            break
    if not found:
        return []
    # Reconstruire le chemin complet (start exclu)
    path = []
    node = found
    while node != (sc, sr):
        path.append(node)
        node = parent[node]
    path.reverse()
    return path


def _active_explo_cells(explosions):
    cells = set()
    for ex in explosions:
        cells |= ex.cells
    return cells


def _can_escape_after_bomb(pos, pidx, players, grid, bombs, bomb_range, flames):
    """
    Vérifie que l'IA peut rejoindre une case safe après avoir posé une bombe à pos.

    Destination safe = hors du blast de la nouvelle bombe
                       + hors des blasts de bombes imminentes (<1.2s)
                       + hors des flammes actives

    Chemin : peut traverser le blast de la nouvelle bombe (3s pour fuir)
             évite uniquement les flammes actives (mort instantanée)
    """
    blast, _, _ = _compute_explosion(pos[0], pos[1], bomb_range, grid, bombs)
    imminent    = _danger_cells(bombs, [], grid, max_timer=1.2)
    safe = {(c, r) for r in range(1, ROWS - 1) for c in range(1, COLS - 1)
            if grid[r][c] == EMPTY
            and (c, r) not in blast
            and (c, r) not in imminent
            and (c, r) not in flames}
    # Le chemin n'est contraint que par les flammes actives (mortelles immédiatement)
    # Le blast et les imminents peuvent être traversés car on a du temps
    path = _bfs_path(pos, safe, grid, players, bombs, pidx,
                     danger=flames, ignore_bombs=True, max_dist=20)
    return len(path) > 0


def _near_bombable(pidx, players, grid):
    """Retourne True si le joueur est adjacent à un bloc ou un ennemi."""
    p = players[pidx]
    for dx, dy in _DIRS:
        nc, nr = p.col + dx, p.row + dy
        if not (0 <= nc < COLS and 0 <= nr < ROWS):
            continue
        if grid[nr][nc] == BLOCK:
            return True
        for i, other in enumerate(players):
            if i != pidx and other.alive and other.col == nc and other.row == nr:
                return True
    return False


def _bombable_targets(pidx, players, grid):
    """Cases EMPTY adjacentes à un bloc ou un ennemi (destinations pour SEEK)."""
    targets = set()
    for r in range(1, ROWS - 1):
        for c in range(1, COLS - 1):
            if grid[r][c] != EMPTY:
                continue
            for dx, dy in _DIRS:
                nc, nr = c + dx, r + dy
                if not (0 <= nc < COLS and 0 <= nr < ROWS):
                    continue
                if grid[nr][nc] == BLOCK:
                    targets.add((c, r))
                    break
                for i, other in enumerate(players):
                    if i != pidx and other.alive and other.col == nc and other.row == nr:
                        targets.add((c, r))
                        break
    return targets


def _ai_update(pidx, ai_state, players, grid, bombs, explosions, bonuses, dt):
    """
    Machine à états IA à 3 états :
      SEEK      → se déplace vers un bloc/ennemi, pose la bombe
      FLEE      → fuit vers une case safe (peut traverser les blasts)
      WAIT_SAFE → attend que le terrain soit calme avant de reprendre
    Retourne (direction: (dx,dy)|None, do_bomb: bool).
    """
    p   = players[pidx]
    pos = (p.col, p.row)
    st  = ai_state

    flames    = _active_explo_cells(explosions)
    all_blast = _danger_cells(bombs, [], grid)  # souffle de toutes les bombes

    # Interruption : flammes actives sous les pieds ou debout sur une bombe → FLEE
    on_bomb    = any(b.col == p.col and b.row == p.row for b in bombs)
    in_flames  = pos in flames
    if (on_bomb or in_flames) and st.state != _AI_FLEE:
        st.state = _AI_FLEE
        return None, False

    # ── SEEK ─────────────────────────────────────────────────────────────────
    if st.state == _AI_SEEK:
        # Petite pause naturelle
        st.pause -= dt
        if st.pause > 0:
            return None, False

        # 1) Ramasser un bonus proche s'il y en a un
        if bonuses:
            bonus_set = {(bx.col, bx.row) for bx in bonuses}
            path = _bfs_path(pos, bonus_set, grid, players, bombs, pidx,
                             danger=flames, max_dist=8)
            if path:
                return (path[0][0] - p.col, path[0][1] - p.row), False

        # 2) Déjà adjacent à un bloc/ennemi → tenter de poser la bombe
        if _near_bombable(pidx, players, grid):
            can_bomb = (p.active_bombs < p.max_bombs
                        and not any(b.col == p.col and b.row == p.row for b in bombs))
            if can_bomb and _can_escape_after_bomb(pos, pidx, players, grid, bombs,
                                                   p.bomb_range, flames):
                st.state = _AI_FLEE
                return None, True  # poser la bombe CE tick
            # Pas encore possible (cd ou pas d'échappatoire) : attendre un peu
            st.pause = random.uniform(0.3, 0.7)
            return None, False

        # 3) Se diriger vers la case adjacent-bloc la plus proche
        targets = _bombable_targets(pidx, players, grid)
        if targets:
            path = _bfs_path(pos, targets, grid, players, bombs, pidx, danger=flames)
            if path:
                return (path[0][0] - p.col, path[0][1] - p.row), False

        # Rien d'accessible, courte attente
        st.pause = random.uniform(0.5, 1.0)
        return None, False

    # ── FLEE ─────────────────────────────────────────────────────────────────
    if st.state == _AI_FLEE:
        # Cases safe = hors du souffle de toutes les bombes ET hors des flammes
        safe = {(c, r) for r in range(1, ROWS - 1) for c in range(1, COLS - 1)
                if grid[r][c] == EMPTY
                and (c, r) not in all_blast
                and (c, r) not in flames}

        # Déjà en zone safe ?
        if pos in safe:
            st.state = _AI_WAIT_SAFE
            st.pause = random.uniform(0.3, 0.7)
            return None, False

        # BFS vers case safe — peut traverser les blasts (pas de danger=)
        # mais évite les flammes actives (mortel immédiat)
        path = _bfs_path(pos, safe, grid, players, bombs, pidx,
                         danger=flames, ignore_bombs=True)
        if path:
            return (path[0][0] - p.col, path[0][1] - p.row), False

        # BFS encore plus permissif (ignore même les flammes en dernier recours)
        path = _bfs_path(pos, safe, grid, players, bombs, pidx, ignore_bombs=True)
        if path:
            return (path[0][0] - p.col, path[0][1] - p.row), False

        # Mouvement brut : n'importe quelle case libre hors flammes
        dirs = list(_DIRS)
        random.shuffle(dirs)
        for dx, dy in dirs:
            nc, nr = p.col + dx, p.row + dy
            if not _is_blocked(nc, nr, grid, players, bombs, pidx) and (nc, nr) not in flames:
                return (dx, dy), False
        for dx, dy in dirs:
            nc, nr = p.col + dx, p.row + dy
            if not _is_blocked(nc, nr, grid, players, bombs, pidx):
                return (dx, dy), False
        return None, False

    # ── WAIT_SAFE ─────────────────────────────────────────────────────────────
    if st.state == _AI_WAIT_SAFE:
        # Danger immédiat → fuit
        if pos in flames or on_bomb or pos in all_blast:
            st.state = _AI_FLEE
            return None, False

        # Pause naturelle avant de bouger
        st.pause -= dt
        if st.pause > 0:
            return None, False

        # Cases considérées comme sûres pour se déplacer : hors de tout blast actif ET flammes
        safe_cells = {(c, r) for r in range(1, ROWS - 1) for c in range(1, COLS - 1)
                      if grid[r][c] == EMPTY
                      and (c, r) not in all_blast
                      and (c, r) not in flames}

        # ── Multi-bombe : si adjacent à un bloc/ennemi et bombe dispo → poser ──
        if _near_bombable(pidx, players, grid):
            can_bomb = (p.active_bombs < p.max_bombs
                        and not any(b.col == p.col and b.row == p.row for b in bombs))
            if can_bomb and _can_escape_after_bomb(pos, pidx, players, grid, bombs,
                                                   p.bomb_range, flames):
                st.state = _AI_FLEE
                return None, True  # poser la bombe maintenant

        # ── Se déplacer vers la prochaine cible EN RESTANT sur des cases sûres ──
        targets = _bombable_targets(pidx, players, grid)
        if targets:
            # BFS strict : ne passe que par des cases safe (pas dans all_blast, pas de flammes)
            path = _bfs_path(pos, targets, grid, players, bombs, pidx,
                             danger=all_blast | flames)
            if path:
                next_cell = path[0]
                # Double-check que la prochaine case est safe
                if next_cell in safe_cells:
                    st.pause = 0.0  # mouvement fluide, pas de pause entre chaque case
                    return (next_cell[0] - p.col, next_cell[1] - p.row), False

        # Rien à faire : quand toutes les bombes ont explosé → SEEK
        if not bombs:
            st.state = _AI_SEEK
            st.pause = random.uniform(0.3, 0.8)
        return None, False

    # Fallback
    st.state = _AI_SEEK
    st.pause = 0.5
    return None, False


# ── Rendu ──────────────────────────────────────────────────────────────────────

# Palette visuelle par thème : (bg, wall_main, wall_hi, block_main, block_hi, floor)
_THEME_PALETTE = {
    # Classique : béton gris + caisses en bois marron
    'classic':   ((15,  15,  25),  (70,  70,  90),  (90,  90, 115),
                  (120, 75,  45),  (160, 110, 60),   (35,  35,  50)),
    # Labyrinthe : donjon sombre, murs de pierre noire + pierres mousseuses
    'labyrinth': ((10,  10,  15),  (45,  45,  55),  (65,  65,  80),
                  (60,  80,  50),  (85,  110, 65),   (22,  22,  30)),
    # Arène : sable chaud, murs de grès ocre + tonneaux rouges
    'arena':     ((30,  22,  10),  (160, 120, 60),  (200, 160, 90),
                  (180, 60,  40),  (220, 90,  60),   (50,  38,  18)),
    # Tunnels : acier industriel, murs métalliques + caisses orangées
    'tunnels':   ((12,  14,  18),  (55,  65,  80),  (80,  95, 115),
                  (180, 100, 30),  (220, 140, 50),   (20,  24,  30)),
    # Croix : glace / cristal, murs bleu-blanc + blocs cyan givré
    'cross':     ((8,   18,  35),  (100, 160, 210), (150, 200, 240),
                  (50,  160, 180), (90,  200, 220),  (15,  30,  55)),
    # Girly : fond violet doux, murs rose fuchsia + blocs rose candy
    'girly':     ((35,  10,  40),  (210, 80,  160), (240, 130, 200),
                  (255, 140, 190), (255, 190, 220),  (60,  20,  70)),
    # Neon : fond noir profond, murs vert fluo + blocs magenta électrique
    'neon':      ((5,   5,   5),   (0,   230, 120), (80,  255, 170),
                  (220, 0,   200), (255, 60,  240),  (12,  12,  12)),
    # Forêt : sous-bois sombre, murs bois vert foncé + troncs brun clair
    'forest':    ((8,   20,  8),   (40,  80,  30),  (65,  120, 45),
                  (110, 70,  30),  (150, 105, 50),   (15,  35,  12)),
    # Feu / lave : fond noir brûlé, murs roche volcanique + blocs braise
    'lava':      ((18,  5,   0),   (90,  30,  10),  (140, 55,  15),
                  (220, 80,  0),   (255, 130, 20),   (30,  10,  5)),
    # Pastel 8-bit : fond gris chiné, murs lilas + blocs jaune beurre
    'pastel':    ((45,  40,  55),  (160, 130, 200), (195, 170, 230),
                  (240, 220, 100), (255, 240, 150),  (60,  55,  75)),
}


def _draw_grid(surface, grid, explosions, theme='classic'):
    pal = _THEME_PALETTE.get(theme, _THEME_PALETTE['classic'])
    bg_col, wall_col, wall_hi, block_col, block_hi, floor_col = pal

    explo_cells = set()
    for ex in explosions:
        explo_cells |= ex.cells

    for r in range(ROWS):
        for c in range(COLS):
            rx   = GRID_X + c * CELL
            ry   = GRID_Y + r * CELL
            rect = pygame.Rect(rx, ry, CELL - 1, CELL - 1)

            if (c, r) in explo_cells:
                pygame.draw.rect(surface, EXPLO_BEAM,   rect, border_radius=2)
                inner = rect.inflate(-8, -8)
                pygame.draw.rect(surface, EXPLO_CENTER, inner, border_radius=2)
            elif grid[r][c] == WALL:
                pygame.draw.rect(surface, wall_col,  rect, border_radius=2)
                pygame.draw.rect(surface, wall_hi,
                                 (rx + 2, ry + 2, CELL - 5, 4), border_radius=1)
            elif grid[r][c] == BLOCK:
                pygame.draw.rect(surface, block_col, rect, border_radius=2)
                pygame.draw.rect(surface, block_hi,
                                 (rx + 2, ry + 2, CELL - 5, 4), border_radius=1)
                # Petite croix décorative sur le bloc (visible sur tous les thèmes)
                mid = CELL // 2 - 1
                dark = (max(0, block_col[0]-40), max(0, block_col[1]-40), max(0, block_col[2]-40))
                pygame.draw.rect(surface, dark, (rx + mid - 1, ry + 4,  3, CELL - 9))
                pygame.draw.rect(surface, dark, (rx + 4, ry + mid - 1, CELL - 9, 3))
            else:
                pygame.draw.rect(surface, floor_col, rect, border_radius=2)


def _draw_bombs(surface, bombs, t):
    for b in bombs:
        cx = GRID_X + b.col * CELL + CELL // 2
        cy = GRID_Y + b.row * CELL + CELL // 2
        r  = CELL // 2 - 4

        freq  = 4 + (1.0 - max(0, b.timer) / BOMB_TIMER) * 12
        pulse = 1.0 + 0.18 * math.sin(t * freq)
        pr    = max(2, int(r * pulse))

        pygame.draw.circle(surface, (40, 40, 40), (cx, cy), pr + 1)
        pygame.draw.circle(surface, BOMB_COLOR,   (cx, cy), pr)
        pygame.draw.circle(surface, (60, 60, 60), (cx - pr // 3, cy - pr // 3), pr // 3)

        pygame.draw.line(surface, FUSE_COLOR, (cx, cy - pr), (cx + 4, cy - pr - 7), 2)
        spark = cy - pr - 7 - int(3 * math.sin(t * 18))
        pygame.draw.circle(surface, (255, 255, 120), (cx + 4, spark), 2)


def _draw_player_char(surface, cx, cy, color, player_idx):
    """Personnage cubique style Bomberman – 4 styles de chapeau."""
    skin  = (255, 210, 160)
    white = (255, 255, 255)
    black = (10,  10,  10)
    dark  = (max(0, color[0] - 60), max(0, color[1] - 60), max(0, color[2] - 60))
    light = (min(255, color[0] + 60), min(255, color[1] + 60), min(255, color[2] + 60))

    # ── Chapeau ──────────────────────────────────────────────────────────────
    if player_idx == 0:
        # Bonnet carré blanc + bande colorée
        pygame.draw.rect(surface, white, (cx - 6, cy - 16, 12, 8))
        pygame.draw.rect(surface, color, (cx - 6, cy - 10, 12, 2))
        pygame.draw.rect(surface, white, (cx - 8, cy -  9, 16, 3))
    elif player_idx == 1:
        # Casquette colorée à visière
        pygame.draw.rect(surface, color, (cx - 6, cy - 16, 12, 6))
        pygame.draw.rect(surface, dark,  (cx - 8, cy - 11, 16, 2))
        pygame.draw.rect(surface, dark,  (cx + 2, cy - 13,  6, 2))
    elif player_idx == 2:
        # Casque robot avec antenne (IA 1)
        pygame.draw.rect(surface, (130, 135, 150), (cx - 7, cy - 16, 14, 8))
        pygame.draw.rect(surface, (170, 175, 190), (cx - 7, cy - 16, 14, 3))
        pygame.draw.rect(surface, color, (cx - 5, cy - 13, 10, 2))
        pygame.draw.rect(surface, (130, 135, 150), (cx, cy - 22, 2, 6))
        pygame.draw.circle(surface, (255, 60, 60), (cx + 1, cy - 23), 2)
    else:
        # Couronne dorée (IA 2)
        gold      = (255, 210, 50)
        dark_gold = (200, 160, 0)
        pygame.draw.rect(surface, gold, (cx - 7, cy - 14, 14, 6))
        pygame.draw.rect(surface, gold, (cx - 6, cy - 19, 3, 5))
        pygame.draw.rect(surface, gold, (cx - 1, cy - 20, 3, 6))
        pygame.draw.rect(surface, gold, (cx + 4, cy - 19, 3, 5))
        pygame.draw.rect(surface, (255, 50, 50), (cx - 5, cy - 17, 2, 2))
        pygame.draw.rect(surface, color,         (cx,     cy - 18, 2, 2))
        pygame.draw.rect(surface, (255, 50, 50), (cx + 4, cy - 17, 2, 2))
        pygame.draw.rect(surface, dark_gold, (cx - 7, cy - 14, 14, 6), 1)

    # ── Tête ─────────────────────────────────────────────────────────────────
    pygame.draw.rect(surface, skin,  (cx - 6, cy - 9, 12, 9))
    pygame.draw.rect(surface, (min(255,skin[0]+30), min(255,skin[1]+20), min(255,skin[2]+10)),
                     (cx - 6, cy - 9, 12, 2))
    pygame.draw.rect(surface, black, (cx - 6, cy - 9, 12, 9), 1)

    pygame.draw.rect(surface, black, (cx - 4, cy - 6, 2, 2))
    pygame.draw.rect(surface, black, (cx + 2, cy - 6, 2, 2))
    pygame.draw.rect(surface, white, (cx - 4, cy - 7, 1, 1))
    pygame.draw.rect(surface, white, (cx + 2, cy - 7, 1, 1))
    pygame.draw.rect(surface, dark, (cx - 3, cy - 2, 6, 1))

    # ── Corps ────────────────────────────────────────────────────────────────
    pygame.draw.rect(surface, color, (cx - 6, cy,  12, 8))
    pygame.draw.rect(surface, light, (cx - 6, cy,  12, 2))
    pygame.draw.rect(surface, dark,  (cx - 6, cy + 6, 12, 2))
    pygame.draw.rect(surface, black, (cx - 6, cy,  12, 8), 1)

    # ── Jambes ───────────────────────────────────────────────────────────────
    pygame.draw.rect(surface, dark,  (cx - 6, cy +  8, 4, 6))
    pygame.draw.rect(surface, dark,  (cx + 2, cy +  8, 4, 6))
    pygame.draw.rect(surface, black, (cx - 6, cy +  8, 4, 6), 1)
    pygame.draw.rect(surface, black, (cx + 2, cy +  8, 4, 6), 1)


_BONUS_COLORS = {
    BONUS_BOMB:  (255, 140,  30),
    BONUS_RANGE: (255, 220,  40),
    BONUS_SPEED: ( 60, 210,  90),
}
_BONUS_LABELS = {
    BONUS_BOMB: 'B', BONUS_RANGE: '+', BONUS_SPEED: '>',
}


def _draw_bonuses(surface, bonuses, t, font):
    for bx in bonuses:
        rx  = GRID_X + bx.col * CELL
        ry  = GRID_Y + bx.row * CELL
        col = _BONUS_COLORS.get(bx.type, (200, 200, 200))
        dark_col = (max(0, col[0] - 70), max(0, col[1] - 70), max(0, col[2] - 70))
        pulse = 0.85 + 0.15 * math.sin(t * 6)

        pygame.draw.rect(surface, (18, 18, 28), (rx + 2, ry + 2, CELL - 5, CELL - 5))

        pad = 5
        bw  = int((CELL - pad * 2) * pulse)
        bh  = int((CELL - pad * 2) * pulse)
        bx_ = rx + (CELL - bw) // 2
        by_ = ry + (CELL - bh) // 2

        pygame.draw.rect(surface, dark_col, (bx_ - 1, by_ - 1, bw + 2, bh + 2))
        pygame.draw.rect(surface, col,      (bx_,     by_,     bw,     bh    ))
        pygame.draw.rect(surface,
                         (min(255, col[0] + 80), min(255, col[1] + 80), min(255, col[2] + 80)),
                         (bx_ + 1, by_ + 1, bw - 2, 3))

        lbl = font.render(_BONUS_LABELS.get(bx.type, '?'), True, (255, 255, 255))
        cx_ = rx + CELL // 2
        cy_ = ry + CELL // 2
        surface.blit(lbl, (cx_ - lbl.get_width() // 2, cy_ - lbl.get_height() // 2))


def _draw_players(surface, players, font=None):
    for i, p in enumerate(players):
        if not p.alive:
            cx = GRID_X + p.col * CELL + CELL // 2
            cy = GRID_Y + p.row * CELL + CELL // 2
            pygame.draw.line(surface, (180, 60, 60), (cx - 8, cy - 8), (cx + 8, cy + 8), 3)
            pygame.draw.line(surface, (180, 60, 60), (cx + 8, cy - 8), (cx - 8, cy + 8), 3)
            continue

        cx = GRID_X + p.col * CELL + CELL // 2
        cy = GRID_Y + p.row * CELL + CELL // 2 + 5
        _draw_player_char(surface, cx, cy, p.color, i)


def _draw_ui(surface, players, font):
    pygame.draw.rect(surface, UI_BG_COLOR, (0, 0, SCREEN_WIDTH, GRID_Y))
    pygame.draw.line(surface, (50, 50, 70), (0, GRID_Y - 1), (SCREEN_WIDTH, GRID_Y - 1))

    # 2 lignes : J1/J2 en haut, IA1/IA2 en bas
    rows = [(0, 1), (2, 3)]
    for row_i, (idx_a, idx_b) in enumerate(rows):
        y = 2 + row_i * 15
        for slot, idx in enumerate((idx_a, idx_b)):
            if idx >= len(players):
                continue
            p = players[idx]
            x = 4 + slot * (SCREEN_WIDTH // 2)
            pygame.draw.rect(surface, p.color, (x, y + 1, 8, 8))
            if not p.alive:
                lbl = font.render(f"{_PLAYER_LABELS[idx]} MORT", True, (180, 60, 60))
            else:
                spd = max(0, round((MOVE_COOLDOWN - p.move_cooldown) / BONUS_SPEED_GAIN))
                lbl = font.render(f"{_PLAYER_LABELS[idx]} B:{p.max_bombs} R:{p.bomb_range} V:{spd}",
                                  True, TEXT_COLOR)
            surface.blit(lbl, (x + 11, y))


# ── Boucle principale ─────────────────────────────────────────────────────────

def run(screen, joysticks):
    clock  = pygame.time.Clock()
    f_sm   = pygame.font.SysFont("Arial", 11, bold=True)
    f_ui   = pygame.font.SysFont("Arial", 10, bold=True)
    sounds = sound_manager.BombermanSounds()

    joy_p1     = joysticks[0] if len(joysticks) > 0 else None
    has_p2_joy = len(joysticks) > 1

    grid, theme = _make_grid()
    players = [
        Player(1,          1,          P1_COLOR),   # J1  haut-gauche
        Player(COLS - 2,   ROWS - 2,   P2_COLOR),   # J2  bas-droite
        Player(COLS - 2,   1,          P3_COLOR),   # IA1 haut-droite
        Player(1,          ROWS - 2,   P4_COLOR),   # IA2 bas-gauche
    ]
    bombs      = []
    explosions = []
    bonuses    = []

    # Machines à états pour les IA (indices 2 et 3)
    ai_states = {2: AIState(), 3: AIState()}

    # Suivi de l'ordre d'élimination (groupes de morts simultanées)
    elimination_order = []

    p1_btns = set()
    p2_btns = set()
    bomb_press = [False, False, False, False]

    quit_combo = QuitCombo()
    t          = 0.0
    rain_timer = 0.0   # compte à rebours avant la prochaine bombe de pluie

    while True:
        dt = clock.tick(FPS) / 1000.0
        t += dt

        bomb_press = [False, False, False, False]

        events = pygame.event.get()
        for e in events:
            quit_combo.handle_event(e)

            if e.type == pygame.QUIT:
                return None

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return None
                if e.key == pygame.K_e:
                    bomb_press[0] = True
                if e.key == pygame.K_p:
                    bomb_press[1] = True

            if e.type == pygame.JOYBUTTONDOWN:
                joy_idx = getattr(e, 'joy', 0)
                if joy_idx == 0:
                    p1_btns.add(e.button)
                    if not has_p2_joy:
                        p2_btns.add(e.button)
                else:
                    p2_btns.add(e.button)

                if joy_idx == 0 and e.button == BTN_P1_BOMB:
                    bomb_press[0] = True
                if (joy_idx == 1 or not has_p2_joy) and e.button == BTN_P2_BOMB:
                    bomb_press[1] = True

            if e.type == pygame.JOYBUTTONUP:
                joy_idx = getattr(e, 'joy', 0)
                if joy_idx == 0:
                    p1_btns.discard(e.button)
                    if not has_p2_joy:
                        p2_btns.discard(e.button)
                else:
                    p2_btns.discard(e.button)

        keys = pygame.key.get_pressed()

        # ── Déplacement joueurs humains (J1 et J2) ───────────────────────────
        for idx in range(2):
            p = players[idx]
            if not p.alive:
                continue
            p.move_cd = max(0.0, p.move_cd - dt)
            p.bomb_cd = max(0.0, p.bomb_cd - dt)

            if p.move_cd <= 0.0:
                d = _get_p1_dir(keys, joy_p1) if idx == 0 else _get_p2_dir(keys, p2_btns)
                if d:
                    nc, nr = p.col + d[0], p.row + d[1]
                    if not _is_blocked(nc, nr, grid, players, bombs, idx):
                        p.col, p.row = nc, nr
                    p.move_cd = p.move_cooldown

            if bomb_press[idx] and p.bomb_cd <= 0.0 and p.active_bombs < p.max_bombs:
                if not any(b.col == p.col and b.row == p.row for b in bombs):
                    bombs.append(Bomb(p.col, p.row, idx, p.bomb_range))
                    p.active_bombs += 1
                    p.bomb_cd = BOMB_PLACE_CD
                    sounds.play('bomb_place')

        # ── Déplacement joueurs IA (IA1 et IA2) ─────────────────────────────
        for idx in range(2, 4):
            p = players[idx]
            if not p.alive:
                continue
            p.move_cd = max(0.0, p.move_cd - dt)
            p.bomb_cd = max(0.0, p.bomb_cd - dt)

            ai_dir, ai_bomb = _ai_update(idx, ai_states[idx], players, grid,
                                         bombs, explosions, bonuses, dt)

            # Filet de sécurité : si l'IA est sur une bombe et ne bouge pas,
            # forcer un déplacement vers une case libre SANS flammes
            if ai_dir is None and any(b.col == p.col and b.row == p.row for b in bombs):
                _flames = _active_explo_cells(explosions)
                for dx, dy in _DIRS:
                    nc, nr = p.col + dx, p.row + dy
                    if not _is_blocked(nc, nr, grid, players, bombs, idx) \
                            and (nc, nr) not in _flames:
                        ai_dir = (dx, dy)
                        break
                if ai_dir is None:
                    for dx, dy in _DIRS:
                        nc, nr = p.col + dx, p.row + dy
                        if not _is_blocked(nc, nr, grid, players, bombs, idx):
                            ai_dir = (dx, dy)
                            break

            if p.move_cd <= 0.0 and ai_dir:
                nc, nr = p.col + ai_dir[0], p.row + ai_dir[1]
                if not _is_blocked(nc, nr, grid, players, bombs, idx):
                    p.col, p.row = nc, nr
                p.move_cd = p.move_cooldown

            if ai_bomb and p.bomb_cd <= 0.0 and p.active_bombs < p.max_bombs:
                if not any(b.col == p.col and b.row == p.row for b in bombs):
                    bombs.append(Bomb(p.col, p.row, idx, p.bomb_range))
                    p.active_bombs += 1
                    p.bomb_cd = BOMB_PLACE_CD
                    sounds.play('bomb_place')

        # ── Ramassage des bonus ──────────────────────────────────────────────
        for p in players:
            if not p.alive:
                continue
            for bx in bonuses[:]:
                if p.col == bx.col and p.row == bx.row:
                    _apply_bonus(p, bx.type)
                    bonuses.remove(bx)
                    sounds.play('bonus')

        # ── Mise à jour bombes ───────────────────────────────────────────────
        for b in bombs:
            b.timer -= dt
            b.next_tick -= dt
            if b.next_tick <= 0.0:
                sounds.play('fuse_tick')
                b.next_tick = 0.12 + 0.55 * max(0.0, b.timer / BOMB_TIMER)
        to_explode = [b for b in bombs if b.timer <= 0.0]
        if to_explode:
            n_explo_before = len(explosions)
            bombs, destroyed_cells = _process_explosions(to_explode, bombs, grid, players, explosions)
            for _ in range(len(explosions) - n_explo_before):
                sounds.play('explosion')
            for dc, dr in destroyed_cells:
                if random.random() < BONUS_SPAWN_CHANCE:
                    if not any(bx.col == dc and bx.row == dr for bx in bonuses):
                        bonuses.append(Bonus(dc, dr, random.choice([BONUS_BOMB, BONUS_RANGE, BONUS_SPEED])))

        # ── Mise à jour explosions ───────────────────────────────────────────
        for ex in explosions:
            ex.timer -= dt
        explosions = [ex for ex in explosions if ex.timer > 0.0]

        # ── Mort subite : pluie de bombes ─────────────────────────────────────
        if t >= SUDDEN_DEATH:
            rain_timer -= dt
            if rain_timer <= 0.0:
                elapsed_sd    = t - SUDDEN_DEATH
                rain_interval = max(0.2, 2.0 - elapsed_sd * 0.025)
                rain_timer    = rain_interval
                candidates = [
                    (c, r)
                    for r in range(1, ROWS - 1)
                    for c in range(1, COLS - 1)
                    if grid[r][c] != WALL
                    and not any(b.col == c and b.row == r for b in bombs)
                ]
                if candidates:
                    rc, rr  = random.choice(candidates)
                    rb      = Bomb(rc, rr, -1, 3)
                    rb.timer = 1.8   # mèche courte
                    bombs.append(rb)
                    sounds.play('bomb_place')
        all_explo = set()
        for ex in explosions:
            all_explo |= ex.cells
        prev_alive = [p.alive for p in players]
        for p in players:
            if p.alive and (p.col, p.row) in all_explo:
                p.alive = False
        newly_dead = [i for i in range(4) if prev_alive[i] and not players[i].alive]
        if newly_dead:
            elimination_order.append(newly_dead)
            for _ in newly_dead:
                sounds.play('death')

        # ── Condition de fin : ≤ 1 joueur en vie ────────────────────────────
        alive = [i for i in range(4) if players[i].alive]
        if len(alive) <= 1:
            # Rendu final puis pause
            screen.fill(BG_COLOR)
            _draw_grid(screen, grid, explosions, theme)
            _draw_bonuses(screen, bonuses, t, f_sm)
            _draw_bombs(screen, bombs, t)
            _draw_players(screen, players, f_sm)
            _draw_ui(screen, players, f_ui)
            pygame.display.flip()
            pygame.time.wait(1200)

            # Construire le classement : survivant(s) puis éliminés (dernier mort → premier)
            rankings = []
            if alive:
                rankings.append(alive)
            for group in reversed(elimination_order):
                rankings.append(group)
            return rankings

        # ── Rendu ────────────────────────────────────────────────────────────
        screen.fill(BG_COLOR)
        _draw_grid(screen, grid, explosions, theme)
        _draw_bonuses(screen, bonuses, t, f_sm)
        _draw_bombs(screen, bombs, t)
        _draw_players(screen, players, f_sm)
        _draw_ui(screen, players, f_ui)

        # ── Compte à rebours / alerte mort subite ───────────────────────────
        if t >= SUDDEN_DEATH:
            if int(t * 3) % 2 == 0:
                sd_surf = f_sm.render('  !! MORT SUBITE !!  ', True, (255, 50, 50))
                sx = (SCREEN_WIDTH - sd_surf.get_width()) // 2
                screen.blit(sd_surf, (sx, 4))
        else:
            countdown = SUDDEN_DEATH - t
            if countdown <= 10.0:
                lbl = f'Mort subite dans {int(countdown) + 1}s'
                c_surf = f_sm.render(lbl, True, (255, 180, 0))
                sx = (SCREEN_WIDTH - c_surf.get_width()) // 2
                screen.blit(c_surf, (sx, 4))

        if quit_combo.update_and_draw(screen):
            return None

        pygame.display.flip()
