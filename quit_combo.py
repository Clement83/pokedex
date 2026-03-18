"""Module partagé – combinaison SELECT + START (boutons 12 + 13) pour quitter
un jeu et retourner au launcher.

Usage dans une boucle pygame :

    quit_combo = QuitCombo()

    # dans la boucle d'événements :
    for e in events:
        quit_combo.handle_event(e)

    # après le rendu, avant pygame.display.flip() :
    if quit_combo.update_and_draw(screen):
        return          # quitter le jeu → retour launcher

    pygame.display.flip()
"""

import pygame

QUIT_BUTTONS  = (12, 13)   # SELECT + START – identiques au combo git-pull du launcher
QUIT_DURATION = 3000       # millisecondes à maintenir avant de quitter


class QuitCombo:
    """Détecte la combinaison SELECT+START et affiche un timer de sortie."""

    def __init__(self):
        self._pressed = set()
        self._start   = None
        self._font    = None   # initialisé à la demande (pygame doit être actif)

    def handle_event(self, event) -> None:
        """À appeler pour chaque événement pygame de la boucle principale."""
        if event.type == pygame.JOYBUTTONDOWN:
            self._pressed.add(event.button)
            if all(b in self._pressed for b in QUIT_BUTTONS):
                if self._start is None:
                    self._start = pygame.time.get_ticks()
        elif event.type == pygame.JOYBUTTONUP:
            self._pressed.discard(event.button)
            if event.button in QUIT_BUTTONS:
                self._start = None

    def update_and_draw(self, screen) -> bool:
        """
        Dessine la barre de progression si le combo est actif.
        Retourne True quand le timer arrive à terme (il faut quitter).
        Doit être appelé AVANT pygame.display.flip().
        """
        if self._start is None:
            return False

        elapsed = pygame.time.get_ticks() - self._start
        if elapsed >= QUIT_DURATION:
            return True

        if self._font is None:
            self._font = pygame.font.SysFont("Arial", 11)

        progress = elapsed / QUIT_DURATION
        w, h     = screen.get_size()
        bar_w    = 220
        bar_h    = 14
        bar_x    = (w - bar_w) // 2
        bar_y    = h - bar_h - 6

        # Fond sombre derrière le texte et la barre
        pygame.draw.rect(screen, (20, 20, 20),
                         (bar_x - 4, bar_y - 18, bar_w + 8, bar_h + 22))

        # Texte
        txt = self._font.render("Maintenir SELECT+START : Retour launcher", True, (210, 210, 210))
        screen.blit(txt, ((w - txt.get_width()) // 2, bar_y - 15))

        # Barre fond
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h))
        # Barre progression
        pygame.draw.rect(screen, (220, 60, 60), (bar_x, bar_y, int(bar_w * progress), bar_h))
        # Bordure
        pygame.draw.rect(screen, (180, 180, 180), (bar_x, bar_y, bar_w, bar_h), 1)

        return False
