import pygame
import math
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FONT_SIZE
from sprites import load_pokeball_sprites, load_masterball_sprite

# Charger les sprites de la pokeball
pokeball_img, pokeball_grayscale_img = load_pokeball_sprites(FONT_SIZE)
masterball_img = load_masterball_sprite(FONT_SIZE)

def draw_text(surface, text, x, y, font, color=(0,0,0)):
    img = font.render(text, True, color)
    surface.blit(img, (x, y))

def draw_rounded_rect(surface, color, rect, radius=8, border=0, border_color=(0,0,0)):
    rect = pygame.Rect(rect)
    shape_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shape_surf, color, shape_surf.get_rect(), border_radius=radius)
    if border > 0:
        pygame.draw.rect(shape_surf, border_color, shape_surf.get_rect(), border, border_radius=radius)
    surface.blit(shape_surf, rect.topleft)

def draw_stats_radar(surface, stats, center, radius, font, color=(0, 120, 200, 120)):
    labels = ["hp", "atk", "def", "spe_atk", "spe_def", "vit"]
    values = [stats.get(l, 0) for l in labels]
    max_stat = 255
    normalized = [v / max_stat for v in values]
    points = []
    for i, val in enumerate(normalized):
        angle = (math.pi * 2 / len(labels)) * i - math.pi/2
        x = center[0] + math.cos(angle) * val * radius
        y = center[1] + math.sin(angle) * val * radius
        points.append((x, y))
    s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    pygame.draw.polygon(s, color, points, width=0)
    surface.blit(s, (0,0))
    pygame.draw.polygon(surface, (0,0,0), points, width=2)
    for i, label in enumerate(labels):
        angle = (math.pi * 2 / len(labels)) * i - math.pi/2
        x = center[0] + math.cos(angle) * radius
        y = center[1] + math.sin(angle) * radius
        pygame.draw.line(surface, (150,150,150), center, (x, y), 1)
        draw_text(surface, label, int(x), int(y), font)

def draw_list_view(screen, pokemon_list, selected_index, scroll_offset, max_visible, current_sprite, font):
    for y in range(SCREEN_HEIGHT):
        c = 255 - int(y * 0.3)
        pygame.draw.line(screen, (c, c, c), (0, y), (SCREEN_WIDTH, y))
    draw_rounded_rect(screen, (245,245,245), (5,5,200,SCREEN_HEIGHT-10), radius=10, border=2)
    start_y = 20
    for i in range(scroll_offset, min(scroll_offset+max_visible, len(pokemon_list))):
        pid, name, _, _, caught, is_shiny = pokemon_list[i]
        y = start_y + (i-scroll_offset)*FONT_SIZE
        if i == selected_index:
            draw_rounded_rect(screen, (255,230,200), (10, y-2, 180, FONT_SIZE+4), radius=6)
        color = (0,0,0) if i != selected_index else (200,30,30)

        # Afficher la pokeball
        if is_shiny and masterball_img:
            screen.blit(masterball_img, (15, y))
        elif caught and pokeball_img:
            screen.blit(pokeball_img, (15, y))
        elif pokeball_grayscale_img:
            screen.blit(pokeball_grayscale_img, (15, y))

        display_name = name if caught else "???"
        draw_text(screen, f"{pid:03d} {display_name}", 15 + FONT_SIZE + 5, y, font, color)
        
    draw_rounded_rect(screen, (240,240,250), (210,20,250,250), radius=20, border=2)
    if current_sprite:
        rect = current_sprite.get_rect(center=(335,145))
        screen.blit(current_sprite, rect)

def draw_detail_view(screen, current_pokemon_data, current_sprite, font, caught=True, is_shiny=False):
    small_font = pygame.font.SysFont("Arial", FONT_SIZE - 2)
    # Fond dégradé vertical
    for y in range(SCREEN_HEIGHT):
        r = 200
        g = min(255, 200 + y // 5)
        b = 255
        pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    # Bandeau en haut : nom à gauche, types à droite
    draw_rounded_rect(screen, (255,255,255), (10,10,SCREEN_WIDTH-20,50), radius=12, border=2)
    name_fr = current_pokemon_data.get("name", {}).get("fr", "???") if caught else "???"
    pid = current_pokemon_data.get("pokedex_id", "?")
    types = [t.get("name", "?") for t in (current_pokemon_data.get("types") or [])] if caught else ["?"]
    
    icon_x = 20
    text_x = icon_x + FONT_SIZE + 5
    if is_shiny and masterball_img:
        screen.blit(masterball_img, (icon_x, 25))
    elif caught and pokeball_img:
        screen.blit(pokeball_img, (icon_x, 25))
    else:
        screen.blit(pokeball_grayscale_img, (icon_x, 25))

    draw_text(screen, f"{pid:03d} - {name_fr}", text_x, 25, font, (30,30,120))
    draw_text(screen, " / ".join(types), SCREEN_WIDTH-20-120, 25, font, (30,120,30))

    if current_sprite:
        sprite_big = pygame.transform.smoothscale(current_sprite, (150, 150))
        rect = sprite_big.get_rect(center=(150, 140))
        screen.blit(sprite_big, rect)

    # Poids et taille à gauche du sprite
    height = current_pokemon_data.get("height", "?") if caught else "?"
    weight = current_pokemon_data.get("weight", "?") if caught else "?"
    draw_text(screen, f"{height}", 20, 120, small_font, (100,100,100))
    draw_text(screen, f"{weight}", 20, 140, small_font, (100,100,100))

    # Radar des stats à droite (sans cadre)
    stats = current_pokemon_data.get("stats") or {}
    if stats and caught:
        draw_stats_radar(screen, stats, center=(310, 140), radius=65, font=font)

    # Infos complémentaires en bas
    talents = [t.get("name", "?") for t in (current_pokemon_data.get("talents") or [])] if caught else ["?"]
    draw_rounded_rect(screen, (255,255,255), (30,230,370,40), radius=10, border=2)
    draw_text(screen, "Talents: " + ", ".join(talents), 40, 240, font)

    evol = (current_pokemon_data.get("evolution", {}) or {}).get("next") or []
    evol_text = ", ".join(e.get("name", "?") for e in evol if isinstance(e, dict)) if caught else "?"
    draw_rounded_rect(screen, (255,255,255), (30,277,370,40), radius=10, border=2)
    draw_text(screen, "Évolutions: " + (evol_text if evol_text else "Aucune"), 40, 290, font)