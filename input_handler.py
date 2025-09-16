import pygame
import random
from pathlib import Path
from db import get_pokemon_data, update_pokemon_caught_status, get_caught_pokemon_count, mew_is_unlocked, get_pokemon_list
from config import SHINY_RATE, GENERATION_THRESHOLDS
import catch_game
import stabilize_game
from sprites import load_sprite

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
                    uncaught_pokemon = [p for p in game_state.pokemon_list if not p[4]]
                    if uncaught_pokemon:
                        target_pokemon = random.choice(uncaught_pokemon)
                        pokedex_id = target_pokemon[0]
                        
                        is_shiny_encounter = (random.random() < SHINY_RATE)

                        sprite_to_load = target_pokemon[3] if is_shiny_encounter else target_pokemon[2]
                        sprite_file = Path(sprite_to_load).name
                        sprite_path = game_state.BASE_DIR / "app" / "data" / "sprites" / sprite_file
                        pokemon_original_sprite = load_sprite(sprite_path)

                        if pokemon_original_sprite:
                            pokemon_sprite_for_game = pygame.transform.scale(pokemon_original_sprite, (100, 100))
                            catch_result = catch_game.run(game_state.screen, game_state.font, pokemon_sprite_for_game, game_state.pokeball_img_small)
                            if catch_result == "caught":
                                stabilize_result = stabilize_game.run(game_state.screen, game_state.font, game_state.pokeball_img_large, pokemon_sprite_for_game)
                                if stabilize_result == "caught":
                                    update_pokemon_caught_status(game_state.conn, pokedex_id, True, is_shiny_encounter)
                                    caught_count = get_caught_pokemon_count(game_state.conn)
                                    mew_unlocked_now = mew_is_unlocked(game_state.conn)

                                    for gen, data in GENERATION_THRESHOLDS.items():
                                        if caught_count >= data['unlock_count'] and game_state.current_max_pokedex_id < data['max_id']:
                                            game_state.current_max_pokedex_id = data['max_id']
                                            print(f"Génération {gen} déverrouillée !")
                                            break
                                    
                                    game_state.pokemon_list = get_pokemon_list(game_state.conn, game_state.current_max_pokedex_id, include_mew=mew_unlocked_now)
                                    game_state.current_pokemon_data = get_pokemon_data(game_state.conn, pokedex_id)
                                    if game_state.current_pokemon_data:
                                        for i, p in enumerate(game_state.pokemon_list):
                                            if p[0] == pokedex_id:
                                                game_state.selected_index = i
                                                if game_state.selected_index < game_state.scroll_offset or game_state.selected_index >= game_state.scroll_offset + game_state.max_visible_items:
                                                    game_state.scroll_offset = max(0, game_state.selected_index - game_state.max_visible_items // 2)
                                                break
                                        game_state.state = "detail"
                                elif stabilize_result == "failed":
                                    game_state.state = "list"
                            elif catch_result == "quit":
                                game_state.running = False
                elif event.key == pygame.K_ESCAPE:
                    game_state.running = False
            elif game_state.state == "detail" and event.key == pygame.K_m:
                game_state.state = "list"
                game_state.current_sprite = None

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_DOWN:
                game_state.key_down_pressed = False
            elif event.key == pygame.K_UP:
                game_state.key_up_pressed = False

    if game_state.state == "list":
        if game_state.key_down_pressed:
            elapsed = now - game_state.down_press_time
            delay = game_state.scroll_delay if elapsed < game_state.scroll_accel_time else game_state.scroll_fast_delay
            if elapsed > game_state.scroll_delay and now - game_state.last_scroll_time > delay:
                if game_state.selected_index < len(game_state.pokemon_list) - 1:
                    game_state.selected_index += 1
                    if game_state.selected_index - game_state.scroll_offset >= game_state.max_visible_items:
                        game_state.scroll_offset += 1
                game_state.last_scroll_time = now
        elif game_state.key_up_pressed:
            elapsed = now - game_state.up_press_time
            delay = game_state.scroll_delay if elapsed < game_state.scroll_accel_time else game_state.scroll_fast_delay
            if elapsed > game_state.scroll_delay and now - game_state.last_scroll_time > delay:
                if game_state.selected_index > 0:
                    game_state.selected_index -= 1
                    if game_state.selected_index < game_state.scroll_offset:
                        game_state.scroll_offset -= 1
                game_state.last_scroll_time = now
