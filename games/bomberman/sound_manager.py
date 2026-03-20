"""
Effets sonores procéduraux – Bomberman
========================================
Aucun fichier audio requis.
Tout est synthétisé via math + array + pygame.mixer.Sound.
Même principe que engine_sound.py dans Shifter.

Sons disponibles
----------------
- bomb_place  : clunk grave quand on pose une bombe
- fuse_tick   : crépitement de mèche (s'accélère avant l'explosion)
- explosion   : boom large bande + grondement basse fréquence
- bonus       : arpège ascendant joyeux (ramassage bonus)
- death       : descente triste (mort d'un joueur)
"""
from __future__ import annotations

import math
import array as _array
import random as _random
import pygame


# ── Helpers bas niveau ────────────────────────────────────────────────────────

def _mixer_sr() -> int:
    """Renvoie la fréquence d'échantillonnage réelle du mixer pygame."""
    info = pygame.mixer.get_init()
    return info[0] if info else 22050


def _to_sound(samples: list, amp: float = 0.95) -> pygame.mixer.Sound:
    """Convertit une liste flottante [-1..1] en Sound pygame stéréo int16."""
    if not samples:
        return pygame.mixer.Sound(buffer=_array.array('h', [0, 0]))
    peak = max(abs(s) for s in samples) or 1.0
    scale = (32767.0 * amp) / peak
    buf = _array.array('h')
    for s in samples:
        val = int(max(-32768.0, min(32767.0, s * scale)))
        buf.append(val)   # canal L
        buf.append(val)   # canal R
    return pygame.mixer.Sound(buffer=buf)


# ── Synthèse de chaque bruitage ───────────────────────────────────────────────

def _make_bomb_place(sr: int) -> pygame.mixer.Sound:
    """Clunk grave + bruit d'impact : son de pose de bombe."""
    dur = 0.18
    n = int(sr * dur)
    samples = []
    for i in range(n):
        p = i / n
        env = math.exp(-9.0 * p)
        # Sinusoïde qui descend en fréquence (210 Hz → 70 Hz)
        f = 210.0 - 140.0 * p
        v = env * math.sin(2 * math.pi * f * i / sr)
        # Petit bruit d'impact concentré au début
        v += 0.30 * env * _random.uniform(-1.0, 1.0) * math.exp(-30.0 * p)
        samples.append(v)
    return _to_sound(samples, amp=0.85)


def _make_fuse_tick(sr: int) -> pygame.mixer.Sound:
    """Sifflement de m\u00e8che 'pshhhiiite' : bruit blanc filtr\u00e9 passe-bande.

    Technique : deux LP en cascade (coupe-bas \u00e0 600 Hz et coupe-haut \u00e0 4500 Hz).
    La diff\u00e9rence donne un signal centr\u00e9 sur les m\u00e9diums-aigus caract\u00e9ristiques
    du sifflement d'une m\u00e8che.
    Enveloppe : mont\u00e9e douce (10 % du son) puis d\u00e9croissance exponentielle.
    """
    dur = 0.22
    n   = int(sr * dur)

    # LP \u00e0 4500 Hz : retire les ultra-hautes fr\u00e9quences parasites
    a_hi  = (2 * math.pi * 4500 / sr)
    a_hi /= (a_hi + 1)
    # LP tr\u00e8s bas \u00e0 600 Hz : sert \u00e0 construire le filtre passe-haut
    a_lo  = (2 * math.pi * 600 / sr)
    a_lo /= (a_lo + 1)

    lp_hi = 0.0
    lp_lo = 0.0
    samples = []
    for i in range(n):
        p = i / n
        # Enveloppe : mont\u00e9e douce sur 10 %, puis d\u00e9croissance
        env = (p / 0.10) if p < 0.10 else math.exp(-5.5 * (p - 0.10))
        noise = _random.uniform(-1.0, 1.0)
        lp_hi = lp_hi + a_hi * (noise - lp_hi)
        lp_lo = lp_lo + a_lo * (noise - lp_lo)
        # passe-bande = LP haute coupe - LP basse coupe
        samples.append(env * (lp_hi - lp_lo))
    return _to_sound(samples, amp=0.65)


