import pygame
import random
from pathlib import Path
from db import get_pokemon_data, update_pokemon_caught_status, get_caught_pokemon_count, mew_is_unlocked, get_pokemon_list
from config import SHINY_RATE, GENERATION_THRESHOLDS
import catch_game
import stabilize_game
from sprites import load_sprite
import hunt # Import the new hunt module

def handle_input(game_state):
    now = pygame.time.get_ticks()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_state.running = False
        elif event.type == pygame.KEYDOWN:
            if game_state.state == "list":
                if event.key == pygame.K_DOWN:
                    game_state.key_down_pressed = True
                    game_state.down_press_time = now
                    game_state.last_scroll_time = now
                    if game_state.selected_index < len(game_state.pokemon_list) - 1:
                        game_state.selected_index += 1
                        if game_state.selected_index - game_state.scroll_offset >= game_state.max_visible_items:
                            game_state.scroll_offset += 1
                elif event.key == pygame.K_UP:
                    game_state.key_up_pressed = True
                    game_state.up_press_time = now
                    game_state.last_scroll_time = now
                    if game_state.selected_index > 0:
                        game_state.selected_index -= 1
                        if game_state.selected_index < game_state.scroll_offset:
                            game_state.scroll_offset -= 1
                elif event.key == pygame.K_LEFT:
                    game_state.selected_index = max(0, game_state.selected_index - 50)
                    if game_state.selected_index < game_state.scroll_offset:
                        game_state.scroll_offset = game_state.selected_index
                elif event.key == pygame.K_RIGHT:
                    game_state.selected_index = min(len(game_state.pokemon_list) - 1, game_state.selected_index + 50)
                    if game_state.selected_index - game_state.scroll_offset >= game_state.max_visible_items:
                        game_state.scroll_offset = game_state.selected_index - game_state.max_visible_items + 1
                elif event.key == pygame.K_n:
                    pid = game_state.pokemon_list[game_state.selected_index][0]
                    game_state.current_pokemon_data = get_pokemon_data(game_state.conn, pid)
                    if game_state.current_pokemon_data:
                        game_state.state = "detail"
                elif event.key == pygame.K_SPACE:
                    hunt_result = hunt.run(game_state.screen, game_state.font, game_state)
                    if hunt_result == "quit":
                        game_state.running = False
                    elif hunt_result == "main_menu": # Assuming "main_menu" means return to list view
                        game_state.state = "list"
                    elif hunt_result == "detail":
                        game_state.state = "detail"
                elif event.key == pygame.K_ESCAPE:
                    game_state.running = False
            elif game_state.state == "detail":
                if event.key == pygame.K_m:
                    game_state.state = "list"
                    game_state.current_sprite = None
                elif event.key == pygame.K_RIGHT:
                    if game_state.selected_index < len(game_state.pokemon_list) - 1:
                        game_state.selected_index += 1
                        pid = game_state.pokemon_list[game_state.selected_index][0]
                        game_state.current_pokemon_data = get_pokemon_data(game_state.conn, pid)
                elif event.key == pygame.K_LEFT:
                    if game_state.selected_index > 0:
                        game_state.selected_index -= 1
                        pid = game_state.pokemon_list[game_state.selected_index][0]
                        game_state.current_pokemon_data = get_pokemon_data(game_state.conn, pid)

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_DOWN:
                game_state.key_down_pressed = False
            elif event.key == pygame.K_UP:
                game_state.key_up_pressed = False

    if game_state.state == "list":
        if game_state.key_down_pressed:
            elapsed = now - game_state.down_press_time
            if elapsed > game_state.scroll_delay:
                delay = game_state.scroll_delay if elapsed < game_state.scroll_accel_time else game_state.scroll_fast_delay
                time_since_last_scroll = now - game_state.last_scroll_time
                if time_since_last_scroll > delay:
                    scroll_steps = time_since_last_scroll // delay
                    if scroll_steps > 0:
                        game_state.selected_index = min(len(game_state.pokemon_list) - 1, game_state.selected_index + scroll_steps)
                        if game_state.selected_index - game_state.scroll_offset >= game_state.max_visible_items:
                            game_state.scroll_offset = game_state.selected_index - game_state.max_visible_items + 1
                        game_state.last_scroll_time = now
        elif game_state.key_up_pressed:
            elapsed = now - game_state.up_press_time
            if elapsed > game_state.scroll_delay:
                delay = game_state.scroll_delay if elapsed < game_state.scroll_accel_time else game_state.scroll_fast_delay
                time_since_last_scroll = now - game_state.last_scroll_time
                if time_since_last_scroll > delay:
                    scroll_steps = time_since_last_scroll // delay
                    if scroll_steps > 0:
                        game_state.selected_index = max(0, game_state.selected_index - scroll_steps)
                        if game_state.selected_index < game_state.scroll_offset:
                            game_state.scroll_offset = game_state.selected_index
                        game_state.last_scroll_time = now
