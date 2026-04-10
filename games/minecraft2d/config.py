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
TILE_TORCH       = 18       # torche (éclairage, plaçable)
TILE_ARROW       = 19       # flèches  (munitions arc, item uniquement)
TILE_SILK        = 20       # fil d'araignée (composant de craft, item uniquement)
TILE_FISH        = 21       # poisson (pêche, nourriture future)
TILE_EGG         = 22       # œuf (pondu par poule familière, nourriture)
TILE_FLAG        = 23       # drapeau de respawn (item outil)
TILE_CRAFT       = 24       # table de craft (item outil)
TILE_ROD         = 25       # canne à pêche (item outil)
# Outils à variante matériau (items non plaçables)
TILE_PICKAXE_WOOD    = 26
TILE_PICKAXE_IRON    = 27
TILE_PICKAXE_GOLD    = 28
TILE_PICKAXE_DIAMOND = 29
TILE_SWORD_WOOD      = 30
TILE_SWORD_IRON      = 31
TILE_SWORD_GOLD      = 32
TILE_SWORD_DIAMOND   = 33
TILE_BOW_WOOD        = 34
TILE_BOW_IRON        = 35
# Armures (portables + plaçables comme blocs)
TILE_HEAD_WOOD       = 36
TILE_HEAD_IRON       = 37
TILE_HEAD_GOLD       = 38
TILE_HEAD_DIAMOND    = 39
TILE_BODY_WOOD       = 40
TILE_BODY_IRON       = 41
TILE_BODY_GOLD       = 42
TILE_BODY_DIAMOND    = 43
TILE_FEET_WOOD       = 44
TILE_FEET_IRON       = 45
TILE_FEET_GOLD       = 46
TILE_FEET_DIAMOND    = 47
# Matériaux spéciaux (drops de mobs)
TILE_BONE            = 48       # os (squelettes, zombies, morts-vivants)
TILE_SLIME_BALL      = 49       # bave de slime
TILE_FANG            = 50       # croc (bêtes : loup, sanglier, ours, scorpion)
TILE_CRYSTAL         = 51       # cristal (golems, trolls, vers, boss)
TILE_FEATHER         = 52       # plume (oiseaux, chauves-souris)
TILE_VENOM           = 53       # venin (araignées, scorpions)
TILE_MAGMA           = 54       # cœur de magma (démons, boss)
# Flèches spéciales
TILE_ARROW_FIRE      = 55       # flèche de feu (dégâts x2.5)
TILE_ARROW_POISON    = 56       # flèche empoisonnée (DoT 4s)
TILE_ARROW_EXPLOSIVE = 57       # flèche explosive (dégâts zone + casse blocs)
# Objets spéciaux craftables
TILE_HEART_CRYSTAL   = 58       # cœur de cristal (consommable : +2 PV max)
TILE_TOTEM           = 59       # totem de résurrection (auto : revit au lieu de mourir)
# Armure cristal (défense tier 3, base pour améliorations)
TILE_HEAD_CRYSTAL    = 60
TILE_BODY_CRYSTAL    = 61
TILE_FEET_CRYSTAL    = 62
# Armures améliorées — Vital (casque, +2 PV max)
TILE_HEAD_WOOD_VITAL     = 63
TILE_HEAD_IRON_VITAL     = 64
TILE_HEAD_GOLD_VITAL     = 65
TILE_HEAD_DIAMOND_VITAL  = 66
TILE_HEAD_CRYSTAL_VITAL  = 67
# Armures améliorées — Force (plastron, +1 dégât épée)
TILE_BODY_WOOD_FORCE     = 68
TILE_BODY_IRON_FORCE     = 69
TILE_BODY_GOLD_FORCE     = 70
TILE_BODY_DIAMOND_FORCE  = 71
TILE_BODY_CRYSTAL_FORCE  = 72
# Armures améliorées — Véloce (bottes, +1.5 vitesse)
TILE_FEET_WOOD_SWIFT     = 73
TILE_FEET_IRON_SWIFT     = 74
TILE_FEET_GOLD_SWIFT     = 75
TILE_FEET_DIAMOND_SWIFT  = 76
TILE_FEET_CRYSTAL_SWIFT  = 77
TILE_GORGON_HEART        = 78   # cœur unique du boss Gorgone
# Portail & livres
TILE_BOOK                = 79   # livre (trouvé dans les coffres, lisible)
TILE_PORTAL_STONE        = 80   # pierre de portail (craftable, composant du portail)
TILE_PORTAL              = 81   # portail actif (non-solide, téléporte vers l'arène boss)

