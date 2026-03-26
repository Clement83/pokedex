"""
Sound design procédural – Minecraft 2D
=======================================
Aucun fichier audio requis. Tous les sons sont générés en mémoire
avec math + array, compatible Python 3.8 / Odroid GO Advance.

Sons disponibles :
  mine_tick()    – tick de frappe (pendant le minage)
  mine_done()    – bloc cassé (pop satisfaisant)
  place()        – pose de bloc (clic mat)
  chest_open()   – loot de coffre (jingle arpège montant)
  inv_change()   – changement d'item dans l'inventaire (beep discret)
"""
from __future__ import annotations

import math
import array as _array
import pygame

# ── Paramètres globaux ────────────────────────────────────────────────────────
_VOLUME = 0.45   # volume global des SFX (0.0 – 1.0)


def _sr() -> int:
    """Sample rate réel du mixer, ou 22050 par défaut."""
    info = pygame.mixer.get_init()
    return info[0] if info else 22050


def _build(samples_f: list, vol: float = 1.0) -> pygame.mixer.Sound | None:
    """
    Convertit une liste flottante [-1,1] en Sound pygame stéréo int16.
    Retourne None si le mixer n'est pas disponible.
    """
    if not pygame.mixer.get_init():
        return None
    peak = max(abs(s) for s in samples_f) or 1.0
    buf  = _array.array('h')
    for s in samples_f:
        v = int(s / peak * 32767 * vol)
        buf.append(v)   # L
        buf.append(v)   # R
    snd = pygame.mixer.Sound(buffer=buf)
    return snd


# ── Générateurs de formes d'onde ──────────────────────────────────────────────

def _noise(n: int) -> list:
    """Bruit blanc simple (pseudo-aléatoire déterministe)."""
    samples = []
    x = 1
    for _ in range(n):
        x = (x * 1664525 + 1013904223) & 0xFFFFFFFF
        samples.append((x / 0x7FFFFFFF) - 1.0)
    return samples


def _sine_decay(freq: float, dur: float, sr: int, decay: float = 8.0) -> list:
    """Sinusoïde avec enveloppe exponentielle décroissante."""
    n   = int(dur * sr)
    tau = 2.0 * math.pi * freq / sr
    return [math.sin(i * tau) * math.exp(-decay * i / n) for i in range(n)]


def _click(dur: float, sr: int) -> list:
    """Bruit blanc avec enveloppe très courte → clic/tap."""
    n    = int(dur * sr)
    raw  = _noise(n)
    # Enveloppe : montée rapide (5 %) + décroissance exponentielle
    env  = [min(1.0, i / (n * 0.05)) * math.exp(-12.0 * i / n) for i in range(n)]
    return [raw[i] * env[i] for i in range(n)]


def _arpeggio(freqs: list, note_dur: float, sr: int, decay: float = 10.0) -> list:
    """Arpège : succession de sinusoïdes courtes."""
    samples = []
    for freq in freqs:
        n   = int(note_dur * sr)
        tau = 2.0 * math.pi * freq / sr
        env_peak = int(n * 0.02)
        for i in range(n):
            env = min(1.0, i / max(1, env_peak)) * math.exp(-decay * i / n)
            samples.append(math.sin(i * tau) * env)
    return samples


# ── Synthèses pré-bake au premier appel ──────────────────────────────────────

_cache: dict = {}


