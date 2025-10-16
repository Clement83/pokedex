import db
import pygame
import math
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FONT_SIZE, LIST_VERTICAL_OFFSET, STATS_AREA_HEIGHT, REGIONS, STATS_FONT_SIZE
from sprites import load_pokeball_sprites, load_masterball_sprite, load_type_icon

def get_region_from_id(pokedex_id):
    for region, data in REGIONS.items():
        if data["min_id"] <= pokedex_id < data["max_id"]:
            return region
    return None

# Charger les sprites de la pokeball
pokeball_img, pokeball_grayscale_img = load_pokeball_sprites(FONT_SIZE)
masterball_img = load_masterball_sprite(FONT_SIZE)

def draw_text(surface, text, x, y, font, color=(0,0,0)):
    img = font.render(text, True, color)
    surface.blit(img, (x, y))

def draw_pokemon_style_text(surface, text, center_pos, font, text_color, outline_color, outline_width=2, with_frame=False):
    """Draws text with a Pokémon-style outline and an optional frame."""
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect()

    outline_surf = font.render(text, True, outline_color)

    if with_frame:
        pokeball_width = pokeball_img.get_width() if pokeball_img else 0
        padding_h = 20  # Horizontal padding inside frame
        padding_v = 10  # Vertical padding inside frame

        # Calculate frame size to fit text and pokeballs
        frame_width = text_rect.width + pokeball_width * 2 + padding_h * 4
        frame_height = text_rect.height + padding_v * 2

        frame_rect = pygame.Rect(0, 0, frame_width, frame_height)
        frame_rect.center = center_pos

        # Draw the frame
        draw_rounded_rect(surface, (255, 255, 255), frame_rect, radius=12, border=3, border_color=(200, 0, 0))

        # Position and draw pokeballs
        if pokeball_img:
            pokeball_y = frame_rect.centery - pokeball_img.get_height() // 2
            surface.blit(pokeball_img, (frame_rect.left + padding_h, pokeball_y))

            right_pokeball_x = frame_rect.right - padding_h - pokeball_width
            surface.blit(pokeball_img, (right_pokeball_x, pokeball_y))

        # Position and draw text in the center of the frame
        text_x = frame_rect.centerx - text_rect.width // 2
        text_y = frame_rect.centery - text_rect.height // 2
        text_pos = (text_x, text_y)

        # Draw outline
        surface.blit(outline_surf, (text_pos[0] - outline_width, text_pos[1] - outline_width))
        surface.blit(outline_surf, (text_pos[0] + outline_width, text_pos[1] - outline_width))
        surface.blit(outline_surf, (text_pos[0] - outline_width, text_pos[1] + outline_width))
        surface.blit(outline_surf, (text_pos[0] + outline_width, text_pos[1] + outline_width))
        # Draw text
        surface.blit(text_surf, text_pos)

    else: # No frame
        text_rect.center = center_pos
        # Draw outline
        surface.blit(outline_surf, (text_rect.x - outline_width, text_rect.y - outline_width))
        surface.blit(outline_surf, (text_rect.x + outline_width, text_rect.y - outline_width))
        surface.blit(outline_surf, (text_rect.x - outline_width, text_rect.y + outline_width))
        surface.blit(outline_surf, (text_rect.x + outline_width, text_rect.y + outline_width))
        # Draw text
        surface.blit(text_surf, text_rect)

def draw_rounded_rect(surface, color, rect, radius=8, border=0, border_color=(0,0,0)):
    rect = pygame.Rect(rect)
    shape_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shape_surf, color, shape_surf.get_rect(), border_radius=radius)
    if border > 0:
        pygame.draw.rect(shape_surf, border_color, shape_surf.get_rect(), border, border_radius=radius)
    surface.blit(shape_surf, rect.topleft)

