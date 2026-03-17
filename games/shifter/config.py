import pygame

SCREEN_WIDTH  = 480
SCREEN_HEIGHT = 320
FPS           = 60
RACE_DISTANCE = 400  # mètres

# Couleur de chaque joueur
PLAYER_COLORS = [
    (255, 80,  80),   # J1 : rouge
    (80,  180, 255),  # J2 : bleu
]

# Ordre des voitures = ordre des frames dans vehicle1.png
# Frame 0 (vert)   = Green Machine   – Nissan S14
# Frame 1 (jaune)  = Yellow Civic    – Honda Civic EK
# Frame 2 (rouge)  = Red GTI         – VW Golf GTI
# Frame 3 (blanc)  = White Ghost     – Nissan 200SX
# Frame 4 (violet) = Purple Eclipse  – Mitsubishi Eclipse
# Frame 5 (bleu)   = Blue Integra    – Honda Integra

CARS = [
    {
        "name":  "Green Machine",
        "cat":   "JDM",
        "desc":  "Nissan S14 – Equilibrée, idéale pour débuter",
        "col":   (18, 138, 28),
        "acc":   (80, 245, 80),
        "sprite_frame": 0,
        "hud":   "sport",
        "stats": dict(power=350, weight=1350, gears=5, maxRPM=8000, optRPM=7200, shiftT=0.15),
        "curve": [(1000,80),(2000,150),(3000,230),(4000,300),(5000,340),(6000,350),(7000,350),(7200,350),(8000,320)],
        "ratios": [3.5, 2.2, 1.6, 1.2, 0.95],
    },
    {
        "name":  "Yellow Civic",
        "cat":   "JDM",
        "desc":  "Honda Civic EK – Légère et agile",
        "col":   (210, 190, 0),
        "acc":   (255, 235, 60),
        "sprite_frame": 1,
        "hud":   "rally",
        "stats": dict(power=300, weight=1150, gears=5, maxRPM=8200, optRPM=7600, shiftT=0.11),
        "curve": [(1000,65),(2000,130),(3000,200),(4000,265),(5000,295),(6000,305),(7000,305),(7600,305),(8200,275)],
        "ratios": [3.7, 2.3, 1.7, 1.25, 0.95],
    },
    {
        "name":  "Red GTI",
        "cat":   "EURO",
        "desc":  "VW Golf GTI – Couple dans les bas régimes",
        "col":   (175, 12, 12),
        "acc":   (255, 80, 80),
        "sprite_frame": 2,
        "hud":   "retro",
        "stats": dict(power=320, weight=1280, gears=6, maxRPM=7000, optRPM=6200, shiftT=0.13),
        "curve": [(1000,100),(2000,200),(3000,290),(4000,320),(5000,325),(6000,320),(7000,290)],
        "ratios": [3.4, 2.0, 1.5, 1.15, 0.9, 0.75],
    },
    {
        "name":  "White Ghost",
        "cat":   "JDM",
        "desc":  "Nissan 200SX – Très précise au shift",
        "col":   (208, 208, 213),
        "acc":   (255, 255, 255),
        "sprite_frame": 3,
        "hud":   "ghost",
        "stats": dict(power=330, weight=1300, gears=5, maxRPM=7800, optRPM=7000, shiftT=0.13),
        "curve": [(1000,75),(2000,145),(3000,210),(4000,275),(5000,315),(6000,330),(7000,330),(7800,300)],
        "ratios": [3.3, 2.1, 1.55, 1.15, 0.9],
    },
    {
        "name":  "Purple Eclipse",
        "cat":   "JDM",
        "desc":  "Mitsubishi Eclipse – Turbo, grande puissance",
        "col":   (120, 40, 180),
        "acc":   (200, 100, 255),
        "sprite_frame": 4,
        "hud":   "race",
        "stats": dict(power=400, weight=1450, gears=5, maxRPM=8000, optRPM=7400, shiftT=0.16),
        "curve": [(1000,80),(2000,155),(3000,240),(4000,320),(5000,375),(6000,400),(7000,400),(7400,400),(8000,360)],
        "ratios": [3.6, 2.2, 1.65, 1.2, 0.92],
    },
    {
        "name":  "Blue Integra",
        "cat":   "JDM",
        "desc":  "Honda Integra – Légère, monte très haut",
        "col":   (18, 48, 200),
        "acc":   (80, 160, 255),
        "sprite_frame": 5,
        "hud":   "street",
        "stats": dict(power=380, weight=1280, gears=6, maxRPM=8500, optRPM=7800, shiftT=0.12),
        "curve": [(1000,70),(2000,140),(3000,220),(4000,290),(5000,340),(6000,370),(7000,380),(7800,380),(8500,340)],
        "ratios": [3.8, 2.3, 1.7, 1.3, 1.0, 0.8],
    },
]

