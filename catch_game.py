import pygame
import math
import random
from pathlib import Path
from config import SCREEN_WIDTH, SCREEN_HEIGHT, KEY_MAPPINGS, REGION_MUSIC
import controls
from sprites import load_sprite

def run(screen, font, pokemon_sprite, pokeball_sprite, region_name, dresseur_sprite, game_state):
    # Start battle music
    if region_name in REGION_MUSIC and REGION_MUSIC[region_name]:
        music_file = random.choice(REGION_MUSIC[region_name])
        music_path = Path.cwd() / "pokemon_audio" / music_file
        if music_path.exists():
            pygame.mixer.music.load(str(music_path))
            pygame.mixer.music.set_volume(game_state.music_volume)
            pygame.mixer.music.play(-1)  # -1 for looping

    if pokeball_sprite:
        pokeball_sprite = pygame.transform.scale(pokeball_sprite, (20, 20))
    BASE_DIR = Path.cwd()
    
    dresseur_front_sprite = None
    if game_state.dresseur:
        dresseur_front_path = BASE_DIR / "app" / "data" / "assets" / "dresseurs" / game_state.dresseur / "face.png"
        dresseur_front_sprite = load_sprite(dresseur_front_path)
    stadium_path = BASE_DIR / "app" / "data" / "assets" / region_name.lower() / "stadium"
    background_image = None
    if stadium_path.is_dir():
        stadium_images = list(stadium_path.glob('*.png')) # Or other image extensions
        if stadium_images:
            random_bg_path = random.choice(stadium_images)
            try:
                background_image = pygame.image.load(random_bg_path).convert()
                background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except pygame.error:
                print(f"Erreur de chargement de l'image de fond: {random_bg_path}")
                background_image = None

    if background_image is None:
        # Fallback to a solid color or default image if no stadium image is found
        BG_PATH = BASE_DIR / "app" / "data" / "assets" / "out.png"
        try:
            background_image = pygame.image.load(BG_PATH).convert()
            background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except pygame.error:
            print(f"Erreur de chargement de l'image de fond par défaut: {BG_PATH}")
            background_image = None

    clock = pygame.time.Clock()
    attempts = 0
    max_attempts = 3
    angle = 45  # degrés, direction du tir
    min_angle = 10
    max_angle = 80
    power = 0
    max_power = 400
    charging = False
    if dresseur_sprite:
        pokeball_pos = [10 + dresseur_sprite.get_width(), SCREEN_HEIGHT - dresseur_sprite.get_height() // 2 - 10]
    else:
        pokeball_pos = [160, SCREEN_HEIGHT - 80]

    move_area = pygame.Rect(200, 40, SCREEN_WIDTH - 240, SCREEN_HEIGHT - 120)
    pokemon_pos = [float(move_area.centerx), float(move_area.centery)]
    pokemon_target_pos = list(pokemon_pos)
    pokemon_state = "WAITING"
    pokemon_wait_end_time = pygame.time.get_ticks() + random.randint(1000, 3000)
    pokemon_speed = 40  # Pixels par seconde
    charging_speed = 200 # Unités de puissance par seconde

    caught = False
    result = None
    last_time = pygame.time.get_ticks()

    while not caught and attempts < max_attempts:
        charging = False
        power = 0
        launched = False
        while not launched:
            now = pygame.time.get_ticks()
            controls.process_joystick_input()

            dt = (now - last_time) / 1000.0
            last_time = now

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.mixer.music.stop()
                    return "quit"
                elif event.type == pygame.KEYDOWN:
                    if event.key in KEY_MAPPINGS["RIGHT"]:
                        angle = max(min_angle, angle - 2)
                    elif event.key in KEY_MAPPINGS["LEFT"]:
                        angle = min(max_angle, angle + 2)
                    elif event.key in KEY_MAPPINGS["CONFIRM"]:
                        charging = True
                    elif event.key in KEY_MAPPINGS["CANCEL"] or event.key in KEY_MAPPINGS["QUIT"]:
                        pygame.mixer.music.stop()
                        return "back"
                elif event.type == pygame.KEYUP:
                    if event.key in KEY_MAPPINGS["CONFIRM"] and charging:
                        launched = True
            
            if charging:
                power = min(max_power, power + charging_speed * dt)

            if pokemon_state == "WAITING":
                if now >= pokemon_wait_end_time:
                    pokemon_target_pos = [
                        random.randint(move_area.left, move_area.right),
                        random.randint(move_area.top, move_area.bottom)
                    ]
                    pokemon_state = "MOVING"
            elif pokemon_state == "MOVING":
                dir_vec = [pokemon_target_pos[0] - pokemon_pos[0], pokemon_target_pos[1] - pokemon_pos[1]]
                distance = math.hypot(dir_vec[0], dir_vec[1])
                move_dist = pokemon_speed * dt

                if distance < move_dist:
                    pokemon_pos = list(pokemon_target_pos)
                    pokemon_state = "WAITING"
                    pokemon_wait_end_time = now + random.randint(3000, 10000)
                else:
                    norm_vec = [dir_vec[0] / distance, dir_vec[1] / distance]
                    pokemon_pos[0] += norm_vec[0] * move_dist
                    pokemon_pos[1] += norm_vec[1] * move_dist
            
            if background_image:
                screen.blit(background_image, (0, 0))
            else:
                screen.fill((180, 220, 255))

            if dresseur_sprite:
                screen.blit(dresseur_sprite, (10, SCREEN_HEIGHT - dresseur_sprite.get_height() - 10))

            if pokemon_sprite:
                rect = pokemon_sprite.get_rect(center=(int(pokemon_pos[0]), int(pokemon_pos[1])))
                screen.blit(pokemon_sprite, rect)
            if pokeball_sprite:
                rect = pokeball_sprite.get_rect(center=pokeball_pos)
                screen.blit(pokeball_sprite, rect)

            rad = math.radians(angle)
            preview_power = power if charging else max_power // 5
            points = []
            pos = list(pokeball_pos)
            # La preview est calculée pour une durée fixe (1s) pour la cohérence
            preview_duration = 1.0
            vx = math.cos(rad) * preview_power * 3.5 / preview_duration
            vy = -math.sin(rad) * preview_power * 3.5 / preview_duration
            gravity = 0.5 * preview_power * 2.0 / preview_duration

            for t_step in range(60):
                t = t_step / 60.0 * preview_duration
                pos[0] = pokeball_pos[0] + vx * t
                pos[1] = pokeball_pos[1] + vy * t + 0.5 * gravity * t * t
                points.append((int(pos[0]), int(pos[1])))

            if len(points) > 1:
                pygame.draw.lines(screen, (255, 0, 0), False, points, 2)

            if pokeball_sprite:
                remaining_attempts = max_attempts - attempts
                pokeball_width = pokeball_sprite.get_width()
                for i in range(remaining_attempts):
                    screen.blit(pokeball_sprite, (10 + i * (pokeball_width + 5), 10))
            
            pygame.display.flip()
            clock.tick(60)

        # Animation du lancer
        throw_duration = 1.0  # secondes
        throw_timer = 0.0
        pos = list(pokeball_pos)
        rad = math.radians(angle)
        vx = math.cos(rad) * power * 3.5 / throw_duration
        vy = -math.sin(rad) * power * 3.5 / throw_duration
        gravity = 0.5 * power * 2.0 / throw_duration
        hit = False

        while throw_timer < throw_duration:
            now = pygame.time.get_ticks()
            dt = (now - last_time) / 1000.0
            last_time = now
            throw_timer += dt

            pos[0] = pokeball_pos[0] + vx * throw_timer
            pos[1] = pokeball_pos[1] + vy * throw_timer + 0.5 * gravity * throw_timer * throw_timer

            if background_image:
                screen.blit(background_image, (0, 0))
            else:
                screen.fill((180, 220, 255))

            if dresseur_sprite:
                screen.blit(dresseur_sprite, (10, SCREEN_HEIGHT - dresseur_sprite.get_height() - 10))

            if pokemon_sprite:
                rect = pokemon_sprite.get_rect(center=(int(pokemon_pos[0]), int(pokemon_pos[1])))
                screen.blit(pokemon_sprite, rect)
            if pokeball_sprite:
                rect = pokeball_sprite.get_rect(center=(int(pos[0]), int(pos[1])))
                screen.blit(pokeball_sprite, rect)
            
            pygame.display.flip()
            clock.tick(60)

            if abs(pos[0] - pokemon_pos[0]) < 32 and abs(pos[1] - pokemon_pos[1]) < 32:
                hit = True
                break
        
        attempts += 1
        if hit:
            caught = True
            result = "caught"
        else:
            result = "miss"
            
    return result, background_image, dresseur_front_sprite
