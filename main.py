import pygame
from state import GameState
from game_logic import update_sprite, render
import input_handler
from db import add_caught_column
from ui import create_list_view_background

def main():
    add_caught_column()
    game_state = GameState()
    game_state.list_view_background = create_list_view_background()

    while game_state.running:
        input_handler.handle_input(game_state)
        update_sprite(game_state)
        render(game_state)
        game_state.clock.tick(60)

    pygame.quit()
    game_state.conn.close()

if __name__ == '__main__':
    main()