# Zones de shift (delta RPM autour de l'optimal)
SHIFT_PERF     = 200   # ±200 RPM = PERFECT (vert)
SHIFT_GOOD     = 500   # ±500 RPM = GOOD    (jaune)
SHIFT_MULT     = {'PERFECT': 1.05, 'GOOD': 1.00, 'BAD': 0.90}
SHIFT_BONUS_DUR = 0.5  # secondes

# Physique (identique au POC JS)
AIR_RES  = 0.0008
ROLL_RES = 0.003

# Surchauffe moteur
OVERHEAT_TIME      = 3.0   # secondes en zone rouge avant surchauffe
OVERHEAT_COOLDOWN  = 5.0   # secondes hors zone rouge pour refroidir complètement
OVERHEAT_SPEED_PEN = 0.45  # multiplicateur de puissance quand surchauffe (−55 %)
OVERHEAT_WARN_TIME = 1.0   # secondes avant surchauffe pour afficher l'alerte

# ── Contrôles ────────────────────────────────────────────────────────────────
# J1 : croix directionnelle / flèches clavier
# J2 : boutons face ABXY    / touches N M , .
#
# En sélection :
#   J1 → LEFT / RIGHT pour changer de voiture, UP pour confirmer « Prêt »
#   J2 → Y(btn3) / X(btn2) pour changer, A(btn0) pour confirmer
#
# En course :
#   J1 → UP   = passer vitesse sup  |  DOWN  = passer vitesse inf
#   J2 → A(0) = passer vitesse sup  |  B(1)  = passer vitesse inf
#
# Manette : axes 0=horizontal, 1=vertical (deadzone 0.7)
#           hat  : (x, y) où x=-1 gauche, x=1 droit, y=1 haut, y=-1 bas
#           btns : 0=A, 1=B, 2=X, 3=Y

CTRL = {
    # ── Joueur 1 (croix) ──────────────────────────────────────────────────────
    'sel_prev_j1':  {'keys': [pygame.K_LEFT],   'hat': (-1,  0), 'axis': (0, -1)},
    'sel_next_j1':  {'keys': [pygame.K_RIGHT],  'hat': ( 1,  0), 'axis': (0,  1)},
    'sel_conf_j1':  {'keys': [pygame.K_UP, pygame.K_RETURN], 'hat': (0, 1), 'axis': (1, -1)},
    'race_up_j1':   {'keys': [pygame.K_UP],     'hat': (0,  1), 'axis': (1, -1)},
    'race_down_j1': {'keys': [pygame.K_DOWN],   'hat': (0, -1), 'axis': (1,  1)},

    # ── Joueur 2 (boutons) ────────────────────────────────────────────────────
    'sel_prev_j2':  {'keys': [pygame.K_COMMA],  'btn': 3},   # Y
    'sel_next_j2':  {'keys': [pygame.K_PERIOD], 'btn': 2},   # X
    'sel_conf_j2':  {'keys': [pygame.K_n],      'btn': 0},   # A
    'race_up_j2':   {'keys': [pygame.K_n],      'btn': 0},   # A
    'race_down_j2': {'keys': [pygame.K_m],      'btn': 1},   # B

    # ── Général ───────────────────────────────────────────────────────────────
    'quit':         {'keys': [pygame.K_ESCAPE]},
}

AXIS_DEAD = 0.7
