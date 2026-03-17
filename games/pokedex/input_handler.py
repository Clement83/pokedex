import pygame
import random
from pathlib import Path
import subprocess
import os
from db import get_pokemon_data, get_caught_pokemon_count, get_shiny_pokemon_count, mew_is_unlocked, get_pokemon_list, get_seen_pokemon_count
from config import REGIONS, KEY_MAPPINGS, SCREEN_WIDTH, SCREEN_HEIGHT
import controls
import catch_game
import stabilize_game
from sprites import load_sprite
import hunt # Import the new hunt module

# --- Debug combination state for keyboard ---
_keyboard_debug_combo_start_time = {}
_keyboard_debug_combo_active = {}
_keyboard_pressed_keys = set()
DEBUG_HOLD_DURATION = 5000  # 5 seconds in milliseconds

def _run_git_pull(game_state):
    """Executes git pull and displays feedback on the screen."""
    screen = game_state.screen
    font = game_state.font
    project_path = game_state.BASE_DIR

    def draw_message(message, color=(255, 255, 255)):
        screen.fill((0, 0, 0)) # Black background
        text_surface = font.render(message, True, color)
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(text_surface, text_rect)
        pygame.display.flip()

    draw_message("Mise à jour en cours via 'git pull'...")
    pygame.time.wait(500)

    try:
        result = subprocess.run(
            ['git', 'pull'],
            cwd=str(project_path),
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )

        output = result.stdout
        if "Already up to date." in output:
            draw_message("Déjà à jour.")
        else:
            draw_message("Mise à jour terminée. Redémarrage requis.")

        print("--- 'git pull' réussi ! ---")
        print(output)
        pygame.time.wait(2000)

    except FileNotFoundError:
        draw_message("Erreur: 'git' non trouvé.", color=(255, 100, 100))
        print("Erreur : La commande 'git' n'a pas été trouvée.")
        pygame.time.wait(3000)
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.strip().split('\n')[-1]
        draw_message(f"Échec: {error_message}", color=(255, 100, 100))
        print(f"--- Erreur lors de 'git pull' (code: {e.returncode}) ---")
        print(e.stderr)
        pygame.time.wait(3000)
    except Exception as e:
        draw_message(f"Erreur inattendue.", color=(255, 100, 100))
        print(f"Une erreur inattendue est survenue : {e}")
        pygame.time.wait(3000)

