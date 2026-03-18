"""
Scène de jeu Bomberman – 2 joueurs.
Retourne 0 (J1 gagne), 1 (J2 gagne), 2 (égalité), ou None (quitter).
"""
import pygame
import random
import math

from config import *
from quit_combo import QuitCombo


# ── Génération de la grille ───────────────────────────────────────────────────

def _make_grid():
    grid = [[EMPTY] * COLS for _ in range(ROWS)]

    # Murs de bordure
    for c in range(COLS):
        grid[0][c] = WALL
        grid[ROWS - 1][c] = WALL
    for r in range(ROWS):
        grid[r][0] = WALL
        grid[r][COLS - 1] = WALL

    # Piliers internes (lignes paires ET colonnes paires)
    for r in range(2, ROWS - 1, 2):
        for c in range(2, COLS - 1, 2):
            grid[r][c] = WALL

    # Zones dégagées autour des spawns
    safe = {
        (1, 1), (2, 1), (1, 2),
        (COLS - 2, ROWS - 2), (COLS - 3, ROWS - 2), (COLS - 2, ROWS - 3),
    }

    # Blocs destructibles aléatoires
    for r in range(1, ROWS - 1):
        for c in range(1, COLS - 1):
            if grid[r][c] == EMPTY and (c, r) not in safe:
                if random.random() < 0.60:
                    grid[r][c] = BLOCK

    return grid


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
        self.col   = col
        self.row   = row
        self.timer = BOMB_TIMER
        self.range = bomb_range
        self.owner = owner_idx


class Explosion:
    def __init__(self, cells):
        self.cells = cells   # set of (col, row)
        self.timer = EXPLOSION_DUR


class Bonus:
    def __init__(self, col, row, bonus_type):
        self.col  = col
        self.row  = row
        self.type = bonus_type


# ── Helpers de contrôle ───────────────────────────────────────────────────────

def _get_p1_dir(keys, joystick):
    """Direction (dx, dy) de J1 via D-pad/hat ou ZQSD."""
    if joystick:
        try:
            hx, hy = joystick.get_hat(0)
            if hx != 0 or hy != 0:
                return hx, -hy   # hat y+1 = haut → row-1
        except Exception:
            pass
    if keys[pygame.K_z]:  return  0, -1
    if keys[pygame.K_s]:  return  0,  1
    if keys[pygame.K_q]:  return -1,  0
    if keys[pygame.K_d]:  return  1,  0
    return None


def _get_p2_dir(keys, p2_btns):
    """Direction (dx, dy) de J2 via boutons ABXY ou OKLM."""
    if BTN_X in p2_btns: return  0, -1   # X = haut
    if BTN_B in p2_btns: return  0,  1   # B = bas
    if BTN_Y in p2_btns: return -1,  0   # Y = gauche
    if BTN_A in p2_btns: return  1,  0   # A = droite
    if keys[pygame.K_o]:  return  0, -1
    if keys[pygame.K_l]:  return  0,  1
    if keys[pygame.K_k]:  return -1,  0
    if keys[pygame.K_m]:  return  1,  0
    return None


def _is_blocked(col, row, grid, players, bombs, exclude_player=-1):
    """True si la case (col, row) est infranchissable."""
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
    """
    Calcule les cellules touchées, les blocs à détruire,
    et les bombes qui entrent en chaîne.
    """
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
                break   # la flamme s'arrête sur le bloc

    return cells, destroy, chain


def _process_explosions(to_explode, bombs, grid, players, explosions):
    """Fait exploser une liste de bombes avec réactions en chaîne."""
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

    # Retirer les bombes explosées
    return [b for b in bombs if id(b) not in processed], all_destroyed


def _apply_bonus(player, bonus_type):
    if bonus_type == BONUS_BOMB:
        player.max_bombs = min(BONUS_MAX_BOMBS, player.max_bombs + 1)
    elif bonus_type == BONUS_RANGE:
        player.bomb_range = min(BONUS_MAX_RANGE, player.bomb_range + 1)
    elif bonus_type == BONUS_SPEED:
        player.move_cooldown = max(BONUS_MIN_CD, player.move_cooldown - BONUS_SPEED_GAIN)


# ── Rendu ──────────────────────────────────────────────────────────────────────

def _draw_grid(surface, grid, explosions):
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
                pygame.draw.rect(surface, WALL_COLOR,  rect, border_radius=2)
                # Reflet
                pygame.draw.rect(surface, (90, 90, 115),
                                 (rx + 2, ry + 2, CELL - 5, 4), border_radius=1)
            elif grid[r][c] == BLOCK:
                pygame.draw.rect(surface, BLOCK_COLOR, rect, border_radius=2)
                pygame.draw.rect(surface, (140, 90, 55),
                                 (rx + 2, ry + 2, CELL - 5, 4), border_radius=1)
            else:
                pygame.draw.rect(surface, EMPTY_COLOR, rect, border_radius=2)


