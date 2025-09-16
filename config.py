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
    7: {'max_id': 649, 'unlock_count': 500}, # Unlock Gen 5 after catching 500 Pokémon
    8: {'max_id': 721, 'unlock_count': 700}, # Unlock Gen 6 after catching 700 Pokémon
    9: {'max_id': 809, 'unlock_count': 800}, # Unlock Gen 7 after catching 800 Pokémon
    10: {'max_id': 1500, 'unlock_count': 900}, # Unlock Gen 8 after catching 900 Pokémon
}