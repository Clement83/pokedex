import pygame
import sys
import os
import subprocess
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
    {
        "title": "Pong",
        "description": "Pong classique 2 joueurs – J1 ↑↓  J2 N/M",
        "image": str(BASE_DIR / "games" / "pong" / "cover.png"),
        "path": str(BASE_DIR / "games" / "pong"),
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

    UPDATE_HOLD_DURATION = 5000  # 5 secondes
    _launcher_pressed = set()
    _update_combo_start = None
    font_ui = pygame.font.SysFont("Arial", 14)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            # ── Combo Select(12) + bouton 13 : git pull & restart ──────────────
            if event.type == pygame.JOYBUTTONDOWN:
                _launcher_pressed.add(event.button)
                if 12 in _launcher_pressed and 13 in _launcher_pressed:
                    if _update_combo_start is None:
                        _update_combo_start = pygame.time.get_ticks()
            elif event.type == pygame.JOYBUTTONUP:
                _launcher_pressed.discard(event.button)
                if event.button in (12, 13):
                    _update_combo_start = None
            # ──────────────────────────────────────────────────────────────────

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
            launcher.update(dt)
            launcher.render()

            # ── Barre de progression du combo update ──────────────────────────
            if _update_combo_start is not None:
                elapsed = pygame.time.get_ticks() - _update_combo_start
                w, h = screen.get_size()
                if elapsed >= UPDATE_HOLD_DURATION:
                    screen.fill((0, 0, 0))
                    msg = font_ui.render("Mise à jour via 'git pull'...", True, (255, 255, 255))
                    screen.blit(msg, ((w - msg.get_width()) // 2, h // 2))
                    pygame.display.flip()
                    try:
                        git_result = subprocess.run(
                            ['git', 'pull'],
                            cwd=str(BASE_DIR),
                            capture_output=True, text=True, check=True, encoding='utf-8'
                        )
                        screen.fill((0, 0, 0))
                        msg = font_ui.render("Mise à jour terminée. Redémarrage...", True, (100, 255, 100))
                        screen.blit(msg, ((w - msg.get_width()) // 2, h // 2))
                        pygame.display.flip()
                        pygame.time.wait(1500)
                        os.execv(sys.executable, ['python'] + sys.argv)
                    except Exception as e:
                        screen.fill((0, 0, 0))
                        msg = font_ui.render(f"Erreur: {e}", True, (255, 100, 100))
                        screen.blit(msg, ((w - msg.get_width()) // 2, h // 2))
                        pygame.display.flip()
                        pygame.time.wait(2000)
                    _update_combo_start = None
                else:
                    progress = elapsed / UPDATE_HOLD_DURATION
                    bar_w, bar_h = 200, 20
                    bar_x = (w - bar_w) // 2
                    bar_y = h - 40
                    pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h))
                    pygame.draw.rect(screen, (255, 200, 0), (bar_x, bar_y, int(bar_w * progress), bar_h))
                    pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 2)
                    text = font_ui.render("Maintenir : Git Pull & Restart", True, (255, 255, 255))
                    screen.blit(text, ((w - text.get_width()) // 2, bar_y - 15))
            # ──────────────────────────────────────────────────────────────────

            pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
