import pygame
import random
import math
from config import SCREEN_WIDTH, SCREEN_HEIGHT

def draw_victory_animation(screen, pokeball_sprite):
    stars = []
    for _ in range(20):
        stars.append({
            "x": SCREEN_WIDTH // 2,
            "y": SCREEN_HEIGHT // 2,
            "angle": random.uniform(0, 2 * math.pi),
            "speed": random.uniform(2, 5),
            "radius": 1
        })

    start_time = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start_time < 1000:
        screen.fill((200, 220, 255))
        if pokeball_sprite:
            pokeball_rect = pokeball_sprite.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(pokeball_sprite, pokeball_rect)

        for star in stars:
            star["x"] += math.cos(star["angle"]) * star["speed"]
            star["y"] += math.sin(star["angle"]) * star["speed"]
            star["radius"] += 0.1
            pygame.draw.circle(screen, (255, 255, 0), (int(star["x"]), int(star["y"])), int(star["radius"]))

        pygame.display.flip()
        pygame.time.Clock().tick(60)

def draw_lose_animation(screen, pokeball_sprite):
    original_size = pokeball_sprite.get_size()
    start_time = pygame.time.get_ticks()
    duration = 1000  # 1 seconde

    while True:
        elapsed = pygame.time.get_ticks() - start_time
        if elapsed > duration:
            break

        progress = elapsed / duration
        new_size = (int(original_size[0] * (1 - progress)), int(original_size[1] * (1 - progress)))
        
        if new_size[0] <= 0 or new_size[1] <= 0:
            break

        scaled_sprite = pygame.transform.scale(pokeball_sprite, new_size)
        
        screen.fill((200, 220, 255))
        pokeball_rect = scaled_sprite.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(scaled_sprite, pokeball_rect)
        pygame.display.flip()
        pygame.time.Clock().tick(60)

def intro_animation(screen, pokeball_sprite, pokemon_sprite):
    clock = pygame.time.Clock()
    pokeball_pos = [SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 - 100]  # pokeball en haut à gauche
    pokemon_start = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80]         # Pokémon en bas au centre
    pokemon_end = pokeball_pos
    duration = 90  # frames (~1.5s)
    start_size = 120
    end_size = 40
    glow_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA) # Create glow_surf once

    # Initialize scaled_pokemon_sprite for optimized scaling
    scaled_pokemon_sprite = None

    for t in range(duration):
        progress = t / duration
        x = int(pokemon_start[0] + (pokemon_end[0] - pokemon_start[0]) * progress)
        y = int(pokemon_start[1] + (pokemon_end[1] - pokemon_start[1]) * progress)
        size = int(start_size + (end_size - start_size) * progress)
        screen.fill((200, 220, 255))
        # Glow effect (simplified)
        glow_surf.fill((0, 0, 0, 0)) # Clear the glow surface each frame
        glow_val = 10 # Fixed glow thickness
        alpha_val = max(30, 180 - glow_val*8) # Calculate alpha for fixed glow
        pygame.draw.line(glow_surf, (0,255,255,alpha_val), pokeball_pos, [x, y], glow_val)
        screen.blit(glow_surf, (0,0))
        pulse = 8 + int(4 * math.sin(t/6.0))
        pygame.draw.line(screen, (0,255,255), pokeball_pos, [x, y], pulse)
        pygame.draw.line(screen, (255,255,255), pokeball_pos, [x, y], 2)
        # Pokeball
        if pokeball_sprite:
            rect = pokeball_sprite.get_rect(center=pokeball_pos)
            screen.blit(pokeball_sprite, rect)
        # Pokémon animé - Optimized scaling
        if pokemon_sprite:
            # Only scale every 5 frames
            if t % 5 == 0:
                scaled_pokemon_sprite = pygame.transform.scale(pokemon_sprite, (size, size))

            if scaled_pokemon_sprite: # Ensure it's not None
                rect = scaled_pokemon_sprite.get_rect(center=(x, y))
                screen.blit(scaled_pokemon_sprite, rect)
        pygame.display.flip()
        clock.tick(60)

    # Descente de la pokeball au centre avec rebonds
    start_pos = pokeball_pos
    end_pos = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2]
    bounce_height = 60
    bounce_count = 2
    bounce_frames = 60
    for b in range(bounce_count):
        for t in range(bounce_frames):
            progress = t / bounce_frames
            # Mouvement vertical avec rebond
            x = int(start_pos[0] + (end_pos[0] - start_pos[0]) * progress)
            # Animation rebond : parabole
            y = int(start_pos[1] + (end_pos[1] - start_pos[1]) * progress - bounce_height * math.sin(math.pi * progress))
            screen.fill((200, 220, 255))
            if pokeball_sprite:
                rect = pokeball_sprite.get_rect(center=(x, y))
                screen.blit(pokeball_sprite, rect)
            pygame.display.flip()
            clock.tick(60)
        # Réduire la hauteur du rebond à chaque fois
        start_pos = [x, end_pos[1]]
        bounce_height = bounce_height // 2
    # Dernière descente douce
    for t in range(30):
        progress = t / 30
        x = int(start_pos[0] + (end_pos[0] - start_pos[0]) * progress)
        y = int(start_pos[1] + (end_pos[1] - start_pos[1]) * progress)
        screen.fill((200, 220, 255))
        if pokeball_sprite:
            rect = pokeball_sprite.get_rect(center=(x, y))
            screen.blit(pokeball_sprite, rect)
        pygame.display.flip()
        clock.tick(60)
    # Les étapes 2 et 3 sont maintenant gérées par le déplacement du Pokémon vers la pokeball

