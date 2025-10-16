import pygame
import random
from pathlib import Path
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FONT_SIZE, GENERATION_THRESHOLDS
from db import get_connection, get_pokemon_list, get_caught_pokemon_count, get_shiny_pokemon_count, mew_is_unlocked, get_seen_pokemon_count
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FONT_SIZE, GENERATION_THRESHOLDS, REGIONS, STATS_AREA_HEIGHT
from sprites import load_pokeball_sprites

class GameState:
    def __init__(self):
        pygame.init()
        pygame.joystick.init() # Initialize joystick module
        self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        if self.joysticks:
            print(f"Found {len(self.joysticks)} joystick(s). Using the first one.")
            # self.joysticks[0].init() # init() is deprecated and called automatically
        else:
            print("No joysticks found.")
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
        self.dresseur = None
        self.state = "init"  # init, dresseur_selection, list, detail
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
        self.seen_count = get_seen_pokemon_count(self.conn)
        self.unlocked_regions_count = 0
        for region_name, data in REGIONS.items():
            if data["min_id"] < self.current_max_pokedex_id:
                self.unlocked_regions_count += 1

        # Evolution text scrolling
        self.evolution_text_scroll_x = 0
        self.evolution_text_surface = None
        self.evolution_scroll_timer = 0
        self.evolution_scroll_direction = 1
        self.evolution_scroll_active = False

        self.pressed_buttons = set()
        self.music_volume = 0.2
        
        # Music handling
        self.MUSIC_END_EVENT = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.MUSIC_END_EVENT)
        self.music_state = 'menu'
        self.music_playlists = {
            'menu': list(Path('./audio').glob('menu_*.mp3')),
            'victory': list(Path('./audio').glob('win_*.mp3'))
        }
        random.shuffle(self.music_playlists['menu'])
        random.shuffle(self.music_playlists['victory'])

    def play_next_menu_song(self):
        self.music_state = 'menu'
        if not self.music_playlists['menu']:
            self.music_playlists['menu'] = list(Path('./audio').glob('menu_*.mp3'))
            random.shuffle(self.music_playlists['menu'])
        
        if self.music_playlists['menu']:
            music_path = self.music_playlists['menu'].pop(0)
            pygame.mixer.music.load(str(music_path))
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play()

    def play_victory_song(self):
        self.music_state = 'victory'
        if not self.music_playlists['victory']:
            self.music_playlists['victory'] = list(Path('./audio').glob('win_*.mp3'))
            random.shuffle(self.music_playlists['victory'])
        
        if self.music_playlists['victory']:
            music_path = self.music_playlists['victory'].pop(0)
            pygame.mixer.music.load(str(music_path))
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(0) # Play once

