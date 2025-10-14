import pygame
import random
import math
from config import SCREEN_WIDTH, SCREEN_HEIGHT, KEY_MAPPINGS
import controls

def draw_victory_animation(screen, font, pokeball_sprite, background_image, dresseur_front_sprite, pokemon_sprite, game_state):
    """A full, redesigned victory animation sequence."""
    game_state.play_victory_song()
    start_time = pygame.time.get_ticks()
    duration = 4000 # 4-second animation

    # Create a larger font for the "ATTRAPÉ !" text
    try:
        large_font = pygame.font.Font(None, 60) # Using default font, size 60
    except:
        large_font = font # Fallback to the passed font

    # Star properties
    stars = []
    star_spawn_time = 500 # ms after start
    stars_spawned = False

    # Text properties
    text_appear_time = 1200 # ms after start

    clock = pygame.time.Clock()

    while pygame.time.get_ticks() - start_time < duration:
        elapsed_time = pygame.time.get_ticks() - start_time

        # --- Drawing --- 
        # Always draw the background first
        if background_image:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill((20, 20, 30)) # Fallback color

        # Phase 1: The pokeball clicks and settles (first 500ms)
        pokeball_rect = pokeball_sprite.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        if elapsed_time < 200:
            # Slight shake before the click
            offset_x = random.randint(-1, 1)
            offset_y = random.randint(-1, 1)
            screen.blit(pokeball_sprite, (pokeball_rect.x + offset_x, pokeball_rect.y + offset_y))
        else:
            # Still pokeball after the click
            screen.blit(pokeball_sprite, pokeball_rect)

        # Phase 2: Starburst (after 500ms)
        if elapsed_time > star_spawn_time and not stars_spawned:
            # Spawn 6 stylized stars
            for i in range(6):
                angle = (i * 60 + random.randint(-10, 10)) * (math.pi / 180)
                stars.append({
                    "pos": [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2],
                    "angle": angle,
                    "speed": random.uniform(3, 5),
                    "size": random.uniform(15, 25),
                    "life": 1000 # live for 1 second
                })
            stars_spawned = True

        # Update and draw stars
        if stars_spawned:
            for star in stars[:]:
                star["pos"][0] += math.cos(star["angle"]) * star["speed"]
                star["pos"][1] += math.sin(star["angle"]) * star["speed"]
                star["life"] -= clock.get_time()
                if star["life"] <= 0:
                    stars.remove(star)
                else:
                    # Draw a simple 4-point star polygon
                    size = star["size"] * (star["life"] / 1000) # Shrink as it dies
                    points = [
                        (star["pos"][0], star["pos"][1] - size),
                        (star["pos"][0] + size * 0.3, star["pos"][1] - size * 0.3),
                        (star["pos"][0] + size, star["pos"][1]),
                        (star["pos"][0] + size * 0.3, star["pos"][1] + size * 0.3),
                        (star["pos"][0], star["pos"][1] + size),
                        (star["pos"][0] - size * 0.3, star["pos"][1] + size * 0.3),
                        (star["pos"][0] - size, star["pos"][1]),
                        (star["pos"][0] - size * 0.3, star["pos"][1] - size * 0.3),
                    ]
                    pygame.draw.polygon(screen, (255, 255, 0), points)
                    pygame.draw.polygon(screen, (255, 255, 255), points, 2)

        # Phase 3: "ATTRAPÉ !" text and Dresseur
        if elapsed_time > text_appear_time:
            # Draw Dresseur
            if dresseur_front_sprite:
                d_rect = dresseur_front_sprite.get_rect(center=(SCREEN_WIDTH * 0.25, SCREEN_HEIGHT * 0.7))
                screen.blit(dresseur_front_sprite, d_rect)
            
            # Draw Text
            text_surf = large_font.render("ATTRAPÉ !", True, (255, 255, 0)) # Yellow text
            outline_surf = large_font.render("ATTRAPÉ !", True, (0, 0, 139)) # Dark blue outline
            text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.2))
            
            # Blit outlines by offset
            screen.blit(outline_surf, (text_rect.x - 2, text_rect.y - 2))
            screen.blit(outline_surf, (text_rect.x + 2, text_rect.y - 2))
            screen.blit(outline_surf, (text_rect.x - 2, text_rect.y + 2))
            screen.blit(outline_surf, (text_rect.x + 2, text_rect.y + 2))
            screen.blit(text_surf, text_rect)

        pygame.display.flip()
        clock.tick(60)

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
    draw_victory_animation(screen, font, pokeball_sprite, background_image, dresseur_front_sprite, pokemon_sprite, game_state)
    return "caught"

