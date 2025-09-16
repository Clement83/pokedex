# Configuration écran & BDD
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 320
LIST_WIDTH = 14
SPRITE_SIZE = 64
FONT_SIZE = 16
DB_PATH = "./pokedex.db"

# Shiny rate (e.g., 0.01 for 1% chance, 0.5 for 50% chance for testing)
SHINY_RATE = 0.01

GENERATION_THRESHOLDS = {
    1: {'max_id': 9, 'unlock_count': 0}, # starters
    2: {'max_id': 149, 'unlock_count': 1}, # Gen 1 (excluding Mew and Mewtwo)
    3: {'max_id': 150, 'unlock_count': 50}, # Gen 1 (Adding Mewtwo)
    4: {'max_id': 251, 'unlock_count': 75}, # Unlock Gen 2 after catching 75 Pokémon
    5: {'max_id': 386, 'unlock_count': 150}, # Unlock Gen 3 after catching 150 Pokémon
    6: {'max_id': 493, 'unlock_count': 300}, # Unlock Gen 4 after catching 300 Pokémon
    7: {'max_id': 649, 'unlock_count': 450}, # Unlock Gen 5 after catching 450 Pokémon
    8: {'max_id': 721, 'unlock_count': 600}, # Unlock Gen 6 after catching 600 Pokémon
    9: {'max_id': 809, 'unlock_count': 700}, # Unlock Gen 7 after catching 700 Pokémon
    10: {'max_id': 906, 'unlock_count': 800}, # Unlock Gen 8 after catching 800 Pokémon
    11: {'max_id': 1026, 'unlock_count': 900}, # Unlock Gen 9 after catching 900 Pokémon
}

# Define regions with their Pokedex ID ranges
REGIONS = {
    "Kanto": {"min_id": 1, "max_id": 152, "image": "kanto.png"}, # Gen 1: 1-151 (max_id is exclusive)
    "Johto": {"min_id": 152, "max_id": 252, "image": "johto.png"}, # Gen 2: 152-251
    "Hoenn": {"min_id": 252, "max_id": 387, "image": "hoenn.png"}, # Gen 3: 252-386
    "Sinnoh": {"min_id": 387, "max_id": 494, "image": "sinnoh.png"}, # Gen 4: 387-493
    "Unova": {"min_id": 494, "max_id": 650, "image": "unova.png"}, # Gen 5: 494-649
    "Kalos": {"min_id": 650, "max_id": 722, "image": "kalos.png"}, # Gen 6: 650-721
    "Alola": {"min_id": 722, "max_id": 810, "image": "alola.png"}, # Gen 7: 722-809
    "Galar": {"min_id": 810, "max_id": 906, "image": "galar.png"}, # Gen 8: 810-905
    "Paldea": {"min_id": 906, "max_id": 1026, "image": "paldea.png"}, # Gen 9: 906-1025
}