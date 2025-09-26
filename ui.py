import pygame
import math
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FONT_SIZE, LIST_VERTICAL_OFFSET, STATS_AREA_HEIGHT, REGIONS, STATS_FONT_SIZE
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

def create_list_view_background():
    background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for y in range(SCREEN_HEIGHT):
        c = 255 - int(y * 0.3)
        pygame.draw.line(background, (c, c, c), (0, y), (SCREEN_WIDTH, y))

    draw_rounded_rect(background, (245,245,245), (5,5,200,SCREEN_HEIGHT-10), radius=10, border=2)
    draw_rounded_rect(background, (240,240,250), (210,5,250,250), radius=20, border=2) # Moved up to align with left frame
    return background

def draw_list_view(screen, pokemon_list, selected_index, scroll_offset, max_visible, current_sprite, font, background):
    screen.blit(background, (0, 0))

    start_y = 20 # Revert list to original position
    for i in range(scroll_offset, min(scroll_offset + max_visible, len(pokemon_list))):
        pid, name, name_en, _, _, caught, is_shiny, _ = pokemon_list[i]
        y = start_y + (i - scroll_offset) * FONT_SIZE

        if i == selected_index:
            draw_rounded_rect(screen, (255, 230, 200), (10, y - 2, 180, FONT_SIZE + 4), radius=6)

        color = (0, 0, 0) if i != selected_index else (200, 30, 30)

        if is_shiny and masterball_img:
            screen.blit(masterball_img, (15, y))
        elif caught and pokeball_img:
            screen.blit(pokeball_img, (15, y))
        elif pokeball_grayscale_img:
            screen.blit(pokeball_grayscale_img, (15, y))

        display_name = name if caught else "???"
        draw_text(screen, f"{pid:03d} {display_name}", 15 + FONT_SIZE + 5, y, font, color)

    if current_sprite:
        rect = current_sprite.get_rect(center=(335, 145 - LIST_VERTICAL_OFFSET))
        screen.blit(current_sprite, rect)

    # Affiche le compteur de captures pour le Pokémon sélectionné
    if selected_index < len(pokemon_list):
        # Le 7ème élément (index 6) est times_caught
        times_caught = pokemon_list[selected_index][6]

        if times_caught > 0:
            # Formate le nombre : 2 chiffres, avec un maximum de 99
            display_count = min(times_caught, 99)
            count_text = f"{display_count:02d}"

            # Crée une petite bulle pour le compteur
            bubble_font = pygame.font.SysFont("Arial", 16, bold=True)
            text_surface = bubble_font.render(count_text, True, (255, 255, 255))

            # Positionne la bulle en haut à gauche du panneau de droite
            bubble_pos_x = 215
            bubble_pos_y = 10
            bubble_rect = pygame.Rect(bubble_pos_x, bubble_pos_y, text_surface.get_width() + 12, text_surface.get_height() + 6)

            draw_rounded_rect(screen, (0, 0, 0, 180), bubble_rect, radius=10) # Fond noir semi-transparent
            text_rect = text_surface.get_rect(center=bubble_rect.center)
            screen.blit(text_surface, text_rect)

def draw_general_stats(screen, game_state, stats_font):
    # Placeholder for now, will implement after db.py changes
    caught_count = game_state.caught_count if hasattr(game_state, 'caught_count') else 0
    shiny_count = game_state.shiny_count if hasattr(game_state, 'shiny_count') else 0
    unlocked_regions_count = game_state.unlocked_regions_count if hasattr(game_state, 'unlocked_regions_count') else 0
    total_pokemon = len(game_state.pokemon_list) if hasattr(game_state, 'pokemon_list') else 0

    stats_y_start = SCREEN_HEIGHT - STATS_AREA_HEIGHT + 5 # Start drawing stats from here

    draw_text(screen, f"Caught: {caught_count}/{total_pokemon}", 220, stats_y_start, stats_font, (255, 255, 255))
    draw_text(screen, f"Shiny: {shiny_count}", 220, stats_y_start + STATS_FONT_SIZE + 2, stats_font, (255, 255, 255))
    draw_text(screen, f"Regions Unlocked: {unlocked_regions_count}/{len(REGIONS)}", 220, stats_y_start + (STATS_FONT_SIZE + 2) * 2, stats_font, (255, 255, 255))


def draw_detail_view(game_state):
    screen = game_state.screen
    current_pokemon_data = game_state.current_pokemon_data
    current_sprite = game_state.current_sprite
    font = game_state.font
    caught = game_state.pokemon_list[game_state.selected_index][5]
    is_shiny = game_state.pokemon_list[game_state.selected_index][6]

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
    type_text = " / ".join(types)
    type_img = font.render(type_text, True, (30,120,30))
    type_rect = type_img.get_rect()
    type_rect.right = SCREEN_WIDTH - 30
    type_rect.top = 25
    screen.blit(type_img, type_rect)

    if current_sprite:
        sprite_big = pygame.transform.smoothscale(current_sprite, (128, 128))
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

    # Evolution text scrolling logic
    evol = (current_pokemon_data.get("evolution", {}) or {}).get("next") or []
    evol_text_content = ", ".join(e.get("name", "?") for e in evol if isinstance(e, dict)) if caught else "" # Empty string if no evolutions, to handle "Aucune" separately

    draw_rounded_rect(screen, (255,255,255), (30,277,370,40), radius=10, border=2)

    # Render static prefix
    prefix_text = "Évolutions: "
    prefix_img = font.render(prefix_text, True, (0,0,0))
    prefix_width = prefix_img.get_width()
    screen.blit(prefix_img, (40, 290))

    # Determine the content to scroll
    if not evol_text_content: # If no evolutions
        scrollable_text = "Aucune"
        game_state.evolution_scroll_active = False
        game_state.evolution_text_surface = None
        draw_text(screen, scrollable_text, 40 + prefix_width, 290, font)
    else:
        scrollable_text = evol_text_content
        scrollable_img = font.render(scrollable_text, True, (0,0,0))
        scrollable_text_width = scrollable_img.get_width()

        # Available width for scrolling text
        # Box starts at 30, width 370. Text starts at 40.
        # So available space is (30 + 370 - 10) - (40 + prefix_width) = 390 - 40 - prefix_width = 350 - prefix_width
        available_scroll_width = 350 - prefix_width

        if scrollable_text_width > available_scroll_width:
            game_state.evolution_scroll_active = True
            if game_state.evolution_text_surface is None or game_state.evolution_text_surface.get_width() != scrollable_text_width:
                game_state.evolution_text_surface = scrollable_img
                game_state.evolution_text_scroll_x = 0 # Reset scroll on new text

            # Create a clipping area for the scrollable part
            clip_rect = pygame.Rect(40 + prefix_width, 290, available_scroll_width, font.get_height())
            screen.set_clip(clip_rect)

            # Blit the scrolling text
            screen.blit(game_state.evolution_text_surface, (40 + prefix_width - game_state.evolution_text_scroll_x, 290))

            # Reset clipping area
            screen.set_clip(None)
        else:
            game_state.evolution_scroll_active = False
            game_state.evolution_text_surface = None
            draw_text(screen, scrollable_text, 40 + prefix_width, 290, font)
