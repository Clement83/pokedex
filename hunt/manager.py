import pygame
import random
from pathlib import Path
from config import SHINY_RATE, REGIONS, REGION_MUSIC
from db import get_caught_pokemon_count
from .region_selection import RegionSelectionHandler
from .encounter import EncounterHandler
from .combat import CombatHandler
from .catching import CatchingHandler
from .stabilizing import StabilizingHandler
from .result import ResultHandler

class HuntManager:
    def __init__(self, screen, font, game_state):
        self.screen = screen
        self.font = font
        self.game_state = game_state
        
        self.target_pokemon_data = None
        self.is_shiny = False
        self.selected_region_name = None
        
        # Handlers
        self.region_selection_handler = RegionSelectionHandler(screen, font, game_state)
        self.encounter_handler = EncounterHandler(screen, game_state)
        self.combat_handler = CombatHandler(screen, font, game_state)
        self.catching_handler = CatchingHandler(screen, font, game_state)
        self.stabilizing_handler = StabilizingHandler(screen, font, game_state)
        self.result_handler = ResultHandler(game_state)

        # State for assets loaded during the hunt
        self.hunt_assets = {}

        # Load attack sprites
        self.game_state.attack_sprites = {}
        attack_sprites_path = self.game_state.BASE_DIR / "app/data/assets/attacks"
        if attack_sprites_path.is_dir():
            for sprite_file in attack_sprites_path.glob("*.png"):
                try:
                    self.game_state.attack_sprites[sprite_file.name] = pygame.image.load(sprite_file).convert_alpha()
                except pygame.error as e:
                    print(f"Warning: Could not load attack sprite {sprite_file.name}: {e}")

        caught_count = get_caught_pokemon_count(self.game_state.conn)
        if caught_count == 0:
            self.state = "ENCOUNTER"
            self.selected_region_name = "Kanto"
            starters = [p for p in self.game_state.pokemon_list if p[0] in [1, 4, 7]]
            if starters:
                self.target_pokemon_data = random.choice(starters)
            else:
                self.state = "REGION_SELECTION"
                return
            self.is_shiny = False
            if self.selected_region_name in REGION_MUSIC and REGION_MUSIC[self.selected_region_name]:
                music_file = random.choice(REGION_MUSIC[self.selected_region_name])
                music_path = self.game_state.BASE_DIR / "pokemon_audio" / music_file
                if music_path.exists():
                    pygame.mixer.music.load(str(music_path))
                    pygame.mixer.music.set_volume(self.game_state.music_volume)
                    pygame.mixer.music.play(-1)
        else:
            self.state = "REGION_SELECTION"

    def run(self):
        running = True
        while running:
            if self.state == "REGION_SELECTION":
                next_state, result = self.region_selection_handler.run()
                if next_state == "encounter":
                    self.selected_region_name = result
                    region_data = REGIONS[self.selected_region_name]
                    available_pokemon = [p for p in self.game_state.pokemon_list if region_data["min_id"] <= p[0] < region_data["max_id"]]
                    if available_pokemon:
                        self.target_pokemon_data = random.choice(available_pokemon)
                        self.is_shiny = random.random() < SHINY_RATE
                        self.state = "ENCOUNTER"
                        if self.selected_region_name in REGION_MUSIC and REGION_MUSIC[self.selected_region_name]:
                            music_file = random.choice(REGION_MUSIC[self.selected_region_name])
                            music_path = self.game_state.BASE_DIR / "pokemon_audio" / music_file
                            if music_path.exists():
                                pygame.mixer.music.load(str(music_path))
                                pygame.mixer.music.set_volume(self.game_state.music_volume)
                                pygame.mixer.music.play(-1)
                    else:
                        self.game_state.message = f"No pokemon in {self.selected_region_name}!"
                        self.game_state.message_timer = pygame.time.get_ticks() + 2000
                        self.state = "REGION_SELECTION" # Stay on region selection
                elif next_state in ["quit", "main_menu"]:
                    return next_state

            elif self.state == "ENCOUNTER":
                assets = self.encounter_handler.run(self.target_pokemon_data, self.is_shiny, self.selected_region_name)
                if assets:
                    self.hunt_assets = assets
                    self.state = "COMBAT"
                else:
                    self.state = "REGION_SELECTION"

            elif self.state == "COMBAT":
                combat_assets = {
                    "pokemon_sprite": self.hunt_assets["pokemon_sprite"],
                    "dresseur_back_sprite": self.hunt_assets["dresseur_back_sprite"],
                    "background_image": self.hunt_assets["background_image"],
                    "pokemon_types": self.hunt_assets["pokemon_types"],
                    "full_pokemon_data": self.hunt_assets["full_pokemon_data"],
                }
                result = self.combat_handler.run(**combat_assets)
                if result == "win":
                    self.state = "CATCHING"
                elif result == "lose":
                    self.state = "FLED"
                else: # quit
                    self.state = "QUIT"

            elif self.state == "CATCHING":
                result, dresseur_front_sprite = self.catching_handler.run(
                    self.target_pokemon_data, self.hunt_assets["pokemon_sprite"], self.selected_region_name,
                    self.hunt_assets["dresseur_back_sprite"], self.hunt_assets["background_image"]
                )
                if result == "caught":
                    self.hunt_assets["dresseur_front_sprite"] = dresseur_front_sprite
                    self.state = "STABILIZING"
                elif result == "fled":
                    self.state = "FLED"
                else: # quit
                    self.state = "QUIT"

            elif self.state == "STABILIZING":
                result = self.stabilizing_handler.run(
                    self.target_pokemon_data, self.hunt_assets["pokemon_sprite"],
                    self.hunt_assets["background_image"], self.hunt_assets["dresseur_front_sprite"]
                )
                if result == "success":
                    self.state = "SUCCESS"
                elif result == "fled":
                    self.state = "FLED"
                else: # quit
                    self.state = "QUIT"

            elif self.state == "SUCCESS":
                return self.result_handler.handle_success(self.target_pokemon_data, self.is_shiny)

            elif self.state == "FLED":
                self.result_handler.handle_fled(self.target_pokemon_data)
                self.state = "QUIT_HUNT"

            elif self.state == "QUIT_HUNT":
                return "main_menu"
                
            elif self.state == "QUIT":
                return "quit"
                
            else:
                print(f"Unknown hunt state: {self.state}")
                running = False
        return "main_menu"

def run(screen, font, game_state):
    """Entry point for the hunt feature."""
    manager = HuntManager(screen, font, game_state)
    return manager.run()