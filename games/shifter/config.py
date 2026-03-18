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

# Sprites : chaque voiture pointe vers sa zone exacte dans la spritesheet.
# "sprite": { "sheet": fichier dans asset/sprite/,
#             "x", "y" : coin haut-gauche du frame dans le sheet (px),
#             "w", "h" : dimensions du frame (px) }
# Ajustez x/y/w/h pour recadrer précisément chaque voiture.

CARS = [
    {
        "name":  "Green Machine",
        "cat":   "JDM",
        "desc":  "Nissan S14 – Equilibrée, idéale pour débuter",
        "col":   (18, 138, 28),
        "acc":   (80, 245, 80),
        "sprite": {"sheet": "vehicle1.png", "x": 0,   "y": 0,   "w": 768, "h": 341},
        "hud":   "sport",
        "stats": dict(power=350, weight=1350, gears=5, maxRPM=8000, optRPM=7200, shiftT=0.15),
        "curve": [(1000,80),(2000,150),(3000,230),(4000,300),(5000,340),(6000,350),(7000,350),(7200,350),(8000,320)],
        "ratios": [3.5, 2.2, 1.6, 1.1, 0.80],
    },
    {
        "name":  "Yellow Civic",
        "cat":   "JDM",
        "desc":  "Honda Civic EK – Légère et agile",
        "col":   (210, 190, 0),
        "acc":   (255, 235, 60),
        "sprite": {"sheet": "vehicle1.png", "x": 768, "y": 0,   "w": 768, "h": 341},
        "hud":   "rally",
        "stats": dict(power=300, weight=1150, gears=5, maxRPM=8200, optRPM=7600, shiftT=0.11),
        "curve": [(1000,65),(2000,130),(3000,200),(4000,265),(5000,295),(6000,305),(7000,305),(7600,305),(8200,275)],
        "ratios": [3.7, 2.3, 1.7, 1.15, 0.80],
    },
    {
        "name":  "Red GTI",
        "cat":   "EURO",
        "desc":  "VW Golf GTI – Couple dans les bas régimes",
        "col":   (175, 12, 12),
        "acc":   (255, 80, 80),
        "sprite": {"sheet": "vehicle1.png", "x": 0,   "y": 341, "w": 768, "h": 300},
        "hud":   "retro",
        "stats": dict(power=320, weight=1280, gears=6, maxRPM=7000, optRPM=6200, shiftT=0.13),
        "curve": [(1000,100),(2000,200),(3000,290),(4000,320),(5000,325),(6000,320),(7000,290)],
        "ratios": [3.4, 2.0, 1.5, 1.1, 0.84, 0.65],
    },
    {
        "name":  "White Ghost",
        "cat":   "JDM",
        "desc":  "Nissan 200SX – Très précise au shift",
        "col":   (208, 208, 213),
        "acc":   (255, 255, 255),
        "sprite": {"sheet": "vehicle1.png", "x": 768, "y": 341, "w": 768, "h": 300},
        "hud":   "ghost",
        "stats": dict(power=330, weight=1300, gears=5, maxRPM=7800, optRPM=7000, shiftT=0.13),
        "curve": [(1000,75),(2000,145),(3000,210),(4000,275),(5000,315),(6000,330),(7000,330),(7800,300)],
        "ratios": [3.3, 2.1, 1.55, 1.05, 0.76],
    },
    {
        "name":  "Purple Eclipse",
        "cat":   "JDM",
        "desc":  "Mitsubishi Eclipse – Turbo, grande puissance",
        "col":   (120, 40, 180),
        "acc":   (200, 100, 255),
        "sprite": {"sheet": "vehicle1.png", "x": 0,   "y": 682, "w": 768, "h": 300},
        "hud":   "race",
        "stats": dict(power=400, weight=1450, gears=5, maxRPM=8000, optRPM=7400, shiftT=0.16),
        "curve": [(1000,80),(2000,155),(3000,240),(4000,320),(5000,375),(6000,400),(7000,400),(7400,400),(8000,360)],
        "ratios": [3.6, 2.2, 1.65, 1.1, 0.78],
    },
    {
        "name":  "Blue Integra",
        "cat":   "JDM",
        "desc":  "Honda Integra – Légère, monte très haut",
        "col":   (18, 48, 200),
        "acc":   (80, 160, 255),
        "sprite": {"sheet": "vehicle1.png", "x": 768, "y": 682, "w": 768, "h": 300},
        "hud":   "street",
        "stats": dict(power=380, weight=1280, gears=6, maxRPM=8500, optRPM=7800, shiftT=0.12),
        "curve": [(1000,70),(2000,140),(3000,220),(4000,290),(5000,340),(6000,370),(7000,380),(7800,380),(8500,340)],
        "ratios": [3.8, 2.3, 1.7, 1.2, 0.92, 0.68],
    },

    # ── vehicle2.png – JDM iconiques tuné (480–520 ch) ───────────────────────
    {
        "name":  "Supra A80",
        "cat":   "JDM",
        "desc":  "Toyota Supra A80 2JZ – Couple massif dès 3500 tr/min",
        "col":   (210, 100, 10),
        "acc":   (255, 160, 40),
        "sprite": {"sheet": "vehicle2.png", "x": 0,   "y": 0,   "w": 768, "h": 341},
        "hud":   "sport",
        "stats": dict(power=480, weight=1450, gears=6, maxRPM=7500, optRPM=6800, shiftT=0.14),
        "curve": [(1000,80),(2000,160),(3000,280),(4000,400),(5000,460),(6000,480),(6800,480),(7500,440)],
        "ratios": [3.4, 2.1, 1.55, 1.1, 0.85, 0.64],
    },
    {
        "name":  "Skyline R34",
        "cat":   "JDM",
        "desc":  "Nissan Skyline GT-R R34 – Twin turbo, traction intégrale",
        "col":   (200, 205, 215),
        "acc":   (230, 235, 255),
        "sprite": {"sheet": "vehicle2.png", "x": 768, "y": 0,   "w": 768, "h": 341},
        "hud":   "ghost",
        "stats": dict(power=520, weight=1560, gears=6, maxRPM=7200, optRPM=6500, shiftT=0.15),
        "curve": [(1000,90),(2000,180),(3000,310),(4000,430),(5000,500),(6000,520),(6500,520),(7200,480)],
        "ratios": [3.5, 2.2, 1.6, 1.1, 0.86, 0.66],
    },
    {
        "name":  "Accord Euro R",
        "cat":   "JDM",
        "desc":  "Honda Accord Euro R – Atmo pur, shift chirurgical",
        "col":   (60, 160, 10),
        "acc":   (140, 240, 60),
        "sprite": {"sheet": "vehicle2.png", "x": 0,   "y": 341, "w": 768, "h": 300},
        "hud":   "rally",
        "stats": dict(power=390, weight=1350, gears=6, maxRPM=8500, optRPM=7800, shiftT=0.11),
        "curve": [(1000,60),(2000,120),(3000,190),(4000,270),(5000,340),(6000,380),(7000,390),(7800,390),(8500,360)],
        "ratios": [3.7, 2.3, 1.65, 1.18, 0.88, 0.70],
    },
    {
        "name":  "RX-8 Spirit R",
        "cat":   "JDM",
        "desc":  "Mazda RX-8 – Rotatif, monte à 9000, fenêtre shift étroite",
        "col":   (25, 80, 200),
        "acc":   (80, 160, 255),
        "sprite": {"sheet": "vehicle2.png", "x": 768, "y": 341, "w": 768, "h": 300},
        "hud":   "race",
        "stats": dict(power=420, weight=1310, gears=6, maxRPM=9000, optRPM=8200, shiftT=0.10),
        "curve": [(1000,40),(2000,100),(3000,180),(4000,270),(5000,360),(6000,410),(7000,420),(8200,420),(9000,390)],
        "ratios": [3.9, 2.4, 1.72, 1.22, 0.92, 0.72],
    },
    {
        "name":  "Eclipse GTS",
        "cat":   "JDM",
        "desc":  "Mitsubishi Eclipse GTS – Turbo puncheur, parfait en mid-range",
        "col":   (200, 175, 0),
        "acc":   (255, 230, 50),
        "sprite": {"sheet": "vehicle2.png", "x": 0,   "y": 682, "w": 768, "h": 300},
        "hud":   "retro",
        "stats": dict(power=440, weight=1470, gears=5, maxRPM=7500, optRPM=6800, shiftT=0.14),
        "curve": [(1000,85),(2000,170),(3000,285),(4000,380),(5000,430),(6000,440),(6800,440),(7500,410)],
        "ratios": [3.6, 2.2, 1.6, 1.1, 0.78],
    },
    {
        "name":  "S2000 AP2",
        "cat":   "JDM",
        "desc":  "Honda S2000 – Léger, très haute révolution, shift précis",
        "col":   (215, 215, 225),
        "acc":   (255, 200, 220),
        "sprite": {"sheet": "vehicle2.png", "x": 768, "y": 682, "w": 768, "h": 300},
        "hud":   "street",
        "stats": dict(power=360, weight=1270, gears=6, maxRPM=8200, optRPM=7500, shiftT=0.11),
        "curve": [(1000,55),(2000,110),(3000,185),(4000,265),(5000,330),(6000,355),(7000,360),(7500,360),(8200,330)],
        "ratios": [3.8, 2.35, 1.68, 1.2, 0.90, 0.70],
    },

    # ── vehicle3.png – Builds extrêmes (550–850 ch) ──────────────────────────
    {
        "name":  "RX-7 FD3S",
        "cat":   "JDM",
        "desc":  "Mazda RX-7 FD3S compressé – Rotatif poussé à l'extrême",
        "col":   (190, 12, 12),
        "acc":   (255, 70, 50),
        "sprite": {"sheet": "vehicle3.png", "x": 0,   "y": 0,   "w": 768, "h": 341},
        "hud":   "race",
        "stats": dict(power=680, weight=1230, gears=5, maxRPM=9500, optRPM=8800, shiftT=0.10),
        "curve": [(1000,60),(2000,150),(3000,320),(4000,520),(5000,640),(6000,680),(7000,670),(8000,640),(8800,680),(9500,620)],
        "ratios": [3.7, 2.2, 1.58, 1.08, 0.78],
    },
    {
        "name":  "Lancer Evo VIII",
        "cat":   "JDM",
        "desc":  "Mitsubishi Lancer Evo VIII – AWD turbo, polyvalent et dévastateur",
        "col":   (15, 55, 190),
        "acc":   (60, 140, 255),
        "sprite": {"sheet": "vehicle3.png", "x": 768, "y": 0,   "w": 768, "h": 341},
        "hud":   "sport",
        "stats": dict(power=550, weight=1450, gears=6, maxRPM=7800, optRPM=7000, shiftT=0.13),
        "curve": [(1000,100),(2000,220),(3000,380),(4000,490),(5000,540),(6000,550),(7000,540),(7800,510)],
        "ratios": [3.5, 2.15, 1.56, 1.1, 0.84, 0.65],
    },
    {
        "name":  "Challenger R/T",
        "cat":   "MUSCLE",
        "desc":  "Dodge Challenger R/T superchargé – V8 brutal, couple dès le ralenti",
        "col":   (40, 130, 20),
        "acc":   (100, 230, 50),
        "sprite": {"sheet": "vehicle3.png", "x": 0,   "y": 341, "w": 768, "h": 300},
        "hud":   "retro",
        "stats": dict(power=780, weight=1900, gears=6, maxRPM=6500, optRPM=5800, shiftT=0.18),
        "curve": [(1000,320),(2000,560),(3000,720),(4000,780),(5000,760),(5800,780),(6500,720)],
        "ratios": [3.1, 1.95, 1.42, 1.05, 0.78, 0.62],
    },
    {
        "name":  "GT86 Time Attack",
        "cat":   "JDM",
        "desc":  "Toyota GT86 Widebody – Léger et précis, shift immédiat",
        "col":   (35, 35, 35),
        "acc":   (200, 165, 50),
        "sprite": {"sheet": "vehicle3.png", "x": 768, "y": 341, "w": 768, "h": 300},
        "hud":   "rally",
        "stats": dict(power=520, weight=1160, gears=6, maxRPM=8500, optRPM=7800, shiftT=0.11),
        "curve": [(1000,70),(2000,150),(3000,270),(4000,390),(5000,480),(6000,510),(7000,520),(7800,520),(8500,490)],
        "ratios": [3.6, 2.2, 1.6, 1.15, 0.87, 0.68],
    },
    {
        "name":  "Barracuda 440",
        "cat":   "MUSCLE",
        "desc":  "Plymouth Barracuda 440ci superchargé – Monstre de couple pur",
        "col":   (200, 80, 10),
        "acc":   (255, 140, 40),
        "sprite": {"sheet": "vehicle3.png", "x": 0,   "y": 682, "w": 768, "h": 300},
        "hud":   "retro",
        "stats": dict(power=850, weight=1780, gears=4, maxRPM=6000, optRPM=5200, shiftT=0.20),
        "curve": [(1000,450),(2000,720),(3000,830),(4000,850),(5000,820),(5200,850),(6000,780)],
        "ratios": [2.5, 1.55, 1.05, 0.62],
    },
    {
        "name":  "Supra MkIV Turbo",
        "cat":   "JDM",
        "desc":  "Toyota Supra 2JZ big single – 800 ch, la référence ultime",
        "col":   (155, 160, 165),
        "acc":   (210, 220, 230),
        "sprite": {"sheet": "vehicle3.png", "x": 768, "y": 682, "w": 768, "h": 300},
        "hud":   "sport",
        "stats": dict(power=800, weight=1480, gears=6, maxRPM=7500, optRPM=6800, shiftT=0.16),
        "curve": [(1000,80),(2000,200),(3000,420),(4000,650),(5000,760),(6000,800),(6800,800),(7500,760)],
        "ratios": [3.3, 2.05, 1.50, 1.07, 0.82, 0.62],
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
#   J1 → croix directionnelle (hat) OU joystick (axes) OU boutons dpad (8=haut, 9=bas, 10=gauche, 11=droite)
#   J2 → Y(btn3) / A(btn0) pour changer véhicule, X(btn2) pour confirmer/montée, B(btn1) pour descente
#
# En course :
#   J1 → UP   = passer vitesse sup  |  DOWN  = passer vitesse inf
#   J2 → X(2) = passer vitesse sup  |  B(1)  = passer vitesse inf
#
# Manette : axes 0=horizontal, 1=vertical (deadzone 0.7)
#           hat  : (x, y) où x=-1 gauche, x=1 droit, y=1 haut, y=-1 bas
#           btns : 0=A, 1=B, 2=X, 3=Y  /  8=↑, 9=↓, 10=←, 11=→ (dpad Odroid)

CTRL = {
    # ── Joueur 1 (croix + joystick gauche + dpad buttons) ────────────────────
    'sel_prev_j1':  {'keys': [pygame.K_LEFT],  'hat': (-1,  0), 'axis': (0, -1), 'btns': [10]},
    'sel_next_j1':  {'keys': [pygame.K_RIGHT], 'hat': ( 1,  0), 'axis': (0,  1), 'btns': [11]},
    'sel_conf_j1':  {'keys': [pygame.K_UP, pygame.K_RETURN], 'hat': (0, 1), 'axis': (1, -1), 'btns': [8]},
    'sel_tier_j1':  {'keys': [pygame.K_DOWN],  'hat': (0, -1), 'btns': [9]},
    'race_up_j1':   {'keys': [pygame.K_UP],    'hat': (0,  1), 'axis': (1, -1), 'btns': [8]},
    'race_down_j1': {'keys': [pygame.K_DOWN],  'hat': (0, -1), 'axis': (1,  1), 'btns': [9]},

    # ── Joueur 2 (boutons A/B/X/Y) ────────────────────────────────────────────
    'sel_prev_j2':  {'keys': [pygame.K_COMMA],  'btns': [3]},   # Y → véhicule précédent
    'sel_next_j2':  {'keys': [pygame.K_PERIOD], 'btns': [1]},   # B → véhicule suivant
    'sel_conf_j2':  {'keys': [pygame.K_n],      'btns': [2]},   # X → prêt
    'sel_tier_j2':  {'keys': [pygame.K_m],      'btns': [0]},   # A → changer tier
    'race_up_j2':   {'keys': [pygame.K_n],      'btns': [2]},   # X → montée de vitesse
    'race_down_j2': {'keys': [pygame.K_m],      'btns': [0]},   # A → descente de vitesse

    # ── Général ───────────────────────────────────────────────────────────────
    'quit':         {'keys': [pygame.K_ESCAPE]},
}

AXIS_DEAD = 0.7