# Tiles qui sont des items (non générés naturellement)
TILE_ITEMS = frozenset(range(19, 82))

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
    TILE_TORCH:       "Torche",
    TILE_ARROW:       "Flèches",
    TILE_SILK:        "Fil d'araignée",
    TILE_FISH:        "Poisson",
    TILE_EGG:         "Œuf",
    TILE_FLAG:        "Drapeau",
    TILE_CRAFT:       "Table de Craft",
    TILE_ROD:         "Canne à pêche",
    TILE_PICKAXE_WOOD:    "Pioche Bois",
    TILE_PICKAXE_IRON:    "Pioche Fer",
    TILE_PICKAXE_GOLD:    "Pioche Or",
    TILE_PICKAXE_DIAMOND: "Pioche Diamant",
    TILE_SWORD_WOOD:      "Épée Bois",
    TILE_SWORD_IRON:      "Épée Fer",
    TILE_SWORD_GOLD:      "Épée Or",
    TILE_SWORD_DIAMOND:   "Épée Diamant",
    TILE_BOW_WOOD:        "Arc Bois",
    TILE_BOW_IRON:        "Arc Fer",
    TILE_HEAD_WOOD:       "Casque Bois",
    TILE_HEAD_IRON:       "Casque Fer",
    TILE_HEAD_GOLD:       "Casque Or",
    TILE_HEAD_DIAMOND:    "Casque Diamant",
    TILE_BODY_WOOD:       "Plastron Bois",
    TILE_BODY_IRON:       "Plastron Fer",
    TILE_BODY_GOLD:       "Plastron Or",
    TILE_BODY_DIAMOND:    "Plastron Diamant",
    TILE_FEET_WOOD:       "Bottes Bois",
    TILE_FEET_IRON:       "Bottes Fer",
    TILE_FEET_GOLD:       "Bottes Or",
    TILE_FEET_DIAMOND:    "Bottes Diamant",
    TILE_BONE:            "Os",
    TILE_SLIME_BALL:      "Bave de slime",
    TILE_FANG:            "Croc",
    TILE_CRYSTAL:         "Cristal",
    TILE_FEATHER:         "Plume",
    TILE_VENOM:           "Venin",
    TILE_MAGMA:           "Cœur de magma",
    TILE_ARROW_FIRE:      "Flèche de feu",
    TILE_ARROW_POISON:    "Flèche poison",
    TILE_ARROW_EXPLOSIVE: "Flèche explosive",
    TILE_HEART_CRYSTAL:   "Cœur de cristal",
    TILE_TOTEM:           "Totem",
    TILE_HEAD_CRYSTAL:    "Casque Cristal",
    TILE_BODY_CRYSTAL:    "Plastron Cristal",
    TILE_FEET_CRYSTAL:    "Bottes Cristal",
    # Améliorées — Vital (+PV)
    TILE_HEAD_WOOD_VITAL:    "Casque Bois ❤",
    TILE_HEAD_IRON_VITAL:    "Casque Fer ❤",
    TILE_HEAD_GOLD_VITAL:    "Casque Or ❤",
    TILE_HEAD_DIAMOND_VITAL: "Casque Diamant ❤",
    TILE_HEAD_CRYSTAL_VITAL: "Casque Cristal ❤",
    # Améliorées — Force (+dégâts)
    TILE_BODY_WOOD_FORCE:    "Plastron Bois ⚔",
    TILE_BODY_IRON_FORCE:    "Plastron Fer ⚔",
    TILE_BODY_GOLD_FORCE:    "Plastron Or ⚔",
    TILE_BODY_DIAMOND_FORCE: "Plastron Diamant ⚔",
    TILE_BODY_CRYSTAL_FORCE: "Plastron Cristal ⚔",
    # Améliorées — Véloce (+vitesse)
    TILE_FEET_WOOD_SWIFT:    "Bottes Bois ➤",
    TILE_FEET_IRON_SWIFT:    "Bottes Fer ➤",
    TILE_FEET_GOLD_SWIFT:    "Bottes Or ➤",
    TILE_FEET_DIAMOND_SWIFT: "Bottes Diamant ➤",
    TILE_FEET_CRYSTAL_SWIFT: "Bottes Cristal ➤",
    TILE_GORGON_HEART:       "Cœur de Gorgone",
    TILE_BOOK:               "Livre ancien",
    TILE_PORTAL_STONE:       "Pierre de Portail",
    TILE_PORTAL:             "Portail",
}

