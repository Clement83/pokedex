import pygame
from state import GameState
from game_logic import update_sprite, render
import input_handler
from db import add_caught_column, create_user_preferences_table, get_user_preference
from ui import create_list_view_background
import dresseur_selection

def main():
    create_user_preferences_table()
    add_caught_column()
    game_state = GameState()
    game_state.list_view_background = create_list_view_background()

    while game_state.running:
        if game_state.state == "init":
            dresseur = get_user_preference(game_state.conn, "dresseur")
            if dresseur:
                game_state.dresseur = dresseur
                game_state.state = "list"
            else:
                game_state.state = "dresseur_selection"
        
        elif game_state.state == "dresseur_selection":
            result = dresseur_selection.run(game_state.screen, game_state.font, game_state)
            if result == "quit":
                game_state.running = False
            else:
                game_state.state = result

        elif game_state.state in ["list", "detail"]:
            input_handler.handle_input(game_state)
            update_sprite(game_state)
            render(game_state)
        
        elif game_state.state == "quit":
            game_state.running = False

        game_state.clock.tick(60)

    pygame.quit()
    game_state.conn.close()

if __name__ == '__main__':
    main()
