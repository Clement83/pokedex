import os
import sys
import subprocess
import pygame
import shutil
import glob
from pathlib import Path
from datetime import datetime
from config import GENERATION_THRESHOLDS
from db import get_caught_pokemon_count, get_seen_pokemon_count

def update_and_restart(game_state):
    """Performs a git pull and restarts the application."""
    screen = game_state.screen
    font = game_state.font
    project_path = game_state.BASE_DIR

    def draw_message(message, color=(255, 255, 255)):
        screen.fill((0, 0, 0))
        text_surface = font.render(message, True, color)
        text_rect = text_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
        screen.blit(text_surface, text_rect)
        pygame.display.flip()

    draw_message("Updating via 'git pull'...")
    try:
        result = subprocess.run(
            ['git', 'pull'],
            cwd=str(project_path),
            capture_output=True, text=True, check=True, encoding='utf-8'
        )
        draw_message("Update complete. Restarting...")
        print("--- Git pull successful ---")
        print(result.stdout)
        pygame.time.wait(1500)
        os.execv(sys.executable, ['python'] + sys.argv)
    except Exception as e:
        draw_message(f"Update failed: {e}", color=(255, 100, 100))
        print(f"--- Git pull failed ---")
        print(e)
        pygame.time.wait(3000)

def reset_game_state(game_state):
    """Resets all Pokémon to uncaught and clears user preferences, with backup."""
    screen = game_state.screen
    font = game_state.font

    def draw_message(message, color=(255, 255, 255)):
        screen.fill((0, 0, 0))
        text_surface = font.render(message, True, color)
        text_rect = text_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
        screen.blit(text_surface, text_rect)
        pygame.display.flip()

    try:
        # --- Create Backup ---
        draw_message("Creating database backup...")
        db_path = game_state.BASE_DIR / "pokedex.db"

        # Generate timestamped backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"pokedex_{timestamp}.bk"
        backup_path = game_state.BASE_DIR / backup_filename
        shutil.copyfile(db_path, backup_path)
        draw_message(f"Backup created: {backup_filename}")
        pygame.time.wait(1000)

        # --- Reset Game State ---
        draw_message("Resetting game state...")
        with game_state.conn:
            game_state.conn.execute("UPDATE pokemon SET caught=0, is_shiny=0, seen=0, times_caught=0")
            game_state.conn.execute("DELETE FROM user_preferences")
        draw_message("Reset complete. Restarting...")
        pygame.time.wait(2000)
        os.execv(sys.executable, ['python'] + sys.argv)
    except Exception as e:
        draw_message(f"Reset failed: {e}", color=(255, 100, 100))
        pygame.time.wait(3000)

def go_to_next_milestone(game_state):
    """Catches Pokémon until one short of the next generation unlock."""
    screen = game_state.screen
    font = game_state.font

    def draw_message(message, color=(255, 255, 255)):
        screen.fill((0, 0, 0))
        text_surface = font.render(message, True, color)
        text_rect = text_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
        screen.blit(text_surface, text_rect)
        pygame.display.flip()

    try:
        caught_count = get_seen_pokemon_count(game_state.conn)
        next_threshold = -1

        # Find the next unlock count
        for gen, data in sorted(GENERATION_THRESHOLDS.items(), key=lambda item: item[1]['unlock_count']):
            if data['unlock_count'] > caught_count:
                next_threshold = data['unlock_count']
                break

        if next_threshold == -1:
            draw_message("All milestones already reached!")
            pygame.time.wait(2000)
            return

        target_caught_count = next_threshold - 1
        pokemon_to_catch = target_caught_count - caught_count

        if pokemon_to_catch <= 0:
            draw_message(f"Already at threshold {target_caught_count}.")
            pygame.time.wait(2000)
            return

        draw_message(f"Catching {pokemon_to_catch} Pokémon...")

        # Get uncaught Pokémon and catch them
        with game_state.conn:
            cursor = game_state.conn.execute(
                "SELECT pokedex_id FROM pokemon WHERE caught = 0 ORDER BY RANDOM() LIMIT ?",
                (pokemon_to_catch,)
            )
            pids_to_catch = [row[0] for row in cursor.fetchall()]

            if len(pids_to_catch) < pokemon_to_catch:
                draw_message("Not enough uncaught Pokémon!", color=(255,100,100))
                pygame.time.wait(2000)
                return

            for pid in pids_to_catch:
                game_state.conn.execute(
                    "UPDATE pokemon SET seen = 1 WHERE pokedex_id = ?",
                    (pid,)
                )

        draw_message(f"Done. Caught: {target_caught_count}. Restarting...")
        pygame.time.wait(2000)
        os.execv(sys.executable, ['python'] + sys.argv)

    except Exception as e:
        draw_message(f"Error: {e}", color=(255, 100, 100))
        pygame.time.wait(3000)