def _make_explosion(sr: int) -> pygame.mixer.Sound:
    """Boom percussif : bruit large bande + grondement basse fréquence."""
    dur = 0.68
    n = int(sr * dur)
    samples = []
    lp = 0.0
    # Filtre passe-bas (fréq. de coupure ~280 Hz) pour la composante grave
    alpha = 2 * math.pi * 280 / sr
    alpha = alpha / (alpha + 1)
    for i in range(n):
        p = i / n
        # Enveloppe : attaque quasi-instantanée, décroissance exponentielle
        env = 1.0 if p < 0.008 else math.exp(-5.5 * (p - 0.008))
        noise = _random.uniform(-1.0, 1.0)
        lp = lp + alpha * (noise - lp)
        # Composante grave : sinus à 55 Hz qui disparaît vite
        boom = 0.38 * math.sin(2 * math.pi * 55 * i / sr) * math.exp(-7.5 * p)
        v = (noise * 0.45 + lp * 0.22 + boom) * env
        samples.append(v)
    return _to_sound(samples, amp=0.95)


def _make_bonus_pickup(sr: int) -> pygame.mixer.Sound:
    """Arpège C5–E5–G5–C6 montant (type 'pièce ramassée')."""
    freqs = [523, 659, 784, 1047]   # C5 E5 G5 C6
    seg = int(sr * 0.065)
    samples = []
    for f in freqs:
        for i in range(seg):
            p = i / seg
            env = (1.0 - p * p) * 0.80
            samples.append(env * math.sin(2 * math.pi * f * i / sr))
    return _to_sound(samples, amp=0.75)


def _make_player_death(sr: int) -> pygame.mixer.Sound:
    """Descente de fréquence triste + vibrato léger."""
    dur = 0.52
    n = int(sr * dur)
    samples = []
    for i in range(n):
        p = i / n
        env = (1.0 - p) ** 0.55 * 0.85
        f = 390.0 - 310.0 * p           # descend de 390 Hz → 80 Hz
        vib = 1.0 + 0.035 * math.sin(2 * math.pi * 7 * p)
        samples.append(env * math.sin(2 * math.pi * f * vib * i / sr))
    return _to_sound(samples, amp=0.80)


# ── Classe façade ─────────────────────────────────────────────────────────────

class BombermanSounds:
    """Synthétise et expose tous les effets sonores du Bomberman.

    Utilisation
    -----------
    sounds = BombermanSounds()          # dans run(), après pygame.init()
    sounds.play('bomb_place')           # pose de bombe
    sounds.play('fuse_tick')            # tick de mèche
    sounds.play('explosion')            # explosion
    sounds.play('bonus')                # bonus ramassé
    sounds.play('death')                # mort joueur
    """

    _VOLUMES = {
        'bomb_place': 0.55,
        'fuse_tick':  0.28,
        'explosion':  0.90,
        'bonus':      0.70,
        'death':      0.65,
    }

    def __init__(self):
        self._ok = False
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        try:
            if not pygame.mixer.get_init():
                return
            # Garantir assez de canaux pour que les sons se superposent
            pygame.mixer.set_num_channels(max(16, pygame.mixer.get_num_channels()))
            sr = _mixer_sr()
            makers = {
                'bomb_place': _make_bomb_place,
                'fuse_tick':  _make_fuse_tick,
                'explosion':  _make_explosion,
                'bonus':      _make_bonus_pickup,
                'death':      _make_player_death,
            }
            for name, fn in makers.items():
                snd = fn(sr)
                snd.set_volume(self._VOLUMES.get(name, 0.60))
                self._sounds[name] = snd
            self._ok = True
        except Exception as exc:
            print(f"[BombermanSounds] init failed: {exc}")

    def play(self, name: str) -> None:
        """Joue l'effet sonore correspondant sur un canal libre."""
        if not self._ok:
            return
        snd = self._sounds.get(name)
        if snd:
            snd.play()