def draw_hp_bar(surface, percent, pos, size, font):
    """Draws a classic Pokémon-style HP bar."""
    x, y = pos
    width, height = size

    # Determine color based on percentage
    if percent > 50:
        bar_color = (30, 200, 30)  # Green
    elif percent > 20:
        bar_color = (255, 200, 0) # Yellow
    else:
        bar_color = (220, 30, 30)  # Red

    # Draw the outer frame
    frame_rect = pygame.Rect(x, y, width, height)
    draw_rounded_rect(surface, (240, 240, 240), frame_rect, radius=5, border=2, border_color=(40, 40, 40))

    # Draw the "PV" label
    pv_text = font.render("PV", True, (40, 40, 40))
    surface.blit(pv_text, (x + 5, y + (height - pv_text.get_height()) // 2))

    # Draw the inner health bar
    bar_width = (width - 35) * (percent / 100)
    bar_rect = pygame.Rect(x + 30, y + 4, bar_width, height - 8)
    pygame.draw.rect(surface, bar_color, bar_rect)

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

def draw_list_view(screen, pokemon_list, selected_index, scroll_offset, max_visible, current_sprite, font, background, game_state):
    screen.blit(background, (0, 0))

    start_y = 20 # Revert list to original position
    for i in range(scroll_offset, min(scroll_offset + max_visible, len(pokemon_list))):
        pid, name, name_en, _, _, caught, is_shiny, _, seen = pokemon_list[i]
        y = start_y + (i - scroll_offset) * FONT_SIZE

        if i == selected_index:
            draw_rounded_rect(screen, (255, 230, 200), (10, y - 2, 180, FONT_SIZE + 4), radius=6)

        color = (0, 0, 0) if i != selected_index else (200, 30, 30)

        if seen:
            if caught and is_shiny and masterball_img:
                screen.blit(masterball_img, (15, y))
            elif caught and pokeball_img:
                screen.blit(pokeball_img, (15, y))
            elif pokeball_grayscale_img:
                screen.blit(pokeball_grayscale_img, (15, y))

        display_name = name if seen else "???"
        draw_text(screen, f"{pid:03d} {display_name}", 15 + FONT_SIZE + 5, y, font, color)

    if current_sprite:
        rect = current_sprite.get_rect(center=(335, 145 - LIST_VERTICAL_OFFSET))
        screen.blit(current_sprite, rect)

    # Display region if seen
    if selected_index < len(pokemon_list):
        # Display first type icon if seen
        pid, _, _, _, _, _, _, _, seen = pokemon_list[selected_index]
        if seen:
            pokemon_data = db.get_pokemon_data(game_state.conn, pid)
            if pokemon_data and pokemon_data.get("types"):
                first_type_name = pokemon_data["types"][0]["name"]
                type_icon = load_type_icon(first_type_name, int(FONT_SIZE * 1.5)) # Use FONT_SIZE * 1.5 for icon size
                if type_icon:
                    # Position the icon at the top-left of the right panel
                    # Right panel starts at (210, 5)
                    icon_x = 210 + 10 # 10 pixels padding from left
                    icon_y = 5 + 5   # 5 pixels padding from top
                    screen.blit(type_icon, (icon_x, icon_y))

        pid, _, _, _, _, _, _, _, seen = pokemon_list[selected_index]
        if seen:
            region = get_region_from_id(pid)
            if region:
                small_font = pygame.font.SysFont("Arial", 16, bold=True)
                region_text_surface = small_font.render(region, True, (100, 100, 100))

                # Calculate x position for right alignment
                text_x = (210 + 250) - region_text_surface.get_width() - 10 # 10 pixels padding from the right edge
                text_y = 10 # Keep y as 10 for top alignment

                draw_text(screen, region, text_x, text_y, small_font, (100, 100, 100))

    # Affiche le compteur de captures pour le Pokémon sélectionné
    if selected_index < len(pokemon_list):
        # Le 8ème élément (index 7) est times_caught
        times_caught = pokemon_list[selected_index][7]

        if times_caught > 0:
            # Formate le nombre : 2 chiffres, avec un maximum de 99
            display_count = min(times_caught, 99)
            count_text = f"{display_count:02d}"

            # Crée une petite bulle pour le compteur
            bubble_font = pygame.font.SysFont("Arial", 16, bold=True)
            text_surface = bubble_font.render(count_text, True, (255, 255, 255))

            # Positionne la bulle en bas à droite du panneau de droite (210,5,250,250)
            # Le panneau de droite a une largeur de 250 et une hauteur de 250, et commence à x=210, y=5
            panel_right_x = 210
            panel_right_y = 5
            panel_right_width = 250
            panel_right_height = 250

            bubble_width = text_surface.get_width() + 12
            bubble_height = text_surface.get_height() + 6

            bubble_pos_x = panel_right_x + panel_right_width - bubble_width - 10 # 10 pixels de padding depuis la droite
            bubble_pos_y = panel_right_y + panel_right_height - bubble_height - 10 # 10 pixels de padding depuis le bas

            bubble_rect = pygame.Rect(bubble_pos_x, bubble_pos_y, bubble_width, bubble_height)

            draw_rounded_rect(screen, (0, 0, 0, 180), bubble_rect, radius=10) # Fond noir semi-transparent
            text_rect = text_surface.get_rect(center=bubble_rect.center)
            screen.blit(text_surface, text_rect)



def draw_general_stats(screen, game_state, stats_font):
    caught_count = game_state.caught_count if hasattr(game_state, 'caught_count') else 0
    shiny_count = game_state.shiny_count if hasattr(game_state, 'shiny_count') else 0
    seen_count = game_state.seen_count if hasattr(game_state, 'seen_count') else 0
    unlocked_regions_count = game_state.unlocked_regions_count if hasattr(game_state, 'unlocked_regions_count') else 0
    total_pokemon = len(game_state.pokemon_list) if hasattr(game_state, 'pokemon_list') else 0

    # Define colors and fonts
    bg_color = (240, 240, 250) # Light grey, matching the sprite panel
    border_color = (100, 100, 100) # Grey border
    text_color = (0, 0, 0) # Black

    stats_font_size = 14
    try:
        stats_font = pygame.font.SysFont("Arial", stats_font_size, bold=True)
    except:
        pass # Use default font

    # Main frame for the stats area
    stats_area_rect = pygame.Rect(210, 260, 250, 55)
    draw_rounded_rect(screen, bg_color, stats_area_rect, radius=12, border=2, border_color=border_color)

    # Layout constants
    padding_x = 10
    padding_y = 5
    col_width = (stats_area_rect.width - padding_x * 2) // 2

    col1_x = stats_area_rect.left + padding_x
    col2_x = col1_x + col_width

    row1_y = stats_area_rect.top + padding_y + 2
    row2_y = row1_y + stats_font_size + 6

    # Column 1: Seen & Caught
    draw_text(screen, f"Vus: {seen_count}/{total_pokemon + 1}", col1_x, row1_y, stats_font, text_color)
    draw_text(screen, f"Capturés: {caught_count}", col1_x, row2_y, stats_font, text_color)

    # Column 2: Shiny & Regions
    draw_text(screen, f"Shinies: {shiny_count}", col2_x, row1_y, stats_font, text_color)
    draw_text(screen, f"Régions: {unlocked_regions_count}/{len(REGIONS)}", col2_x, row2_y, stats_font, text_color)


def draw_detail_view(game_state):
    screen = game_state.screen
    current_pokemon_data = game_state.current_pokemon_data
    current_sprite = game_state.current_sprite
    font = game_state.font
    selected_pokemon = game_state.pokemon_list[game_state.selected_index]
    caught = selected_pokemon[5]
    is_shiny = selected_pokemon[6]
    seen = selected_pokemon[8]

    small_font = pygame.font.SysFont("Arial", FONT_SIZE - 2)
    # Fond dégradé vertical
    for y in range(SCREEN_HEIGHT):
        r = 200
        g = min(255, 200 + y // 5)
        b = 255
        pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    # Bandeau en haut : nom à gauche, types à droite
    draw_rounded_rect(screen, (255,255,255), (10,10,SCREEN_WIDTH-20,50), radius=12, border=2)
    name_fr = current_pokemon_data.get("name", {}).get("fr", "???") if seen else "???"
    pid = current_pokemon_data.get("pokedex_id", "?")
    types = [t.get("name", "?") for t in (current_pokemon_data.get("types") or [])] if seen else ["?"]

    icon_x = 20
    text_x = icon_x + FONT_SIZE + 5
    if seen:
        if is_shiny and masterball_img:
            screen.blit(masterball_img, (icon_x, 25))
        elif caught and pokeball_img:
            screen.blit(pokeball_img, (icon_x, 25))
        else: # Seen but not caught
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
        if not seen: # If not seen, make it darker
            sprite_to_draw = sprite_big.copy()
            sprite_to_draw.set_alpha(128)
        else:
            sprite_to_draw = sprite_big
        rect = sprite_to_draw.get_rect(center=(150, 140))
        screen.blit(sprite_to_draw, rect)

    # Poids et taille à gauche du sprite
    height = current_pokemon_data.get("height", "?") if seen else "?"
    weight = current_pokemon_data.get("weight", "?") if seen else "?"
    draw_text(screen, f"{height}", 20, 120, small_font, (100,100,100))
    draw_text(screen, f"{weight}", 20, 140, small_font, (100,100,100))

    # Radar des stats à droite (sans cadre)
    stats = current_pokemon_data.get("stats") or {}
    if stats and caught:
        draw_stats_radar(screen, stats, center=(310, 140), radius=65, font=font)

    # Infos complémentaires en bas
    talents = [t.get("name", "?") for t in (current_pokemon_data.get("talents") or [])] if seen else ["?"]
    draw_rounded_rect(screen, (255,255,255), (30,230,370,40), radius=10, border=2)
    draw_text(screen, "Talents: " + ", ".join(talents), 40, 240, font)

    # Evolution text scrolling logic
    evol = (current_pokemon_data.get("evolution", {}) or {}).get("next") or []
    evol_text_content = ", ".join(e.get("name", "?") for e in evol if isinstance(e, dict)) if seen else "" # Empty string if no evolutions, to handle "Aucune" separately

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

    # Display game_state.message if active
    if game_state.message and pygame.time.get_ticks() < game_state.message_timer:
        try:
            big_font = pygame.font.Font(None, 40)
        except:
            big_font = font # Fallback

        center_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2) # Centered on screen
        text_color = (255, 255, 0)   # Yellow text
        outline_color = (0, 0, 139) # Dark blue outline

        draw_pokemon_style_text(screen, game_state.message, center_pos, big_font, text_color, outline_color, with_frame=True)
