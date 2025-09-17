import pygame
import os
from pathlib import Path
from db import set_user_preference
from sprites import load_sprite
from config import SCREEN_WIDTH, SCREEN_HEIGHT

def draw_arrow(screen, direction, position, size=20, color=(255, 255, 255)):
    if direction == 'left':
        points = [(position[0], position[1]), 
                  (position[0] - size, position[1] - size // 2), 
                  (position[0] - size, position[1] + size // 2)]
    else: # right
        points = [(position[0], position[1]), 
                  (position[0] + size, position[1] - size // 2), 
                  (position[0] + size, position[1] + size // 2)]
    pygame.draw.polygon(screen, color, points)

def run(screen, font, game_state):
    background_path = Path(game_state.BASE_DIR) / "app" / "data" / "assets" / "select.png"
    background_image = load_sprite(background_path)

    dresseur_path = Path(game_state.BASE_DIR) / "app" / "data" / "assets" / "dresseurs"
    dresseur_folders = sorted([d for d in dresseur_path.iterdir() if d.is_dir()])

    if not dresseur_folders:
        print("No dresseur folders found in app/data/assets/dresseurs/")
        return "list" 

    dresseur_sprites = []
    for d_folder in dresseur_folders:
        face_sprite = load_sprite(d_folder / "face.png")
        dos_sprite = load_sprite(d_folder / "dos.png")
        if face_sprite and dos_sprite:
            dresseur_sprites.append({
                "name": d_folder.name,
                "face": face_sprite,
                "dos": dos_sprite
            })

    selected_dresseur_index = 0
    show_face = True

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT: # Swapped
                    selected_dresseur_index = (selected_dresseur_index - 1) % len(dresseur_sprites)
                elif event.key == pygame.K_LEFT: # Swapped
                    selected_dresseur_index = (selected_dresseur_index + 1) % len(dresseur_sprites)
                elif event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    show_face = not show_face
                elif event.key == pygame.K_n:
                    selected_dresseur_name = dresseur_sprites[selected_dresseur_index]["name"]
                    set_user_preference(game_state.conn, "dresseur", selected_dresseur_name)
                    game_state.dresseur = selected_dresseur_name
                    return "list"

        if background_image:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill((0, 0, 0))

        if dresseur_sprites:
            current_dresseur = dresseur_sprites[selected_dresseur_index]
            sprite_to_show = current_dresseur["face"] if show_face else current_dresseur["dos"]
            
            width, height = sprite_to_show.get_size()
            scaled_sprite = pygame.transform.scale(sprite_to_show, (width * 2, height * 2))
            
            rect = scaled_sprite.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(scaled_sprite, rect)
            
            name_surface = font.render(current_dresseur["name"], True, (255, 255, 255))
            name_rect = name_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
            screen.blit(name_surface, name_rect)

            # Draw arrows
            arrow_y = SCREEN_HEIGHT // 2
            draw_arrow(screen, 'right', (SCREEN_WIDTH // 2 - 80, arrow_y))
            draw_arrow(screen, 'left', (SCREEN_WIDTH // 2 + 80, arrow_y))


        pygame.display.flip()
        pygame.time.Clock().tick(60)

    return "quit"