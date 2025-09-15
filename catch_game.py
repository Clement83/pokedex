import pygame
import math
import random
from pathlib import Path
from config import SCREEN_WIDTH, SCREEN_HEIGHT

def run(screen, font, pokemon_sprite, pokeball_sprite):
    BASE_DIR = Path.cwd()
    BG_PATH = BASE_DIR / "app" / "data" / "assets" / "out.png"
    try:
        background_image = pygame.image.load(BG_PATH).convert()
        background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except pygame.error:
        print(f"Erreur de chargement de l'image de fond: {BG_PATH}")
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
    pokeball_pos = [160, SCREEN_HEIGHT - 80] # Position de départ de la pokeball

    # --- Logique de déplacement du Pokémon ---
    # Zone de déplacement en pixels (partie droite de l'écran)
    # On laisse une marge pour que le pokémon ne colle pas aux bords
    move_area = pygame.Rect(200, 40, SCREEN_WIDTH - 240, SCREEN_HEIGHT - 120)
    
    # Position et état du Pokémon en coordonnées pixel
    pokemon_pos = [float(move_area.centerx), float(move_area.centery)]
    pokemon_target_pos = list(pokemon_pos)
    pokemon_state = "WAITING"  # "MOVING" ou "WAITING"
    pokemon_wait_end_time = pygame.time.get_ticks() + random.randint(1000, 3000) # Attente initiale
    pokemon_speed = 40  # Pixels par seconde

    caught = False
    result = None

    while not caught and attempts < max_attempts:
        charging = False
        power = 0
        launched = False
        while not launched:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RIGHT: # Diminue l'angle (tir plus bas et plus long)
                        angle = max(min_angle, angle - 2)
                    elif event.key == pygame.K_LEFT: # Augmente l'angle (tir plus haut et plus court)
                        angle = min(max_angle, angle + 2)
                    elif event.key == pygame.K_UP:
                        charging = True
                    elif event.key == pygame.K_ESCAPE:
                        return "back"
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP and charging:
                        launched = True
            if charging:
                power = min(max_power, power + 2)
            
            # Déplacement du Pokémon (logique de cible et d'attente)
            now = pygame.time.get_ticks()
            if pokemon_state == "WAITING":
                if now >= pokemon_wait_end_time:
                    # Fin de l'attente, choisir une nouvelle cible au hasard dans la zone
                    pokemon_target_pos = [
                        random.randint(move_area.left, move_area.right),
                        random.randint(move_area.top, move_area.bottom)
                    ]
                    pokemon_state = "MOVING"
            
            elif pokemon_state == "MOVING":
                dir_vec = [pokemon_target_pos[0] - pokemon_pos[0], 
                           pokemon_target_pos[1] - pokemon_pos[1]]
                distance = math.hypot(dir_vec[0], dir_vec[1])
                
                # Vitesse pour ce frame (à 60 FPS)
                move_dist = pokemon_speed / 60.0

                if distance < move_dist:
                    # Cible atteinte
                    pokemon_pos = list(pokemon_target_pos)
                    pokemon_state = "WAITING"
                    pokemon_wait_end_time = now + random.randint(3000, 10000)
                else:
                    # Déplacer le pokémon vers la cible
                    norm_vec = [dir_vec[0] / distance, dir_vec[1] / distance]
                    pokemon_pos[0] += norm_vec[0] * move_dist
                    pokemon_pos[1] += norm_vec[1] * move_dist
            
            if background_image:
                screen.blit(background_image, (0, 0))
            else:
                screen.fill((180, 220, 255))

            # Affichage du Pokémon
            if pokemon_sprite:
                # On ne redimensionne plus le pokémon, il garde une taille fixe
                rect = pokemon_sprite.get_rect(center=(int(pokemon_pos[0]), int(pokemon_pos[1])))
                screen.blit(pokemon_sprite, rect)
            # Affichage de la pokeball
            if pokeball_sprite:
                rect = pokeball_sprite.get_rect(center=pokeball_pos)
                screen.blit(pokeball_sprite, rect)
            # Visualisation de la courbe de la pokeball
            rad = math.radians(angle)
            preview_power = power if charging else max_power // 5
            points = []
            pos = list(pokeball_pos)
            dx = math.cos(rad) * preview_power / 60 * 3.5
            dy = -math.sin(rad) * preview_power / 60 * 3.5
            for t in range(60):
                pos[0] += dx
                pos[1] += dy
                pos[1] += 0.5 * t / 60 * preview_power / 20
                points.append((int(pos[0]), int(pos[1])))
            if len(points) > 1:
                pygame.draw.lines(screen, (255,0,0), False, points, 2)
            # UI - Affichage des essais restants avec des pokeballs
            if pokeball_sprite:
                remaining_attempts = max_attempts - attempts
                pokeball_width = pokeball_sprite.get_width()
                for i in range(remaining_attempts):
                    screen.blit(pokeball_sprite, (10 + i * (pokeball_width + 5), 10))
            pygame.display.flip()
            clock.tick(60)
        # Animation du lancer
        steps = 60
        pos = list(pokeball_pos)
        rad = math.radians(angle)
        dx = math.cos(rad) * power / steps * 3.5
        dy = -math.sin(rad) * power / steps * 3.5
        hit = False
        for t in range(steps):
            pos[0] += dx
            pos[1] += dy
            # Simule une parabole simple
            pos[1] += 0.5 * t / steps * power / 20
            if background_image:
                screen.blit(background_image, (0, 0))
            else:
                screen.fill((180, 220, 255))

            # Le pokémon reste à sa dernière position pendant le lancer
            if pokemon_sprite:
                rect = pokemon_sprite.get_rect(center=(int(pokemon_pos[0]), int(pokemon_pos[1])))
                screen.blit(pokemon_sprite, rect)
            if pokeball_sprite:
                rect = pokeball_sprite.get_rect(center=(int(pos[0]), int(pos[1])))
                screen.blit(pokeball_sprite, rect)
            pygame.display.flip()
            clock.tick(60)
            # Détection de collision
            # On utilise la position en pixels du pokémon
            if abs(pos[0] - pokemon_pos[0]) < 40 and abs(pos[1] - pokemon_pos[1]) < 40:
                hit = True
                break
        attempts += 1
        if hit:
            caught = True
            result = "caught"
        else:
            result = "miss"
    return result
