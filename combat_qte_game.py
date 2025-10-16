import pygame
import random
import math
from config import SCREEN_WIDTH, SCREEN_HEIGHT, KEY_MAPPINGS
import controls
from ui import draw_hp_bar

# Game settings
QTE_BUTTONS = ["UP", "DOWN", "LEFT", "RIGHT"]
PROMPT_SPEED_BASE = 3
# Predefined timing patterns for QTE prompts to create rhythmic sequences
QTE_TIMING_PATTERN = [
    150, 100, 250, 100, 150, 800, 100, 150, 100, 250,  # Fast, then slow break
    400, 150, 100, 750, 150, 100, 250, 150, 100, 900,  # Mixed with slow breaks
    500, 150, 100, 250, 150, 700, 300, 400, 150, 100,   # Varied, with slow breaks
    200, 100, 150, 100, 200, 850, 100, 150, 100, 200,   # Another fast, then slow
    600, 200, 100, 700, 200, 100, 200, 200, 100, 950,   # Some longer, some fast, with slow
    700, 200, 100, 250, 200, 800, 300, 500, 200, 100    # Varied, with slow breaks
]
HIT_ZONE_X = SCREEN_WIDTH // 2 - 25 # Center of the screen
HIT_ZONE_WIDTH = 50
MAX_MISSES = 3
SUCCESS_THRESHOLD = 10 # Number of successful hits to win
BUTTON_SIZE = 40
MIN_PROMPT_SPACING = BUTTON_SIZE # Minimum spacing between prompts to avoid overlap

# Speed multipliers based on catch rate
SPEED_MULTIPLIER_RARE = 1.2  # catch_rate < 100
SPEED_MULTIPLIER_LEGENDARY = 1.5  # catch_rate < 45

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

