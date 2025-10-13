import pygame
import random
from pathlib import Path
from config import SCREEN_WIDTH, SCREEN_HEIGHT, SHINY_RATE, GENERATION_THRESHOLDS, REGIONS, STABILIZE_CATCH_RATE_THRESHOLD, KEY_MAPPINGS
from db import get_pokemon_data, update_pokemon_caught_status, get_caught_pokemon_count, mew_is_unlocked, get_pokemon_list, get_user_preference, set_user_preference
import controls
import catch_game
import stabilize_game
import combat_dodge_game
from sprites import load_sprite

# Grid configuration for regions
GRID_COLS = 3
IMAGE_SIZE = 90 # Size for region images (increased)
GRID_START_Y = 5 # Starting Y position for the grid (moved up further)
GRID_PADDING = 10 # Padding between images (reduced)

class HuntManager:
    def __init__(self, screen, font, game_state):
        self.screen = screen
        self.font = font
        self.game_state = game_state
        self.state = "REGION_SELECTION"
        self.target_pokemon_data = None
        self.is_shiny = False
        self.selected_region_name = None
        self.pokemon_sprite = None
        self.dresseur_back_sprite = None
        self.catch_game_output = None
        self.background_image = None
        self.pokemon_types = None

    def run(self):
        """Main loop for the hunt state machine."""
        running = True
        while running:
            if self.state == "REGION_SELECTION":
                result = self._handle_region_selection()
                if result in ["quit", "main_menu"]:
                    return result
            elif self.state == "ENCOUNTER":
                self._handle_encounter()
            elif self.state == "COMBAT":
                self._handle_combat()
            elif self.state == "CATCHING":
                self._handle_catching()
            elif self.state == "STABILIZING":
                self._handle_stabilizing()
            elif self.state == "SUCCESS":
                return self._handle_success()
            elif self.state == "FLED":
                self._handle_fled()
            elif self.state == "QUIT":
                return "quit"
            else:
                print(f"Unknown hunt state: {self.state}")
                running = False
        return "main_menu"

    def _handle_region_selection(self):
        """Handles the region selection screen."""
        region_names = list(REGIONS.keys())
        num_regions = len(region_names)
        GRID_ROWS = (num_regions + GRID_COLS - 1) // GRID_COLS

        region_images_loaded = {
            name: pygame.transform.scale(load_sprite(self.game_state.BASE_DIR / f"app/data/assets/{name.lower()}/icon.png"), (IMAGE_SIZE, IMAGE_SIZE))
            for name in region_names
        }

        selected_row, selected_col = 0, 0
        last_region = get_user_preference(self.game_state.conn, "last_selected_region")
        if last_region and last_region in region_names:
            idx = region_names.index(last_region)
            selected_row, selected_col = idx // GRID_COLS, idx % GRID_COLS

        while True:
            for event in pygame.event.get():
                controls.process_joystick_input(self.game_state, event)
                if event.type == pygame.QUIT: return "quit"
                if event.type == pygame.KEYDOWN:
                    key_actions = {
                        "UP": lambda: (selected_row - 1) % GRID_ROWS,
                        "DOWN": lambda: (selected_row + 1) % GRID_ROWS,
                        "LEFT": lambda: (selected_col - 1) % GRID_COLS,
                        "RIGHT": lambda: (selected_col + 1) % GRID_COLS,
                    }
                    if event.key in KEY_MAPPINGS["UP"]: selected_row = key_actions["UP"]()
                    elif event.key in KEY_MAPPINGS["DOWN"]: selected_row = key_actions["DOWN"]()
                    elif event.key in KEY_MAPPINGS["LEFT"]: selected_col = key_actions["LEFT"]()
                    elif event.key in KEY_MAPPINGS["RIGHT"]: selected_col = key_actions["RIGHT"]()
                    elif event.key in KEY_MAPPINGS["QUIT"]: return "quit"
                    elif event.key in KEY_MAPPINGS["CANCEL"]: return "main_menu"
                    elif event.key in KEY_MAPPINGS["CONFIRM"]:
                        idx = selected_row * GRID_COLS + selected_col
                        if idx < num_regions:
                            self.selected_region_name = region_names[idx]
                            region_data = REGIONS[self.selected_region_name]
                            if region_data["min_id"] >= self.game_state.current_max_pokedex_id:
                                continue
                            
                            set_user_preference(self.game_state.conn, "last_selected_region", self.selected_region_name)
                            available_pokemon = [p for p in self.game_state.pokemon_list if region_data["min_id"] <= p[0] < region_data["max_id"]]
                            
                            if available_pokemon:
                                self.target_pokemon_data = random.choice(available_pokemon)
                                self.is_shiny = random.random() < SHINY_RATE
                                self.state = "ENCOUNTER"
                                return
                            else:
                                self.game_state.message = f"No pokemon in {self.selected_region_name}!"
                                self.game_state.message_timer = pygame.time.get_ticks() + 2000

            self.screen.fill((0, 0, 0))
            self._draw_region_grid(region_names, region_images_loaded, selected_row, selected_col, GRID_ROWS)
            self._draw_region_info(region_names, selected_row, selected_col)
            self._display_messages()
            pygame.display.flip()
            pygame.time.Clock().tick(60)

    def _draw_region_grid(self, region_names, images, sel_row, sel_col, grid_rows):
        start_x = (SCREEN_WIDTH - (GRID_COLS * IMAGE_SIZE + (GRID_COLS - 1) * GRID_PADDING)) // 2
        for i, name in enumerate(region_names):
            row, col = i // GRID_COLS, i % GRID_COLS
            if row >= grid_rows: continue
            
            x = start_x + col * (IMAGE_SIZE + GRID_PADDING)
            y = GRID_START_Y + row * (IMAGE_SIZE + GRID_PADDING)
            
            self.screen.blit(images[name], (x, y))
            
            if REGIONS[name]["min_id"] >= self.game_state.current_max_pokedex_id:
                overlay = pygame.Surface((IMAGE_SIZE, IMAGE_SIZE), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 150))
                self.screen.blit(overlay, (x, y))
            
            if row == sel_row and col == sel_col:
                pygame.draw.rect(self.screen, (255, 255, 0), (x, y, IMAGE_SIZE, IMAGE_SIZE), 3)

    def _draw_region_info(self, region_names, sel_row, sel_col):
        idx = sel_row * GRID_COLS + sel_col
        if idx < len(region_names):
            name = region_names[idx]
            is_locked = REGIONS[name]["min_id"] >= self.game_state.current_max_pokedex_id
            text = f"{name} - LOCKED" if is_locked else name
            color = (255, 100, 100) if is_locked else (255, 255, 255)
            
            rendered_text = self.font.render(text, True, color)
            rect = rendered_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 10))
            self.screen.blit(rendered_text, rect)

    def _display_messages(self):
        if self.game_state.message and pygame.time.get_ticks() < self.game_state.message_timer:
            text = self.font.render(self.game_state.message, True, (255, 0, 0))
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(text, rect)

    def _handle_encounter(self):
        """Prepares for the encounter by loading assets."""
        # Get Pokemon types for styling
        pokedex_id = self.target_pokemon_data[0]
        full_pokemon_data = get_pokemon_data(self.game_state.conn, pokedex_id)
        if full_pokemon_data and 'types' in full_pokemon_data:
            self.pokemon_types = [t['name'] for t in full_pokemon_data['types'] if 'name' in t]
        else:
            self.pokemon_types = ["Normal"] # Fallback type

        sprite_path_key = 4 if self.is_shiny else 3
        sprite_filename = Path(self.target_pokemon_data[sprite_path_key]).name
        sprite_path = self.game_state.BASE_DIR / "app/data/sprites" / sprite_filename
        
        original_sprite = load_sprite(sprite_path)
        if not original_sprite:
            self.game_state.message = f"Sprite for {self.target_pokemon_data[1]} not found!"
            self.game_state.message_timer = pygame.time.get_ticks() + 2000
            self.state = "REGION_SELECTION"
            return

        self.pokemon_sprite = pygame.transform.scale(original_sprite, (64, 64))
        dresseur_path = self.game_state.BASE_DIR / f"app/data/assets/dresseurs/{self.game_state.dresseur}/dos.png"
        self.dresseur_back_sprite = load_sprite(dresseur_path)

        # Load background image once for the entire hunt
        stadium_path = self.game_state.BASE_DIR / "app" / "data" / "assets" / self.selected_region_name.lower() / "stadium"
        background_image = None
        if stadium_path.is_dir():
            stadium_images = list(stadium_path.glob('*.png'))
            if stadium_images:
                random_bg_path = random.choice(stadium_images)
                try:
                    background_image = pygame.image.load(random_bg_path).convert()
                except pygame.error:
                    print(f"Error loading stadium background: {random_bg_path}")
        
        if background_image is None:
            fallback_path = self.game_state.BASE_DIR / "app" / "data" / "assets" / "out.png"
            try:
                background_image = pygame.image.load(fallback_path).convert()
            except pygame.error:
                print(f"Error loading fallback background: {fallback_path}")

        if background_image:
            self.background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        else:
            # If all loading fails, create a placeholder surface
            self.background_image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.background_image.fill((20, 20, 30)) # Fallback color

        # This is where you can add logic to decide between combat and catching
        self.state = "COMBAT"

    def _handle_combat(self):
        """Runs the combat mini-game."""
        # Here you can add logic to select from multiple combat games
        # For now, we only have one.
        combat_minigames = [combat_dodge_game.run]
        selected_game = random.choice(combat_minigames)

        # The dresseur_back_sprite is used as the player sprite in the dodge game
        result = selected_game(self.screen, self.font, self.game_state, self.pokemon_sprite, self.dresseur_back_sprite, self.background_image, self.pokemon_types)

        if result == "win":
            self.state = "CATCHING"
        elif result == "lose":
            self.state = "FLED"
        else: # quit
            self.state = "QUIT"

    def _handle_catching(self):
        """Runs the catch mini-game."""
        pokedex_id = self.target_pokemon_data[0]
        pokemon_name_en = self.target_pokemon_data[2]

        output = catch_game.run(
            self.screen, self.font, self.pokemon_sprite, self.game_state.pokeball_img_small,
            self.selected_region_name, self.dresseur_back_sprite, self.game_state, pokedex_id, pokemon_name_en, self.background_image
        )

        if not isinstance(output, tuple):
            self.state = "QUIT" if output == "quit" else "REGION_SELECTION"
            return

        result, dresseur_front_sprite = output
        self.catch_game_output = dresseur_front_sprite # Store only the front sprite now
        self.state = "STABILIZING" if result == "caught" else "FLED"

    def _handle_stabilizing(self):
        """Runs the stabilize mini-game."""
        pokedex_id = self.target_pokemon_data[0]
        dresseur_front_sprite = self.catch_game_output

        pokemon_data = get_pokemon_data(self.game_state.conn, pokedex_id)
        catch_rate = pokemon_data.get('catch_rate', 0) if pokemon_data else 0
        
        run_stabilize = stabilize_game.run_intro_only if catch_rate > STABILIZE_CATCH_RATE_THRESHOLD else stabilize_game.run
        result = run_stabilize(
            self.screen, self.font, self.game_state.pokeball_img_large,
            self.pokemon_sprite, self.background_image, dresseur_front_sprite, self.game_state
        )
        
        if result == "caught": self.state = "SUCCESS"
        elif result == "failed": self.state = "FLED"
        else: self.state = "REGION_SELECTION"
    def _handle_success(self):
        """Handles the logic for a successful catch."""
        pokedex_id = self.target_pokemon_data[0]
        update_pokemon_caught_status(self.game_state.conn, pokedex_id, True, self.is_shiny)
        
        caught_count = get_caught_pokemon_count(self.game_state.conn)
        for gen, data in GENERATION_THRESHOLDS.items():
            if caught_count >= data['unlock_count'] and self.game_state.current_max_pokedex_id < data['max_id']:
                self.game_state.current_max_pokedex_id = data['max_id']
                break
        
        mew_unlocked = mew_is_unlocked(self.game_state.conn)
        self.game_state.pokemon_list = get_pokemon_list(self.game_state.conn, self.game_state.current_max_pokedex_id, include_mew=mew_unlocked)
        self.game_state.current_pokemon_data = get_pokemon_data(self.game_state.conn, pokedex_id)
        
        if self.game_state.current_pokemon_data:
            for i, p in enumerate(self.game_state.pokemon_list):
                if p[0] == pokedex_id:
                    self.game_state.selected_index = i
                    self.game_state.scroll_offset = max(0, i - self.game_state.max_visible_items // 2)
                    break
            self.game_state.state = "detail"
        
        return "detail"

    def _handle_fled(self):
        """Handles the Pokémon fleeing."""
        self.game_state.message = f"{self.target_pokemon_data[1]} fled!"
        self.game_state.message_timer = pygame.time.get_ticks() + 2000
        self.state = "REGION_SELECTION"

def run(screen, font, game_state):
    """Entry point for the hunt feature."""
    manager = HuntManager(screen, font, game_state)
    return manager.run()
