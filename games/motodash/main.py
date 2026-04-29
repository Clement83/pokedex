import sys
import pygame

import config
import scores as scores_io


def _ensure_pygame():
    if not pygame.get_init():
        pygame.init()
    if not pygame.display.get_init():
        pygame.display.init()
    if not pygame.font.get_init():
        pygame.font.init()
    if not pygame.joystick.get_init():
        pygame.joystick.init()
    for i in range(pygame.joystick.get_count()):
        try:
            pygame.joystick.Joystick(i).init()
        except Exception:
            pass


def _make_screen():
    surf = pygame.display.get_surface()
    if surf is None or surf.get_size() != (config.SCREEN_WIDTH, config.SCREEN_HEIGHT):
        surf = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Motodash")
    return surf


def _splash(screen):
    font = pygame.font.SysFont("Arial", 36, bold=True)
    sub = pygame.font.SysFont("Arial", 14)
    title = font.render("MOTODASH", True, (250, 220, 90))
    s = sub.render("BETA — Trials 2D", True, (200, 200, 200))
    for _ in range(60):
        screen.fill((15, 18, 24))
        w, h = screen.get_size()
        screen.blit(title, ((w - title.get_width()) // 2, h // 2 - 30))
        screen.blit(s, ((w - s.get_width()) // 2, h // 2 + 10))
        pygame.display.flip()
        pygame.time.delay(16)


def _run_game(screen, level_id, scores_state):
    from scene_game import GameScene
    from scene_result import ResultScene

    while True:
        scene = GameScene(screen, level_id)
        clock = pygame.time.Clock()
        result = None
        while result is None:
            dt = clock.tick(config.FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                scene.handle_event(event)
            result = scene.update(dt)
            scene.render()
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
        rresult = None
        while rresult is None:
            dt = clock.tick(config.FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                rscene.handle_event(event)
            rresult = rscene.update(dt)
            rscene.render()
            pygame.display.flip()
        if rresult["choice"] == "retry":
            continue
        return "menu"


def main():
    _ensure_pygame()
    screen = _make_screen()
    _splash(screen)
    scores_state = scores_io.load()

    while True:
        from scene_select import SelectScene
        select = SelectScene(screen, scores_state)
        clock = pygame.time.Clock()
        result = None
        while result is None:
            dt = clock.tick(config.FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                select.handle_event(event)
            result = select.update(dt)
            select.render()
            pygame.display.flip()

        if result["choice"] == "quit":
            return
        outcome = _run_game(screen, result["choice"], scores_state)
        if outcome == "quit":
            return


if __name__ == "__main__":
    main()
    sys.exit(0)
