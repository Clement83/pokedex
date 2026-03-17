import pygame
import sys
import os
import importlib
from pathlib import Path

BASE_DIR = Path(__file__).parent

SCREEN_WIDTH = 480
SCREEN_HEIGHT = 320

GAMES = [
    {
        "title": "Pokédex",
        "description": "Attrape et explore les Pokémon",
        "image": str(BASE_DIR / "games" / "pokedex" / "app" / "data" / "assets" / "splash.png"),
        "path": str(BASE_DIR / "games" / "pokedex"),
        "entry": "main",
    },
    {
        "title": "Shifter",
        "description": "Drag Race 2 joueurs – style NFS Underground",
        "image": str(BASE_DIR / "games" / "shifter" / "asset" / "cover" / "cover.jpg"),
        "path": str(BASE_DIR / "games" / "shifter"),
        "entry": "main",
    },
]


def launch_game(game):
    """Lance un jeu : chdir dans son dossier, importe son main et l'exécute."""
    game_path = Path(game["path"])
    entry = game.get("entry", "main")

    if not (game_path / f"{entry}.py").exists():
        return

    original_cwd = Path.cwd()
    original_syspath = sys.path.copy()
    original_modules = set(sys.modules.keys())

    try:
        os.chdir(game_path)
        sys.path.insert(0, str(game_path))

        pygame.quit()

        mod = importlib.import_module(entry)
        mod.main()

    finally:
        # Nettoyer les modules chargés par le jeu
        for key in list(sys.modules.keys()):
            if key not in original_modules:
                del sys.modules[key]
        sys.path[:] = original_syspath
        os.chdir(original_cwd)


def main():
    pygame.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    if joysticks:
        print(f"Manette détectée : {joysticks[0].get_name()}")

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Game Launcher")
    clock = pygame.time.Clock()

    from launcher import Launcher
    launcher = Launcher(screen, GAMES, BASE_DIR)
    launcher.render()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            result = launcher.handle_event(event)

            if result is not None:
                if result == -1:
                    running = False
                else:
                    game = GAMES[result]
                    launch_game(game)

                    # Réinitialiser pygame et le launcher après le retour du jeu
                    pygame.init()
                    pygame.joystick.init()
                    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
                    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                    pygame.display.set_caption("Game Launcher")
                    launcher = Launcher(screen, GAMES, BASE_DIR)

        if running:
            launcher.render()
            pygame.display.flip()

        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
