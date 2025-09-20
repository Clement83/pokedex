import pygame
import random
import math
from config import SCREEN_WIDTH, SCREEN_HEIGHT, KEY_MAPPINGS
import controls

def draw_victory_animation(screen, pokeball_sprite, game_state):
    game_state.play_victory_song()
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

def draw_lose_animation(screen, pokeball_sprite, game_state):
    pygame.mixer.music.stop()
    game_state.play_next_menu_song()
    original_size = pokeball_sprite.get_size()
    start_time = pygame.time.get_ticks()
    duration = 1000

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

def intro_animation(screen, pokeball_sprite, pokemon_sprite, background_image, dresseur_front_sprite):
    clock = pygame.time.Clock()
    pokeball_pos = [SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 - 100]
    pokemon_start = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80]
    pokemon_end = pokeball_pos
    duration = 60
    start_size = 120
    end_size = 40
    glow_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    scaled_pokemon_sprite = None

    for t in range(duration):
        progress = t / duration
        x = int(pokemon_start[0] + (pokemon_end[0] - pokemon_start[0]) * progress)
        y = int(pokemon_start[1] + (pokemon_end[1] - pokemon_start[1]) * progress)
        size = int(start_size + (end_size - start_size) * progress)
        
        # Draw background and dresseur sprite
        if background_image:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill((200, 220, 255)) # Fallback to default background

        if dresseur_front_sprite:
            screen.blit(dresseur_front_sprite, (10, SCREEN_HEIGHT - dresseur_front_sprite.get_height() - 10)) # Bottom-left corner

        pygame.draw.line(screen, (0,255,255), pokeball_pos, [x, y], 10)
        pulse = 8 + int(4 * math.sin(t/6.0))
        pygame.draw.line(screen, (0,255,255), pokeball_pos, [x, y], pulse)
        pygame.draw.line(screen, (255,255,255), pokeball_pos, [x, y], 2)
        if pokeball_sprite:
            rect = pokeball_sprite.get_rect(center=pokeball_pos)
            screen.blit(pokeball_sprite, rect)
        if pokemon_sprite:
            if t % 5 == 0:
                scaled_pokemon_sprite = pygame.transform.scale(pokemon_sprite, (size, size))

            if scaled_pokemon_sprite:
                rect = scaled_pokemon_sprite.get_rect(center=(x, y))
                screen.blit(scaled_pokemon_sprite, rect)
        pygame.display.flip()
        clock.tick(60)

    start_pos = pokeball_pos
    end_pos = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2]
    bounce_height = 60
    bounce_count = 2
    bounce_frames = 40
    for b in range(bounce_count):
        for t in range(bounce_frames):
            progress = t / bounce_frames
            x = int(start_pos[0] + (end_pos[0] - start_pos[0]) * progress)
            y = int(start_pos[1] + (end_pos[1] - start_pos[1]) * progress - bounce_height * math.sin(math.pi * progress))
            
            # Draw background and dresseur sprite
            if background_image:
                screen.blit(background_image, (0, 0))
            else:
                screen.fill((200, 220, 255)) # Fallback to default background

            if dresseur_front_sprite:
                screen.blit(dresseur_front_sprite, (10, SCREEN_HEIGHT - dresseur_front_sprite.get_height() - 10)) # Bottom-left corner

            if pokeball_sprite:
                rect = pokeball_sprite.get_rect(center=(x, y))
                screen.blit(pokeball_sprite, rect)
            pygame.display.flip()
            clock.tick(60)
        start_pos = [x, end_pos[1]]
        bounce_height = bounce_height // 2
    for t in range(20):
        progress = t / 30
        x = int(start_pos[0] + (end_pos[0] - start_pos[0]) * progress)
        y = int(start_pos[1] + (end_pos[1] - start_pos[1]) * progress)
        
        # Draw background and dresseur sprite
        if background_image:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill((200, 220, 255)) # Fallback to default background

        if dresseur_front_sprite:
            screen.blit(dresseur_front_sprite, (10, SCREEN_HEIGHT - dresseur_front_sprite.get_height() - 10)) # Bottom-left corner

        if pokeball_sprite:
            rect = pokeball_sprite.get_rect(center=(x, y))
            screen.blit(pokeball_sprite, rect)
        pygame.display.flip()
        clock.tick(60)

