import pygame
import random
import math
from config import SCREEN_WIDTH, SCREEN_HEIGHT, KEY_MAPPINGS
import controls

# Game settings
SURVIVAL_TIME_MS = 15000  # 15 seconds
PLAYER_SPEED = 5
PROJECTILE_SPEED = 4
PROJECTILE_ADD_RATE = 20  # Lower is faster, adds a projectile every X frames

class Player(pygame.sprite.Sprite):
    def __init__(self, dresseur_sprite):
        super().__init__()
        # Assuming dresseur_sprite is the back view, which is what we have.
        # For this game, a front-facing or smaller sprite might be better,
        # but we'll use what we have.
        self.image = pygame.transform.scale(dresseur_sprite, (48, 48))
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))

    def update(self, keys):
        if keys["left"]:
            self.rect.x -= PLAYER_SPEED
        if keys["right"]:
            self.rect.x += PLAYER_SPEED
        if keys["up"]:
            self.rect.y -= PLAYER_SPEED
        if keys["down"]:
            self.rect.y += PLAYER_SPEED

        # Keep player on screen
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(SCREEN_WIDTH, self.rect.right)
        self.rect.top = max(0, self.rect.top)
        self.rect.bottom = min(SCREEN_HEIGHT, self.rect.bottom)

class Projectile(pygame.sprite.Sprite):
    TYPE_COLORS = {
        "Plante": (120, 200, 80), "Poison": (160, 64, 160), "Feu": (240, 128, 48),
        "Vol": (168, 144, 240), "Eau": (104, 144, 240), "Insecte": (168, 184, 32),
        "Normal": (168, 168, 120), "Électrik": (248, 208, 48), "Sol": (224, 192, 104),
        "Fée": (238, 153, 172), "Combat": (192, 48, 40), "Psy": (248, 88, 136),
        "Roche": (184, 160, 56), "Acier": (184, 184, 208), "Glace": (152, 216, 216),
        "Spectre": (112, 88, 152), "Dragon": (112, 56, 248), "Ténèbres": (112, 88, 72),
    }

    def __init__(self, start_pos, pokemon_types):
        super().__init__()
        
        primary_type = pokemon_types[0] if pokemon_types else "Normal"
        self.color = self.TYPE_COLORS.get(primary_type, (255, 255, 255))

        self.image = self._create_surface(primary_type)
        self.rect = self.image.get_rect(center=start_pos)
        
        target_x = random.randint(0, SCREEN_WIDTH)
        target_y = random.randint(SCREEN_HEIGHT // 2, SCREEN_HEIGHT)
        
        self.velocity = pygame.math.Vector2(target_x - start_pos[0], target_y - start_pos[1]).normalize() * PROJECTILE_SPEED
        
        # Rotate sprite to face direction of movement
        angle = self.velocity.angle_to(pygame.math.Vector2(1, 0))
        self.image = pygame.transform.rotate(self.image, angle)

    def _create_surface(self, p_type):
        surface = pygame.Surface((30, 30), pygame.SRCALPHA)
        if p_type == "Eau":
            pygame.draw.circle(surface, self.color, (15, 15), 10)
            pygame.draw.circle(surface, (255, 255, 255, 90), (12, 12), 3)
        elif p_type == "Feu":
            pygame.draw.polygon(surface, self.color, [(5, 30), (15, 0), (25, 30)])
        elif p_type in ["Plante", "Insecte"]:
            pygame.draw.line(surface, self.color, (0, 15), (30, 15), 4)
            pygame.draw.line(surface, self.color, (20, 5), (30, 15), 4)
            pygame.draw.line(surface, self.color, (20, 25), (30, 15), 4)
        elif p_type in ["Sol", "Roche"]:
            pygame.draw.rect(surface, self.color, (5, 5, 20, 20))
        elif p_type == "Électrik":
            pygame.draw.polygon(surface, self.color, [(0, 15), (10, 0), (10, 10), (20, 0), (20, 15), (30, 15), (20, 30), (20, 20), (10, 30), (10, 15)])
        elif p_type in ["Psy", "Fée"]:
            # Simple star
            points = []
            for i in range(5):
                angle = math.radians(i * 72 - 54)
                outer_point = (15 + 14 * math.cos(angle), 15 + 14 * math.sin(angle))
                angle += math.radians(36)
                inner_point = (15 + 6 * math.cos(angle), 15 + 6 * math.sin(angle))
                points.extend([outer_point, inner_point])
            pygame.draw.polygon(surface, self.color, points)
        else: # Normal, Vol, etc.
            pygame.draw.line(surface, self.color, (0, 15), (30, 15), 5)
        return surface

    def update(self):
        self.rect.move_ip(self.velocity)
        if not pygame.Rect(-30, -30, SCREEN_WIDTH + 60, SCREEN_HEIGHT + 60).colliderect(self.rect):
            self.kill()

def run(screen, font, game_state, pokemon_sprite, dresseur_sprite, background_image, pokemon_types):
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()

    player = Player(dresseur_sprite)
    player_group = pygame.sprite.GroupSingle(player)
    projectiles = pygame.sprite.Group()

    pokemon_pos = (SCREEN_WIDTH // 2, 60)
    pokemon_rect = pokemon_sprite.get_rect(center=pokemon_pos)
    
    keys = {"up": False, "down": False, "left": False, "right": False}
    
    projectile_timer = 0

    while True:
        for event in pygame.event.get():
            controls.process_joystick_input(game_state, event)
            if event.type == pygame.QUIT: return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key in KEY_MAPPINGS["UP"]: keys["up"] = True
                if event.key in KEY_MAPPINGS["DOWN"]: keys["down"] = True
                if event.key in KEY_MAPPINGS["LEFT"]: keys["left"] = True
                if event.key in KEY_MAPPINGS["RIGHT"]: keys["right"] = True
                if event.key in KEY_MAPPINGS["QUIT"]: return "quit"
                if event.key in KEY_MAPPINGS["CANCEL"]: return "lose"
            if event.type == pygame.KEYUP:
                if event.key in KEY_MAPPINGS["UP"]: keys["up"] = False
                if event.key in KEY_MAPPINGS["DOWN"]: keys["down"] = False
                if event.key in KEY_MAPPINGS["LEFT"]: keys["left"] = False
                if event.key in KEY_MAPPINGS["RIGHT"]: keys["right"] = False

        player.update(keys)
        projectiles.update()

        projectile_timer += 1
        if projectile_timer >= PROJECTILE_ADD_RATE:
            projectile_timer = 0
            projectiles.add(Projectile(pokemon_rect.center, pokemon_types))

        if pygame.sprite.spritecollide(player, projectiles, True, pygame.sprite.collide_mask):
            return "lose"

        if pygame.time.get_ticks() - start_time >= SURVIVAL_TIME_MS:
            return "win"

        if background_image:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill((20, 20, 30)) # Dark blue background
        screen.blit(pokemon_sprite, pokemon_rect)
        player_group.draw(screen)
        projectiles.draw(screen)

        time_left = (SURVIVAL_TIME_MS - (pygame.time.get_ticks() - start_time)) / 1000
        timer_text = font.render(f"SURVIVE: {max(0, time_left):.1f}s", True, (255, 255, 255))
        screen.blit(timer_text, (10, 10))

        pygame.display.flip()
        clock.tick(60)
