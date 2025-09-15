import pygame
from pathlib import Path
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FONT_SIZE
from db import get_connection, get_pokemon_list, get_pokemon_data, add_caught_column, update_pokemon_caught_status
from sprites import load_sprite, load_pokeball_sprites, apply_shadow_effect
from ui import draw_list_view, draw_detail_view
import catch_game
import stabilize_game

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pokédex Pi Zero")
clock = pygame.time.Clock()
import pygame.font
font = pygame.font.SysFont("Arial", FONT_SIZE, bold=True)

# Ajout de la colonne 'caught' si elle n'existe pas
add_caught_column()

conn = get_connection()
pokemon_list = get_pokemon_list(conn)

# Charger les sprites de la pokeball
pokeball_img_small, _ = load_pokeball_sprites(30)
pokeball_img_large, _ = load_pokeball_sprites(50)

selected_index = 0
state = "list"  # list, detail
scroll_offset = 0
max_visible = (SCREEN_HEIGHT - 20) // FONT_SIZE
current_pokemon_data = None
current_sprite = None
BASE_DIR = Path.cwd()

running = True

# Variables pour le scroll accéléré
key_down_pressed = False
key_up_pressed = False
down_press_time = 0
up_press_time = 0
scroll_delay = 200
scroll_fast_delay = 50
scroll_accel_time = 2000
last_scroll_time = 0

while running:
    screen.fill((255, 255, 255))
    now = pygame.time.get_ticks()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if state == "list":
                if event.key == pygame.K_DOWN:
                    key_down_pressed = True
                    down_press_time = now
                    last_scroll_time = now
                elif event.key == pygame.K_UP:
                    key_up_pressed = True
                    up_press_time = now
                    last_scroll_time = now
                elif event.key == pygame.K_RETURN:
                    pid = pokemon_list[selected_index][0]
                    current_pokemon_data = get_pokemon_data(conn, pid)
                    if current_pokemon_data:
                        state = "detail"
                elif event.key == pygame.K_SPACE:
                    pokedex_id = pokemon_list[selected_index][0]
                    current_caught_status = pokemon_list[selected_index][3]
                    if not current_caught_status:
                        # Lancer le premier mini-jeu
                        pokemon_sprite = pygame.transform.scale(original_sprite, (100, 100))
                        catch_result = catch_game.run(screen, font, pokemon_sprite, pokeball_img_small)
                        if catch_result == "caught":
                            # Lancer le second mini-jeu
                            stabilize_result = stabilize_game.run(screen, font, pokeball_img_large)
                            if stabilize_result == "caught":
                                update_pokemon_caught_status(conn, pokedex_id, True)
                                pokemon_list = get_pokemon_list(conn)
                                current_pokemon_data = get_pokemon_data(conn, pokedex_id)
                                if current_pokemon_data:
                                    state = "detail"
                            elif stabilize_result == "failed":
                                state = "list"
                        elif catch_result == "quit":
                            running = False
                    else: # Si déjà attrapé, on le relâche
                        update_pokemon_caught_status(conn, pokedex_id, False)
                        pokemon_list = get_pokemon_list(conn) # Refresh list
                elif event.key == pygame.K_ESCAPE:
                    running = False
            elif state == "detail" and event.key == pygame.K_ESCAPE:
                state = "list"
                current_sprite = None

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_DOWN:
                key_down_pressed = False
            elif event.key == pygame.K_UP:
                key_up_pressed = False

    # Scroll immédiat au premier appui
    if state == "list":
        if key_down_pressed and (now - down_press_time == 0):
            if selected_index < len(pokemon_list) - 1:
                selected_index += 1
                if selected_index - scroll_offset >= max_visible:
                    scroll_offset += 1
        elif key_up_pressed and (now - up_press_time == 0):
            if selected_index > 0:
                selected_index -= 1
                if selected_index < scroll_offset:
                    scroll_offset -= 1

    # Scroll continu si touche maintenue
    if state == "list":
        if key_down_pressed:
            elapsed = now - down_press_time
            delay = scroll_delay if elapsed < scroll_accel_time else scroll_fast_delay
            if elapsed > scroll_delay and (now - last_scroll_time > delay):
                if selected_index < len(pokemon_list) - 1:
                    selected_index += 1
                    if selected_index - scroll_offset >= max_visible:
                        scroll_offset += 1
                last_scroll_time = now
        elif key_up_pressed:
            elapsed = now - up_press_time
            delay = scroll_delay if elapsed < scroll_accel_time else scroll_fast_delay
            if elapsed > scroll_delay and (now - last_scroll_time > delay):
                if selected_index > 0:
                    selected_index -= 1
                    if selected_index < scroll_offset:
                        scroll_offset -= 1
                last_scroll_time = now

    # Gestion du sprite
    sprite_file = Path(pokemon_list[selected_index][2]).name
    caught = pokemon_list[selected_index][3]
    SPRITES_DIR = BASE_DIR / "app" / "data" / "sprites"
    sprite_path = SPRITES_DIR / sprite_file

    original_sprite = load_sprite(sprite_path)
    if original_sprite:
        processed_sprite = original_sprite
        if not caught:
            processed_sprite = apply_shadow_effect(original_sprite)

        if state == "list":
            current_sprite = pygame.transform.scale(processed_sprite, (200, 200))
        elif state == "detail":
            current_sprite = processed_sprite # la vue détail s'occupe du scale

    # Affichage
    if state == "list":
        draw_list_view(screen, pokemon_list, selected_index, scroll_offset, max_visible, current_sprite, font)
    elif state == "detail" and current_pokemon_data:
        draw_detail_view(screen, current_pokemon_data, current_sprite, font, caught)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
conn.close()