# ── Outils ────────────────────────────────────────────────────────────────────
TOOL_HAND    = 0   # saisir / interagir : ouvrir coffres
TOOL_PICKAXE = 1   # creuser uniquement
TOOL_PLACER  = 2   # poser des blocs (appui simple MINE)
TOOL_SWORD   = 3   # épée : attaque les mobs (MINE = coup d'épée)
TOOL_FLAG    = 4   # drapeau : pose le point de respawn au sol
TOOL_CRAFT   = 5   # table de craft : action=ouvrir menu, alt=fermer
TOOL_BOW     = 6   # arc : tirer une flèche (consomme TILE_ARROW)
TOOL_ROD     = 7   # canne à pêche : pêcher dans l'eau
TOOL_TORCH   = 8   # torche en main : poser une torche à portée
TOOL_NAMES   = {TOOL_HAND: "Main", TOOL_PICKAXE: "Pioche",
                TOOL_PLACER: "Canon", TOOL_SWORD: "Épée", TOOL_FLAG: "Drapeau",
                TOOL_CRAFT: "Table Craft", TOOL_BOW: "Arc", TOOL_ROD: "Canne à pêche",
                TOOL_TORCH: "Torche"}
TOOLS_LIST   = [TOOL_HAND, TOOL_PICKAXE, TOOL_PLACER, TOOL_SWORD, TOOL_FLAG, TOOL_CRAFT,
                TOOL_BOW, TOOL_ROD, TOOL_TORCH]

# ── Équipements ───────────────────────────────────────────────────────────────
# Slot d'équipement
EQUIP_HEAD    = 0   # casque
EQUIP_BODY    = 1   # plastron
EQUIP_FEET    = 2   # bottes
EQUIP_SWORD   = 3   # épée (main)
EQUIP_PICKAXE = 4   # pioche (main)
EQUIP_BOW     = 5   # arc (arme à distance)

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
MAT_CRYSTAL = 4
MAT_NAMES = {MAT_WOOD: "Bois", MAT_IRON: "Fer", MAT_GOLD: "Or", MAT_DIAMOND: "Diamant", MAT_CRYSTAL: "Cristal"}

# Couleurs des matériaux sur le bonhomme
MAT_COLORS = {
    MAT_WOOD:    (139,  90,  43),   # brun bois
    MAT_IRON:    (170, 170, 185),   # gris métal
    MAT_GOLD:    (255, 200,   0),   # jaune or
    MAT_DIAMOND: ( 80, 220, 235),   # cyan diamant
    MAT_CRYSTAL: (180, 130, 255),   # violet cristallin
}

# Tier de matériau (pour vérification pioche/épée)
MAT_TIER = {MAT_WOOD: 1, MAT_IRON: 2, MAT_GOLD: 3, MAT_DIAMOND: 4, MAT_CRYSTAL: 3}

# Défense d'armure par matériau (par pièce portée)
# Full Fer=3, Full Or=3, Full Diamant=6
ARMOR_DEF = {MAT_WOOD: 0, MAT_IRON: 1, MAT_GOLD: 1, MAT_DIAMOND: 2, MAT_CRYSTAL: 1}

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
    # Arcs
    (EQUIP_BOW, MAT_WOOD):  "Arc Bois",
    (EQUIP_BOW, MAT_IRON):  "Arc Fer",
    # Armure cristal
    (EQUIP_HEAD, MAT_CRYSTAL): "Casque Cristal",
    (EQUIP_BODY, MAT_CRYSTAL): "Plastron Cristal",
    (EQUIP_FEET, MAT_CRYSTAL): "Bottes Cristal",
}

