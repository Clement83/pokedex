import pygame
import random
from config import SCREEN_WIDTH, SCREEN_HEIGHT, KEY_MAPPINGS
import controls

# Game settings
BASE_SPEED = 5
# Speed multipliers based on catch rate
SPEED_MULTIPLIER_RARE = 1.5  # catch_rate < 100
SPEED_MULTIPLIER_LEGENDARY = 2.0  # catch_rate < 45

def run(screen, font, game_state, pokemon_sprite, dresseur_sprite, background_image, pokemon_types, full_pokemon_data):
    """Runs the QTE reflex mini-game."""
    clock = pygame.time.Clock()

    # Determine speed based on rarity from the full pokemon data
    catch_rate = full_pokemon_data.get('catch_rate', 255)
    speed = BASE_SPEED
    if catch_rate < 45:
        speed *= SPEED_MULTIPLIER_LEGENDARY
    elif catch_rate < 100:
        speed *= SPEED_MULTIPLIER_RARE

    # Target zone setup
    target_width = 80
    target_height = 100
    target_x = (SCREEN_WIDTH - target_width) // 2
    target_y = (SCREEN_HEIGHT - target_height) // 2
    target_zone = pygame.Rect(target_x, target_y, target_width, target_height)
    target_color = (255, 255, 0, 100)  # Semi-transparent yellow

    # Pokemon setup
    pokemon_rect = pokemon_sprite.get_rect(centery=target_zone.centery)
    pokemon_rect.left = 0
    
    # Add a small grace period at the start
    start_time = pygame.time.get_ticks()
    grace_period_ms = 500

    while True:
        for event in pygame.event.get():
            controls.process_joystick_input(game_state, event)
            if event.type == pygame.QUIT: return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key in KEY_MAPPINGS["QUIT"]: return "quit"
                if event.key in KEY_MAPPINGS["CANCEL"]: return "lose"
                if event.key in KEY_MAPPINGS["CONFIRM"]:
                    if pygame.time.get_ticks() - start_time < grace_period_ms:
                        continue # Ignore input during grace period
                    if target_zone.colliderect(pokemon_rect):
                        return "win"
                    else:
                        return "lose"

        # Update pokemon position
        pokemon_rect.x += speed
        if pokemon_rect.left <= 0 or pokemon_rect.right >= SCREEN_WIDTH:
            speed *= -1
            pokemon_rect.x += speed

        # --- Drawing ---
        if background_image:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill((20, 20, 30))

        # Draw target zone
        target_surface = pygame.Surface(target_zone.size, pygame.SRCALPHA)
        target_surface.fill(target_color)
        screen.blit(target_surface, target_zone.topleft)
        pygame.draw.rect(screen, (255, 255, 0), target_zone, 3) # Border

        # Draw pokemon
        screen.blit(pokemon_sprite, pokemon_rect)
        
        # Draw instructions
        instruction_text = font.render("Appuyez sur CONFIRMER dans la zone !", True, (255, 255, 255))
        text_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
        screen.blit(instruction_text, text_rect)

        pygame.display.flip()
        clock.tick(60)
