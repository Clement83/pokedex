import pygame
import random
import combat_dodge_game
import combat_qte_game
import combat_memory_game
from ui import draw_hp_bar
from transitions import play_lose_transition
from config import SCREEN_WIDTH, SCREEN_HEIGHT

class CombatHandler:
    def __init__(self, screen, font, game_state):
        self.screen = screen
        self.font = font
        self.game_state = game_state

    def run(self, pokemon_sprite, dresseur_back_sprite, background_image, pokemon_types, full_pokemon_data):
        """Runs the combat mini-game."""
        combat_minigames = [combat_memory_game.run] # [combat_dodge_game.run, combat_qte_game.run, combat_memory_game.run]
        selected_game = random.choice(combat_minigames)

        result = selected_game(
            self.screen, self.font, self.game_state,
            pokemon_sprite, dresseur_back_sprite,
            background_image, pokemon_types, full_pokemon_data
        )

        if result == "win":
            self._play_hp_depletion_animation(pokemon_sprite, dresseur_back_sprite, background_image)
            return "win"
        elif result == "lose":
            play_lose_transition(self.screen, pygame.time.Clock())
            return "lose"
        else: # quit
            return "quit"

    def _play_hp_depletion_animation(self, pokemon_sprite, dresseur_back_sprite, background_image):
        start_time = pygame.time.get_ticks()
        duration = 1500 # 1.5 seconds
        clock = pygame.time.Clock()

        while True:
            elapsed = pygame.time.get_ticks() - start_time
            if elapsed > duration:
                break

            # Draw the static background scene
            self.screen.blit(background_image, (0, 0))
            if dresseur_back_sprite:
                self.screen.blit(dresseur_back_sprite, (10, SCREEN_HEIGHT - dresseur_back_sprite.get_height() - 10))
            if pokemon_sprite:
                p_rect = pokemon_sprite.get_rect(center=(SCREEN_WIDTH * 0.75, SCREEN_HEIGHT * 0.35))
                self.screen.blit(pokemon_sprite, p_rect)

            # Calculate HP percentage
            progress = elapsed / duration
            hp_percent = 100 * (1 - progress)
            hp_percent = max(10, hp_percent) # Ensure it stops at a small amount

            # Draw the HP bar
            draw_hp_bar(self.screen, hp_percent, pos=(SCREEN_WIDTH - 160, 20), size=(150, 20), font=self.font)

            pygame.display.flip()
            clock.tick(60)
