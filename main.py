import pygame
from pathlib import Path
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FONT_SIZE
from db import get_connection, get_pokemon_list, get_pokemon_data
from sprites import load_sprite
from ui import draw_list_view, draw_detail_view

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pokédex Pi Zero")
clock = pygame.time.Clock()
import pygame.font
font = pygame.font.SysFont("Arial", FONT_SIZE, bold=True)
font = pygame.font.SysFont("Arial", FONT_SIZE, bold=True)

conn = get_connection()
pokemon_list = get_pokemon_list(conn)

## Helpers déplacés dans ui.py et sprites.py

selected_index = 0
state = "list"  # list ou detail
scroll_offset = 0
max_visible = (SCREEN_HEIGHT - 20)//FONT_SIZE
current_pokemon_data = None
current_sprite = None
BASE_DIR = Path.cwd()

## Fonctions d'affichage déplacées dans ui.py

running = True

# Variables pour le scroll accéléré et double click
key_down_pressed = False
key_up_pressed = False
down_press_time = 0
up_press_time = 0
scroll_delay = 200  # ms entre scrolls au début
scroll_fast_delay = 50  # ms après accélération
scroll_accel_time = 3000  # ms avant accélération
last_scroll_time = 0
## Suppression de la détection du double click

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
                    last_scroll_time = 0
                    # Scroll immédiat au premier appui
                    if selected_index < len(pokemon_list)-1:
                        selected_index += 1
                        if selected_index - scroll_offset >= max_visible:
                            scroll_offset += 1
                elif event.key == pygame.K_UP:
                    key_up_pressed = True
                    up_press_time = now
                    last_scroll_time = 0
                    if selected_index > 0:
                        selected_index -= 1
                        if selected_index < scroll_offset:
                            scroll_offset -= 1
                elif event.key == pygame.K_RETURN:
                    pid = pokemon_list[selected_index][0]
                    current_pokemon_data = get_pokemon_data(conn, pid)
                    if current_pokemon_data:
                        state = "detail"
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

    # Scroll continu si touche maintenue
    if state == "list":
        if key_down_pressed:
            elapsed = now - down_press_time
            delay = scroll_delay if elapsed < scroll_accel_time else scroll_fast_delay
            if last_scroll_time == 0 or now - last_scroll_time > delay:
                if selected_index < len(pokemon_list)-1:
                    selected_index += 1
                    if selected_index - scroll_offset >= max_visible:
                        scroll_offset += 1
                last_scroll_time = now
        elif key_up_pressed:
            elapsed = now - up_press_time
            delay = scroll_delay if elapsed < scroll_accel_time else scroll_fast_delay
            if last_scroll_time == 0 or now - last_scroll_time > delay:
                if selected_index > 0:
                    selected_index -= 1
                    if selected_index < scroll_offset:
                        scroll_offset -= 1
                last_scroll_time = now

    # Gestion du sprite
    sprite_file = Path(pokemon_list[selected_index][2]).name
    SPRITES_DIR = BASE_DIR / "app" / "data" / "sprites"
    sprite_path = SPRITES_DIR / sprite_file

    original_sprite = load_sprite(sprite_path)
    if original_sprite:
        if state == "list":
            current_sprite = pygame.transform.scale(original_sprite, (200, 200))
        elif state == "detail":
            current_sprite = pygame.transform.smoothscale(original_sprite, (200, 200))

    # Affichage
    if state == "list":
        draw_list_view(screen, pokemon_list, selected_index, scroll_offset, max_visible, current_sprite, font)
    elif state == "detail" and current_pokemon_data:
        draw_detail_view(screen, current_pokemon_data, current_sprite, font)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
conn.close()
