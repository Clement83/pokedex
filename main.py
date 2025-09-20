import pygame
from state import GameState
from game_logic import update_sprite, render, update_animations
import input_handler
import controls # Import the controls module
from db import add_caught_column, create_user_preferences_table, get_user_preference
from ui import create_list_view_background
import dresseur_selection

def main():
    create_user_preferences_table()
    add_caught_column()
    game_state = GameState()
    game_state.list_view_background = create_list_view_background()
    game_state.play_next_menu_song()  # Start music

    while game_state.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_state.running = False
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
            if result == "quit":
                game_state.running = False
            else:
                game_state.state = result

        elif game_state.state in ["list", "detail"]:
            # input_handler.handle_input(game_state) # This is now handled in the event loop
            update_sprite(game_state)
            update_animations(game_state)
            render(game_state)
        
        elif game_state.state == "quit":
            game_state.running = False

        game_state.clock.tick(60)

    pygame.quit()
    game_state.conn.close()

if __name__ == '__main__':
    main()
