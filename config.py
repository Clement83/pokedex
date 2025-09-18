import pygame

# Configuration écran & BDD
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 320
LIST_WIDTH = 14
SPRITE_SIZE = 64
FONT_SIZE = 16
DB_PATH = "./pokedex.db"

# UI adjustments for list screen
STATS_FONT_SIZE = 12
LIST_VERTICAL_OFFSET = 20
STATS_AREA_HEIGHT = 60

# Shiny rate (e.g., 0.01 for 1% chance, 0.5 for 50% chance for testing)
SHINY_RATE = 0.01

# Key Mappings for Odroid Go Advance compatibility
KEY_MAPPINGS = {
    "UP": [pygame.K_UP],
    "DOWN": [pygame.K_DOWN],
    "LEFT": [pygame.K_LEFT],
    "RIGHT": [pygame.K_RIGHT],
    "CONFIRM": [pygame.K_n, pygame.K_RETURN], # Validate button (A on Odroid)
    "CANCEL": [pygame.K_m],                   # Cancel button (B on Odroid)
    "ACTION": [pygame.K_SPACE],               # Action button (e.g., Start on Odroid)
    "QUIT": [pygame.K_ESCAPE],                # Quit/Menu button
}

# Joystick Mappings for Odroid Go Advance / Standard Gamepads
# NOTE: Button numbers might need to be adjusted for your specific controller.
# Common mappings: 0=A, 1=B, 8=Select, 9=Start
JOYSTICK_MAPPINGS = {
    "BUTTONS": {
        0: "CONFIRM",  # A button
        1: "CANCEL",   # B button
        2: "ACTION", # X button (not used yet)
        # 3: "Y_ACTION", # Y button (not used yet)
        8: "UP",   
        9: "DOWN", 
        10: "LEFT",  # Left Bumper (not used yet)
        11: "RIGHT", # Right Bumper (not used yet)
    },
    "HATS": {
        # Hat 0 is usually the D-Pad
        # Value is (x, y), where x is -1 (left), 0, 1 (right) and y is -1 (down), 0, 1 (up)
        # This mapping is handled by the controls.py logic directly
    },
    "AXES": {
        # (axis_index, direction): "ACTION"
        # direction is -1 for up/left, 1 for down/right
        # Axis 0: Left Stick L/R
        # Axis 1: Left Stick U/D
        (1, -1): "UP",
        (1, 1): "DOWN",
        (0, -1): "LEFT",
        (0, 1): "RIGHT",
    },
    "AXIS_DEADZONE": 0.7 # Use a higher deadzone to avoid drift
}


# Stabilize game configuration
STABILIZE_CATCH_RATE_THRESHOLD = 60  # Skip stabilize mini-game if catch_rate > this value

GENERATION_THRESHOLDS = {
    1: {'max_id': 9, 'unlock_count': 0}, # starters
    2: {'max_id': 150, 'unlock_count': 1}, # Gen 1 (excluding Mew)
    4: {'max_id': 251, 'unlock_count': 50}, # Unlock Gen 2 after catching 100 Pokémon
    5: {'max_id': 386, 'unlock_count': 100}, # Unlock Gen 3 after catching 150 Pokémon
    6: {'max_id': 493, 'unlock_count': 150}, # Unlock Gen 4 after catching 250 Pokémon
    7: {'max_id': 649, 'unlock_count': 200}, # Unlock Gen 5 after catching 300 Pokémon
    8: {'max_id': 721, 'unlock_count': 250}, # Unlock Gen 6 after catching 350 Pokémon
    9: {'max_id': 809, 'unlock_count': 300}, # Unlock Gen 7 after catching 400 Pokémon
    10: {'max_id': 906, 'unlock_count': 350}, # Unlock Gen 8 after catching 450 Pokémon
    11: {'max_id': 1026, 'unlock_count': 400}, # Unlock Gen 9 after catching 500 Pokémon
}

# Define regions with their Pokedex ID ranges
REGIONS = {
    "Kanto": {"min_id": 1, "max_id": 152}, # Gen 1: 1-151 (max_id is exclusive)
    "Johto": {"min_id": 152, "max_id": 252}, # Gen 2: 152-251
    "Hoenn": {"min_id": 252, "max_id": 387}, # Gen 3: 252-386
    "Sinnoh": {"min_id": 387, "max_id": 494}, # Gen 4: 387-493
    "Unova": {"min_id": 494, "max_id": 650}, # Gen 5: 494-649
    "Kalos": {"min_id": 650, "max_id": 722}, # Gen 6: 650-721
    "Alola": {"min_id": 722, "max_id": 810}, # Gen 7: 722-809
    "Galar": {"min_id": 810, "max_id": 906}, # Gen 8: 810-905
    "Paldea": {"min_id": 906, "max_id": 1026}, # Gen 9: 906-1025
}