def create_button_surface(button_type, size, color):
    """Draws a simple button (A or B) on a new surface."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surf, color, (size // 2, size // 2), size // 2 - 2, 2) # Circle outline
    font_size = int(size * 0.6)
    font = pygame.font.Font(None, font_size)
    text_surf = font.render(button_type, True, color)
    text_rect = text_surf.get_rect(center=(size // 2, size // 2))
    surf.blit(text_surf, text_rect)
    return surf

HIT_EFFECT_DURATION_MS = 200 # How long the hit effect lasts
CLICK_ZONE_EFFECT_COLOR = (255, 255, 0, 128) # Yellow overlay for click zone

class QTEPrompt(pygame.sprite.Sprite):
    def __init__(self, button_type, image_surface, start_x, y_pos):
        super().__init__()
        self.button_type = button_type
        self.original_image = image_surface # Store original image
        self.image = image_surface
        self.rect = self.image.get_rect(center=(start_x, y_pos))
        self.hit = False # To track if this prompt has been successfully hit
        self.hit_effect_active = False
        self.hit_effect_start_time = 0

    def update(self, speed):
        self.rect.x -= speed

    def trigger_hit_effect(self):
        self.hit_effect_active = True
        self.hit_effect_start_time = pygame.time.get_ticks()

    def draw(self, screen, in_click_zone=False):
        current_image = self.original_image.copy()

        if self.hit_effect_active:
            elapsed_time = pygame.time.get_ticks() - self.hit_effect_start_time
            if elapsed_time < HIT_EFFECT_DURATION_MS:
                current_image.fill((0, 255, 0, 128), special_flags=pygame.BLEND_RGBA_ADD) # Green overlay for hit
            else:
                self.hit_effect_active = False # Effect ended

        if in_click_zone and not self.hit_effect_active: # Apply click zone effect only if not already hitting
            current_image.fill(CLICK_ZONE_EFFECT_COLOR, special_flags=pygame.BLEND_RGBA_ADD) # Yellow overlay for click zone

        screen.blit(current_image, self.rect)

class Feedback:
    def __init__(self, text, color, position, duration, font_size=30):
        self.text = text
        self.color = color
        self.position = list(position) # Make it mutable
        self.duration = duration # Milliseconds
        self.start_time = pygame.time.get_ticks()
        self.font_size = font_size

    def update(self):
        elapsed_time = pygame.time.get_ticks() - self.start_time
        if elapsed_time > self.duration:
            return False # Indicate that this feedback is expired

        # Move upwards and fade out slightly
        self.position[1] -= 0.5 # Move up
        return True

    def draw(self, screen, font):
        # Calculate alpha based on remaining time
        elapsed_time = pygame.time.get_ticks() - self.start_time
        remaining_time = self.duration - elapsed_time
        alpha = max(0, min(255, int(255 * (remaining_time / self.duration))))

        # Create a surface with alpha channel for the text
        text_surf = font.render(self.text, True, self.color)
        text_surf.set_alpha(alpha)

        text_rect = text_surf.get_rect(center=self.position)
        screen.blit(text_surf, text_rect)



def run(screen, font, game_state, pokemon_sprite, dresseur_sprite, background_image, pokemon_types, full_pokemon_data):
    """Runs the QTE rhythm mini-game."""
    clock = pygame.time.Clock()

    # Determine speed based on rarity from the full pokemon data
    catch_rate = full_pokemon_data.get('catch_rate', 255)
    prompt_speed = PROMPT_SPEED_BASE
    if catch_rate < 45:
        prompt_speed *= SPEED_MULTIPLIER_LEGENDARY
    elif catch_rate < 100:
        prompt_speed *= SPEED_MULTIPLIER_RARE

    # Pre-render all button surfaces
    button_surfaces = {}
    for btn_type in QTE_BUTTONS:
        if btn_type in ["UP", "DOWN", "LEFT", "RIGHT"]:
            button_surfaces[btn_type] = create_arrow_surface(btn_type, BUTTON_SIZE, (255, 255, 255))
        else: # A or B
            button_surfaces[btn_type] = create_button_surface(btn_type, BUTTON_SIZE, (255, 255, 255))

    active_prompts = pygame.sprite.Group()
    current_pattern_index = random.randint(0, len(QTE_TIMING_PATTERN) - 1)
    next_prompt_time = pygame.time.get_ticks() + QTE_TIMING_PATTERN[current_pattern_index]

    score = 0
    misses = 0
    player_hp_percent = 100.0
    game_over = False
    active_feedback = [] # List to hold active feedback messages

    pokemon_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    pokemon_rect = pokemon_sprite.get_rect(center=pokemon_pos)

    # Click zone rectangle (around the pokemon)
    click_zone_rect = pygame.Rect(pokemon_rect.centerx - BUTTON_SIZE // 2, pokemon_rect.centery - BUTTON_SIZE // 2, BUTTON_SIZE, BUTTON_SIZE)

    while True:
        current_time = pygame.time.get_ticks()

        # --- HP Bar Animation and Game Over Logic ---
        player_hp = MAX_MISSES - misses
        target_hp_percent = (player_hp / MAX_MISSES) * 100 if MAX_MISSES > 0 else 0
        if player_hp_percent > target_hp_percent:
            player_hp_percent -= 1.0  # Animation speed

        if game_over and player_hp_percent <= target_hp_percent:
            pygame.time.wait(500)
            return "lose"

        # --- Event Handling ---
        for event in pygame.event.get():
            controls.process_joystick_input(game_state, event)
            if event.type == pygame.KEYDOWN:

                if not game_over:
                    pressed_button_type = None
                    if event.key in KEY_MAPPINGS["UP"]: pressed_button_type = "UP"
                    elif event.key in KEY_MAPPINGS["DOWN"]: pressed_button_type = "DOWN"
                    elif event.key in KEY_MAPPINGS["LEFT"]: pressed_button_type = "LEFT"
                    elif event.key in KEY_MAPPINGS["RIGHT"]: pressed_button_type = "RIGHT"
                    elif event.key in KEY_MAPPINGS["CONFIRM"]: pressed_button_type = "A"
                    elif event.key in KEY_MAPPINGS["CANCEL"]: pressed_button_type = "B"

                    if pressed_button_type:
                        hit_found = False
                        for prompt in active_prompts:
                            if click_zone_rect.colliderect(prompt.rect) and prompt.button_type == pressed_button_type and not prompt.hit:
                                score += 1
                                active_feedback.append(Feedback("HIT!", (0, 255, 0), click_zone_rect.center, 700))
                                prompt.trigger_hit_effect()
                                prompt.hit = True
                                hit_found = True
                                break
                        if not hit_found:
                            misses += 1
                            active_feedback.append(Feedback("MISS!", (255, 0, 0), click_zone_rect.center, 700))

        if not game_over:
            # --- Prompt Spawning ---
            # --- Prompt Spawning ---
            if current_time >= next_prompt_time:
                can_spawn_physically = True
                if active_prompts:
                    rightmost_prompt = max(active_prompts, key=lambda p: p.rect.right)
                    # Check if the new prompt would overlap or be too close to the rightmost existing prompt
                    # The new prompt's left edge would be SCREEN_WIDTH - BUTTON_SIZE / 2
                    if rightmost_prompt.rect.right + MIN_PROMPT_SPACING > SCREEN_WIDTH - BUTTON_SIZE / 2:
                        can_spawn_physically = False

                if can_spawn_physically:
                    random_button = random.choice(QTE_BUTTONS)
                    new_prompt = QTEPrompt(random_button, button_surfaces[random_button], SCREEN_WIDTH, pokemon_rect.centery)
                    active_prompts.add(new_prompt)

                # ALWAYS update next_prompt_time, regardless of whether a prompt was actually spawned
                current_pattern_index = (current_pattern_index + 1) % len(QTE_TIMING_PATTERN)
                next_prompt_time = current_time + QTE_TIMING_PATTERN[current_pattern_index]

            # --- Update Prompts ---
            active_prompts.update(prompt_speed)

            for prompt in list(active_prompts):
                if prompt.rect.right < click_zone_rect.left and not prompt.hit:
                    misses += 1
                    prompt.kill()
                elif prompt.hit and not prompt.hit_effect_active:
                    prompt.kill()

            # --- Win/Lose Conditions ---
            if score >= SUCCESS_THRESHOLD:
                return "win"
            if misses >= MAX_MISSES:
                game_over = True

        # --- Drawing ---
        if background_image:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill((20, 20, 30))

        if dresseur_sprite:
            screen.blit(dresseur_sprite, (10, SCREEN_HEIGHT - dresseur_sprite.get_height() - 10))

        # Draw Pokémon
        screen.blit(pokemon_sprite, pokemon_rect)

        # # Draw hit zone (stylized target)
        # pygame.draw.line(screen, (255, 255, 0), (hit_zone_rect.centerx, hit_zone_rect.top), (hit_zone_rect.centerx, hit_zone_rect.bottom), 3)
        # pygame.draw.line(screen, (255, 255, 0), (hit_zone_rect.left, hit_zone_rect.centery), (hit_zone_rect.right, hit_zone_rect.centery), 3)
        # pygame.draw.circle(screen, (255, 255, 0), hit_zone_rect.center, hit_zone_rect.width // 2, 2) # Outer circle
        # pygame.draw.circle(screen, (255, 255, 0), hit_zone_rect.center, hit_zone_rect.width // 4, 2) # Inner circle

        # Draw active prompts
        for prompt in active_prompts:
            in_click_zone = click_zone_rect.colliderect(prompt.rect)
            prompt.draw(screen, in_click_zone=in_click_zone)

        # Draw the Pokemon HP bar
        draw_hp_bar(screen, 100, pos=(SCREEN_WIDTH - 160, 20), size=(150, 20), font=font)

        # Draw the Player HP bar
        draw_hp_bar(screen, player_hp_percent, pos=(20, 20), size=(150, 20), font=font)

        # Draw and update feedback messages
        for feedback in list(active_feedback): # Iterate over a copy to allow modification
            if feedback.update():
                feedback.draw(screen, font)
            else:
                active_feedback.remove(feedback)

        pygame.display.flip()
        clock.tick(60)
