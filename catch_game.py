import pygame
import math
from config import SCREEN_WIDTH, SCREEN_HEIGHT

def run(screen, font, pokemon_sprite, pokeball_sprite):
    def draw_iso_grid(surface, color=(180,200,220), cell_size=48, rows=12, cols=12):
        origin_x = SCREEN_WIDTH // 2
        origin_y = 80
        for row in range(rows):
            for col in range(cols):
                x = origin_x + (col - row) * cell_size // 2
                y = origin_y + (col + row) * cell_size // 4
                points = [
                    (x, y),
                    (x + cell_size//2, y + cell_size//4),
                    (x, y + cell_size//2),
                    (x - cell_size//2, y + cell_size//4)
                ]
                pygame.draw.polygon(surface, color, points, 1)
    clock = pygame.time.Clock()
    attempts = 0
    max_attempts = 3
    angle = 45  # degrés, direction du tir
    min_angle = 10
    max_angle = 80
    power = 0
    max_power = 400
    charging = False
    pokeball_pos = [60, SCREEN_HEIGHT - 60]
    # Position du Pokémon sur la grille (row, col)
    grid_rows, grid_cols = 12, 12
    cell_size = 48
    pokemon_grid = [grid_rows//2, grid_cols//2]
    pokemon_dir = [1, 1]
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
                    if event.key == pygame.K_LEFT:
                        angle = max(min_angle, angle - 2)
                    elif event.key == pygame.K_RIGHT:
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
            screen.fill((180, 220, 255))
            draw_iso_grid(screen, color=(160,180,200), cell_size=40, rows=7, cols=7)
            # Déplacement du Pokémon sur la grille avec flèches
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        angle = max(min_angle, angle - 2)
                        pokemon_grid[1] = max(0, pokemon_grid[1] - 1)
                    elif event.key == pygame.K_RIGHT:
                        angle = min(max_angle, angle + 2)
                        pokemon_grid[1] = min(grid_cols-1, pokemon_grid[1] + 1)
                    elif event.key == pygame.K_UP:
                        charging = True
                        pokemon_grid[0] = max(0, pokemon_grid[0] - 1)
                    elif event.key == pygame.K_DOWN:
                        pokemon_grid[0] = min(grid_rows-1, pokemon_grid[0] + 1)
                    elif event.key == pygame.K_ESCAPE:
                        return "back"
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP and charging:
                        launched = True
            # Calcul position isométrique du Pokémon
            origin_x = SCREEN_WIDTH // 2
            origin_y = 80
            px = origin_x + (pokemon_grid[1] - pokemon_grid[0]) * cell_size // 2
            py = origin_y + (pokemon_grid[1] + pokemon_grid[0]) * cell_size // 4
            # Taille selon la profondeur (plus loin = plus petit)
            depth = grid_rows - pokemon_grid[0]
            pokemon_size = int(40 + 40 * depth / grid_rows)
            # Affichage du Pokémon
            if pokemon_sprite:
                scaled = pygame.transform.smoothscale(pokemon_sprite, (pokemon_size, pokemon_size))
                rect = scaled.get_rect(center=(px, py))
                screen.blit(scaled, rect)
            # Affichage de la pokeball
            if pokeball_sprite:
                rect = pokeball_sprite.get_rect(center=pokeball_pos)
                screen.blit(pokeball_sprite, rect)
            # Visualisation de la courbe de la pokeball
            rad = math.radians(angle)
            preview_power = power if charging else max_power // 2
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
            # UI
            font.render(f"Angle: {angle}°", True, (0,0,0))
            screen.blit(font.render(f"Angle: {angle}°", True, (0,0,0)), (20, 20))
            font.render(f"Puissance: {power}", True, (0,0,0))
            screen.blit(font.render(f"Puissance: {power}", True, (0,0,0)), (20, 50))
            font.render(f"Essais restants: {max_attempts-attempts}", True, (0,0,0))
            screen.blit(font.render(f"Essais restants: {max_attempts-attempts}", True, (0,0,0)), (20, 80))
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
            screen.fill((180, 220, 255))
            if pokemon_sprite:
                rect = pokemon_sprite.get_rect(center=(px, py))
                screen.blit(pokemon_sprite, rect)
            if pokeball_sprite:
                rect = pokeball_sprite.get_rect(center=(int(pos[0]), int(pos[1])))
                screen.blit(pokeball_sprite, rect)
            pygame.display.flip()
            clock.tick(60)
            # Détection de collision
            if abs(pos[0] - px) < 40 and abs(pos[1] - py) < 40:
                hit = True
                break
        attempts += 1
        if hit:
            caught = True
            result = "caught"
        else:
            result = "miss"
    return result