def run(screen, font, pokeball_sprite, pokemon_sprite, background_image, dresseur_front_sprite, game_state):
    if pokemon_sprite:
        intro_animation(screen, pokeball_sprite, pokemon_sprite, background_image, dresseur_front_sprite)

    timing_hits = 0
    lives = 3
    
    # --- Poké-Lock Gameplay Variables ---
    track_height = SCREEN_HEIGHT // 2 + 100  # Moved lower
    pokeball_y = track_height
    pokeball_x = 0
    pokeball_speed = 5
    
    moving_pokeball_sprite = game_state.pokeball_img_small
    if moving_pokeball_sprite is None:
        moving_pokeball_sprite = pygame.transform.scale(pokeball_sprite, (25, 25))

    target_zone_width = 150
    target_zone_height = 40
    target_zone_x = (SCREEN_WIDTH - target_zone_width) // 2
    target_zone_rect = pygame.Rect(target_zone_x, track_height - target_zone_height // 2, target_zone_width, target_zone_height)
    
    shake_angle = 0
    shake_speed = 5
    shake_magnitude = 5

    clock = pygame.time.Clock()
    
    while True:
        for event in pygame.event.get():
            controls.process_joystick_input(game_state, event)
            if event.type == pygame.QUIT:
                pygame.mixer.music.stop()
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key in KEY_MAPPINGS["CONFIRM"]:
                    if target_zone_rect.left < pokeball_x < target_zone_rect.right:
                        timing_hits += 1
                        target_zone_rect.width = max(30, target_zone_rect.width * 0.75)
                        target_zone_rect.centerx = SCREEN_WIDTH // 2
                        pokeball_speed *= 1.2
                    else:
                        lives -= 1
                        if lives == 0:
                            draw_lose_animation(screen, pokeball_sprite, game_state)
                            return "failed"
                if event.key in KEY_MAPPINGS["CANCEL"] or event.key in KEY_MAPPINGS["QUIT"]:
                    pygame.mixer.music.stop()
                    return "back"

        pokeball_x += pokeball_speed
        if pokeball_x > SCREEN_WIDTH or pokeball_x < 0:
            pokeball_speed = -pokeball_speed
        
        time_in_seconds = pygame.time.get_ticks() / 1000.0
        shake_angle = math.sin(time_in_seconds * shake_speed) * shake_magnitude
        shake_offset_x = math.cos(time_in_seconds * shake_speed * 0.7) * shake_magnitude
        shake_offset_y = math.sin(time_in_seconds * shake_speed * 0.5) * shake_magnitude

        if timing_hits >= 3:
            draw_victory_animation(screen, font, pokeball_sprite, background_image, dresseur_front_sprite, pokemon_sprite, game_state)
            return "caught"

        # --- Drawing ---
        if background_image:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill((200, 220, 255))

        if dresseur_front_sprite:
            screen.blit(dresseur_front_sprite, (10, SCREEN_HEIGHT - dresseur_front_sprite.get_height() - 10))
        
        if pokeball_sprite:
            rotated_pokeball = pygame.transform.rotate(pokeball_sprite, shake_angle)
            pokeball_rect = rotated_pokeball.get_rect(center=(SCREEN_WIDTH // 2 + shake_offset_x, SCREEN_HEIGHT // 2 + shake_offset_y))
            screen.blit(rotated_pokeball, pokeball_rect)
        
        # --- Draw New UI Elements ---
        glow_color = (255, 80, 80, 60)  # Reddish glow
        for i in range(5, 0, -1):
            glow_rect = target_zone_rect.inflate(i*4, i*4)
            pygame.draw.rect(screen, glow_color, glow_rect, border_radius=15)

        pygame.draw.rect(screen, (255, 255, 255), target_zone_rect, 3, border_radius=12) # White border

        if moving_pokeball_sprite:
            moving_rect = moving_pokeball_sprite.get_rect(center=(pokeball_x, pokeball_y))
            screen.blit(moving_pokeball_sprite, moving_rect)

        # Draw timing hits indicators as pokeballs
        indicator_y = track_height - 60
        if game_state.pokeball_img_small:
            pokeball_indicator_sprite = pygame.transform.scale(game_state.pokeball_img_small, (24, 24))
            for i in range(3):
                pos = (SCREEN_WIDTH // 2 - 45 + i * 40, indicator_y)
                screen.blit(pokeball_indicator_sprite, pos)
                if i >= timing_hits:
                    # Darken the sprite if the hit is not yet achieved
                    darken_surface = pygame.Surface(pokeball_indicator_sprite.get_size(), pygame.SRCALPHA)
                    darken_surface.fill((0, 0, 0, 180))
                    screen.blit(darken_surface, pos)

        # Draw lives
        if game_state.pokeball_img_small:
            for i in range(lives):
                screen.blit(game_state.pokeball_img_small, (10 + i * 35, 10))

        pygame.display.flip()
        clock.tick(60)




