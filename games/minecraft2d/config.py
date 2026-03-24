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
ROWS       = 120            # hauteur du monde en tuiles

# Indices de tuile
TILE_AIR   = 0
TILE_DIRT  = 1
TILE_STONE = 2
TILE_GRASS = 3
TILE_SAND  = 4
TILE_WOOD  = 5
TILE_COAL  = 6              # bloc décoratif minable
TILE_BRICK = 7              # brique (structures)
TILE_CHEST = 8              # coffre (contient du loot d'équipement)
TILE_OBSIDIAN = 9           # obsidienne (très dure, fonds de donjon)
TILE_GLASS = 10             # vitre (fenêtres et hublots)
TILE_IRON_ORE    = 11       # minerai de fer
TILE_GOLD_ORE    = 12       # minerai d'or
TILE_DIAMOND_ORE = 13       # minerai de diamant
TILE_SNOW        = 14       # neige (surface biome glace)
TILE_ICE         = 15       # glace (sous-sol biome glace)
TILE_LAVA        = 16       # lave (non-solide, dégâts au contact)
TILE_WATER       = 17       # eau (non-solide, ralentit le joueur)

# Noms affichés dans l'inventaire
TILE_NAMES = {
    TILE_AIR:         "Air",
    TILE_DIRT:        "Terre",
    TILE_STONE:       "Pierre",
    TILE_GRASS:       "Herbe",
    TILE_SAND:        "Sable",
    TILE_WOOD:        "Bois",
    TILE_COAL:        "Charbon",
    TILE_BRICK:       "Brique",
    TILE_CHEST:       "Coffre",
    TILE_OBSIDIAN:    "Obsidienne",
    TILE_GLASS:       "Vitre",
    TILE_IRON_ORE:    "Minerai de Fer",
    TILE_GOLD_ORE:    "Minerai d'Or",
    TILE_DIAMOND_ORE: "Minerai de Diamant",
    TILE_SNOW:        "Neige",
    TILE_ICE:         "Glace",
    TILE_LAVA:        "Lave",
    TILE_WATER:       "Eau",
}

# ── Outils ────────────────────────────────────────────────────────────────────
TOOL_HAND    = 0   # saisir / interagir : ouvrir coffres
TOOL_PICKAXE = 1   # creuser uniquement
TOOL_PLACER  = 2   # poser des blocs (appui simple MINE)
TOOL_SWORD   = 3   # épée : attaque les mobs (MINE = coup d'épée)
TOOL_FLAG    = 4   # drapeau : pose le point de respawn au sol
TOOL_CRAFT   = 5   # table de craft : action=ouvrir menu, alt=fermer
TOOL_NAMES   = {TOOL_HAND: "Main", TOOL_PICKAXE: "Pioche",
                TOOL_PLACER: "Canon", TOOL_SWORD: "Épée", TOOL_FLAG: "Drapeau",
                TOOL_CRAFT: "Table Craft"}
TOOLS_LIST   = [TOOL_HAND, TOOL_PICKAXE, TOOL_PLACER, TOOL_SWORD, TOOL_FLAG, TOOL_CRAFT]

# ── Équipements ───────────────────────────────────────────────────────────────
# Slot d'équipement
EQUIP_HEAD    = 0   # casque
EQUIP_BODY    = 1   # plastron
EQUIP_FEET    = 2   # bottes
EQUIP_SWORD   = 3   # épée (main)
EQUIP_PICKAXE = 4   # pioche (main)

# Matériaux
# ── Biomes ───────────────────────────────────────────────────────────────────
BIOME_FOREST = 0
BIOME_DESERT = 1
BIOME_ICE    = 2
BIOME_FREQ   = 0.008   # biomes ~120 cols de large (4 écrans), autre biome à ~2 écrans

BIOME_NAMES = {BIOME_FOREST: "Forêt", BIOME_DESERT: "Désert", BIOME_ICE: "Glace"}

# Couleur du ciel (tuiles AIR) par biome
BIOME_SKY_COLORS = {
    BIOME_FOREST: (100, 160, 220),   # bleu classique
    BIOME_DESERT: (170, 155, 120),   # ciel chaud sableux
    BIOME_ICE:    (155, 190, 225),   # ciel froid bleuté
}

MAT_WOOD    = 0
MAT_IRON    = 1
MAT_GOLD    = 2
MAT_DIAMOND = 3
MAT_NAMES = {MAT_WOOD: "Bois", MAT_IRON: "Fer", MAT_GOLD: "Or", MAT_DIAMOND: "Diamant"}

# Couleurs des matériaux sur le bonhomme
MAT_COLORS = {
    MAT_WOOD:    (139,  90,  43),   # brun bois
    MAT_IRON:    (170, 170, 185),   # gris métal
    MAT_GOLD:    (255, 200,   0),   # jaune or
    MAT_DIAMOND: ( 80, 220, 235),   # cyan diamant
}

# Tier de matériau (pour vérification pioche/épée)
MAT_TIER = {MAT_WOOD: 1, MAT_IRON: 2, MAT_GOLD: 3, MAT_DIAMOND: 4}

# Défense d'armure par matériau (par pièce portée)
# Full Fer=3, Full Or=3, Full Diamant=6
ARMOR_DEF = {MAT_WOOD: 0, MAT_IRON: 1, MAT_GOLD: 1, MAT_DIAMOND: 2}