def handle_input(game_state, event):
    global _keyboard_debug_combo_start_time, _keyboard_debug_combo_active, _keyboard_pressed_keys
    now = pygame.time.get_ticks()

    if event.type == pygame.KEYDOWN:
        _keyboard_pressed_keys.add(event.key)

        # --- Debug Actions Check (require holding for 5 seconds) ---
        # Check for combinations with F1 key
        if pygame.K_F1 in _keyboard_pressed_keys:
            if pygame.K_F2 in _keyboard_pressed_keys:  # F1 + F2 (update and restart)
                combo_key = "update_restart"
                if combo_key not in _keyboard_debug_combo_start_time:
                    _keyboard_debug_combo_start_time[combo_key] = now
                    _keyboard_debug_combo_active[combo_key] = False
                return
            elif pygame.K_F3 in _keyboard_pressed_keys:  # F1 + F3 (reset game)
                combo_key = "reset_game"
                if combo_key not in _keyboard_debug_combo_start_time:
                    _keyboard_debug_combo_start_time[combo_key] = now
                    _keyboard_debug_combo_active[combo_key] = False
                return
            elif pygame.K_F4 in _keyboard_pressed_keys:  # F1 + F4 (next milestone)
                combo_key = "next_milestone"
                if combo_key not in _keyboard_debug_combo_start_time:
                    _keyboard_debug_combo_start_time[combo_key] = now
                    _keyboard_debug_combo_active[combo_key] = False
                return

        if event.key in KEY_MAPPINGS["GIT_PULL"] and pygame.K_F1 not in _keyboard_pressed_keys:
            _run_git_pull(game_state)
            # After pulling, the app should ideally be restarted.
            # For now, we just continue the loop.
            return # Use return to skip the rest of the handler for this event

        if event.key in KEY_MAPPINGS["ACTION"] and game_state.state in ["list", "detail"]:
            hunt_result = hunt.run(game_state.screen, game_state.font, game_state)

            # Après être revenu de la chasse, mettez à jour les statistiques générales.
            game_state.caught_count = get_caught_pokemon_count(game_state.conn)
            game_state.shiny_count = get_shiny_pokemon_count(game_state.conn)
            game_state.seen_count = get_seen_pokemon_count(game_state.conn)
            unlocked_regions = 0
            for region_name, data in REGIONS.items():
                if data["min_id"] < game_state.current_max_pokedex_id:
                    unlocked_regions += 1
            game_state.unlocked_regions_count = unlocked_regions

            if hunt_result == "quit":
                game_state.running = False
            elif hunt_result == "main_menu": # Go back to list view
                game_state.state = "list"
            elif hunt_result == "detail":
                game_state.state = "detail"
            # Skip other key handling for this frame as hunt has its own loop
            return # Use return

        if game_state.state == "list":
            if event.key in KEY_MAPPINGS["DOWN"]:
                game_state.key_down_pressed = True
                game_state.down_press_time = now
                game_state.last_scroll_time = now
                if game_state.selected_index < len(game_state.pokemon_list) - 1:
                    game_state.selected_index += 1
                    if game_state.selected_index - game_state.scroll_offset >= game_state.max_visible_items:
                        game_state.scroll_offset += 1
            elif event.key in KEY_MAPPINGS["UP"]:
                game_state.key_up_pressed = True
                game_state.up_press_time = now
                game_state.last_scroll_time = now
                if game_state.selected_index > 0:
                    game_state.selected_index -= 1
                    if game_state.selected_index < game_state.scroll_offset:
                        game_state.scroll_offset -= 1
            elif event.key in KEY_MAPPINGS["LEFT"]:
                game_state.selected_index = max(0, game_state.selected_index - 50)
                if game_state.selected_index < game_state.scroll_offset:
                    game_state.scroll_offset = game_state.selected_index
            elif event.key in KEY_MAPPINGS["RIGHT"]:
                game_state.selected_index = min(len(game_state.pokemon_list) - 1, game_state.selected_index + 50)
                if game_state.selected_index - game_state.scroll_offset >= game_state.max_visible_items:
                    game_state.scroll_offset = game_state.selected_index - game_state.max_visible_items + 1
            elif event.key in KEY_MAPPINGS["CONFIRM"]:
                pid = game_state.pokemon_list[game_state.selected_index][0]
                game_state.current_pokemon_data = get_pokemon_data(game_state.conn, pid)
                if game_state.current_pokemon_data:
                    game_state.state = "detail"
                    # Only play cry if the Pokémon has been seen
                    is_pokemon_seen = game_state.pokemon_list[game_state.selected_index][8]
                    if is_pokemon_seen:
                        pokemon_name_en = game_state.pokemon_list[game_state.selected_index][2]
                        cry_path = game_state.BASE_DIR / "pokemon_audio" / "cries" / f"{pokemon_name_en.lower()}.mp3"
                        if cry_path.exists():
                            try:
                                cry_sound = pygame.mixer.Sound(str(cry_path))
                                cry_sound.set_volume(game_state.music_volume)
                                cry_sound.play()
                            except pygame.error as e:
                                print(f"Error playing cry: {e}")
            elif event.key in KEY_MAPPINGS["QUIT"]:
                game_state.running = False
        elif game_state.state == "detail":
            if event.key in KEY_MAPPINGS["CANCEL"]:
                game_state.state = "list"
                game_state.current_sprite = None
            elif event.key in KEY_MAPPINGS["RIGHT"]:
                if game_state.selected_index < len(game_state.pokemon_list) - 1:
                    game_state.selected_index += 1
                    pid = game_state.pokemon_list[game_state.selected_index][0]
                    game_state.current_pokemon_data = get_pokemon_data(game_state.conn, pid)
            elif event.key in KEY_MAPPINGS["LEFT"]:
                if game_state.selected_index > 0:
                    game_state.selected_index -= 1
                    pid = game_state.pokemon_list[game_state.selected_index][0]
                    game_state.current_pokemon_data = get_pokemon_data(game_state.conn, pid)
            elif event.key in KEY_MAPPINGS["CONFIRM"]:
                if game_state.current_pokemon_data:
                    is_pokemon_seen = game_state.pokemon_list[game_state.selected_index][8] # Get caught status
                    if is_pokemon_seen:
                        pokemon_name = game_state.pokemon_list[game_state.selected_index][2] # Get name_en from pokemon_list
                        cry_path = game_state.BASE_DIR / "pokemon_audio" / "cries" / f"{pokemon_name.lower()}.mp3"
                        if cry_path.exists():
                            try:
                                cry_sound = pygame.mixer.Sound(str(cry_path))
                                cry_sound.set_volume(game_state.music_volume)
                                cry_sound.play()
                            except pygame.error as e:
                                print(f"Error playing cry: {e}")

    elif event.type == pygame.KEYUP:
        if event.key in _keyboard_pressed_keys:
            _keyboard_pressed_keys.discard(event.key)

        # Reset debug combo timers when keys are released
        if event.key in [pygame.K_F1, pygame.K_F2, pygame.K_F3, pygame.K_F4]:
            _keyboard_debug_combo_start_time.clear()
            _keyboard_debug_combo_active.clear()

        if event.key in KEY_MAPPINGS["DOWN"]:
            game_state.key_down_pressed = False
        elif event.key in KEY_MAPPINGS["UP"]:
            game_state.key_up_pressed = False