# ── Mapping tiles-outils ↔ (tool, mat) ──────────────────────────────────────
TILE_TOOL_MAP = {
    TILE_PICKAXE_WOOD:    (TOOL_PICKAXE, MAT_WOOD),
    TILE_PICKAXE_IRON:    (TOOL_PICKAXE, MAT_IRON),
    TILE_PICKAXE_GOLD:    (TOOL_PICKAXE, MAT_GOLD),
    TILE_PICKAXE_DIAMOND: (TOOL_PICKAXE, MAT_DIAMOND),
    TILE_SWORD_WOOD:      (TOOL_SWORD, MAT_WOOD),
    TILE_SWORD_IRON:      (TOOL_SWORD, MAT_IRON),
    TILE_SWORD_GOLD:      (TOOL_SWORD, MAT_GOLD),
    TILE_SWORD_DIAMOND:   (TOOL_SWORD, MAT_DIAMOND),
    TILE_BOW_WOOD:        (TOOL_BOW, MAT_WOOD),
    TILE_BOW_IRON:        (TOOL_BOW, MAT_IRON),
}
TOOL_MAT_TO_TILE = {v: k for k, v in TILE_TOOL_MAP.items()}
_TOOL_TO_EQUIP = {TOOL_PICKAXE: EQUIP_PICKAXE, TOOL_SWORD: EQUIP_SWORD, TOOL_BOW: EQUIP_BOW}
EQUIP_TO_TILE = {(_TOOL_TO_EQUIP[t], m): tile for tile, (t, m) in TILE_TOOL_MAP.items()}

# Mapping tuile armure → (equip_slot, matériau)
ARMOR_TILE_MAP = {
    TILE_HEAD_WOOD:    (EQUIP_HEAD, MAT_WOOD),
    TILE_HEAD_IRON:    (EQUIP_HEAD, MAT_IRON),
    TILE_HEAD_GOLD:    (EQUIP_HEAD, MAT_GOLD),
    TILE_HEAD_DIAMOND: (EQUIP_HEAD, MAT_DIAMOND),
    TILE_BODY_WOOD:    (EQUIP_BODY, MAT_WOOD),
    TILE_BODY_IRON:    (EQUIP_BODY, MAT_IRON),
    TILE_BODY_GOLD:    (EQUIP_BODY, MAT_GOLD),
    TILE_BODY_DIAMOND: (EQUIP_BODY, MAT_DIAMOND),
    TILE_FEET_WOOD:    (EQUIP_FEET, MAT_WOOD),
    TILE_FEET_IRON:    (EQUIP_FEET, MAT_IRON),
    TILE_FEET_GOLD:    (EQUIP_FEET, MAT_GOLD),
    TILE_FEET_DIAMOND: (EQUIP_FEET, MAT_DIAMOND),
    TILE_HEAD_CRYSTAL: (EQUIP_HEAD, MAT_CRYSTAL),
    TILE_BODY_CRYSTAL: (EQUIP_BODY, MAT_CRYSTAL),
    TILE_FEET_CRYSTAL: (EQUIP_FEET, MAT_CRYSTAL),
}
# Compléter EQUIP_TO_TILE avec les armures de BASE uniquement
EQUIP_TO_TILE.update({v: k for k, v in ARMOR_TILE_MAP.items()})

# Armures améliorées : même (slot, mat) que la base → défense identique, bonus spéciaux
# Ajoutées APRÈS EQUIP_TO_TILE pour ne pas écraser les mappings de craft de base
_ENHANCED_ARMOR = {
    # Vital — casques (+2 PV max)
    TILE_HEAD_WOOD_VITAL:    (EQUIP_HEAD, MAT_WOOD),
    TILE_HEAD_IRON_VITAL:    (EQUIP_HEAD, MAT_IRON),
    TILE_HEAD_GOLD_VITAL:    (EQUIP_HEAD, MAT_GOLD),
    TILE_HEAD_DIAMOND_VITAL: (EQUIP_HEAD, MAT_DIAMOND),
    TILE_HEAD_CRYSTAL_VITAL: (EQUIP_HEAD, MAT_CRYSTAL),
    # Force — plastrons (+1 dégât épée)
    TILE_BODY_WOOD_FORCE:    (EQUIP_BODY, MAT_WOOD),
    TILE_BODY_IRON_FORCE:    (EQUIP_BODY, MAT_IRON),
    TILE_BODY_GOLD_FORCE:    (EQUIP_BODY, MAT_GOLD),
    TILE_BODY_DIAMOND_FORCE: (EQUIP_BODY, MAT_DIAMOND),
    TILE_BODY_CRYSTAL_FORCE: (EQUIP_BODY, MAT_CRYSTAL),
    # Véloce — bottes (+1.5 vitesse)
    TILE_FEET_WOOD_SWIFT:    (EQUIP_FEET, MAT_WOOD),
    TILE_FEET_IRON_SWIFT:    (EQUIP_FEET, MAT_IRON),
    TILE_FEET_GOLD_SWIFT:    (EQUIP_FEET, MAT_GOLD),
    TILE_FEET_DIAMOND_SWIFT: (EQUIP_FEET, MAT_DIAMOND),
    TILE_FEET_CRYSTAL_SWIFT: (EQUIP_FEET, MAT_CRYSTAL),
}
ARMOR_TILE_MAP.update(_ENHANCED_ARMOR)

