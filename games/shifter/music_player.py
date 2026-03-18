"""
Gestionnaire de musique aléatoire – Shifter
===========================================
Module singleton. Utilise pygame.mixer.music (un seul flux à la fois).

Utilisation
-----------
    import music_player

    # Changer de dossier (démarre une piste aléatoire immédiatement)
    music_player.load_folder('/chemin/vers/audio/menu')

    # Dans chaque boucle de frame :
    music_player.tick(events)

    # Arrêter (optionnel – load_folder() arrête automatiquement ce qui joue)
    music_player.stop()

Comportement
------------
- Chaque piste joue une fois (non en boucle).
- À la fin d'une piste, une nouvelle est choisie aléatoirement parmi
  les autres fichiers du même dossier (évite la répétition immédiate).
- Formats acceptés : mp3, ogg, wav, flac.
"""
from __future__ import annotations
import os
import random
import pygame

# Événement pygame déclenché automatiquement par SDL en fin de piste
_END_EVENT: int = pygame.USEREVENT + 10

# État interne du module
_folder:    str  = ''
_files:     list = []
_last_file: str  = ''


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

    Détecte la fin de piste et enchaîne automatiquement sur une nouvelle.
    """
    for e in events:
        if e.type == _END_EVENT:
            _play_next()


def stop() -> None:
    """Arrête la musique et désactive l'événement de fin."""
    pygame.mixer.music.stop()
    pygame.mixer.music.set_endevent()   # supprime l'endevent


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
        pygame.mixer.music.set_volume(0.55)
        pygame.mixer.music.play()   # joue une fois → fin → _END_EVENT → _play_next
    except Exception as exc:
        print(f'[MusicPlayer] erreur lecture {os.path.basename(track)}: {exc}')