def check_keyboard_debug_combos(game_state):
    """
    Checks if keyboard debug combinations have been held long enough and triggers actions.
    Should be called in the main game loop.
    """
    global _keyboard_debug_combo_start_time, _keyboard_debug_combo_active
    import debug_actions

    if not _keyboard_debug_combo_start_time:
        return

    now = pygame.time.get_ticks()
    screen = game_state.screen
    font = game_state.font

    for combo_key, start_time in list(_keyboard_debug_combo_start_time.items()):
        elapsed = now - start_time

        # Draw progress bar
        if elapsed < DEBUG_HOLD_DURATION:
            progress = elapsed / DEBUG_HOLD_DURATION
            bar_width = 200
            bar_height = 20
            bar_x = (screen.get_width() - bar_width) // 2
            bar_y = screen.get_height() - 40

            # Draw background
            pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
            # Draw progress
            pygame.draw.rect(screen, (255, 200, 0), (bar_x, bar_y, int(bar_width * progress), bar_height))
            # Draw border
            pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)

            # Draw text
            combo_names = {
                "update_restart": "Git Pull & Restart",
                "reset_game": "Reset Game",
                "next_milestone": "Next Milestone"
            }
            text = font.render(f"Hold for: {combo_names.get(combo_key, 'Debug Action')}", True, (255, 255, 255))
            text_rect = text.get_rect(center=(screen.get_width() // 2, bar_y - 15))
            screen.blit(text, text_rect)

        # Execute action if held long enough
        elif not _keyboard_debug_combo_active.get(combo_key, False):
            _keyboard_debug_combo_active[combo_key] = True

            if combo_key == "update_restart":
                debug_actions.update_and_restart(game_state)
            elif combo_key == "reset_game":
                debug_actions.reset_game_state(game_state)
            elif combo_key == "next_milestone":
                debug_actions.go_to_next_milestone(game_state)

            # Clear the combo after execution
            _keyboard_debug_combo_start_time.clear()
            _keyboard_debug_combo_active.clear()
            break

def handle_continuous_input(game_state):
    now = pygame.time.get_ticks()
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
