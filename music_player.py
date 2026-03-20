"""
Gestionnaire de musique centralisé
====================================
Module singleton partagé par tous les jeux/applications du projet.
Utilise pygame.mixer.music (un seul flux à la fois).

Utilisation
-----------
    import music_player

    # Changer de dossier (démarre une piste aléatoire immédiatement)
    music_player.load_folder('/chemin/vers/audio/menu')

    # Dans chaque boucle de frame (gère aussi le volume PageUp/PageDown) :
    music_player.tick(events)

    # Contrôle du volume
    music_player.volume_up()          # +10 %
    music_player.volume_down()        # -10 %
    music_player.set_volume(0.4)      # valeur absolue [0.0 – 1.0]
    vol = music_player.get_volume()

    # Arrêter (optionnel – load_folder() arrête automatiquement ce qui joue)
    music_player.stop()

Comportement
------------
- Chaque piste joue une fois (non en boucle).
- À la fin d'une piste, une nouvelle est choisie aléatoirement parmi
  les autres fichiers du même dossier (évite la répétition immédiate).
- Formats acceptés : mp3, ogg, wav, flac.
- tick() traite automatiquement les touches PageUp/PageDown et les boutons
  joystick 15 (vol+) / 14 (vol-) sans configuration supplémentaire.
"""
from __future__ import annotations
import os
import random
import pygame

# Événement pygame déclenché automatiquement par SDL en fin de piste
_END_EVENT: int = pygame.USEREVENT + 10

# État interne du module
_folder:    str   = ''
_files:     list  = []
_last_file: str   = ''
_volume:    float = 0.55   # volume courant [0.0 – 1.0]

# Boutons joystick pour le volume (identiques à la config Pokédex)
_BTN_VOL_UP:   int = 15
_BTN_VOL_DOWN: int = 14
_muted:        bool = False


# ── API publique ──────────────────────────────────────────────────────────────

def load_folder(folder: str) -> None:
    """Change de dossier audio et démarre immédiatement une piste aléatoire.

    Si le dossier est vide ou inexistant, la musique s'arrête silencieusement.
    Stoppe automatiquement ce qui joue déjà.
    """
    global _folder, _files, _last_file
    _folder    = folder
    _last_file = ''
    _files     = _scan(folder)
    pygame.mixer.music.set_endevent(_END_EVENT)
    _play_next()


def tick(events) -> None:
    """Appeler chaque frame avec la liste des événements pygame.

    Détecte la fin de piste, enchaîne automatiquement sur une nouvelle,
    et gère le volume via PageUp/PageDown (clavier) et boutons 15/14 (joystick).
    """
    for e in events:
        if e.type == _END_EVENT:
            _play_next()
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_PAGEUP:
                volume_up()
            elif e.key == pygame.K_PAGEDOWN:
                volume_down()
        elif e.type == pygame.JOYBUTTONDOWN:
            if e.button == _BTN_VOL_UP:
                volume_up()
            elif e.button == _BTN_VOL_DOWN:
                volume_down()


def stop() -> None:
    """Arrête la musique et désactive l'événement de fin."""
    pygame.mixer.music.stop()
    pygame.mixer.music.set_endevent()   # supprime l'endevent


def set_volume(v: float) -> None:
    """Définit le volume (0.0 – 1.0) et l'applique immédiatement."""
    global _volume
    _volume = max(0.0, min(1.0, v))
    pygame.mixer.music.set_volume(_volume)


def get_volume() -> float:
    """Retourne le volume courant (0.0 – 1.0)."""
    return _volume


def volume_up(step: float = 0.1) -> None:
    """Augmente le volume d'un cran (défaut : +10 %)."""
    set_volume(_volume + step)


def volume_down(step: float = 0.1) -> None:
    """Diminue le volume d'un cran (défaut : -10 %)."""
    set_volume(_volume - step)


def toggle_mute() -> bool:
    """Coupe/remet la musique. Retourne True si muté après bascule."""
    global _muted
    _muted = not _muted
    pygame.mixer.music.set_volume(0.0 if _muted else _volume)
    return _muted


def is_muted() -> bool:
    """Retourne True si la musique est actuellement coupée."""
    return _muted


# ── Internals ─────────────────────────────────────────────────────────────────

_EXTS = {'.mp3', '.ogg', '.wav', '.flac'}


def _scan(folder: str) -> list:
    """Retourne la liste des fichiers audio dans le dossier."""
    try:
        return [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if os.path.splitext(f)[1].lower() in _EXTS
        ]
    except OSError:
        return []


def _play_next() -> None:
    """Choisit et lance une piste aléatoire (différente de la précédente)."""
    global _last_file
    if not _files:
        return

    # Privilégier une piste différente de la précédente
    choices = [f for f in _files if f != _last_file]
    if not choices:
        choices = _files

    track = random.choice(choices)
    _last_file = track

    try:
        pygame.mixer.music.load(track)
        pygame.mixer.music.set_volume(_volume)
        pygame.mixer.music.play()   # joue une fois → fin → _END_EVENT → _play_next
    except Exception as exc:
        print(f'[MusicPlayer] erreur lecture {os.path.basename(track)}: {exc}')