# Sets de détection des bonus d'armure améliorée
VITAL_TILES = frozenset((TILE_HEAD_WOOD_VITAL, TILE_HEAD_IRON_VITAL, TILE_HEAD_GOLD_VITAL,
                         TILE_HEAD_DIAMOND_VITAL, TILE_HEAD_CRYSTAL_VITAL))
FORCE_TILES = frozenset((TILE_BODY_WOOD_FORCE, TILE_BODY_IRON_FORCE, TILE_BODY_GOLD_FORCE,
                         TILE_BODY_DIAMOND_FORCE, TILE_BODY_CRYSTAL_FORCE))
SWIFT_TILES = frozenset((TILE_FEET_WOOD_SWIFT, TILE_FEET_IRON_SWIFT, TILE_FEET_GOLD_SWIFT,
                         TILE_FEET_DIAMOND_SWIFT, TILE_FEET_CRYSTAL_SWIFT))

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
    TILE_TORCH:       (255, 190,  40),   # jaune flamme
    TILE_ARROW:       (180, 155,  90),   # beige bois
    TILE_SILK:        (210, 215, 225),   # gris blanc
    TILE_FISH:        ( 60, 180, 180),   # cyan aquatique
    TILE_EGG:         (245, 235, 210),   # crème coquille
    TILE_FLAG:        (255,  80,  80),   # rouge drapeau
    TILE_CRAFT:       (180, 120,  60),   # brun bois (table)
    TILE_ROD:         (155, 100,  42),   # brun canne
    TILE_PICKAXE_WOOD:    (139,  90,  43),
    TILE_PICKAXE_IRON:    (170, 170, 185),
    TILE_PICKAXE_GOLD:    (255, 200,   0),
    TILE_PICKAXE_DIAMOND: ( 80, 220, 235),
    TILE_SWORD_WOOD:      (139,  90,  43),
    TILE_SWORD_IRON:      (170, 170, 185),
    TILE_SWORD_GOLD:      (255, 200,   0),
    TILE_SWORD_DIAMOND:   ( 80, 220, 235),
    TILE_BOW_WOOD:        (139,  90,  43),
    TILE_BOW_IRON:        (170, 170, 185),
    TILE_HEAD_WOOD:       (139,  90,  43),
    TILE_HEAD_IRON:       (170, 170, 185),
    TILE_HEAD_GOLD:       (255, 200,   0),
    TILE_HEAD_DIAMOND:    ( 80, 220, 235),
    TILE_BODY_WOOD:       (139,  90,  43),
    TILE_BODY_IRON:       (170, 170, 185),
    TILE_BODY_GOLD:       (255, 200,   0),
    TILE_BODY_DIAMOND:    ( 80, 220, 235),
    TILE_FEET_WOOD:       (139,  90,  43),
    TILE_FEET_IRON:       (170, 170, 185),
    TILE_FEET_GOLD:       (255, 200,   0),
    TILE_FEET_DIAMOND:    ( 80, 220, 235),
    TILE_BONE:            (220, 210, 190),   # ivoire
    TILE_SLIME_BALL:      (100, 220,  80),   # vert gluant
    TILE_FANG:            (235, 225, 200),   # blanc cassé
    TILE_CRYSTAL:         (180, 130, 255),   # violet cristallin
    TILE_FEATHER:         (240, 240, 250),   # blanc duveteux
    TILE_VENOM:           ( 80, 180,  50),   # vert toxique
    TILE_MAGMA:           (255, 100,  20),   # orange incandescent
    TILE_ARROW_FIRE:      (255, 120,  30),   # orange feu
    TILE_ARROW_POISON:    (100, 200,  60),   # vert poison
    TILE_ARROW_EXPLOSIVE: (255,  60,  60),   # rouge explosif
    TILE_HEART_CRYSTAL:   (220, 100, 255),   # violet rosé
    TILE_TOTEM:           (255, 220, 100),   # doré lumineux
    TILE_HEAD_CRYSTAL:    (180, 130, 255),
    TILE_BODY_CRYSTAL:    (180, 130, 255),
    TILE_FEET_CRYSTAL:    (180, 130, 255),
    # Vital — teinte rosée
    TILE_HEAD_WOOD_VITAL:    (175,  95,  75),
    TILE_HEAD_IRON_VITAL:    (195, 150, 175),
    TILE_HEAD_GOLD_VITAL:    (255, 175, 100),
    TILE_HEAD_DIAMOND_VITAL: (150, 190, 235),
    TILE_HEAD_CRYSTAL_VITAL: (210, 120, 230),
    # Force — teinte orangée
    TILE_BODY_WOOD_FORCE:    (175, 105,  45),
    TILE_BODY_IRON_FORCE:    (195, 160, 145),
    TILE_BODY_GOLD_FORCE:    (255, 180,  50),
    TILE_BODY_DIAMOND_FORCE: (140, 200, 200),
    TILE_BODY_CRYSTAL_FORCE: (200, 130, 200),
    # Véloce — teinte bleutée
    TILE_FEET_WOOD_SWIFT:    (150, 130, 105),
    TILE_FEET_IRON_SWIFT:    (175, 190, 210),
    TILE_FEET_GOLD_SWIFT:    (230, 210, 130),
    TILE_FEET_DIAMOND_SWIFT: (120, 220, 245),
    TILE_FEET_CRYSTAL_SWIFT: (180, 170, 255),
    TILE_GORGON_HEART:       (170,  10,  80),   # rouge-violet sombre, loot boss
    TILE_BOOK:               (160, 120,  60),   # brun parchemin
    TILE_PORTAL_STONE:       ( 80,  30, 120),   # violet sombre
    TILE_PORTAL:             (120,  40, 200),   # violet lumineux (actif)
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
    TILE_TORCH:       0.2,   # torche cassable rapidement à la main
    # Items posés dans le monde : cassables à la main en 0.3s
    TILE_ARROW: 0.3, TILE_SILK: 0.3,  TILE_FISH: 0.3,  TILE_EGG: 0.3,
    TILE_FLAG:  0.3, TILE_CRAFT: 0.3, TILE_ROD:  0.3,
    TILE_PICKAXE_WOOD: 0.3, TILE_PICKAXE_IRON: 0.3, TILE_PICKAXE_GOLD: 0.3, TILE_PICKAXE_DIAMOND: 0.3,
    TILE_SWORD_WOOD:   0.3, TILE_SWORD_IRON:   0.3, TILE_SWORD_GOLD:   0.3, TILE_SWORD_DIAMOND:   0.3,
    TILE_BOW_WOOD:     0.3, TILE_BOW_IRON:     0.3,
    TILE_HEAD_WOOD: 0.3, TILE_HEAD_IRON: 0.3, TILE_HEAD_GOLD: 0.3, TILE_HEAD_DIAMOND: 0.3,
    TILE_BODY_WOOD: 0.3, TILE_BODY_IRON: 0.3, TILE_BODY_GOLD: 0.3, TILE_BODY_DIAMOND: 0.3,
    TILE_FEET_WOOD: 0.3, TILE_FEET_IRON: 0.3, TILE_FEET_GOLD: 0.3, TILE_FEET_DIAMOND: 0.3,
    TILE_BONE: 0.3, TILE_SLIME_BALL: 0.3, TILE_FANG: 0.3, TILE_CRYSTAL: 0.3,
    TILE_FEATHER: 0.3, TILE_VENOM: 0.3, TILE_MAGMA: 0.3,
    TILE_ARROW_FIRE: 0.3, TILE_ARROW_POISON: 0.3, TILE_ARROW_EXPLOSIVE: 0.3,
    TILE_HEART_CRYSTAL: 0.3, TILE_TOTEM: 0.3,
    TILE_HEAD_CRYSTAL: 0.3, TILE_BODY_CRYSTAL: 0.3, TILE_FEET_CRYSTAL: 0.3,
    TILE_HEAD_WOOD_VITAL: 0.3, TILE_HEAD_IRON_VITAL: 0.3, TILE_HEAD_GOLD_VITAL: 0.3,
    TILE_HEAD_DIAMOND_VITAL: 0.3, TILE_HEAD_CRYSTAL_VITAL: 0.3,
    TILE_BODY_WOOD_FORCE: 0.3, TILE_BODY_IRON_FORCE: 0.3, TILE_BODY_GOLD_FORCE: 0.3,
    TILE_BODY_DIAMOND_FORCE: 0.3, TILE_BODY_CRYSTAL_FORCE: 0.3,
    TILE_FEET_WOOD_SWIFT: 0.3, TILE_FEET_IRON_SWIFT: 0.3, TILE_FEET_GOLD_SWIFT: 0.3,
    TILE_FEET_DIAMOND_SWIFT: 0.3, TILE_FEET_CRYSTAL_SWIFT: 0.3,
    TILE_BOOK: 0.3, TILE_PORTAL_STONE: 2.0,
}

