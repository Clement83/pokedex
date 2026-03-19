import pygame

SCREEN_WIDTH  = 480
SCREEN_HEIGHT = 320
FPS           = 60

# ── Grille ────────────────────────────────────────────────────────────────────
COLS   = 15
ROWS   = 9
CELL   = 30
GRID_X = (SCREEN_WIDTH  - COLS * CELL) // 2   # 15 px de marge
GRID_Y = 30                                     # barre UI en haut

# Types de cellules
EMPTY = 0
WALL  = 1   # indestructible
BLOCK = 2   # destructible

# ── Couleurs ──────────────────────────────────────────────────────────────────
BG_COLOR      = (15,  15,  25)
UI_BG_COLOR   = (10,  10,  20)
WALL_COLOR    = (70,  70,  90)
BLOCK_COLOR   = (120, 75,  45)
EMPTY_COLOR   = (35,  35,  50)
BOMB_COLOR    = (20,  20,  20)
FUSE_COLOR    = (255, 200,  0)
EXPLO_CENTER  = (255, 230,  80)
EXPLO_BEAM    = (255, 120,  20)
P1_COLOR      = (255,  80,  80)
P2_COLOR      = ( 80, 180, 255)
TEXT_COLOR    = (210, 210, 230)

# ── Paramètres de jeu ─────────────────────────────────────────────────────────
BOMB_TIMER    = 3.0    # secondes avant explosion
BOMB_RANGE    = 2      # portée en cellules
EXPLOSION_DUR = 0.6    # durée d'affichage de l'explosion
MOVE_COOLDOWN = 0.14   # secondes entre chaque déplacement d'une case
BOMB_PLACE_CD = 0.3    # anti-double placement

# ── Boutons manette ───────────────────────────────────────────────────────────
BTN_A        = 0    # P2 → bas
BTN_B        = 1    # P2 → droite
BTN_X        = 2    # P2 → haut
BTN_Y        = 3    # P2 → gauche
BTN_P1_BOMB  = 12   # P1 pose une bombe
BTN_P2_BOMB  = 17   # P2 pose une bombe

AXIS_DEAD = 0.4

# ── Bonus ─────────────────────────────────────────────────────────────────────
BONUS_BOMB         = 'bomb'    # +1 bombe simultanée
BONUS_RANGE        = 'range'   # +1 portée d'explosion
BONUS_SPEED        = 'speed'   # déplacement plus rapide

BONUS_SPAWN_CHANCE = 0.60      # probabilité qu'un bloc laisse un bonus
BONUS_SPEED_GAIN   = 0.025     # réduction move_cooldown par bonus vitesse
BONUS_MAX_BOMBS    = 4
BONUS_MAX_RANGE    = 6
BONUS_MIN_CD       = 0.05      # cooldown minimal de déplacement
