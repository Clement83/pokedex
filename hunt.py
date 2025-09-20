import pygame
import random
from pathlib import Path
from config import SCREEN_WIDTH, SCREEN_HEIGHT, SHINY_RATE, GENERATION_THRESHOLDS, REGIONS, STABILIZE_CATCH_RATE_THRESHOLD, KEY_MAPPINGS
from db import get_pokemon_data, update_pokemon_caught_status, get_caught_pokemon_count, mew_is_unlocked, get_pokemon_list, get_user_preference, set_user_preference
import controls
import catch_game
import stabilize_game
from sprites import load_sprite


# Grid configuration for regions
GRID_COLS = 3
IMAGE_SIZE = 90 # Size for region images (increased)
GRID_START_Y = 5 # Starting Y position for the grid (moved up further)
GRID_PADDING = 10 # Padding between images (reduced)

def run(screen, font, game_state): # Added game_state parameter
    region_names = list(REGIONS.keys())
    num_regions = len(region_names)
    
    # Calculate grid dimensions
    GRID_ROWS = (num_regions + GRID_COLS - 1) // GRID_COLS

    # Load region images once
    region_images_loaded = {}
    for region_name, data in REGIONS.items():
        image_path = game_state.BASE_DIR / "app" / "data" / "assets" / region_name.lower() / "icon.png"
        loaded_image = load_sprite(image_path)
        if loaded_image:
            region_images_loaded[region_name] = pygame.transform.scale(loaded_image, (IMAGE_SIZE, IMAGE_SIZE))
        else:
            print(f"Warning: Could not load image for region {region_name} at {image_path}")
            region_images_loaded[region_name] = pygame.Surface((IMAGE_SIZE, IMAGE_SIZE)) # Placeholder

    # Initial selection
    selected_row = 0
    selected_col = 0

    # Load last selected region from preferences
    last_region = get_user_preference(game_state.conn, "last_selected_region")
    if last_region and last_region in region_names:
        last_region_index = region_names.index(last_region)
        selected_row = last_region_index // GRID_COLS
        selected_col = last_region_index % GRID_COLS

    running = True
    while running:
        for event in pygame.event.get():
            controls.process_joystick_input(game_state, event)
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key in KEY_MAPPINGS["UP"]:
                    selected_row = (selected_row - 1) % GRID_ROWS
                elif event.key in KEY_MAPPINGS["DOWN"]:
                    selected_row = (selected_row + 1) % GRID_ROWS
                elif event.key in KEY_MAPPINGS["LEFT"]:
                    selected_col = (selected_col - 1) % GRID_COLS
                elif event.key in KEY_MAPPINGS["RIGHT"]:
                    selected_col = (selected_col + 1) % GRID_COLS
                elif event.key in KEY_MAPPINGS["QUIT"]:
                    return "quit"
                elif event.key in KEY_MAPPINGS["CONFIRM"]:
                    selected_region_index = selected_row * GRID_COLS + selected_col
                    if selected_region_index < num_regions: # Ensure a valid region is selected
                        selected_region_name = region_names[selected_region_index]
                        region_data = REGIONS[selected_region_name]
                        
                        # Check if region is locked
                        is_locked = region_data["min_id"] >= game_state.current_max_pokedex_id
                        
                        if is_locked:
                            continue # Stay on the current screen, do not proceed with hunt logic
                        else:
                            # Save the last selected region
                            set_user_preference(game_state.conn, "last_selected_region", selected_region_name)
                            # Get all pokemon in the selected region
                            available_pokemon_in_region = [p for p in game_state.pokemon_list if p[0] >= region_data["min_id"] and p[0] < region_data["max_id"]]
                            
                            if available_pokemon_in_region:
                                target_pokemon = random.choice(available_pokemon_in_region)
                                pokedex_id = target_pokemon[0]
                                
                                is_shiny_encounter = (random.random() < SHINY_RATE)

                                sprite_to_load = target_pokemon[4] if is_shiny_encounter else target_pokemon[3]
                                sprite_file = Path(sprite_to_load).name
                                sprite_path = game_state.BASE_DIR / "app" / "data" / "sprites" / sprite_file
                                pokemon_original_sprite = load_sprite(sprite_path)

                                if not pokemon_original_sprite:
                                    game_state.message = f"Sprite for {target_pokemon[1]} not found!"
                                    game_state.message_timer = pygame.time.get_ticks() + 2000 # Display for 2 seconds
                                    # continue # Removed for debugging

                                dresseur_sprite_path = game_state.BASE_DIR / "app" / "data" / "assets" / "dresseurs" / game_state.dresseur / "dos.png"
                                dresseur_back_sprite = load_sprite(dresseur_sprite_path)
                                pokemon_sprite_for_game = pygame.transform.scale(pokemon_original_sprite, (64, 64))
                                catch_game_output = catch_game.run(game_state.screen, game_state.font, pokemon_sprite_for_game, game_state.pokeball_img_small, selected_region_name, dresseur_back_sprite, game_state)

                                if not isinstance(catch_game_output, tuple):
                                    if catch_game_output == "quit":
                                        return "quit"
                                    continue # For "back" or other cases, just redraw hunt screen

                                catch_result, background_image, dresseur_front_sprite = catch_game_output
                                if catch_result == "caught":
                                    # Get pokemon data to check catch_rate
                                    pokemon_data = get_pokemon_data(game_state.conn, pokedex_id)
                                    catch_rate = pokemon_data.get('catch_rate', 0) if pokemon_data else 0
                                    
                                    # Skip stabilize mini-game if catch_rate is high enough, but keep intro animation
                                    if catch_rate > STABILIZE_CATCH_RATE_THRESHOLD:
                                        stabilize_result = stabilize_game.run_intro_only(game_state.screen, game_state.font, game_state.pokeball_img_large, pokemon_sprite_for_game, background_image, dresseur_front_sprite, game_state)
                                    else:
                                        stabilize_result = stabilize_game.run(game_state.screen, game_state.font, game_state.pokeball_img_large, pokemon_sprite_for_game, background_image, dresseur_front_sprite, game_state)
                                    
                                    if stabilize_result == "caught":
                                        update_pokemon_caught_status(game_state.conn, pokedex_id, True, is_shiny_encounter)
                                        caught_count = get_caught_pokemon_count(game_state.conn)
                                        mew_unlocked_now = mew_is_unlocked(game_state.conn)

                                        for gen, data in GENERATION_THRESHOLDS.items():
                                            if caught_count >= data['unlock_count'] and game_state.current_max_pokedex_id < data['max_id']:
                                                game_state.current_max_pokedex_id = data['max_id']
                                                print(f"Génération {gen - 1} déverrouillée !")
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
                                        return "detail" # Return to main loop to show detail view
                                    elif stabilize_result == "failed":
                                        game_state.state = "list"
                                    # Other stabilize results ("quit", "back") will just fall through, redrawing the hunt screen.

                            # --- End of moved logic ---
                            else: # This else corresponds to 'if available_pokemon_in_region:'
                                # No pokemon in this region, display a message
                                game_state.message = f"No pokemon in {selected_region_name}!"
                                game_state.message_timer = pygame.time.get_ticks() + 2000 # Display for 2 seconds
                                # Stay on the current screen
                                # Do not return "main_menu" here.


                elif event.key in KEY_MAPPINGS["CANCEL"]: # Allow escaping from hunt screen
                    return "main_menu" # Go back to list view

        screen.fill((0, 0, 0)) # Black background

        # Calculate grid drawing parameters
        total_grid_width = GRID_COLS * IMAGE_SIZE + (GRID_COLS - 1) * GRID_PADDING
        start_x = (SCREEN_WIDTH - total_grid_width) // 2
        
        for i, region_name in enumerate(region_names):
            row = i // GRID_COLS
            col = i % GRID_COLS

            if row >= GRID_ROWS: # Don't draw if outside calculated rows
                continue

            x_pos = start_x + col * (IMAGE_SIZE + GRID_PADDING)
            y_pos = GRID_START_Y + row * (IMAGE_SIZE + GRID_PADDING)

            # Draw region image
            if region_name in region_images_loaded:
                region_image = region_images_loaded[region_name]
                screen.blit(region_image, (x_pos, y_pos))
                
                # Check if region is locked
                region_data = REGIONS[region_name]
                is_locked = region_data["min_id"] >= game_state.current_max_pokedex_id

                if is_locked:
                    # Create a semi-transparent black overlay
                    overlay = pygame.Surface(region_image.get_size(), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 150)) # Black with 150 alpha (out of 255)
                    screen.blit(overlay, (x_pos, y_pos))
            
            # Draw highlight if selected
            if row == selected_row and col == selected_col:
                pygame.draw.rect(screen, (255, 255, 0), (x_pos, y_pos, IMAGE_SIZE, IMAGE_SIZE), 3) # Yellow border

        # Display selected region name and status at the bottom
        selected_region_index = selected_row * GRID_COLS + selected_col
        if selected_region_index < num_regions:
            current_region_name = region_names[selected_region_index]
            region_data = REGIONS[current_region_name]
            is_locked = region_data["min_id"] >= game_state.current_max_pokedex_id
            
            if is_locked:
                display_text = f"{current_region_name} - LOCKED"
                text_color = (255, 100, 100)  # Light red for locked regions
            else:
                display_text = current_region_name
                text_color = (255, 255, 255)  # White for unlocked regions
            
            region_name_text = font.render(display_text, True, text_color)
            region_name_rect = region_name_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 10)) # 10 pixels from bottom
            screen.blit(region_name_text, region_name_rect)

        # Display messages if any (keeping for other potential messages)
        if game_state.message and pygame.time.get_ticks() < game_state.message_timer:
            message_text = font.render(game_state.message, True, (255, 0, 0)) # Red color for messages
            message_rect = message_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(message_text, message_rect)

        pygame.display.flip()
        pygame.time.Clock().tick(60)

    return "main_menu" # Default return if loop exits unexpectedly