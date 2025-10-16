import pygame
import random
from config import SCREEN_WIDTH, SCREEN_HEIGHT, REGIONS, KEY_MAPPINGS
from db import get_user_preference, set_user_preference
import controls
from sprites import load_sprite
from ui import draw_rounded_rect

# Grid configuration for regions
GRID_COLS = 3
IMAGE_SIZE = 90 # Size for region images (increased)
GRID_START_Y = 5 # Starting Y position for the grid (moved up further)
GRID_PADDING = 10 # Padding between images (reduced)

class RegionSelectionHandler:
    def __init__(self, screen, font, game_state):
        self.screen = screen
        self.font = font
        self.game_state = game_state

    def run(self):
        unlocked_region = get_user_preference(self.game_state.conn, 'new_region_unlocked')
        if unlocked_region:
            self._play_region_unlock_animation(unlocked_region)
            set_user_preference(self.game_state.conn, 'new_region_unlocked', '')

        region_names = list(REGIONS.keys())
        num_regions = len(region_names)
        GRID_ROWS = (num_regions + GRID_COLS - 1) // GRID_COLS
        region_images_loaded = {name: pygame.transform.scale(load_sprite(self.game_state.BASE_DIR / f"app/data/assets/{name.lower()}/icon.png"), (IMAGE_SIZE, IMAGE_SIZE)) for name in region_names}

        selected_row, selected_col = 0, 0
        last_region = get_user_preference(self.game_state.conn, "last_selected_region")
        if last_region and last_region in region_names:
            idx = region_names.index(last_region)
            selected_row, selected_col = idx // GRID_COLS, idx % GRID_COLS

        while True:
            for event in pygame.event.get():
                controls.process_joystick_input(self.game_state, event)
                if event.type == pygame.QUIT:
                    return "quit", None
                if event.type == pygame.KEYDOWN:
                    key_actions = {"UP": lambda: (selected_row - 1) % GRID_ROWS, "DOWN": lambda: (selected_row + 1) % GRID_ROWS, "LEFT": lambda: (selected_col - 1) % GRID_COLS, "RIGHT": lambda: (selected_col + 1) % GRID_COLS}
                    if event.key in KEY_MAPPINGS["UP"]: selected_row = key_actions["UP"]()
                    elif event.key in KEY_MAPPINGS["DOWN"]: selected_row = key_actions["DOWN"]()
                    elif event.key in KEY_MAPPINGS["LEFT"]: selected_col = key_actions["LEFT"]()
                    elif event.key in KEY_MAPPINGS["RIGHT"]: selected_col = key_actions["RIGHT"]()
                    elif event.key in KEY_MAPPINGS["QUIT"]:
                        return "quit", None
                    elif event.key in KEY_MAPPINGS["CANCEL"]:
                        return "main_menu", None
                    elif event.key in KEY_MAPPINGS["CONFIRM"]:
                        idx = selected_row * GRID_COLS + selected_col
                        if idx < num_regions:
                            selected_region_name = region_names[idx]
                            region_data = REGIONS[selected_region_name]
                            if region_data["min_id"] >= self.game_state.current_max_pokedex_id:
                                continue
                            set_user_preference(self.game_state.conn, "last_selected_region", selected_region_name)
                            return "encounter", selected_region_name

            self.screen.fill((0, 0, 0))
            self._draw_region_grid(region_names, region_images_loaded, selected_row, selected_col, GRID_ROWS)
            self._draw_region_info(region_names, selected_row, selected_col)
            pygame.display.flip()
            pygame.time.Clock().tick(60)

    def _play_region_unlock_animation(self, unlocked_region_name):
        from ui import draw_rounded_rect
        region_names = list(REGIONS.keys())
        region_images = {name: load_sprite(self.game_state.BASE_DIR / f"app/data/assets/{name.lower()}/icon.png") for name in region_names}
        unlocked_image = region_images.get(unlocked_region_name)
        if not unlocked_image:
            return

        try:
            unlocked_idx = region_names.index(unlocked_region_name)
        except ValueError:
            return

        GRID_ROWS = (len(region_names) + GRID_COLS - 1) // GRID_COLS
        unlocked_row, unlocked_col = unlocked_idx // GRID_COLS, unlocked_idx % GRID_COLS
        start_x = (SCREEN_WIDTH - (GRID_COLS * IMAGE_SIZE + (GRID_COLS - 1) * GRID_PADDING)) // 2
        end_pos = (start_x + unlocked_col * (IMAGE_SIZE + GRID_PADDING), GRID_START_Y + unlocked_row * (IMAGE_SIZE + GRID_PADDING))

        clock = pygame.time.Clock()
        start_time = pygame.time.get_ticks()
        total_duration = 5000 # 5 seconds total
        msg_duration = 2000
        anim_duration = 1500
        settle_duration = 1500

        try:
            big_font = pygame.font.Font(None, 40)
        except: big_font = self.font

        while True:
            elapsed = pygame.time.get_ticks() - start_time
            if elapsed > total_duration: break

            for event in pygame.event.get():
                if event.type == pygame.QUIT: return "quit"
                if event.type == pygame.KEYDOWN and elapsed > msg_duration:
                    if event.key in KEY_MAPPINGS["CONFIRM"] or event.key in KEY_MAPPINGS["CANCEL"]:
                        return

            self.screen.fill((0, 0, 0))
            self._draw_region_grid(region_names, {n: pygame.transform.scale(i, (IMAGE_SIZE, IMAGE_SIZE)) for n, i in region_images.items()}, -1, -1, GRID_ROWS)

            if elapsed < msg_duration:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                self.screen.blit(overlay, (0, 0))
                msg_rect = pygame.Rect(40, SCREEN_HEIGHT // 2 - 50, SCREEN_WIDTH - 80, 100)
                draw_rounded_rect(self.screen, (240, 240, 255), msg_rect, radius=15, border=2, border_color=(20,20,20))
                line1_surf = big_font.render("Nouvelle région !", True, (0, 0, 139))
                line2_surf = self.font.render(f"La région de {unlocked_region_name} est disponible !", True, (30, 30, 30))
                self.screen.blit(line1_surf, (msg_rect.centerx - line1_surf.get_width() // 2, msg_rect.y + 15))
                self.screen.blit(line2_surf, (msg_rect.centerx - line2_surf.get_width() // 2, msg_rect.y + 55))
            elif elapsed < msg_duration + anim_duration:
                progress = (elapsed - msg_duration) / anim_duration
                start_size = SCREEN_HEIGHT
                end_size = IMAGE_SIZE
                curr_size = int(start_size + (end_size - start_size) * progress)
                start_center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                end_center = (end_pos[0] + IMAGE_SIZE // 2, end_pos[1] + IMAGE_SIZE // 2)
                curr_center_x = int(start_center[0] + (end_center[0] - start_center[0]) * progress)
                curr_center_y = int(start_center[1] + (end_center[1] - start_center[1]) * progress)
                
                scaled_img = pygame.transform.smoothscale(unlocked_image, (curr_size, curr_size))
                img_rect = scaled_img.get_rect(center=(curr_center_x, curr_center_y))
                self.screen.blit(scaled_img, img_rect)
            else:
                if int((elapsed - (msg_duration + anim_duration)) / 250) % 2 == 0:
                    pygame.draw.rect(self.screen, (255, 255, 0), (end_pos[0], end_pos[1], IMAGE_SIZE, IMAGE_SIZE), 4)

            pygame.display.flip()
            clock.tick(60)

    def _draw_region_grid(self, region_names, images, sel_row, sel_col, grid_rows):
        start_x = (SCREEN_WIDTH - (GRID_COLS * IMAGE_SIZE + (GRID_COLS - 1) * GRID_PADDING)) // 2
        for i, name in enumerate(region_names):
            row, col = i // GRID_COLS, i % GRID_COLS
            if row >= grid_rows: continue
            x = start_x + col * (IMAGE_SIZE + GRID_PADDING)
            y = GRID_START_Y + row * (IMAGE_SIZE + GRID_PADDING)
            self.screen.blit(images[name], (x, y))
            if REGIONS[name]["min_id"] >= self.game_state.current_max_pokedex_id:
                overlay = pygame.Surface((IMAGE_SIZE, IMAGE_SIZE), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 150))
                self.screen.blit(overlay, (x, y))
            if row == sel_row and col == sel_col:
                pygame.draw.rect(self.screen, (255, 255, 0), (x, y, IMAGE_SIZE, IMAGE_SIZE), 3)

    def _draw_region_info(self, region_names, sel_row, sel_col):
        idx = sel_row * GRID_COLS + sel_col
        if idx < len(region_names):
            name = region_names[idx]
            is_locked = REGIONS[name]["min_id"] >= self.game_state.current_max_pokedex_id
            text = f"{name} - LOCKED" if is_locked else name
            color = (255, 100, 100) if is_locked else (255, 255, 255)
            
            rendered_text = self.font.render(text, True, color)
            rect = rendered_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 10))
            self.screen.blit(rendered_text, rect)
