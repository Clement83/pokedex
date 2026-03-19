"""
Configuration du mini-jeu Minecraft 2D – 2 joueurs.
Conçu pour tourner sur Odroid GO Advance (480×320, Python 3.8).
"""
import pygame

SCREEN_WIDTH  = 480
SCREEN_HEIGHT = 320
FPS           = 30          # 30 fps pour les performances

# ── Tuiles ────────────────────────────────────────────────────────────────────
TILE_SIZE  = 16             # pixels par tuile
COLS       = 120            # largeur du monde en tuiles
ROWS       = 60             # hauteur du monde en tuiles

# Indices de tuile
TILE_AIR   = 0
TILE_DIRT  = 1
TILE_STONE = 2
TILE_GRASS = 3
TILE_SAND  = 4
TILE_WOOD  = 5
TILE_COAL  = 6              # bloc décoratif minable

# Noms affichés dans l'inventaire
TILE_NAMES = {
    TILE_AIR:   "Air",
    TILE_DIRT:  "Terre",
    TILE_STONE: "Pierre",
    TILE_GRASS: "Herbe",
    TILE_SAND:  "Sable",
    TILE_WOOD:  "Bois",
    TILE_COAL:  "Charbon",
}

# Couleurs des tuiles (dessin simple, pas de sprites)
TILE_COLORS = {
    TILE_AIR:   (100, 160, 220),   # ciel
    TILE_DIRT:  (139,  90,  43),
    TILE_STONE: (120, 120, 130),
    TILE_GRASS: ( 76, 153,  0),
    TILE_SAND:  (210, 190, 110),
    TILE_WOOD:  (180, 120,  60),
    TILE_COAL:  ( 60,  60,  70),
}

# Temps en secondes pour casser un bloc (appui continu)
TILE_BREAK_TIME = {
    TILE_DIRT:  0.4,
    TILE_STONE: 0.9,
    TILE_GRASS: 0.4,
    TILE_SAND:  0.3,
    TILE_WOOD:  0.5,
    TILE_COAL:  0.8,
}

# ── Génération du terrain ─────────────────────────────────────────────────────
SURFACE_Y      = 18     # ligne de surface (tuile de haut en bas)
TERRAIN_AMPLITUDE = 6   # amplitude max des collines
TERRAIN_FREQ   = 0.07   # fréquence des collines (plus petit = plus doux)
STONE_DEPTH    = 8      # nombre de tuiles de terre avant la pierre
CAVE_PROB      = 0.045  # probabilité d'une cellule de cave (autom. cellulaire)
CAVE_ITERATIONS = 4     # itérations de lissage des caves

# ── Joueurs ───────────────────────────────────────────────────────────────────
PLAYER_W       = 10     # pixels (hitbox)
PLAYER_H       = 20     # pixels (hitbox)
GRAVITY        = 28.0   # tiles/s²  (accélération vers le bas)
JUMP_VEL       = -9.5   # tiles/s   vitesse initiale du saut
WALK_SPEED     = 5.5    # tiles/s   vitesse horizontale
MAX_FALL_SPEED = 18.0   # tiles/s   vitesse de chute max
CLIMB_SPEED    = 4.5    # tiles/s   vitesse d'escalade de mur

REACH_RADIUS   = 4      # rayon max (en tuiles) pour placer/casser

# Inventaire : 5 slots (indices 0-4) + 2 slots actifs
INVENTORY_SLOTS = 5
HOTBAR_Y        = 10    # position Y de la hotbar (pixels depuis le haut)

# ── Couleurs UI ───────────────────────────────────────────────────────────────
BG_SKY       = (100, 160, 220)
BG_DEEP      = ( 20,  20,  35)
UI_BG        = (  0,   0,   0, 160)
TEXT_COLOR   = (240, 240, 240)
P1_COLOR     = (255, 100, 100)
P2_COLOR     = (100, 180, 255)
CURSOR_COLOR = (255, 255,   0, 180)
BREAK_BAR_COLOR = (255, 200,  50)

# ── Contrôles ─────────────────────────────────────────────────────────────────
# Schéma 7 boutons par joueur :
#   4 directions  = se déplacer / sauter (haut)
#   BTN_MINE      = maintenu sur bloc -> miner
#   BTN_MODIFIER  = maintenu + dirs   -> changer de slot
#                   maintenu + MINE   -> poser un bloc
#   BTN_FREE      = libre (sprint, attaque, craft...)
#
# Manette – axes / hat
AXIS_DEAD = 0.4

# J1 – joystick 0 (côté gauche OGA)
J1_BTN_MINE     =  6   # L2 (gâchette)
J1_BTN_MODIFIER =  7   # R2 (gâchette)
J1_BTN_FREE     = -1   # non utilisé

# Boutons D-pad J1 (Odroid GO Advance)
J1_BTN_UP    =  8
J1_BTN_DOWN  =  9
J1_BTN_LEFT  = 10
J1_BTN_RIGHT = 11

# J2 – joystick 1 (côté droit OGA)
BTN_A = 0   # J2 : bas
BTN_B = 1   # J2 : droite
BTN_X = 2   # J2 : haut / saut
BTN_Y = 3   # J2 : gauche
J2_BTN_MINE     =  4   # L1 (gâchette)
J2_BTN_MODIFIER =  5   # R1 (gâchette)
J2_BTN_FREE     = -1   # non utilisé

# Clavier – J1 : WASD + E (mine) + R (modifier)
KB_J1_UP       = pygame.K_w
KB_J1_DOWN     = pygame.K_s
KB_J1_LEFT     = pygame.K_a
KB_J1_RIGHT    = pygame.K_d
KB_J1_MINE     = pygame.K_e       # E  seul = miner
KB_J1_MODIFIER = pygame.K_r       # R + dirs = slot | R + E = poser

# Clavier – J2 : Flèches + RCTRL (mine) + Entrée (modifier)
KB_J2_UP       = pygame.K_UP
KB_J2_DOWN     = pygame.K_DOWN
KB_J2_LEFT     = pygame.K_LEFT
KB_J2_RIGHT    = pygame.K_RIGHT
KB_J2_MINE     = pygame.K_RCTRL   # RCTRL seul = miner
KB_J2_MODIFIER = pygame.K_RETURN  # ENTREE + dirs = slot | ENTREE + RCTRL = poser
