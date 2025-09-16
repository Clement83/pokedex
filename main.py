import pygame
from state import GameState
from game_logic import game_loop, update_sprite, render
import input_handler
from db import add_caught_column

def main():
    add_caught_column()
    game_state = GameState()

    while game_state.running:
        input_handler.handle_input(game_state)
        update_sprite(game_state)
        render(game_state)
        game_state.clock.tick(60)

    pygame.quit()
    game_state.conn.close()

if __name__ == '__main__':
    main()