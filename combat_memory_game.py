import pygame
import random
from config import SCREEN_WIDTH, SCREEN_HEIGHT, KEY_MAPPINGS
import controls

# Game settings
SEQUENCE_LENGTH = 4  # Fixed length of 4 steps

TIME_PER_INPUT_MS = 3000  # 3 seconds per input
SHOW_DURATION_MS = 500
PAUSE_DURATION_MS = 250

ARROW_SIZE = 50

def create_arrow_surface(direction, size, color):
    """Draws a simple arrow on a new surface."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    s = size
    padding = int(s * 0.2)
    thickness = 3

    if direction == "UP":
        start_pos = (s / 2, s - padding)
        end_pos = (s / 2, padding)
        arrow_head = [(padding, padding * 2), (s - padding, padding * 2)]
    elif direction == "DOWN":
        start_pos = (s / 2, padding)
        end_pos = (s / 2, s - padding)
        arrow_head = [(padding, s - padding * 2), (s - padding, s - padding * 2)]
    elif direction == "LEFT":
        start_pos = (s - padding, s / 2)
        end_pos = (padding, s / 2)
        arrow_head = [(padding * 2, padding), (padding * 2, s - padding)]
    elif direction == "RIGHT":
        start_pos = (padding, s / 2)
        end_pos = (s - padding, s / 2)
        arrow_head = [(s - padding * 2, padding), (s - padding * 2, s - padding)]

    pygame.draw.line(surf, color, start_pos, end_pos, thickness)
    pygame.draw.line(surf, color, end_pos, arrow_head[0], thickness)
    pygame.draw.line(surf, color, end_pos, arrow_head[1], thickness)
    return surf

def run(screen, font, game_state, pokemon_sprite, dresseur_sprite, background_image, pokemon_types, full_pokemon_data):
    """Runs the fixed sequence memory mini-game."""
    clock = pygame.time.Clock()

    # --- Setup ---
    possible_inputs = [("UP", KEY_MAPPINGS["UP"]), ("DOWN", KEY_MAPPINGS["DOWN"]), ("LEFT", KEY_MAPPINGS["LEFT"]), ("RIGHT", KEY_MAPPINGS["RIGHT"])]
    sequence = [random.choice(possible_inputs) for _ in range(SEQUENCE_LENGTH)]
    player_input_index = 0

    arrow_surfaces = {
        name: create_arrow_surface(name, ARROW_SIZE, (255, 255, 255))
        for name, keys in possible_inputs
    }

    # --- State Management ---
    game_phase = "INTRO"
    phase_timer = pygame.time.get_ticks()
    sequence_index = 0

    pokemon_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    pokemon_rect = pokemon_sprite.get_rect(center=pokemon_pos)
    arrow_pos = (pokemon_rect.centerx, pokemon_rect.top - ARROW_SIZE // 2)

    while True:
        for event in pygame.event.get():
            controls.process_joystick_input(game_state, event)
            if event.type == pygame.QUIT: return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key in KEY_MAPPINGS["QUIT"]: return "quit"
                if event.key in KEY_MAPPINGS["CANCEL"]: return "lose"
                
                if game_phase == "INPUT" and player_input_index < len(sequence):
                    expected_keys = sequence[player_input_index][1]
                    if event.key in expected_keys:
                        player_input_index += 1
                        if player_input_index == len(sequence):
                            return "win"
                    else:
                        return "lose"

        current_time = pygame.time.get_ticks()
        if game_phase == "INTRO":
            if current_time - phase_timer > 1500:
                game_phase = "SHOWING"
                phase_timer = current_time
        elif game_phase == "SHOWING":
            if sequence_index < len(sequence):
                if current_time - phase_timer > SHOW_DURATION_MS + PAUSE_DURATION_MS:
                    sequence_index += 1
                    phase_timer = current_time
            else:
                game_phase = "INPUT"
                phase_timer = current_time

        if background_image:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill((20, 20, 30))
        
        screen.blit(pokemon_sprite, pokemon_rect)

        if game_phase == "INTRO":
            text = font.render("Mémorisez la séquence !", True, (255, 255, 255))
            screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, 100)))

        elif game_phase == "SHOWING" and sequence_index < len(sequence):
            if current_time - phase_timer < SHOW_DURATION_MS:
                arrow_name = sequence[sequence_index][0]
                arrow_img = arrow_surfaces[arrow_name]
                screen.blit(arrow_img, arrow_img.get_rect(center=arrow_pos))

        elif game_phase == "INPUT":
            time_limit = len(sequence) * TIME_PER_INPUT_MS
            if current_time - phase_timer > time_limit:
                return "lose"

            turn_text = font.render("À vous !", True, (255, 255, 255))
            screen.blit(turn_text, turn_text.get_rect(center=(SCREEN_WIDTH // 2, 100)))
            
            # Draw placeholders and correct inputs
            progress_y = SCREEN_HEIGHT - ARROW_SIZE - 40
            total_width = len(sequence) * (ARROW_SIZE + 10) - 10
            start_x = (SCREEN_WIDTH - total_width) // 2
            for i in range(len(sequence)):
                box_rect = pygame.Rect(start_x + i * (ARROW_SIZE + 10), progress_y, ARROW_SIZE, ARROW_SIZE)
                # Draw placeholder box
                pygame.draw.rect(screen, (80, 80, 80), box_rect, 2)

                if i < player_input_index:
                    # If input is correct, draw green box and the arrow
                    pygame.draw.rect(screen, (0, 255, 0), box_rect)
                    arrow_name = sequence[i][0]
                    arrow_img = arrow_surfaces[arrow_name]
                    screen.blit(arrow_img, arrow_img.get_rect(center=box_rect.center))

            time_left = (time_limit - (current_time - phase_timer)) / 1000
            timer_text = font.render(f"Temps: {max(0, time_left):.1f}s", True, (255, 255, 255))
            screen.blit(timer_text, (10, 10))

        pygame.display.flip()
        clock.tick(60)
