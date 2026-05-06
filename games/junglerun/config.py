"""Constantes du runner Jungle Run."""
import pygame

SCREEN_WIDTH  = 480
SCREEN_HEIGHT = 320
FPS           = 60

# ── Split-screen ─────────────────────────────────────────────────────────────
# 480x320 coupé en 2 bandes horizontales : J1 en haut, J2 en bas.
VIEW_W = SCREEN_WIDTH
VIEW_H = SCREEN_HEIGHT // 2  # 160 px par joueur
SEPARATOR_H = 2              # ligne de séparation entre les 2 vues

# ── Couleurs (jungle / temple) ───────────────────────────────────────────────
SKY_TOP       = (40,  90,  60)
SKY_BOTTOM    = (90, 140,  80)
PLATFORM_SOLID   = (95,  60,  35)   # bois solide
PLATFORM_BRITTLE = (140, 90,  50)   # bois pourri (plus clair)
PLATFORM_TOP     = (60, 130, 60)   # gazon au-dessus du bois
VINE_COLOR    = (60, 200, 90)
ROCK_COLOR    = (80, 75, 70)
BRANCH_COLOR  = (60, 40, 25)
BOULDER_COLOR = (70, 50, 35)
FEATHER_COLOR = (250, 240, 180)
PLAYER_J1     = (255, 210,  60)   # jaune
PLAYER_J2     = (90, 200, 255)    # bleu cyan
TEXT_COLOR    = (240, 240, 240)
DEAD_OVERLAY  = (0, 0, 0, 160)
SEPARATOR_COL = (20, 20, 20)
HUD_BG        = (0, 0, 0, 130)

# ── Physique joueur ──────────────────────────────────────────────────────────
PLAYER_W      = 14
PLAYER_H      = 20
GRAVITY       = 1400.0   # px/s²
JUMP_VY       = -480.0   # impulsion verticale (px/s)
DOUBLE_JUMP_VY = -420.0  # double saut un peu plus faible
PLAYER_SCREEN_X = 90     # x fixe à l'écran (le monde scrolle)

# ── Scrolling / difficulté ───────────────────────────────────────────────────
START_SPEED   = 180.0    # px/s au début
SPEED_RAMP    = 4.0      # px/s gagnés par seconde de jeu
MAX_SPEED     = 420.0
BOULDER_BOOST = 1.5      # multiplicateur de vitesse pendant événement boulder

# ── Génération procédurale ───────────────────────────────────────────────────
GROUND_Y_BASE = VIEW_H - 36   # niveau "sol" de référence dans la viewport (y croît vers le bas)
GROUND_Y_MIN  = VIEW_H - 90   # plateforme la plus haute possible
GROUND_Y_MAX  = VIEW_H - 24   # plateforme la plus basse possible
PLATFORM_W_MIN = 70
PLATFORM_W_MAX = 200
GAP_MIN       = 38
GAP_MAX       = 110
DOUBLE_JUMP_GAP = 130         # un gap de cette taille passe avec double saut
BRITTLE_CHANCE = 0.22
ROCK_CHANCE    = 0.18         # rock posé sur la plateforme
BRANCH_CHANCE  = 0.12         # branche basse au-dessus de la plateforme
FEATHER_CHANCE = 0.06         # plume sur la plateforme

BOULDER_INTERVAL_MIN = 18.0   # secondes
BOULDER_INTERVAL_MAX = 32.0
BOULDER_DURATION     = 4.5

# ── Contrôles ────────────────────────────────────────────────────────────────
# J1 : n'importe quel bouton du D-pad (8-11) OU hat OU axes.
#      Au clavier : flèche du haut (ou espace).
# J2 : n'importe quel bouton de face (0=B, 1=A, 2=X, 3=Y).
#      Au clavier : touche N.
J1_DPAD_BTNS  = (8, 9, 10, 11)
J2_FACE_BTNS  = (0, 1, 2, 3)
J1_KEYS       = (pygame.K_UP, pygame.K_SPACE)
J2_KEYS       = (pygame.K_n, pygame.K_RETURN)

AXIS_DEAD = 0.5
