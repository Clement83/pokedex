import pygame
import random
from pathlib import Path
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from db import get_pokemon_data
from sprites import load_sprite
from transitions import play_spiral_cubes_transition

class EncounterHandler:
    def __init__(self, screen, game_state):
        self.screen = screen
        self.game_state = game_state

    def run(self, target_pokemon_data, is_shiny, selected_region_name):
        """Prepares for the encounter, loads assets, and runs the transition."""
        # 1. Load all assets for combat
        pokedex_id = target_pokemon_data[0]
        full_pokemon_data = get_pokemon_data(self.game_state.conn, pokedex_id)
        pokemon_types = [t['name'] for t in full_pokemon_data.get('types', []) if 'name' in t] or ["Normal"]

        sprite_path_key = 4 if is_shiny else 3
        sprite_filename = Path(target_pokemon_data[sprite_path_key]).name
        sprite_path = self.game_state.BASE_DIR / "app/data/sprites" / sprite_filename
        original_sprite = load_sprite(sprite_path)

        if not original_sprite:
            self.game_state.message = f"Sprite for {target_pokemon_data[1]} not found!"
            self.game_state.message_timer = pygame.time.get_ticks() + 2000
            return None

        pokemon_sprite = pygame.transform.scale(original_sprite, (128, 128))
        dresseur_path = self.game_state.BASE_DIR / f"app/data/assets/dresseurs/{self.game_state.dresseur}/dos.png"
        dresseur_back_sprite = load_sprite(dresseur_path)

        stadium_path = self.game_state.BASE_DIR / "app/data/assets" / selected_region_name.lower() / "stadium"
        background_image_path = random.choice(list(stadium_path.glob('*.png'))) if stadium_path.is_dir() and any(stadium_path.glob('*.png')) else None
        if background_image_path:
            background_image = pygame.image.load(background_image_path).convert()
        else:
            fallback_path = self.game_state.BASE_DIR / "app/data/assets/out.png"
            background_image = pygame.image.load(fallback_path).convert()
        background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

        # 2. Pre-render the initial combat scene
        combat_scene_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        combat_scene_surface.blit(background_image, (0, 0))
        if dresseur_back_sprite:
            combat_scene_surface.blit(dresseur_back_sprite, (10, SCREEN_HEIGHT - dresseur_back_sprite.get_height() - 10))
        if pokemon_sprite:
            # Position the pokemon more centrally and higher up
            p_rect = pokemon_sprite.get_rect(center=(SCREEN_WIDTH * 0.75, SCREEN_HEIGHT * 0.35))
            combat_scene_surface.blit(pokemon_sprite, p_rect)

        # 3. Run the transition
        play_spiral_cubes_transition(self.screen, pygame.time.Clock(), combat_scene_surface)

        return {
            "pokemon_sprite": pokemon_sprite,
            "dresseur_back_sprite": dresseur_back_sprite,
            "background_image": background_image,
            "full_pokemon_data": full_pokemon_data,
            "pokemon_types": pokemon_types,
        }