def _get(name: str) -> pygame.mixer.Sound | None:
    if name in _cache:
        return _cache[name]
    if not pygame.mixer.get_init():
        return None
    sr = _sr()

    if name == "mine_tick":
        # Tap sourd sur de la roche : bruit bref + légère tonalité basse
        n   = int(0.06 * sr)
        raw = _noise(n)
        low = _sine_decay(120.0, 0.06, sr, decay=18.0)
        s   = [raw[i] * 0.4 + low[i] * 0.6 for i in range(n)]
        snd = _build(s, vol=_VOLUME * 0.6)

    elif name == "mine_done":
        # Pop + clic grave : bloc qui tombe
        n    = int(0.12 * sr)
        low  = _sine_decay(90.0, 0.12, sr, decay=12.0)
        mid  = _sine_decay(200.0, 0.05, sr, decay=25.0)
        mid += [0.0] * (n - len(mid))
        s    = [low[i] * 0.7 + mid[i] * 0.5 for i in range(n)]
        snd  = _build(s, vol=_VOLUME * 0.9)

    elif name == "place":
        # Clic court et mat (bois/pierre)
        s   = _click(0.07, sr)
        # Légère résonance grave
        low = _sine_decay(180.0, 0.07, sr, decay=20.0)
        n   = min(len(s), len(low))
        s   = [s[i] * 0.5 + low[i] * 0.5 for i in range(n)]
        snd = _build(s, vol=_VOLUME * 0.75)

    elif name == "chest_open":
        # Jingle arpège pentatonique montant (Do Mi Sol Si Do)
        freqs = [523.25, 659.25, 783.99, 987.77, 1046.5]   # C5 E5 G5 B5 C6
        s     = _arpeggio(freqs, note_dur=0.10, sr=sr, decay=8.0)
        snd   = _build(s, vol=_VOLUME)

    elif name == "inv_change":
        # Beep discret : sinusoïde courte, neutre
        s   = _sine_decay(660.0, 0.05, sr, decay=22.0)
        snd = _build(s, vol=_VOLUME * 0.45)

    elif name == "jump":
        # Whoosh léger : sinusoïde qui monte rapidement
        n   = int(0.10 * sr)
        s   = []
        for i in range(n):
            freq  = 200.0 + 400.0 * (i / n)
            phase = 2.0 * math.pi * freq * i / sr
            env   = math.exp(-8.0 * i / n)
            s.append(math.sin(phase) * env)
        snd = _build(s, vol=_VOLUME * 0.4)

    elif name == "sword_hit":
        # Sifflement métallique court + impact sourd
        n     = int(0.12 * sr)
        s     = []
        for i in range(n):
            t     = i / sr
            # Swoosh descendant (haute fréquence → basse)
            freq  = 900.0 - 600.0 * (i / n)
            phase = 2.0 * math.pi * freq * t
            env   = math.exp(-18.0 * i / n)
            s.append(math.sin(phase) * env * 0.6)
        # Impact grave bref (bruit filtré)
        n2  = int(0.04 * sr)
        imp = _noise(n2)
        imp = [v * math.exp(-30.0 * k / n2) for k, v in enumerate(imp)]
        for k in range(min(n2, n)):
            s[k] += imp[k] * 0.5
        snd = _build(s, vol=_VOLUME * 0.9)
        snd = None

    elif name == "flag_place":
        # Jingle court 3 notes montantes : Do-Mi-Sol
        freqs = [523.25, 659.25, 783.99]
        s     = _arpeggio(freqs, note_dur=0.08, sr=sr, decay=10.0)
        snd   = _build(s, vol=_VOLUME * 0.85)

    elif name == "tame":
        # Jingle doux 4 notes montantes : Mi-Sol-Si-Do (adoption familier)
        freqs = [659.25, 783.99, 987.77, 1046.5]
        s     = _arpeggio(freqs, note_dur=0.12, sr=sr, decay=7.0)
        snd   = _build(s, vol=_VOLUME * 0.9)

    elif name == "egg":
        # Pop court et aigu (ponte d'œuf)
        s   = _sine_decay(880.0, 0.08, sr, decay=15.0)
        snd = _build(s, vol=_VOLUME * 0.55)

    _cache[name] = snd
    return snd


# ── Volume et mute global ────────────────────────────────────────────────────

_muted:      bool  = False
_sfx_master: float = 1.0   # multiplicateur runtime [0.0 – 1.0]

# Boutons joystick (mêmes que music_player)
_BTN_VOL_UP:   int = 15
_BTN_VOL_DOWN: int = 14


def _apply_master() -> None:
    """Applique _sfx_master à tous les sons déjà en cache."""
    for snd in _cache.values():
        if snd is not None:
            snd.set_volume(_sfx_master)


def set_sfx_volume(v: float) -> None:
    """Définit le volume global des SFX (0.0 – 1.0)."""
    global _sfx_master
    _sfx_master = max(0.0, min(1.0, v))
    _apply_master()


def get_sfx_volume() -> float:
    return _sfx_master


def volume_up(step: float = 0.1) -> None:
    set_sfx_volume(_sfx_master + step)


def volume_down(step: float = 0.1) -> None:
    set_sfx_volume(_sfx_master - step)


def tick(events) -> None:
    """Appeler chaque frame : gère PageUp/PageDown et boutons joystick 15/14."""
    import pygame
    for e in events:
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_PAGEUP:
                volume_up()
            elif e.key == pygame.K_PAGEDOWN:
                volume_down()
        elif e.type == pygame.JOYBUTTONDOWN:
            if e.button == _BTN_VOL_UP:
                volume_up()
            elif e.button == _BTN_VOL_DOWN:
                volume_down()


def toggle_mute() -> bool:
    """Coupe/remet les SFX. Retourne True si muté après bascule."""
    global _muted
    _muted = not _muted
    return _muted


def is_muted() -> bool:
    return _muted


def _play(snd) -> None:
    """Joue un son sauf si muté."""
    if snd and not _muted:
        snd.play()


# ── API publique ──────────────────────────────────────────────────────────────

def mine_tick():
    _play(_get("mine_tick"))

def mine_done():
    _play(_get("mine_done"))

def place():
    _play(_get("place"))

def chest_open():
    _play(_get("chest_open"))

def inv_change():
    _play(_get("inv_change"))

def jump():
    _play(_get("jump"))

def sword_hit():
    _play(_get("sword_hit"))

def flag_place():
    _play(_get("flag_place"))

def tame():
    _play(_get("tame"))

def egg():
    _play(_get("egg"))
