import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT

def run(screen, font, pokemon_sprite, pokeball_sprite):
    pokeball_x = 0
    pokeball_y = SCREEN_HEIGHT // 2
    pokeball_speed = 5
    pokeball_launched = False

    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    pokeball_launched = True
                if event.key == pygame.K_ESCAPE:
                    return "back"

        if not pokeball_launched:
            pokeball_y += pokeball_speed
            if pokeball_y > SCREEN_HEIGHT or pokeball_y < 0:
                pokeball_speed = -pokeball_speed
        else:
            pokeball_x += 10
            pokemon_rect = pokemon_sprite.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            pokeball_rect = pokeball_sprite.get_rect(topleft=(pokeball_x, pokeball_y))
            if pokemon_rect.colliderect(pokeball_rect):
                return "caught"
            if pokeball_x > SCREEN_WIDTH:
                return "failed"

        screen.fill((200, 220, 255))
        if pokemon_sprite:
            pokemon_rect = pokemon_sprite.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(pokemon_sprite, pokemon_rect)
        
        if pokeball_sprite:
            screen.blit(pokeball_sprite, (pokeball_x, pokeball_y))

        font.render("Appuyez sur Espace pour lancer la Pokéball !", True, (0,0,0))
        screen.blit(font.render("Appuyez sur Espace pour lancer la Pokéball !", True, (0,0,0)), (20, 20))

        pygame.display.flip()
        clock.tick(60)
