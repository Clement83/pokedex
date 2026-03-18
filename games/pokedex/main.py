import pygame
from state import GameState
from game_logic import update_sprite, render, update_animations
import input_handler
from input_handler import handle_continuous_input # Import the new function
import controls # Import the controls module
from db import add_caught_column, create_user_preferences_table, get_user_preference
from ui import create_list_view_background
import dresseur_selection
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from logger import log
from quit_combo import QuitCombo
import music_player

def main():
    create_user_preferences_table()
    add_caught_column()
    log("[Pokemon] GameState init...")
    game_state = GameState()
    log(f"[Pokemon] Demarrage, state={game_state.state!r}, joysticks={len(game_state.joysticks)}")
    game_state.list_view_background = create_list_view_background()
    game_state.play_next_menu_song()  # Start music
    game_state.quit_combo    = QuitCombo()
    game_state.quit_requested = False

    while game_state.running:
        events = pygame.event.get()
        music_player.tick(events)
        game_state.music_volume = music_player.get_volume()

        for event in events:
            if event.type == pygame.QUIT:
                pass  # On ne quitte pas
            if event.type == game_state.MUSIC_END_EVENT:
                if game_state.music_state == 'victory':
                    game_state.play_next_menu_song()
                else:
                    game_state.play_next_menu_song()

            controls.process_joystick_input(game_state, event)
            game_state.quit_combo.handle_event(event)
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
            log(f"[Pokemon] dresseur_selection retourne : {result!r}")
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

        if game_state.quit_requested:
            game_state.running = False

        game_state.clock.tick(60)

    log("[Pokemon] Boucle principale terminée (game_state.running=False)")
    pygame.quit()
    game_state.conn.close()

if __name__ == '__main__':
    main()