def _draw_bombs(surface, bombs, t):
    for b in bombs:
        cx = GRID_X + b.col * CELL + CELL // 2
        cy = GRID_Y + b.row * CELL + CELL // 2
        r  = CELL // 2 - 4

        # Pulsation accélère quand timer baisse
        freq  = 4 + (1.0 - max(0, b.timer) / BOMB_TIMER) * 12
        pulse = 1.0 + 0.18 * math.sin(t * freq)
        pr    = max(2, int(r * pulse))

        pygame.draw.circle(surface, (40, 40, 40), (cx, cy), pr + 1)   # ombre
        pygame.draw.circle(surface, BOMB_COLOR,   (cx, cy), pr)
        pygame.draw.circle(surface, (60, 60, 60), (cx - pr // 3, cy - pr // 3), pr // 3)  # reflet

        # Mèche
        pygame.draw.line(surface, FUSE_COLOR, (cx, cy - pr), (cx + 4, cy - pr - 7), 2)
        spark = cy - pr - 7 - int(3 * math.sin(t * 18))
        pygame.draw.circle(surface, (255, 255, 120), (cx + 4, spark), 2)


def _draw_player_char(surface, cx, cy, color, player_idx):
    """
    Personnage cubique style Bomberman – 100% rectangles.
    Tout est aligné sur une grille de 2px pour un look pixel-art net.
    """
    skin  = (255, 210, 160)
    white = (255, 255, 255)
    black = (10,  10,  10)
    dark  = (max(0, color[0] - 60), max(0, color[1] - 60), max(0, color[2] - 60))
    light = (min(255, color[0] + 60), min(255, color[1] + 60), min(255, color[2] + 60))

    # ── Chapeau ───────────────────────────────────────────────────────────────
    if player_idx == 0:
        # Bonnet carré blanc + bande colorée
        pygame.draw.rect(surface, white, (cx - 6, cy - 16, 12, 8))   # calotte
        pygame.draw.rect(surface, color, (cx - 6, cy - 10, 12, 2))   # bande
        pygame.draw.rect(surface, white, (cx - 8, cy -  9, 16, 3))   # rebord
    else:
        # Casquette colorée à visière
        pygame.draw.rect(surface, color, (cx - 6, cy - 16, 12, 6))   # calotte
        pygame.draw.rect(surface, dark,  (cx - 8, cy - 11, 16, 2))   # rebord
        pygame.draw.rect(surface, dark,  (cx + 2, cy - 13,  6, 2))   # visière

    # ── Tête (cube chair) ─────────────────────────────────────────────────────
    pygame.draw.rect(surface, skin,  (cx - 6, cy - 9, 12, 9))
    # Face claire (côté haut-gauche)
    pygame.draw.rect(surface, (min(255,skin[0]+30), min(255,skin[1]+20), min(255,skin[2]+10)),
                     (cx - 6, cy - 9, 12, 2))
    # Contour sombre
    pygame.draw.rect(surface, black, (cx - 6, cy - 9, 12, 9), 1)

    # Yeux (2×2 px)
    pygame.draw.rect(surface, black, (cx - 4, cy - 6, 2, 2))
    pygame.draw.rect(surface, black, (cx + 2, cy - 6, 2, 2))
    # Reflet œil (1×1)
    pygame.draw.rect(surface, white, (cx - 4, cy - 7, 1, 1))
    pygame.draw.rect(surface, white, (cx + 2, cy - 7, 1, 1))

    # Bouche (petite barre sombre)
    pygame.draw.rect(surface, dark, (cx - 3, cy - 2, 6, 1))

    # ── Corps ─────────────────────────────────────────────────────────────────
    pygame.draw.rect(surface, color, (cx - 6, cy,  12, 8))
    pygame.draw.rect(surface, light, (cx - 6, cy,  12, 2))   # reflet haut
    pygame.draw.rect(surface, dark,  (cx - 6, cy + 6, 12, 2))  # ombre bas
    pygame.draw.rect(surface, black, (cx - 6, cy,  12, 8), 1)

    # ── Jambes ────────────────────────────────────────────────────────────────
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

        # Fond sombre sur toute la case
        pygame.draw.rect(surface, (18, 18, 28), (rx + 2, ry + 2, CELL - 5, CELL - 5))

        # Carré coloré centré, taille fixe lisible
        pad = 5
        bw  = int((CELL - pad * 2) * pulse)
        bh  = int((CELL - pad * 2) * pulse)
        bx_ = rx + (CELL - bw) // 2
        by_ = ry + (CELL - bh) // 2

        pygame.draw.rect(surface, dark_col, (bx_ - 1, by_ - 1, bw + 2, bh + 2))
        pygame.draw.rect(surface, col,      (bx_,     by_,     bw,     bh    ))
        # Reflet
        pygame.draw.rect(surface,
                         (min(255, col[0] + 80), min(255, col[1] + 80), min(255, col[2] + 80)),
                         (bx_ + 1, by_ + 1, bw - 2, 3))

        # Lettre blanche par-dessus
        lbl = font.render(_BONUS_LABELS.get(bx.type, '?'), True, (255, 255, 255))
        cx_ = rx + CELL // 2
        cy_ = ry + CELL // 2
        surface.blit(lbl, (cx_ - lbl.get_width() // 2, cy_ - lbl.get_height() // 2))


def _draw_players(surface, players, font=None):
    for i, p in enumerate(players):
        if not p.alive:
            # Croix de mort
            cx = GRID_X + p.col * CELL + CELL // 2
            cy = GRID_Y + p.row * CELL + CELL // 2
            pygame.draw.line(surface, (180, 60, 60), (cx - 8, cy - 8), (cx + 8, cy + 8), 3)
            pygame.draw.line(surface, (180, 60, 60), (cx + 8, cy - 8), (cx - 8, cy + 8), 3)
            continue

        cx = GRID_X + p.col * CELL + CELL // 2
        cy = GRID_Y + p.row * CELL + CELL // 2 + 5   # légère descente pour centrer visuellement
        _draw_player_char(surface, cx, cy, p.color, i)


def _draw_ui(surface, players, font):
    pygame.draw.rect(surface, UI_BG_COLOR, (0, 0, SCREEN_WIDTH, GRID_Y))
    pygame.draw.line(surface, (50, 50, 70), (0, GRID_Y - 1), (SCREEN_WIDTH, GRID_Y - 1))

    bonus_icons = {BONUS_BOMB: ('B', _BONUS_COLORS[BONUS_BOMB]),
                   BONUS_RANGE:('+', _BONUS_COLORS[BONUS_RANGE]),
                   BONUS_SPEED:('>', _BONUS_COLORS[BONUS_SPEED])}
    for i, p in enumerate(players):
        x = 10 + i * (SCREEN_WIDTH // 2)
        pygame.draw.rect(surface, p.color, (x, 5, 10, 10))
        if not p.alive:
            lbl = font.render(f"J{i + 1}  MORT", True, (180, 60, 60))
            surface.blit(lbl, (x + 14, 5))
        else:
            spd = max(0, round((MOVE_COOLDOWN - p.move_cooldown) / BONUS_SPEED_GAIN))
            lbl = font.render(f"J{i + 1}  B:{p.max_bombs}  R:{p.bomb_range}  V:{spd}", True, TEXT_COLOR)
            surface.blit(lbl, (x + 14, 5))


# ── Boucle principale ─────────────────────────────────────────────────────────

def run(screen, joysticks):
    clock  = pygame.time.Clock()
    f_sm   = pygame.font.SysFont("Arial", 11, bold=True)
    f_ui   = pygame.font.SysFont("Arial", 13, bold=True)

    # Assignation manettes : joy 0 → J1, joy 1 → J2 (fallback sur joy 0)
    joy_p1 = joysticks[0] if len(joysticks) > 0 else None
    has_p2_joy = len(joysticks) > 1

    grid       = _make_grid()
    players    = [
        Player(1,          1,          P1_COLOR),
        Player(COLS - 2,   ROWS - 2,   P2_COLOR),
    ]
    bombs      = []
    explosions = []
    bonuses    = []

    # Boutons manette par joueur (séparés par index joystick)
    p1_btns = set()
    p2_btns = set()

    # Presses de bombe ce frame (event-based, pas hold)
    bomb_press_p1 = False
    bomb_press_p2 = False

    quit_combo = QuitCombo()
    t = 0.0

    while True:
        dt = clock.tick(FPS) / 1000.0
        t += dt

        bomb_press_p1 = False
        bomb_press_p2 = False

        events = pygame.event.get()
        for e in events:
            quit_combo.handle_event(e)

            if e.type == pygame.QUIT:
                return None

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return None
                if e.key == pygame.K_e:
                    bomb_press_p1 = True
                if e.key == pygame.K_p:
                    bomb_press_p2 = True

            if e.type == pygame.JOYBUTTONDOWN:
                # Trier les boutons par joueur selon l'index joystick
                joy_idx = getattr(e, 'joy', 0)
                if joy_idx == 0:
                    p1_btns.add(e.button)
                    if has_p2_joy is False:
                        p2_btns.add(e.button)   # joy unique → les deux joueurs
                else:
                    p2_btns.add(e.button)

                if joy_idx == 0 and e.button == BTN_P1_BOMB:
                    bomb_press_p1 = True
                if (joy_idx == 1 or not has_p2_joy) and e.button == BTN_P2_BOMB:
                    bomb_press_p2 = True

            if e.type == pygame.JOYBUTTONUP:
                joy_idx = getattr(e, 'joy', 0)
                if joy_idx == 0:
                    p1_btns.discard(e.button)
                    if not has_p2_joy:
                        p2_btns.discard(e.button)
                else:
                    p2_btns.discard(e.button)

        keys = pygame.key.get_pressed()

        # ── Déplacement J1 ─────────────────────────────────────────────────────
        p1 = players[0]
        if p1.alive:
            p1.move_cd = max(0.0, p1.move_cd - dt)
            p1.bomb_cd = max(0.0, p1.bomb_cd - dt)

            if p1.move_cd <= 0.0:
                d = _get_p1_dir(keys, joy_p1)
                if d:
                    nc, nr = p1.col + d[0], p1.row + d[1]
                    if not _is_blocked(nc, nr, grid, players, bombs, 0):
                        p1.col, p1.row = nc, nr
                    p1.move_cd = p1.move_cooldown

            if bomb_press_p1 and p1.bomb_cd <= 0.0 and p1.active_bombs < p1.max_bombs:
                if not any(b.col == p1.col and b.row == p1.row for b in bombs):
                    bombs.append(Bomb(p1.col, p1.row, 0, p1.bomb_range))
                    p1.active_bombs += 1
                    p1.bomb_cd = BOMB_PLACE_CD

        # ── Déplacement J2 ─────────────────────────────────────────────────────
        p2 = players[1]
        if p2.alive:
            p2.move_cd = max(0.0, p2.move_cd - dt)
            p2.bomb_cd = max(0.0, p2.bomb_cd - dt)

            if p2.move_cd <= 0.0:
                d = _get_p2_dir(keys, p2_btns)
                if d:
                    nc, nr = p2.col + d[0], p2.row + d[1]
                    if not _is_blocked(nc, nr, grid, players, bombs, 1):
                        p2.col, p2.row = nc, nr
                    p2.move_cd = p2.move_cooldown

            if bomb_press_p2 and p2.bomb_cd <= 0.0 and p2.active_bombs < p2.max_bombs:
                if not any(b.col == p2.col and b.row == p2.row for b in bombs):
                    bombs.append(Bomb(p2.col, p2.row, 1, p2.bomb_range))
                    p2.active_bombs += 1
                    p2.bomb_cd = BOMB_PLACE_CD

        # ── Ramassage des bonus ────────────────────────────────────────────────
        for p in players:
            if not p.alive:
                continue
            for bx in bonuses[:]:
                if p.col == bx.col and p.row == bx.row:
                    _apply_bonus(p, bx.type)
                    bonuses.remove(bx)

        # ── Mise à jour bombes ─────────────────────────────────────────────────
        for b in bombs:
            b.timer -= dt
        to_explode = [b for b in bombs if b.timer <= 0.0]
        if to_explode:
            bombs, destroyed_cells = _process_explosions(to_explode, bombs, grid, players, explosions)
            for dc, dr in destroyed_cells:
                if random.random() < BONUS_SPAWN_CHANCE:
                    if not any(bx.col == dc and bx.row == dr for bx in bonuses):
                        bonuses.append(Bonus(dc, dr, random.choice([BONUS_BOMB, BONUS_RANGE, BONUS_SPEED])))

        # ── Mise à jour explosions ─────────────────────────────────────────────
        for ex in explosions:
            ex.timer -= dt
        explosions = [ex for ex in explosions if ex.timer > 0.0]

        # ── Mort des joueurs ───────────────────────────────────────────────────
        all_explo = set()
        for ex in explosions:
            all_explo |= ex.cells
        for p in players:
            if p.alive and (p.col, p.row) in all_explo:
                p.alive = False

        # ── Condition de fin ───────────────────────────────────────────────────
        if not all(p.alive for p in players):
            # Rendu final puis pause
            screen.fill(BG_COLOR)
            _draw_grid(screen, grid, explosions)
            _draw_bonuses(screen, bonuses, t, f_sm)
            _draw_bombs(screen, bombs, t)
            _draw_players(screen, players, f_sm)
            _draw_ui(screen, players, f_ui)
            pygame.display.flip()
            pygame.time.wait(1200)

            a0, a1 = players[0].alive, players[1].alive
            if a0 and not a1: return 0
            if a1 and not a0: return 1
            return 2

        # ── Rendu ───────────────────────────────────────────────────────────────
        screen.fill(BG_COLOR)
        _draw_grid(screen, grid, explosions)
        _draw_bonuses(screen, bonuses, t, f_sm)
        _draw_bombs(screen, bombs, t)
        _draw_players(screen, players, f_sm)
        _draw_ui(screen, players, f_ui)

        if quit_combo.update_and_draw(screen):
            return None

        pygame.display.flip()
