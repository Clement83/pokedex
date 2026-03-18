import pygame
from state import GameState
from game_logic import update_sprite, render, update_animations
import input_handler
from input_handler import handle_continuous_input # Import the new function
import controls # Import the controls module
from db import add_caught_column, create_user_preferences_table, get_user_preference
from ui import create_list_view_background
import dresseur_selection

def main():
    create_user_preferences_table()
    add_caught_column()
    print("[Pokemon] GameState init...")
    game_state = GameState()
    print(f"[Pokemon] Demarrage, state={game_state.state!r}")
    game_state.list_view_background = create_list_view_background()
    game_state.play_next_menu_song()  # Start music

    while game_state.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pass  # On ne quitte pas
            if event.type == game_state.MUSIC_END_EVENT:
                if game_state.music_state == 'victory':
                    game_state.play_next_menu_song()
                else:
                    game_state.play_next_menu_song()

            controls.process_joystick_input(game_state, event)
            input_handler.handle_input(game_state, event) # Pass event to input handler

        if game_state.state == "init":
            dresseur = get_user_preference(game_state.conn, "dresseur")
            if dresseur:
                game_state.dresseur = dresseur
                game_state.state = "list"
            else:
                game_state.state = "dresseur_selection"

        elif game_state.state == "dresseur_selection":
            result = dresseur_selection.run(game_state.screen, game_state.font, game_state)
            print(f"[Pokemon] dresseur_selection retourne : {result!r}")
            if result in ("quit", None):
                game_state.state = "dresseur_selection"  # rester sur la sélection
            else:
                game_state.state = result

        elif game_state.state in ["list", "detail"]:
            handle_continuous_input(game_state) # Handle continuous input for scrolling
            controls.check_debug_combos(game_state) # Check if debug combos are held
            input_handler.check_keyboard_debug_combos(game_state) # Check keyboard debug combos
            update_sprite(game_state)
            update_animations(game_state)
            render(game_state)

        elif game_state.state == "quit":
            pass  # On ne quitte pas

        game_state.clock.tick(60)

    pygame.quit()
    game_state.conn.close()

if __name__ == '__main__':
    main()
