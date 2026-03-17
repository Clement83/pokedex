import pygame
import stabilize_game
from db import get_pokemon_data
from config import STABILIZE_CATCH_RATE_THRESHOLD
from transitions import play_lose_transition

class StabilizingHandler:
    def __init__(self, screen, font, game_state):
        self.screen = screen
        self.font = font
        self.game_state = game_state

    def run(self, target_pokemon_data, pokemon_sprite, background_image, dresseur_front_sprite):
        """Runs the stabilize mini-game."""
        pokedex_id = target_pokemon_data[0]

        pokemon_data = get_pokemon_data(self.game_state.conn, pokedex_id)
        catch_rate = pokemon_data.get('catch_rate', 0) if pokemon_data else 0
        
        run_stabilize = stabilize_game.run_intro_only if catch_rate > STABILIZE_CATCH_RATE_THRESHOLD else stabilize_game.run
        result = run_stabilize(
            self.screen, self.font, self.game_state.pokeball_img_large,
            pokemon_sprite, background_image, dresseur_front_sprite, self.game_state
        )
        
        if result == "caught":
            return "success"
        elif result == "failed":
            play_lose_transition(self.screen, pygame.time.Clock())
            return "fled"
        elif result == "quit":
            return "quit"
        else:
            return "fled"