def run(screen, font, pokeball_sprite, pokemon_sprite=None):
    if pokemon_sprite:
        intro_animation(screen, pokeball_sprite, pokemon_sprite)
    timing_hits = 0
    lives = 3
    bar_cursor_x = 0
    bar_cursor_speed = 3
    
    shake_angle = 0
    shake_offset = 0
    shake_speed = 3
    shake_magnitude = 5

    def new_green_zone():
        green_zone_width = 100
        green_zone_x = random.randint(0, SCREEN_WIDTH - green_zone_width)
        return pygame.Rect(green_zone_x, SCREEN_HEIGHT - 30, green_zone_width, 20)

    green_zone_rect = new_green_zone()
    clock = pygame.time.Clock()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_n:
                    cursor_rect = pygame.Rect(bar_cursor_x, SCREEN_HEIGHT - 30, 5, 20)
                    if cursor_rect.colliderect(green_zone_rect):
                        timing_hits += 1
                        if timing_hits < 3:
                            green_zone_rect = new_green_zone()
                    else:
                        lives -= 1
                        if lives == 0:
                            draw_lose_animation(screen, pokeball_sprite)
                            return "failed"
                if event.key == pygame.K_m:
                    return "back"

        bar_cursor_x += bar_cursor_speed
        if bar_cursor_x > SCREEN_WIDTH or bar_cursor_x < 0:
            bar_cursor_speed = -bar_cursor_speed
        
        # Shake animation
        time_in_seconds = pygame.time.get_ticks() / 1000.0
        shake_angle = math.sin(time_in_seconds * shake_speed) * shake_magnitude
        shake_offset_x = math.cos(time_in_seconds * shake_speed * 0.7) * shake_magnitude
        shake_offset_y = math.sin(time_in_seconds * shake_speed * 0.5) * shake_magnitude

        if timing_hits >= 3:
            draw_victory_animation(screen, pokeball_sprite)
            return "caught"

        screen.fill((200, 220, 255))
        if pokeball_sprite:
            rotated_pokeball = pygame.transform.rotate(pokeball_sprite, shake_angle)
            pokeball_rect = rotated_pokeball.get_rect(center=(SCREEN_WIDTH // 2 + shake_offset_x, SCREEN_HEIGHT // 2 + shake_offset_y))
            screen.blit(rotated_pokeball, pokeball_rect)
        
        bar_rect = pygame.Rect(0, SCREEN_HEIGHT - 30, SCREEN_WIDTH, 20)
        pygame.draw.rect(screen, (100, 100, 100), bar_rect)
        pygame.draw.rect(screen, (0, 255, 0), green_zone_rect)
        cursor_rect = pygame.Rect(bar_cursor_x, SCREEN_HEIGHT - 30, 5, 20)
        pygame.draw.rect(screen, (255, 0, 0), cursor_rect)

        font.render("Appuyez sur Espace dans la zone verte !", True, (0,0,0))
        screen.blit(font.render("Appuyez sur Espace dans la zone verte !", True, (0,0,0)), (20, 20))
        font.render(f"Succès: {timing_hits} / 3", True, (0,0,0))
        screen.blit(font.render(f"Succès: {timing_hits} / 3", True, (0,0,0)), (20, 50))
        font.render(f"Vies: {lives}", True, (0,0,0))
        screen.blit(font.render(f"Vies: {lives}", True, (0,0,0)), (20, 80))

        pygame.display.flip()
        clock.tick(60)
