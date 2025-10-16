import pygame
import random
from config import SCREEN_WIDTH, SCREEN_HEIGHT, KEY_MAPPINGS
import controls
from ui import draw_hp_bar, draw_rounded_rect

# Game settings
# SEQUENCE_LENGTH will be determined dynamically based on pokemon difficulty

TIME_PER_INPUT_MS = 3000  # 3 seconds per input
SHOW_DURATION_MS = 500
PAUSE_DURATION_MS = 250

ARROW_SIZE = 50

def create_arrow_surface(direction, size, color):
    """Draws a new, cleaner Pokémon-style arrow."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Style
    bg_color = (255, 255, 255) # White background
    arrow_color = (74, 144, 226) # Medium blue
    border_color = arrow_color

    # Background
    draw_rounded_rect(surf, bg_color, surf.get_rect(), radius=8, border=3, border_color=border_color)

    # Arrow (Chevron-style)
    s = size
    padding = int(s * 0.3)

    if direction == "UP":
        points = [(padding, s * 0.6), (s/2, s * 0.3), (s - padding, s * 0.6), (s/2, s*0.45)]
    elif direction == "DOWN":
        points = [(padding, s * 0.4), (s/2, s * 0.7), (s - padding, s * 0.4), (s/2, s*0.55)]
    elif direction == "LEFT":
        points = [(s * 0.6, padding), (s * 0.3, s/2), (s * 0.6, s - padding), (s*0.45, s/2)]
    elif direction == "RIGHT":
        points = [(s * 0.4, padding), (s * 0.7, s/2), (s * 0.4, s - padding), (s*0.55, s/2)]

    pygame.draw.polygon(surf, arrow_color, points)
    return surf

def draw_sequence_boxes(screen, sequence, player_input_index, flash_box_index, flash_duration, arrow_surfaces, font, progress_y):
    total_width = len(sequence) * (ARROW_SIZE + 10) - 10
    start_x = (SCREEN_WIDTH - total_width) // 2
    for i in range(len(sequence)):
        box_rect = pygame.Rect(start_x + i * (ARROW_SIZE + 10), progress_y, ARROW_SIZE, ARROW_SIZE)
        
        is_flashing_box = i == flash_box_index and flash_duration > 0
        if is_flashing_box and (flash_duration // 4) % 2 == 0:
            pygame.draw.rect(screen, (255, 0, 0), box_rect)
        elif i < player_input_index:
            pygame.draw.rect(screen, (0, 255, 0), box_rect)
            arrow_name = sequence[i][0]
            arrow_img = arrow_surfaces[arrow_name]
            screen.blit(arrow_img, arrow_img.get_rect(center=box_rect.center))
        else:
            pygame.draw.rect(screen, (80, 80, 80), box_rect, 2)

def run(screen, font, game_state, pokemon_sprite, dresseur_sprite, background_image, pokemon_types, full_pokemon_data):
    """Runs the fixed sequence memory mini-game."""
    clock = pygame.time.Clock()

    # --- Game State ---
    player_hp = 3
    max_player_hp = 3
    player_hp_percent = 100.0
    flash_box_index = -1
    flash_duration = 0
    game_over = False

    # --- Setup ---
    catch_rate = full_pokemon_data.get('catch_rate', 255)
    if catch_rate < 45: # Hard/Legendary
        SEQUENCE_LENGTH = 6
    elif catch_rate < 100: # Medium
        SEQUENCE_LENGTH = 5
    else: # Easy
        SEQUENCE_LENGTH = 4

    possible_inputs = [("UP", KEY_MAPPINGS["UP"]), ("DOWN", KEY_MAPPINGS["DOWN"]), ("LEFT", KEY_MAPPINGS["LEFT"]), ("RIGHT", KEY_MAPPINGS["RIGHT"])]
    sequence = [random.choice(possible_inputs) for _ in range(SEQUENCE_LENGTH)]
    player_input_index = 0

    arrow_surfaces = {
        name: create_arrow_surface(name, ARROW_SIZE, (255, 255, 255))
        for name, keys in possible_inputs
    }

    # --- Phase Management ---
    game_phase = "INTRO"
    phase_timer = pygame.time.get_ticks()
    sequence_index = 0

    pokemon_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    pokemon_rect = pokemon_sprite.get_rect(center=pokemon_pos)
    arrow_pos = (pokemon_rect.centerx, pokemon_rect.top - ARROW_SIZE // 2)

    def handle_mistake():
        nonlocal player_hp, game_over, flash_box_index, flash_duration, player_input_index, game_phase, sequence_index, phase_timer
        player_hp -= 1
        flash_box_index = player_input_index
        flash_duration = 30  # frames
        player_input_index = 0
        if player_hp <= 0:
            player_hp = 0
            game_over = True
        else:
            game_phase = "SHOWING"
            sequence_index = 0
            phase_timer = pygame.time.get_ticks()

    while True:
        current_time = pygame.time.get_ticks()
        time_limit = len(sequence) * TIME_PER_INPUT_MS

        # --- Event Handling ---
        for event in pygame.event.get():
            controls.process_joystick_input(game_state, event)
            if event.type == pygame.QUIT: return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key in KEY_MAPPINGS["QUIT"]: return "quit"
                if event.key in KEY_MAPPINGS["CANCEL"]: return "lose"
                
                if game_phase == "INPUT" and player_input_index < len(sequence) and not game_over:
                    expected_keys = sequence[player_input_index][1]
                    if event.key in expected_keys:
                        player_input_index += 1
                        if player_input_index == len(sequence):
                            game_phase = "WIN_FLASH"
                            phase_timer = current_time
                    else:
                        handle_mistake()

        # --- Animations and Game Over ---
        target_hp_percent = (player_hp / max_player_hp) * 100
        if player_hp_percent > target_hp_percent:
            player_hp_percent -= 1.0
        
        if flash_duration > 0:
            flash_duration -= 1
        
        if game_over and player_hp_percent <= target_hp_percent:
            pygame.time.wait(500)
            return "lose"

        # --- Phase Logic ---
        if game_phase == "INTRO":
            if current_time - phase_timer > 1500:
                game_phase = "SHOWING"
                phase_timer = current_time
        elif game_phase == "SHOWING":
            if sequence_index < len(sequence):
                if current_time - phase_timer > SHOW_DURATION_MS + PAUSE_DURATION_MS:
                    sequence_index += 1
                    phase_timer = current_time
            else: # sequence_index >= len(sequence)
                game_phase = "INPUT"
                phase_timer = current_time
                flash_box_index = -1 # Reset flash
                flash_duration = 0   # Reset flash
        elif game_phase == "INPUT":
            if not game_over and current_time - phase_timer > time_limit:
                player_hp = 0
                game_over = True
        elif game_phase == "WIN_FLASH":
            if current_time - phase_timer > 1000: # 1 second delay
                return "win"

        # --- Drawing ---
        if background_image:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill((20, 20, 30))

        if dresseur_sprite:
            screen.blit(dresseur_sprite, (10, SCREEN_HEIGHT - dresseur_sprite.get_height() - 10))
        
        screen.blit(pokemon_sprite, pokemon_rect)

        if game_phase == "INTRO":
            text = font.render("Mémorisez la séquence !", True, (255, 255, 255))
            screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, 100)))

        elif game_phase == "SHOWING":
            progress_y = SCREEN_HEIGHT - ARROW_SIZE - 40 # Define progress_y here for SHOWING phase
            draw_sequence_boxes(screen, sequence, player_input_index, flash_box_index, flash_duration, arrow_surfaces, font, progress_y)

            if sequence_index < len(sequence):
                if current_time - phase_timer < SHOW_DURATION_MS:
                    arrow_name = sequence[sequence_index][0]
                    arrow_img = arrow_surfaces[arrow_name]
                    screen.blit(arrow_img, arrow_img.get_rect(center=arrow_pos))

        elif game_phase == "INPUT":
            turn_text = font.render("À vous !", True, (255, 255, 255))
            screen.blit(turn_text, turn_text.get_rect(center=(SCREEN_WIDTH // 2, 100)))
            
            progress_y = SCREEN_HEIGHT - ARROW_SIZE - 40
            draw_sequence_boxes(screen, sequence, player_input_index, flash_box_index, flash_duration, arrow_surfaces, font, progress_y)
        elif game_phase == "WIN_FLASH":
            text = font.render("Séquence réussie !", True, (0, 255, 0))
            screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, 100)))

            progress_y = SCREEN_HEIGHT - ARROW_SIZE - 40
            total_width = len(sequence) * (ARROW_SIZE + 10) - 10
            start_x = (SCREEN_WIDTH - total_width) // 2
            for i in range(len(sequence)):
                box_rect = pygame.Rect(start_x + i * (ARROW_SIZE + 10), progress_y, ARROW_SIZE, ARROW_SIZE)
                
                # Green flashing logic
                if (current_time // 100) % 2 == 0: # Flash every 100ms
                    pygame.draw.rect(screen, (0, 255, 0), box_rect)
                else:
                    pygame.draw.rect(screen, (0, 150, 0), box_rect) # Darker green when off
                
                # Draw arrows on top of flashing boxes
                arrow_name = sequence[i][0]
                arrow_img = arrow_surfaces[arrow_name]
                screen.blit(arrow_img, arrow_img.get_rect(center=box_rect.center))


        # Draw player HP bar
        draw_hp_bar(screen, player_hp_percent, pos=(20, 20), size=(150, 20), font=font)
        # Draw pokemon HP bar
        draw_hp_bar(screen, 100, pos=(SCREEN_WIDTH - 160, 20), size=(150, 20), font=font)

        pygame.display.flip()
        clock.tick(60)
