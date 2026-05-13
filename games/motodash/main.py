import sys
import os

# Ajouter le dossier du jeu et la racine du projet au sys.path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pygame

import config
import scores as scores_io
from quit_combo import QuitCombo

# Import du logger pour debug Odroid
try:
    from logger import log
except ImportError:
    def log(msg, level="info"):
        print(f"[{level.upper()}] {msg}")


def _ensure_pygame():
    if not pygame.get_init():
        pygame.init()
    if not pygame.display.get_init():
        pygame.display.init()
    if not pygame.font.get_init():
        pygame.font.init()
    if not pygame.joystick.get_init():
        pygame.joystick.init()
    
    # Initialiser tous les joysticks disponibles
    joy_count = pygame.joystick.get_count()
    log(f"[Motodash] {joy_count} joystick(s) détecté(s)")
    for i in range(joy_count):
        try:
            joy = pygame.joystick.Joystick(i)
            joy.init()
            log(f"[Motodash] Joystick {i} : {joy.get_name()}, {joy.get_numbuttons()} boutons, {joy.get_numaxes()} axes, {joy.get_numhats()} hats")
        except Exception as e:
            log(f"[Motodash] Erreur init joystick {i} : {e}", "error")
    
    # Vider le buffer d'événements (critique sur Odroid)
    pygame.event.pump()
    pygame.event.clear()
    log("[Motodash] pygame initialisé, événements vidés")


def _make_screen():
    surf = pygame.display.get_surface()
    if surf is None or surf.get_size() != (config.SCREEN_WIDTH, config.SCREEN_HEIGHT):
        surf = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Motodash")
    return surf


def _splash(screen):
    """Splash screen court avec gestion des événements (compatible Odroid)."""
    font = pygame.font.SysFont("Arial", 36, bold=True)
    sub = pygame.font.SysFont("Arial", 14)
    title = font.render("MOTODASH", True, (250, 220, 90))
    s = sub.render("Trials 2D", True, (200, 200, 200))
    
    clock = pygame.time.Clock()
    frames = 0
    max_frames = 60  # 1 seconde à 60 FPS
    
    while frames < max_frames:
        clock.tick(60)
        frames += 1
        
        # Gérer les événements pour ne pas bloquer sur Odroid
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            # N'importe quelle touche/bouton skip le splash
            if event.type in (pygame.KEYDOWN, pygame.JOYBUTTONDOWN):
                return
        
        screen.fill((15, 18, 24))
        w, h = screen.get_size()
        screen.blit(title, ((w - title.get_width()) // 2, h // 2 - 30))
        screen.blit(s, ((w - s.get_width()) // 2, h // 2 + 10))
        pygame.display.flip()


def _run_game(screen, level_id, scores_state):
    from scene_game import GameScene
    from scene_result import ResultScene

    while True:
        scene = GameScene(screen, level_id)
        clock = pygame.time.Clock()
        quit_combo = QuitCombo()
        result = None
        while result is None:
            dt = clock.tick(config.FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                quit_combo.handle_event(event)
                scene.handle_event(event)
            result = scene.update(dt)
            scene.render()
            if quit_combo.update_and_draw(screen):
                return "menu"
            pygame.display.flip()

        if result.get("quit") or not result.get("finished"):
            return "menu"

        is_new_best = scores_io.record_time(
            scores_state, result["level_id"], result["time"], result["medal"],
        )
        if is_new_best:
            scores_io.save(scores_state)

        import levels
        level = levels.get(level_id)
        rscene = ResultScene(
            screen, level, result["time"], result["medal"], is_new_best,
        )
        quit_combo_result = QuitCombo()
        rresult = None
        while rresult is None:
            dt = clock.tick(config.FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                quit_combo_result.handle_event(event)
                rscene.handle_event(event)
            rresult = rscene.update(dt)
            rscene.render()
            if quit_combo_result.update_and_draw(screen):
                return "menu"
            pygame.display.flip()
        if rresult["choice"] == "retry":
            continue
        return "menu"


def main():
    log("[Motodash] Démarrage du jeu")
    _ensure_pygame()
    screen = _make_screen()
    _splash(screen)
    scores_state = scores_io.load()
    log("[Motodash] Scores chargés, entrée dans la boucle de sélection")
    
    # Importer les scènes une seule fois (hors boucle)
    from scene_select import SelectScene

    while True:
        log("[Motodash] Création de la scène de sélection")
        select = SelectScene(screen, scores_state)
        clock = pygame.time.Clock()
        quit_combo = QuitCombo()
        result = None
        
        # Afficher immédiatement la première frame pour feedback visuel
        select.render()
        pygame.display.flip()
        log("[Motodash] Première frame affichée")
        
        log("[Motodash] Entrée dans la boucle d'événements de sélection")
        while result is None:
            dt = clock.tick(config.FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                quit_combo.handle_event(event)
                select.handle_event(event)
            result = select.update(dt)
            select.render()
            if quit_combo.update_and_draw(screen):
                return
            pygame.display.flip()

        if result["choice"] == "quit":
            return
        outcome = _run_game(screen, result["choice"], scores_state)
        if outcome == "quit":
            return


if __name__ == "__main__":
    main()
    sys.exit(0)
