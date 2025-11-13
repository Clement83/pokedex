import random

import pygame

import combat_dodge_game
import combat_memory_game
import combat_qte_game
from config import SCREEN_HEIGHT, SCREEN_WIDTH
from transitions import play_lose_transition
from ui import draw_hp_bar


class CombatHandler:
    def __init__(self, screen, font, game_state):
        self.screen = screen
        self.font = font
        self.game_state = game_state

    def run(self, pokemon_sprite, dresseur_back_sprite, background_image, pokemon_types, full_pokemon_data):
        """Runs the combat mini-game."""
        combat_minigames = [combat_qte_game.run ] #, combat_dodge_game.run, combat_memory_game.run]
        selected_game = random.choice(combat_minigames)

        result = selected_game(
            self.screen, self.font, self.game_state,
            pokemon_sprite, dresseur_back_sprite,
            background_image, pokemon_types, full_pokemon_data
        )

        if result == "win":
            self._play_hp_depletion_animation(pokemon_sprite, dresseur_back_sprite, background_image, full_pokemon_data)
            return "win"
        elif result == "lose":
            play_lose_transition(self.screen, pygame.time.Clock())
            return "lose"
        else: # quit
            return "quit"

    def _play_hp_depletion_animation(self, pokemon_sprite, dresseur_back_sprite, background_image, full_pokemon_data):
        start_time = pygame.time.get_ticks()
        duration = 1500 # 1.5 seconds
        clock = pygame.time.Clock()
        shake_duration = 90  # Shake for the entire animation duration (1.5 seconds at 60 fps)

        # Play pokemon cry
        pokemon_name_en = full_pokemon_data.get('name', {}).get('en', '')
        if pokemon_name_en:
            cry_path = self.game_state.BASE_DIR / "pokemon_audio" / "cries" / f"{pokemon_name_en.lower()}.mp3"
            if cry_path.exists():
                try:
                    cry_sound = pygame.mixer.Sound(str(cry_path))
                    cry_sound.set_volume(self.game_state.music_volume)
                    cry_sound.play()
                except pygame.error as e:
                    print(f"Error playing cry: {e}")

        while True:
            elapsed = pygame.time.get_ticks() - start_time
            if elapsed > duration:
                break

            # Screen shake logic
            shake_offset = (0, 0)
            if shake_duration > 0:
                shake_duration -= 1
                if shake_duration > 0:
                    shake_offset = (random.randint(-7, 7), random.randint(-7, 7))

            # Draw to game surface
            game_surface = pygame.Surface(self.screen.get_size())
            game_surface.blit(background_image, (0, 0))
            if dresseur_back_sprite:
                game_surface.blit(dresseur_back_sprite, (10, SCREEN_HEIGHT - dresseur_back_sprite.get_height() - 10))
            if pokemon_sprite:
                p_rect = pokemon_sprite.get_rect(center=(SCREEN_WIDTH * 0.75, SCREEN_HEIGHT * 0.35))
                game_surface.blit(pokemon_sprite, p_rect)

            # Calculate HP percentage
            progress = elapsed / duration
            hp_percent = 100 * (1 - progress)
            hp_percent = max(10, hp_percent) # Ensure it stops at a small amount

            # Draw the HP bar
            draw_hp_bar(game_surface, hp_percent, pos=(SCREEN_WIDTH - 160, 20), size=(150, 20), font=self.font)

            # Blit the game surface to the screen with shake offset
            self.screen.blit(game_surface, shake_offset)

            pygame.display.flip()
            clock.tick(60)