# Ensemble des tiles flèche (pour le système d'arc)
ARROW_TILES = frozenset((TILE_ARROW, TILE_ARROW_FIRE, TILE_ARROW_POISON, TILE_ARROW_EXPLOSIVE))

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
    TILE_PORTAL_STONE: 3,
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

# ── Portail & Arène Boss ─────────────────────────────────────────────────────
BOSS_ARENA_COL = -500_000   # colonne de l'arène boss (très loin à gauche)
BOSS_ARENA_W   = 40         # largeur de l'arène (colonnes)
BOSS_ARENA_H   = 35         # hauteur de l'arène (rangées)

# Textes des livres anciens (lore + guide)
BOOK_TEXTS = [
    # 0 — Guide du portail
    [
        "~ LE PORTAIL ~",
        "",
        "Les anciens parlent d'un portail",
        "menant au repaire de la Gorgone.",
        "",
        "Construction :",
        "  Creusez un trou de 3 blocs.",
        "  Entourez d'Obsidienne",
        "  (lave + eau = obsidienne).",
        "  Placez 3 Pierres de Portail",
        "  au centre du cadre.",
        "",
        "  OBS [P] [P] [P] OBS",
        "  OBS OBS OBS OBS OBS",
        "",
        "Pierre de Portail :",
        "  Table Diamant : Cristal x2",
        "  Magma x2, Diamant x1",
        "",
        "Sautez dedans... si vous l'osez.",
    ],
    # 1 — Les biomes
    [
        "~ LES TROIS TERRES ~",
        "",
        "Foret : terres verdoyantes,",
        "arbres denses, cabanes de bois.",
        "Les sangliers et loups y rodent.",
        "",
        "Desert : dunes de sable brulant,",
        "pyramides oubliees, scorpions",
        "et vautours tournoyants.",
        "",
        "Glace : etendues gelees,",
        "igloos enneiges. Les ours",
        "polaires et pingouins y vivent.",
        "",
        "Chaque terre cache ses propres",
        "structures et ses dangers.",
    ],
    # 2 — Faune de surface
    [
        "~ BESTIAIRE DE SURFACE ~",
        "",
        "Poulets : inoffensifs, donnent",
        "  oeufs et plumes. Apprivoisables.",
        "Grenouilles : paisibles, foret.",
        "Mouettes : survolent les cotes.",
        "Crabes : agressifs sur le sable.",
        "Sangliers : chargent en foret.",
        "Loups : neutres, attaquent en",
        "  meute si provoques. Domptables.",
        "Chats : timides, apprivoisables.",
        "",
        "Nourrir un loup ou chat avec",
        "un poisson pour l'apprivoiser.",
    ],
    # 3 — Horreurs des profondeurs
    [
        "~ LES PROFONDEURS ~",
        "",
        "Sous la pierre, le danger croit.",
        "",
        "Slimes : cavernes peu profondes.",
        "Araignees : tissent dans l'ombre.",
        "Zombies : errent sans relache.",
        "Squelettes : embusques, profonds.",
        "Trolls : lents mais resistants.",
        "Vers : traversent la roche meme.",
        "Spectres : flottent dans l'abime.",
        "Demons : gardiens des laves,",
        "  seule une epee d'Or les blesse.",
        "",
        "Plus on creuse, plus c'est mortel.",
    ],
    # 4 — Structures
    [
        "~ RUINES ET BATISSES ~",
        "",
        "Cabanes : petites, en bois,",
        "  gardees par un Golem de pierre.",
        "  Coffre a l'interieur.",
        "",
        "Chateaux : murs de brique,",
        "  fenetres de verre. Foret/glace.",
        "",
        "Pyramides : briques et obsidienne.",
        "  Grandes pyramides dans le desert",
        "  cachent 2 coffres en leur sein.",
        "",
        "Navires pirates : echoues,",
        "  2 coffres dans la cale.",
        "",
        "Donjons : sous terre, obsidienne.",
        "  Butin precieux dans les coffres.",
    ],
    # 5 — Minerais
    [
        "~ RICHESSES SOUTERRAINES ~",
        "",
        "Charbon : partout sous la pierre.",
        "  Sert aux torches et au craft.",
        "",
        "Fer : profondeur moyenne.",
        "  Outils et armures solides.",
        "",
        "Or : grottes profondes.",
        "  Armes capables de blesser",
        "  les demons et la Vrille.",
        "",
        "Diamant : abimes les plus bas.",
        "  Le materiau ultime. Requis",
        "  pour la table de craft finale.",
        "",
        "Obsidienne : ou lave et eau",
        "  se rencontrent. Quasi eternelle.",
    ],
    # 6 — L'art du craft
    [
        "~ L'ART DU CRAFT ~",
        "",
        "La table de craft evolue :",
        "  Bois -> Fer -> Or -> Diamant",
        "  Chaque tier debloque de",
        "  nouvelles recettes.",
        "",
        "Fleches speciales :",
        "  Feu (Magma), Poison (Venin),",
        "  Explosive (Bave + Magma).",
        "",
        "Armures ameliorees :",
        "  Vital (casque) : +2 PV max",
        "  Force (plastron) : +1 degat",
        "  Veloce (bottes) : +vitesse",
        "",
        "Le Cristal forge une armure",
        "aussi solide que l'Or.",
    ],
    # 7 — Familiers
    [
        "~ COMPAGNONS FIDELES ~",
        "",
        "Trois creatures domesticables :",
        "",
        "Loup : offrez-lui un poisson.",
        "  Il combattra a vos cotes,",
        "  attaquant vos ennemis.",
        "",
        "Chat : offrez-lui un poisson.",
        "  Compagnon fidele et discret.",
        "",
        "Poulet : approchez avec la Main.",
        "  Pond des oeufs regulierement.",
        "",
        "Un seul familier par joueur.",
        "Prenez-en soin : ils ne",
        "reviennent pas une fois perdus.",
    ],
    # 8 — La Gorgone
    [
        "~ LA LEGENDE DE LA GORGONE ~",
        "",
        "Dans les entrailles du monde,",
        "une creature ancestrale sommeille.",
        "",
        "La Gorgone : un serpent geant",
        "ancre au sol par ses racines.",
        "Sa tete oscille, cherchant",
        "le moindre bruit, la moindre",
        "vibration dans la roche.",
        "",
        "50 coups pour l'abattre.",
        "Seule une epee d'Or ou mieux",
        "peut entamer sa chair.",
        "",
        "Son coeur est un trophee",
        "unique... pour les survivants.",
    ],
    # 9 — Survie
    [
        "~ CONSEILS DE SURVIE ~",
        "",
        "Posez un drapeau : c'est votre",
        "  point de respawn a la mort.",
        "",
        "La nuit, les zombies emergent.",
        "  Ils brulent a l'aube.",
        "",
        "Torches : eclairent les grottes",
        "  et eloignent l'obscurite.",
        "",
        "Totem : vous ressuscite une",
        "  fois sur place. Precieux.",
        "",
        "Coeur de cristal : +2 PV max",
        "  permanent. Ne les gaspillez pas.",
        "",
        "L'eau ralentit. La lave tue.",
        "Grimpez aux murs avec Haut.",
    ],
]
