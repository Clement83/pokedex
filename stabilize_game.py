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

def run(screen, font, pokeball_sprite):
    timing_hits = 0
    lives = 3
    bar_cursor_x = 0
    bar_cursor_speed = 5
    
    shake_angle = 0
    shake_offset = 0
    shake_speed = 3
    shake_magnitude = 5

    def new_green_zone():
        green_zone_width = 50
        green_zone_x = random.randint(0, SCREEN_WIDTH - green_zone_width)
        return pygame.Rect(green_zone_x, SCREEN_HEIGHT - 30, green_zone_width, 20)

    green_zone_rect = new_green_zone()
    clock = pygame.time.Clock()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
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
                if event.key == pygame.K_ESCAPE:
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
