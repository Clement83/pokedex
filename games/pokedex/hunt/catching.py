import catch_game

class CatchingHandler:
    def __init__(self, screen, font, game_state):
        self.screen = screen
        self.font = font
        self.game_state = game_state

    def run(self, target_pokemon_data, pokemon_sprite, selected_region_name, dresseur_back_sprite, background_image):
        """Runs the catch mini-game."""
        pokedex_id = target_pokemon_data[0]
        pokemon_name_en = target_pokemon_data[2]

        output = catch_game.run(
            self.screen, self.font, pokemon_sprite, self.game_state.pokeball_img_small,
            selected_region_name, dresseur_back_sprite, self.game_state, pokedex_id, pokemon_name_en, background_image
        )

        if not isinstance(output, tuple):
            if output == "quit":
                return "quit", None
            else:
                return "fled", None

        result, dresseur_front_sprite = output
        if result == "caught":
            return "caught", dresseur_front_sprite
        else:
            return "fled", None
