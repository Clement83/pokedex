import pygame
import sqlite3
import json
import math
from pathlib import Path

# ------------------------------
# Configuration écran & BDD
# ------------------------------
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 320
LIST_WIDTH = 14
SPRITE_SIZE = 64
FONT_SIZE = 16
DB_PATH = "./pokedex.db"

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pokédex Pi Zero")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", FONT_SIZE, bold=True)

# ------------------------------
# Connexion BDD
# ------------------------------
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT pokedex_id, name_fr, sprite_regular FROM pokemon ORDER BY pokedex_id")
pokemon_list = cur.fetchall()

# ------------------------------
# Helpers
# ------------------------------
def draw_text(surface, text, x, y, color=(0,0,0)):
    img = font.render(text, True, color)
    surface.blit(img, (x, y))

def draw_rounded_rect(surface, color, rect, radius=8, border=0, border_color=(0,0,0)):
    rect = pygame.Rect(rect)
    shape_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shape_surf, color, shape_surf.get_rect(), border_radius=radius)
    if border > 0:
        pygame.draw.rect(shape_surf, border_color, shape_surf.get_rect(), border, border_radius=radius)
    surface.blit(shape_surf, rect.topleft)

def draw_stats_radar(surface, stats, center, radius, color=(0, 120, 200, 120)):
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
        draw_text(surface, label, int(x), int(y))

# ------------------------------
# Sprite cache
# ------------------------------
sprite_cache = {}  # clé : chemin complet, valeur : pygame.Surface originale

def load_sprite(path):
    if not path or not Path(path).exists():
        return None
    if path not in sprite_cache:
        try:
            img = pygame.image.load(path).convert_alpha()
            sprite_cache[path] = img
        except Exception as e:
            print(f"[ERREUR] Impossible de charger {path} : {e}")
            return None
    return sprite_cache[path]

# ------------------------------
# État
# ------------------------------
selected_index = 0
state = "list"  # list ou detail
scroll_offset = 0
max_visible = (SCREEN_HEIGHT - 20)//FONT_SIZE
current_pokemon_data = None
current_sprite = None
BASE_DIR = Path.cwd()

# ------------------------------
# Fonctions d'affichage
# ------------------------------
def draw_list_view():
    for y in range(SCREEN_HEIGHT):
        c = 255 - int(y * 0.3)
        pygame.draw.line(screen, (c, c, c), (0, y), (SCREEN_WIDTH, y))

    draw_rounded_rect(screen, (245,245,245), (5,5,200,SCREEN_HEIGHT-10), radius=10, border=2)

    start_y = 20
    for i in range(scroll_offset, min(scroll_offset+max_visible, len(pokemon_list))):
        pid, name, _ = pokemon_list[i]
        y = start_y + (i-scroll_offset)*FONT_SIZE

        if i == selected_index:
            draw_rounded_rect(screen, (255,230,200), (10, y-2, 180, FONT_SIZE+4), radius=6)

        color = (0,0,0) if i != selected_index else (200,30,30)
        draw_text(screen, f"{pid:03d} {name}", 15, y, color)

    draw_rounded_rect(screen, (240,240,250), (210,20,250,250), radius=20, border=2)
    if current_sprite:
        rect = current_sprite.get_rect(center=(335,145))
        screen.blit(current_sprite, rect)

def draw_detail_view():
    for y in range(SCREEN_HEIGHT):
        r = 200
        g = min(255, 200 + y // 5)
        b = 255
        pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    draw_rounded_rect(screen, (255,255,255), (5,5,SCREEN_WIDTH-10,40), radius=10, border=2)
    name_fr = current_pokemon_data.get("name", {}).get("fr", "???")
    pid = current_pokemon_data.get("pokedex_id", "?")
    draw_text(screen, f"{pid:03d} - {name_fr}", 15, 15, (30,30,120))

    draw_rounded_rect(screen, (250,250,250), (10,60,100,100), radius=12, border=2)
    if current_sprite:
        rect = current_sprite.get_rect(center=(60,110))
        screen.blit(current_sprite, rect)

    draw_rounded_rect(screen, (255,255,255), (120,60,SCREEN_WIDTH-130,120), radius=12, border=2)
    types = [t.get("name", "?") for t in (current_pokemon_data.get("types") or [])]
    draw_text(screen, "Types: " + ", ".join(types), 130, 70)

    talents = [t.get("name", "?") for t in (current_pokemon_data.get("talents") or [])]
    draw_text(screen, "Talents: " + ", ".join(talents), 130, 110)

    evol = (current_pokemon_data.get("evolution", {}) or {}).get("next") or []
    evol_text = ", ".join(e.get("name", "?") for e in evol if isinstance(e, dict))
    draw_text(screen, "Évolutions: " + (evol_text if evol_text else "Aucune"), 130, 130)

    stats = current_pokemon_data.get("stats") or {}
    if stats:
        draw_stats_radar(screen, stats, center=(SCREEN_WIDTH-100, SCREEN_HEIGHT//2), radius=70)

# ------------------------------
# Boucle principale
# ------------------------------
running = True
while running:
    screen.fill((255, 255, 255))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if state == "list":
                if event.key == pygame.K_DOWN and selected_index < len(pokemon_list)-1:
                    selected_index += 1
                    if selected_index - scroll_offset >= max_visible:
                        scroll_offset += 1
                elif event.key == pygame.K_UP and selected_index > 0:
                    selected_index -= 1
                    if selected_index < scroll_offset:
                        scroll_offset -= 1
                elif event.key == pygame.K_RETURN:
                    pid = pokemon_list[selected_index][0]
                    cur.execute("SELECT raw_json FROM pokemon WHERE pokedex_id=?", (pid,))
                    row = cur.fetchone()
                    if row:
                        current_pokemon_data = json.loads(row[0])
                        state = "detail"
                elif event.key == pygame.K_ESCAPE:
                    running = False
            elif state == "detail" and event.key == pygame.K_ESCAPE:
                state = "list"
                current_sprite = None

    # ------------------------------
    # Gestion du sprite
    # ------------------------------
    sprite_file = Path(pokemon_list[selected_index][2]).name
    SPRITES_DIR = BASE_DIR / "app" / "data" / "sprites"
    sprite_path = SPRITES_DIR / sprite_file

    original_sprite = load_sprite(sprite_path)
    if original_sprite:
        if state == "list":
            current_sprite = pygame.transform.scale(original_sprite, (200, 200))
        else:
            current_sprite = pygame.transform.scale(original_sprite, (64, 64))

    # ------------------------------
    # Affichage
    # ------------------------------
    if state == "list":
        draw_list_view()
    elif state == "detail" and current_pokemon_data:
        draw_detail_view()

    pygame.display.flip()
    clock.tick(20)

pygame.quit()
conn.close()
