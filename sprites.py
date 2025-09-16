import pygame
from pathlib import Path

sprite_cache = {}

def load_sprite(path):
    if not path or not Path(path).exists():
        return None
    if path not in sprite_cache:
        try:
            img = pygame.image.load(str(path)).convert_alpha()
            sprite_cache[path] = img
        except Exception as e:
            print(f"[ERREUR] Impossible de charger {path} : {e}")
            return None
    return sprite_cache[path]

def load_pokeball_sprites(size):
    BASE_DIR = Path.cwd()
    POKEBALL_PATH = BASE_DIR / "app" / "data" / "assets" / "pokeball.png"
    try:
        pokeball_img = pygame.image.load(POKEBALL_PATH)
        pokeball_img = pygame.transform.scale(pokeball_img, (size, size))
        pokeball_grayscale_img = pokeball_img.copy()
        # Convertir en niveaux de gris
        for x in range(pokeball_grayscale_img.get_width()):
            for y in range(pokeball_grayscale_img.get_height()):
                r, g, b, a = pokeball_grayscale_img.get_at((x, y))
                gray = int(0.299 * r + 0.587 * g + 0.114 * b)
                pokeball_grayscale_img.set_at((x, y), (gray, gray, gray, a))
        return pokeball_img, pokeball_grayscale_img
    except pygame.error:
        return None, None

def load_masterball_sprite(size):
    BASE_DIR = Path.cwd()
    MASTERBALL_PATH = BASE_DIR / "app" / "data" / "assets" / "masterball.png"
    try:
        masterball_img = pygame.image.load(MASTERBALL_PATH)
        masterball_img = pygame.transform.scale(masterball_img, (size, size))
        return masterball_img
    except pygame.error:
        return None

def apply_shadow_effect(image):
    """Applies a shadow effect to an image, turning it into a black silhouette."""
    if image is None:
        return None
    shadow_surface = image.copy()
    w, h = image.get_size()
    for x in range(w):
        for y in range(h):
            a = image.get_at((x, y))[3]
            if a > 0:
                shadow_surface.set_at((x, y), (0, 0, 0, a))
    return shadow_surface