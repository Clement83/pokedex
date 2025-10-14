import pygame
import random
from pathlib import Path
from config import SCREEN_WIDTH, SCREEN_HEIGHT, SHINY_RATE, GENERATION_THRESHOLDS, REGIONS, STABILIZE_CATCH_RATE_THRESHOLD, KEY_MAPPINGS, REGION_MUSIC
from db import get_pokemon_data, update_pokemon_caught_status, get_caught_pokemon_count, mew_is_unlocked, get_pokemon_list, get_user_preference, set_user_preference
import controls
import catch_game
import stabilize_game
import combat_dodge_game
import combat_qte_game
import combat_memory_game
from ui import draw_hp_bar
from sprites import load_sprite
from transitions import play_spiral_cubes_transition, play_lose_transition

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
        self.full_pokemon_data = None

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

                                # Start battle music
                                if self.selected_region_name in REGION_MUSIC and REGION_MUSIC[self.selected_region_name]:
                                    music_file = random.choice(REGION_MUSIC[self.selected_region_name])
                                    music_path = self.game_state.BASE_DIR / "pokemon_audio" / music_file
                                    if music_path.exists():
                                        pygame.mixer.music.load(str(music_path))
                                        pygame.mixer.music.set_volume(self.game_state.music_volume)
                                        pygame.mixer.music.play(-1)  # -1 for looping

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
        """Prepares for the encounter, loads assets, and runs the transition."""
        # 1. Load all assets for combat
        pokedex_id = self.target_pokemon_data[0]
        self.full_pokemon_data = get_pokemon_data(self.game_state.conn, pokedex_id)
        self.pokemon_types = [t['name'] for t in self.full_pokemon_data.get('types', []) if 'name' in t] or ["Normal"]

        sprite_path_key = 4 if self.is_shiny else 3
        sprite_filename = Path(self.target_pokemon_data[sprite_path_key]).name
        sprite_path = self.game_state.BASE_DIR / "app/data/sprites" / sprite_filename
        original_sprite = load_sprite(sprite_path)

        if not original_sprite:
            self.game_state.message = f"Sprite for {self.target_pokemon_data[1]} not found!"
            self.game_state.message_timer = pygame.time.get_ticks() + 2000
            self.state = "REGION_SELECTION"
            return

        self.pokemon_sprite = pygame.transform.scale(original_sprite, (128, 128))
        dresseur_path = self.game_state.BASE_DIR / f"app/data/assets/dresseurs/{self.game_state.dresseur}/dos.png"
        self.dresseur_back_sprite = load_sprite(dresseur_path)

        stadium_path = self.game_state.BASE_DIR / "app/data/assets" / self.selected_region_name.lower() / "stadium"
        background_image_path = random.choice(list(stadium_path.glob('*.png'))) if stadium_path.is_dir() else None
        if background_image_path:
            self.background_image = pygame.image.load(background_image_path).convert()
        else:
            fallback_path = self.game_state.BASE_DIR / "app/data/assets/out.png"
            self.background_image = pygame.image.load(fallback_path).convert()
        self.background_image = pygame.transform.scale(self.background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

        # 2. Pre-render the initial combat scene
        combat_scene_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        combat_scene_surface.blit(self.background_image, (0, 0))
        if self.dresseur_back_sprite:
            combat_scene_surface.blit(self.dresseur_back_sprite, (10, SCREEN_HEIGHT - self.dresseur_back_sprite.get_height() - 10))
        if self.pokemon_sprite:
            # Position the pokemon more centrally and higher up
            p_rect = self.pokemon_sprite.get_rect(center=(SCREEN_WIDTH * 0.75, SCREEN_HEIGHT * 0.35))
            combat_scene_surface.blit(self.pokemon_sprite, p_rect)

        # 3. Run the transition
        play_spiral_cubes_transition(self.screen, pygame.time.Clock(), combat_scene_surface)

        # 4. Proceed to combat
        self.state = "COMBAT"

    def _handle_combat(self):
        """Runs the combat mini-game."""
        combat_minigames = [combat_dodge_game.run, combat_qte_game.run, combat_memory_game.run]
        selected_game = random.choice(combat_minigames)

        result = selected_game(
            self.screen, self.font, self.game_state, 
            self.pokemon_sprite, self.dresseur_back_sprite, 
            self.background_image, self.pokemon_types, self.full_pokemon_data
        )

        if result == "win":
            # --- HP Bar Depletion Animation ---
            start_time = pygame.time.get_ticks()
            duration = 1500 # 1.5 seconds
            clock = pygame.time.Clock()
            
            while True:
                elapsed = pygame.time.get_ticks() - start_time
                if elapsed > duration:
                    break

                # Draw the static background scene
                self.screen.blit(self.background_image, (0, 0))
                if self.dresseur_back_sprite:
                    self.screen.blit(self.dresseur_back_sprite, (10, SCREEN_HEIGHT - self.dresseur_back_sprite.get_height() - 10))
                if self.pokemon_sprite:
                    p_rect = self.pokemon_sprite.get_rect(center=(SCREEN_WIDTH * 0.75, SCREEN_HEIGHT * 0.35))
                    self.screen.blit(self.pokemon_sprite, p_rect)

                # Calculate HP percentage
                progress = elapsed / duration
                hp_percent = 100 * (1 - progress)
                hp_percent = max(10, hp_percent) # Ensure it stops at a small amount

                # Draw the HP bar
                draw_hp_bar(self.screen, hp_percent, pos=(SCREEN_WIDTH - 160, 20), size=(150, 20), font=self.font)

                pygame.display.flip()
                clock.tick(60)

            self.state = "CATCHING"
        elif result == "lose":
            play_lose_transition(self.screen, pygame.time.Clock())
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
        self.catch_game_output = dresseur_front_sprite
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
        elif result == "failed":
            play_lose_transition(self.screen, pygame.time.Clock())
            self.state = "FLED"
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
        self.game_state.play_next_menu_song()
        self.game_state.message = f"{self.target_pokemon_data[1]} fled!"
        self.game_state.message_timer = pygame.time.get_ticks() + 2000
        self.state = "REGION_SELECTION"

def run(screen, font, game_state):
    """Entry point for the hunt feature."""
    manager = HuntManager(screen, font, game_state)
    return manager.run()
