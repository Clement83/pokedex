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
