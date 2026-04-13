import pygame

SCREEN_WIDTH  = 480
SCREEN_HEIGHT = 320
FPS           = 30

# Résolution interne du raycaster (×2 → plein écran)
RENDER_W      = 240
RENDER_H      = 160
HALF_H        = RENDER_H // 2

# Raycaster
N_RAYS        = RENDER_W
MAX_DDA_STEPS = 28

# Camera plane half-length : tan(FOV/2) où FOV ≈ 66°
# tan(33°) ≈ 0.6494
CAM_PLANE     = 0.6494

# Joueur
PLAYER_SPEED  = 3.5    # cases/s
ROTATE_SPEED  = 2.2    # rad/s
PLAYER_HP     = 100
STARTING_AMMO = 30

# Arme
FIRE_COOLDOWN = 0.40   # s entre deux tirs
BULLET_DAMAGE = 35

# Ennemi
ENEMY_HP             = 60
ENEMY_DAMAGE         = 12
ENEMY_SPEED          = 1.6
ENEMY_SIGHT_RANGE    = 12.0
ENEMY_ATTACK_RANGE   = 1.2
ENEMY_SHOOT_COOLDOWN = 2.2

# Couleurs (RGB)
COL_CEILING = (22, 22, 42)
COL_FLOOR   = (44, 32, 18)

# Couleurs des murs par type : {type: (r, g, b)}
WALL_COLORS = {
    1: (160,  88,  50),   # brique
    2: ( 95, 125,  88),   # pierre/mousse
    3: (125, 125, 148),   # métal
    4: (210, 172,  48),   # or/décoratif
    5: (178, 138,  68),   # porte
}

# Contrôles OGA (indices joystick 0)
BTN_B       = 0    # utiliser / ouvrir
BTN_A       = 1    # tirer
BTN_R1      = 4    # strafe gauche
BTN_L1      = 6    # strafe droite
BTN_SELECT  = 12
BTN_START   = 17

AXIS_DEAD   = 0.18
