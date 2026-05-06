"""Scène de jeu Jungle Run.

Deux mondes côte à côte (split-screen vertical : J1 en haut, J2 en bas).
Survie pure : chaque joueur court tant qu'il vit. Quand les deux sont morts,
on retourne le gagnant (= celui qui a parcouru le plus loin) ou -1 en cas
d'égalité parfaite.
"""
import random
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    VIEW_W, VIEW_H, SEPARATOR_H, SEPARATOR_COL,
    PLAYER_J1, PLAYER_J2,
    J1_DPAD_BTNS, J2_FACE_BTNS, J1_KEYS, J2_KEYS, AXIS_DEAD,
)
from quit_combo import QuitCombo
from world import World
from renderer import draw as draw_world


def _is_j1_jump_event(e) -> bool:
    """Détecte un edge "press" J1 (haut/bas/gauche/droite ou clavier)."""
    if e.type == pygame.KEYDOWN and e.key in J1_KEYS:
        return True
    if e.type == pygame.JOYBUTTONDOWN and e.button in J1_DPAD_BTNS:
        return True
    if e.type == pygame.JOYHATMOTION:
        x, y = e.value
        if x != 0 or y != 0:
            return True
    if e.type == pygame.JOYAXISMOTION and e.axis in (0, 1):
        if abs(e.value) > AXIS_DEAD:
            return True
    return False


def _is_j2_jump_event(e) -> bool:
    if e.type == pygame.KEYDOWN and e.key in J2_KEYS:
        return True
    if e.type == pygame.JOYBUTTONDOWN and e.button in J2_FACE_BTNS:
        return True
    return False


def run(screen, joysticks):
    """Lance une partie.

    Retourne `(winner, dist1, dist2)` avec winner ∈ {0, 1, -1} (-1 = égalité),
    ou `None` si le joueur quitte (combo SELECT+START / fenêtre fermée).
    """
    clock = pygame.time.Clock()
    font_hud = pygame.font.SysFont("Arial", 12, bold=True)

    seed = random.randint(0, 1_000_000)
    world1 = World(seed)
    world2 = World(seed + 1)

    # Surfaces de viewport (480x160 chacune).
    surf1 = pygame.Surface((VIEW_W, VIEW_H))
    surf2 = pygame.Surface((VIEW_W, VIEW_H))

    quit_combo = QuitCombo()

    # Anti-rebond pour éviter qu'un seul "press" ne déclenche aussi le saut au prochain frame.
    # On consomme l'event et on positionne un flag pour le prochain update().
    prev_axis_state = {0: 0, 1: 0}  # pour edge detection sur axes

    # Petite intro "GO" pour stabiliser l'affichage.
    _show_go(screen, font_hud)

    while True:
        dt = clock.tick(FPS) / 1000.0
        events = pygame.event.get()

        jump1 = False
        jump2 = False
        for e in events:
            quit_combo.handle_event(e)
            if e.type == pygame.QUIT:
                return None

            # Filtre l'edge "axes" pour ne pas re-tirer chaque frame.
            if e.type == pygame.JOYAXISMOTION and e.axis in (0, 1):
                prev = prev_axis_state.get(e.axis, 0)
                cur = 1 if e.value > AXIS_DEAD else (-1 if e.value < -AXIS_DEAD else 0)
                if cur != prev and cur != 0:
                    jump1 = True
                prev_axis_state[e.axis] = cur
                continue

            if _is_j1_jump_event(e):
                jump1 = True
            if _is_j2_jump_event(e):
                jump2 = True

        world1.update(dt, jump1)
        world2.update(dt, jump2)

        # Rendu.
        draw_world(surf1, world1, PLAYER_J1, font_hud, "J1")
        draw_world(surf2, world2, PLAYER_J2, font_hud, "J2")

        screen.blit(surf1, (0, 0))
        pygame.draw.rect(screen, SEPARATOR_COL, (0, VIEW_H, SCREEN_WIDTH, SEPARATOR_H))
        screen.blit(surf2, (0, VIEW_H + SEPARATOR_H))

        # Fin de partie quand les 2 joueurs sont morts ET assez tombés pour disparaître.
        both_dead = (not world1.player.alive and not world2.player.alive)
        if both_dead:
            # Petite tempo pour voir la chute finale du dernier mort.
            pygame.time.wait(500)
            d1, d2 = world1.distance, world2.distance
            if d1 > d2: return (0, d1, d2)
            if d2 > d1: return (1, d1, d2)
            return (-1, d1, d2)

        if quit_combo.update_and_draw(screen):
            return None
        pygame.display.flip()


def _show_go(screen, font_hud):
    """Affiche un compte à rebours 3-2-1-GO! avant de lancer la course."""
    clock = pygame.time.Clock()
    font_big = pygame.font.SysFont("Arial", 90, bold=True)
    for label, color in [("3", (250, 200, 80)),
                         ("2", (250, 180, 80)),
                         ("1", (250, 130, 80)),
                         ("GO !", (90, 230, 90))]:
        t0 = pygame.time.get_ticks()
        while pygame.time.get_ticks() - t0 < (350 if label != "GO !" else 500):
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return
            screen.fill((20, 30, 25))
            surf = font_big.render(label, True, color)
            screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2,
                               SCREEN_HEIGHT // 2 - surf.get_height() // 2))
            sub = font_hud.render("J1 = D-pad / J2 = boutons droits", True, (180, 180, 180))
            screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2,
                              SCREEN_HEIGHT - 22))
            pygame.display.flip()
            clock.tick(FPS)
