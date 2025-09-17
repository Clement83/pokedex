import pygame
from pathlib import Path
from sprites import load_sprite, apply_shadow_effect
from ui import draw_list_view, draw_detail_view, draw_general_stats
from config import STATS_FONT_SIZE

def update_sprite(game_state):
    pokemon_id = game_state.pokemon_list[game_state.selected_index][0]
    is_pokemon_caught = game_state.pokemon_list[game_state.selected_index][4]
    is_pokemon_shiny = game_state.pokemon_list[game_state.selected_index][5]
    view_state = game_state.state

    # Clé de cache unique pour chaque état du sprite
    cache_key = (pokemon_id, is_pokemon_shiny, is_pokemon_caught, view_state)

    # Vérifier si le sprite est déjà en cache
    if cache_key in game_state.sprite_cache:
        game_state.current_sprite = game_state.sprite_cache[cache_key]
        return

    # Si non, charger et traiter le sprite
    if is_pokemon_shiny and game_state.pokemon_list[game_state.selected_index][3]:
        sprite_to_load_name = game_state.pokemon_list[game_state.selected_index][3]
    else:
        sprite_to_load_name = game_state.pokemon_list[game_state.selected_index][2]
    
    sprite_file = Path(sprite_to_load_name).name
    SPRITES_DIR = game_state.BASE_DIR / "app" / "data" / "sprites"
    sprite_path = SPRITES_DIR / sprite_file

    original_sprite = load_sprite(sprite_path)
    if original_sprite:
        processed_sprite = original_sprite
        if not is_pokemon_caught:
            # L'effet d'ombre modifie la surface, il faut copier pour ne pas affecter le cache original
            processed_sprite = apply_shadow_effect(original_sprite.copy())

        if view_state == "list":
            final_sprite = pygame.transform.scale(processed_sprite, (128, 128))
        elif view_state == "detail":
            final_sprite = processed_sprite
        else:
            final_sprite = processed_sprite # Fallback

        game_state.current_sprite = final_sprite
        # Mettre le sprite final en cache
        game_state.sprite_cache[cache_key] = final_sprite

def update_animations(game_state):
    # Evolution text scrolling animation
    if game_state.state == "detail" and game_state.evolution_scroll_active:
        if game_state.evolution_text_surface:
            now = pygame.time.get_ticks()
            if now - game_state.evolution_scroll_timer > 20: # Control scroll speed
                game_state.evolution_scroll_timer = now
                
                text_width = game_state.evolution_text_surface.get_width()
                box_width = 350
                scroll_limit = text_width - box_width

                if scroll_limit > 0:
                    game_state.evolution_text_scroll_x += game_state.evolution_scroll_direction
                    if game_state.evolution_text_scroll_x >= scroll_limit or game_state.evolution_text_scroll_x <= 0:
                        game_state.evolution_scroll_direction *= -1

def render(game_state):
    stats_font = pygame.font.SysFont("Arial", STATS_FONT_SIZE, bold=True) # Define stats_font here
    if game_state.state == "list":
        draw_list_view(game_state.screen, game_state.pokemon_list, game_state.selected_index, game_state.scroll_offset, game_state.max_visible_items, game_state.current_sprite, game_state.font, game_state.list_view_background)
        draw_general_stats(game_state.screen, game_state, stats_font) # Call draw_general_stats
    elif game_state.state == "detail" and game_state.current_pokemon_data:
        is_pokemon_caught = game_state.pokemon_list[game_state.selected_index][4]
        is_shiny = game_state.pokemon_list[game_state.selected_index][5]
        draw_detail_view(game_state)

    pygame.display.flip()

def game_loop(game_state, input_handler):
    while game_state.running:
        input_handler.handle_input(game_state)
        update_sprite(game_state)
        render(game_state)
        game_state.clock.tick(60)
