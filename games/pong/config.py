import pygame

SCREEN_WIDTH  = 480
SCREEN_HEIGHT = 320
FPS           = 60

# ── Couleurs ──────────────────────────────────────────────────────────────────
BG_COLOR      = (8,  8, 18)
PADDLE_J1     = (255,  80,  80)   # rouge – J1
PADDLE_J2     = ( 80, 180, 255)   # bleu  – J2
BALL_COLOR    = (240, 240, 240)
NET_COLOR     = ( 38,  38,  65)
TEXT_COLOR    = (200, 200, 200)

# ── Raquettes ─────────────────────────────────────────────────────────────────
PADDLE_W      = 10
PADDLE_H      = 60
PADDLE_SPEED  = 230   # px/s

# ── Balle ────────────────────────────────────────────────────────────────────
BALL_SIZE     = 10    # diamètre
BALL_SPEED_X  = 210   # vitesse initiale px/s
BALL_SPEED_Y  = 160
BALL_ACCEL    = 1.06  # multiplicateur de vitesse à chaque rebond sur raquette
BALL_MAX_SPEED = 480  # plafond px/s

# ── Partie ────────────────────────────────────────────────────────────────────
WIN_SCORE     = 7

# ── Contrôles ────────────────────────────────────────────────────────────────
#   J1 : flèches haut/bas  (+ hat joystick / axe 1)
#   J2 : touche N = descendre, touche M = monter  (identique à Shifter A/B)
#        bouton 0 (A manette) = descendre, bouton 1 (B manette) = monter
CTRL = {
    'up_j1':   {'keys': [pygame.K_UP],   'hat': (0,  1), 'axis': (1, -1)},
    'down_j1': {'keys': [pygame.K_DOWN], 'hat': (0, -1), 'axis': (1,  1)},
    'up_j2':   {'keys': [pygame.K_m],    'btn': 1},   # B
    'down_j2': {'keys': [pygame.K_n],    'btn': 0},   # A
    'quit':    {'keys': [pygame.K_ESCAPE]},
    'confirm': {'keys': [pygame.K_RETURN, pygame.K_SPACE], 'btn': 0},
}

AXIS_DEAD = 0.3
