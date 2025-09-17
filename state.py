import pygame
from pathlib import Path
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FONT_SIZE, GENERATION_THRESHOLDS
from db import get_connection, get_pokemon_list, get_caught_pokemon_count, get_shiny_pokemon_count, mew_is_unlocked
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FONT_SIZE, GENERATION_THRESHOLDS, REGIONS, STATS_AREA_HEIGHT
from sprites import load_pokeball_sprites

class GameState:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Pokédex Pi Zero")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", FONT_SIZE, bold=True)
        
        self.conn = get_connection()
        caught_count_at_startup = get_caught_pokemon_count(self.conn)
        mew_unlocked_at_startup = mew_is_unlocked(self.conn)

        self.current_max_pokedex_id = GENERATION_THRESHOLDS[1]['max_id']
        for gen, data in GENERATION_THRESHOLDS.items():
            if caught_count_at_startup >= data['unlock_count'] and self.current_max_pokedex_id < data['max_id']:
                self.current_max_pokedex_id = data['max_id']

        self.pokemon_list = get_pokemon_list(self.conn, self.current_max_pokedex_id, include_mew=mew_unlocked_at_startup)
        
        self.pokeball_img_small, _ = load_pokeball_sprites(30)
        self.pokeball_img_large, _ = load_pokeball_sprites(50)

        self.selected_index = 0
        self.state = "list"  # list, detail
        self.scroll_offset = 0
        self.max_visible_items = (SCREEN_HEIGHT - 40) // FONT_SIZE
        self.current_pokemon_data = None
        self.current_sprite = None
        self.BASE_DIR = Path.cwd()

        self.running = True

        self.key_down_pressed = False
        self.key_up_pressed = False
        self.down_press_time = 0
        self.up_press_time = 0
        self.scroll_delay = 200
        self.scroll_fast_delay = 50
        self.scroll_accel_time = 2000
        self.last_scroll_time = 0
        self.sprite_cache = {}
        self.list_view_background = None
        self.message = None
        self.message_timer = 0

        # General stats
        self.caught_count = get_caught_pokemon_count(self.conn)
        self.shiny_count = get_shiny_pokemon_count(self.conn)
        self.unlocked_regions_count = 0
        for region_name, data in REGIONS.items():
            if data["min_id"] < self.current_max_pokedex_id:
                self.unlocked_regions_count += 1