def run_intro_only(screen, font, pokeball_sprite, pokemon_sprite, background_image, dresseur_front_sprite, game_state):
    intro_animation(screen, pokeball_sprite, pokemon_sprite, background_image, dresseur_front_sprite)
    draw_victory_animation(screen, pokeball_sprite, game_state)
    return "caught"

def run(screen, font, pokeball_sprite, pokemon_sprite, background_image, dresseur_front_sprite, game_state):
    if pokemon_sprite:
        intro_animation(screen, pokeball_sprite, pokemon_sprite, background_image, dresseur_front_sprite)
    timing_hits = 0
    lives = 3
    bar_cursor_x = 0
    bar_cursor_speed = 5
    
    shake_angle = 0
    shake_offset = 0
    shake_speed = 5
    shake_magnitude = 5

    def new_green_zone():
        green_zone_width = 100
        green_zone_x = random.randint(0, SCREEN_WIDTH - green_zone_width)
        return pygame.Rect(green_zone_x, SCREEN_HEIGHT - 30, green_zone_width, 20)

    green_zone_rect = new_green_zone()
    clock = pygame.time.Clock()
    
    while True:
        for event in pygame.event.get():
            controls.process_joystick_input(game_state, event)
            if event.type == pygame.QUIT:
                pygame.mixer.music.stop()
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key in KEY_MAPPINGS["CONFIRM"]:
                    cursor_rect = pygame.Rect(bar_cursor_x, SCREEN_HEIGHT - 30, 5, 20)
                    if cursor_rect.colliderect(green_zone_rect):
                        timing_hits += 1
                        if timing_hits < 3:
                            green_zone_rect = new_green_zone()
                    else:
                        lives -= 1
                        if lives == 0:
                            draw_lose_animation(screen, pokeball_sprite, game_state)
                            # pygame.mixer.music.stop()
                            return "failed"
                if event.key in KEY_MAPPINGS["CANCEL"] or event.key in KEY_MAPPINGS["QUIT"]:
                    pygame.mixer.music.stop()
                    return "back"

        bar_cursor_x += bar_cursor_speed
        if bar_cursor_x > SCREEN_WIDTH or bar_cursor_x < 0:
            bar_cursor_speed = -bar_cursor_speed
        
        time_in_seconds = pygame.time.get_ticks() / 1000.0
        shake_angle = math.sin(time_in_seconds * shake_speed) * shake_magnitude
        shake_offset_x = math.cos(time_in_seconds * shake_speed * 0.7) * shake_magnitude
        shake_offset_y = math.sin(time_in_seconds * shake_speed * 0.5) * shake_magnitude

        if timing_hits >= 3:
            draw_victory_animation(screen, pokeball_sprite, game_state)
            # pygame.mixer.music.stop()
            return "caught"

        if background_image:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill((200, 220, 255)) # Fallback to default background

        if dresseur_front_sprite:
            screen.blit(dresseur_front_sprite, (10, SCREEN_HEIGHT - dresseur_front_sprite.get_height() - 10)) # Bottom-left corner
        if pokeball_sprite:
            rotated_pokeball = pygame.transform.rotate(pokeball_sprite, shake_angle)
            pokeball_rect = rotated_pokeball.get_rect(center=(SCREEN_WIDTH // 2 + shake_offset_x, SCREEN_HEIGHT // 2 + shake_offset_y))
            screen.blit(rotated_pokeball, pokeball_rect)
        
        bar_rect = pygame.Rect(0, SCREEN_HEIGHT - 30, SCREEN_WIDTH, 20)
        pygame.draw.rect(screen, (100, 100, 100), bar_rect)
        pygame.draw.rect(screen, (0, 255, 0), green_zone_rect)
        cursor_rect = pygame.Rect(bar_cursor_x, SCREEN_HEIGHT - 30, 5, 20)
        pygame.draw.rect(screen, (255, 0, 0), cursor_rect)

        

        pygame.display.flip()
        clock.tick(60)