# item_id = (slot, material) — tuples uniques
# ex. (EQUIP_HEAD, MAT_WOOD) = casque en bois
EQUIP_NAMES = {
    (EQUIP_HEAD, MAT_WOOD): "Casque Bois",
    (EQUIP_HEAD, MAT_IRON): "Casque Fer",
    (EQUIP_HEAD, MAT_GOLD): "Casque Or",
    (EQUIP_BODY, MAT_WOOD): "Plastron Bois",
    (EQUIP_BODY, MAT_IRON): "Plastron Fer",
    (EQUIP_BODY, MAT_GOLD): "Plastron Or",
    (EQUIP_FEET, MAT_WOOD): "Bottes Bois",
    (EQUIP_FEET, MAT_IRON): "Bottes Fer",
    (EQUIP_FEET, MAT_GOLD): "Bottes Or",
    # Épées
    (EQUIP_SWORD, MAT_WOOD): "Épée Bois",
    (EQUIP_SWORD, MAT_IRON): "Épée Fer",
    (EQUIP_SWORD, MAT_GOLD): "Épée Or",
    # Épées diamant / pioches diamant
    (EQUIP_SWORD,   MAT_DIAMOND): "Épée Diamant",
    (EQUIP_PICKAXE, MAT_DIAMOND): "Pioche Diamant",
    # Armures diamant
    (EQUIP_HEAD, MAT_DIAMOND):   "Casque Diamant",
    (EQUIP_BODY, MAT_DIAMOND):   "Plastron Diamant",
    (EQUIP_FEET, MAT_DIAMOND):   "Bottes Diamant",
    # Pioches
    (EQUIP_PICKAXE, MAT_WOOD): "Pioche Bois",
    (EQUIP_PICKAXE, MAT_IRON): "Pioche Fer",
    (EQUIP_PICKAXE, MAT_GOLD): "Pioche Or",
}

# Couleurs des tuiles (dessin simple, pas de sprites)
TILE_COLORS = {
    TILE_AIR:         (100, 160, 220),   # ciel
    TILE_DIRT:        (139,  90,  43),
    TILE_STONE:       (120, 120, 130),
    TILE_GRASS:       ( 76, 153,   0),
    TILE_SAND:        (210, 190, 110),
    TILE_WOOD:        (180, 120,  60),
    TILE_COAL:        ( 60,  60,  70),
    TILE_BRICK:       (180,  80,  50),   # rouge brique
    TILE_CHEST:       (200, 140,  50),   # coffre brun-doré
    TILE_OBSIDIAN:    ( 30,  20,  50),   # violet très sombre
    TILE_GLASS:       (180, 220, 250),   # bleu clair translucide
    TILE_IRON_ORE:    (135, 108,  92),   # brun-rouille
    TILE_GOLD_ORE:    (180, 155,  55),   # jaune-pierre
    TILE_DIAMOND_ORE: ( 70, 200, 215),   # bleu glacier
    TILE_SNOW:        (230, 240, 255),   # blanc bleuté
    TILE_ICE:         (150, 200, 240),   # bleu glace
    TILE_LAVA:        (220,  80,   0),   # orange lave
    TILE_WATER:       ( 40,  90, 200),   # bleu eau
}

# Temps en secondes pour casser un bloc (appui continu)
TILE_BREAK_TIME = {
    TILE_DIRT:        0.4,
    TILE_STONE:       0.9,
    TILE_GRASS:       0.4,
    TILE_SAND:        0.3,
    TILE_WOOD:        0.5,
    TILE_COAL:        0.8,
    TILE_BRICK:       1.2,
    TILE_CHEST:       0.3,   # coffre : s'ouvre vite avec la main
    TILE_OBSIDIAN:    3.0,
    TILE_GLASS:       0.3,
    TILE_IRON_ORE:    1.2,
    TILE_GOLD_ORE:    1.8,
    TILE_DIAMOND_ORE: 2.5,
    TILE_SNOW:        0.3,
    TILE_ICE:         0.5,
}

# Tier de pioche minimum requis pour miner un bloc
# 0=main/n'importe, 1=Bois, 2=Fer, 3=Or, 4=Diamant
TILE_PICKAXE_TIER = {
    TILE_DIRT:        0,
    TILE_GRASS:       0,
    TILE_SAND:        0,
    TILE_WOOD:        0,
    TILE_COAL:        1,
    TILE_STONE:       1,
    TILE_GLASS:       1,
    TILE_BRICK:       2,
    TILE_IRON_ORE:    1,
    TILE_GOLD_ORE:    2,
    TILE_OBSIDIAN:    3,
    TILE_DIAMOND_ORE: 3,
    TILE_SNOW:        0,
    TILE_ICE:         1,
}

# ── Génération du terrain ─────────────────────────────────────────────────────
SURFACE_Y      = 30     # ligne de surface (tuile de haut en bas)
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
J1_BTN_MODIFIER = 12   # I (SELECT)
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
J2_BTN_MINE     =  4   # R2 (gâchette)
J2_BTN_MINE2    =  5   # R  (gâchette alt)
J2_BTN_MODIFIER = 17   # VI (START)
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

# Craft (menu de fabrication)
KB_J1_CRAFT = pygame.K_c
KB_J2_CRAFT = pygame.K_n
