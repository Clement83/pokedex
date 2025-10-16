import pygame
from config import GENERATION_THRESHOLDS
from db import (
    update_pokemon_caught_status,
    get_caught_pokemon_count,
    mew_is_unlocked,
    get_pokemon_list,
    set_user_preference,
    get_pokemon_data
)

class ResultHandler:
    def __init__(self, game_state):
        self.game_state = game_state

    def handle_success(self, target_pokemon_data, is_shiny):
        """Handles the logic for a successful catch."""
        pokedex_id = target_pokemon_data[0]
        update_pokemon_caught_status(self.game_state.conn, pokedex_id, True, is_shiny)

        caught_count = get_caught_pokemon_count(self.game_state.conn)

        last_unlocked_region = None
        previous_max_pokedex_id = self.game_state.current_max_pokedex_id

        for gen, data in sorted(GENERATION_THRESHOLDS.items(), key=lambda item: item[1]['unlock_count']):
            if caught_count >= data['unlock_count'] and previous_max_pokedex_id < data['max_id']:
                self.game_state.current_max_pokedex_id = data['max_id']
                last_unlocked_region = data['unlocked_region']
                break
        
        if last_unlocked_region and last_unlocked_region != "None":
            set_user_preference(self.game_state.conn, 'new_region_unlocked', last_unlocked_region)

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

    def handle_fled(self, target_pokemon_data):
        """Handles the Pokémon fleeing."""
        self.game_state.play_next_menu_song()
        self.game_state.message = f"{target_pokemon_data[1]} s'est enfui !"
        self.game_state.message_timer = pygame.time.get_ticks() + 2000

        self.game_state.state = "list"
        return "quit_hunt"
