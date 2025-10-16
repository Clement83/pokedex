import pygame
import random
from config import SCREEN_WIDTH, SCREEN_HEIGHT, KEY_MAPPINGS
import controls
from ui import draw_hp_bar, draw_rounded_rect

# Game settings
SEQUENCE_LENGTH = 4  # Fixed length of 4 steps

TIME_PER_INPUT_MS = 3000  # 3 seconds per input
SHOW_DURATION_MS = 500
PAUSE_DURATION_MS = 250

ARROW_SIZE = 50

def create_arrow_surface(direction, size, color):
    """Draws a Pokémon-style arrow on a new surface."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Background
    bg_color = (23, 23, 115) # Dark blue
    border_color = (179, 179, 255) # Light blue
    draw_rounded_rect(surf, bg_color, surf.get_rect(), radius=8, border=3, border_color=border_color)

    # Arrow
    s = size
    padding = int(s * 0.25)
    arrow_color = (255, 255, 0) # Bright yellow

    if direction == "UP":
        points = [(s/2, padding), (s - padding, s/2), (padding, s/2)]
    elif direction == "DOWN":
        points = [(s/2, s - padding), (s - padding, s/2), (padding, s/2)]
    elif direction == "LEFT":
        points = [(padding, s/2), (s/2, padding), (s/2, s - padding)]
    elif direction == "RIGHT":
        points = [(s - padding, s/2), (s/2, padding), (s/2, s - padding)]

    pygame.draw.polygon(surf, arrow_color, points)
    return surf

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
                            return "win"
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
            else:
                game_phase = "INPUT"
                phase_timer = current_time
        elif game_phase == "INPUT":
            if not game_over and current_time - phase_timer > time_limit:
                player_hp = 0
                game_over = True

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

        elif game_phase == "SHOWING" and sequence_index < len(sequence):
            if current_time - phase_timer < SHOW_DURATION_MS:
                arrow_name = sequence[sequence_index][0]
                arrow_img = arrow_surfaces[arrow_name]
                screen.blit(arrow_img, arrow_img.get_rect(center=arrow_pos))

        elif game_phase == "INPUT":
            turn_text = font.render("À vous !", True, (255, 255, 255))
            screen.blit(turn_text, turn_text.get_rect(center=(SCREEN_WIDTH // 2, 100)))
            
            progress_y = SCREEN_HEIGHT - ARROW_SIZE - 40
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


        # Draw player HP bar
        draw_hp_bar(screen, player_hp_percent, pos=(20, 20), size=(150, 20), font=font)
        # Draw pokemon HP bar
        draw_hp_bar(screen, 100, pos=(SCREEN_WIDTH - 160, 20), size=(150, 20), font=font)

        pygame.display.flip()
        clock.tick(60)
