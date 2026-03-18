"""
Synthèse procédurale de son moteur – Shifter
=============================================
Aucun fichier audio ni numpy requis.
Compatible Python 3.8+ (Odroid Go Advance).

Principe
--------
1. Au démarrage (`EngineSound.__init__`), on pré-bake une bibliothèque de
   sons pour chaque palier de _RPM_STEP RPM (1000 → max_rpm).
   Chaque son est exactement un cycle de la waveform → loop seamless.

2. À chaque frame (`update`), si le palier courant change on démarre un
   cross-fade de _FADE_DUR secondes entre les deux canaux pygame.

3. Pendant un changement de rapport (`is_shifting = True`) le volume est
   réduit pour simuler la coupure d'injection.

Types de moteur
---------------
- '4cyl'  : JDM / EURO → série de Fourier (dent-de-scie)
- 'v8'    : MUSCLE     → harmoniques pairs + sous-harmonique grondant
- 'rotary': (réservé)  → ondes riches en harmoniques
"""
from __future__ import annotations

import math
import array as _array
import pygame

# ── Paramètres ────────────────────────────────────────────────────────────────
# _RPM_STEP DOIT être un diviseur de 1000 pour que les clés du dict
# soient alignées avec _nearest() (qui arrondit au multiple de _RPM_STEP).
# 200 → clés : 1000, 1200, 1400, …  (1000 = 5 × 200 ✓)
_RPM_STEP  = 200     # résolution de la bibliothèque pré-bake (RPM)
_FADE_DUR  = 0.04    # durée d'un cross-fade (s) – 40 ms
_BASE_VOL  = 0.30    # volume canal (0–1) – le buffer est généré à pleine amplitude
_SHIFT_VOL = 0.45    # fraction du volume pendant un changement de rapport
_NUM_HARM  = 8       # harmoniques pour la synthèse 4-cyl


# ── Helpers bas niveau ────────────────────────────────────────────────────────

def _mixer_sr() -> int:
    """Sample rate réel du mixer pygame (ou 22050 par défaut)."""
    info = pygame.mixer.get_init()
    return info[0] if info else 22050


def _fund_freq(rpm: float, etype: str) -> float:
    """Fréquence fondamentale (Hz) selon le régime et le type de moteur."""
    if etype == 'v8':
        return rpm / 60.0 * 4.0    # V8 : 8 cyl → 4 allumages/tour
    if etype == 'rotary':
        return rpm / 60.0 * 3.0    # Wankel : 3 faces → 3 allumages/tour
    return rpm / 60.0 * 2.0        # 4-cyl   : 4 cyl → 2 allumages/tour


def _make_sound(rpm: float, etype: str, sr: int, _vol_unused: float = 1.0) -> pygame.mixer.Sound:
    """Génère un cycle complet (loop seamless) et retourne un Sound pygame.

    Utilise uniquement math + array – aucune dépendance externe.
    Buffer PCM : int16 signé, stéréo entrelacé (L R L R …).
    """
    freq  = _fund_freq(rpm, etype)
    n     = max(16, int(sr / freq))
    tau   = 2.0 * math.pi

    # ── Génération des échantillons flottants ─────────────────────────────────
    samples = []
    for i in range(n):
        t = tau * i / n
        if etype == 'v8':
            v = (0.45 * math.sin(t)
                 + 0.28 * math.sin(2.0 * t)
                 + 0.14 * math.sin(3.0 * t)
                 + 0.08 * math.sin(4.0 * t)
                 + 0.18 * math.sin(0.5 * t))   # sub-harmonique grondant
        elif etype == 'rotary':
            v = sum((0.55 / k) * math.sin(k * t + k * 0.3) for k in range(1, 7))
        else:
            # 4-cyl : série de Fourier + micro-texture déterministe
            v = sum((0.65 / k) * math.sin(k * t) for k in range(1, _NUM_HARM + 1))
            v += 0.02 * math.sin(t * 17.3)
        samples.append(v)

    # ── Normalisation + conversion int16 stéréo ───────────────────────────────
    peak  = max(abs(s) for s in samples) or 1.0
    # vol ignoré ici : le buffer est généré à pleine amplitude (32767).
    # Le volume est contrôlé au niveau du canal pygame (Channel.set_volume).
    scale = 32767.0 / peak
    buf   = _array.array('h')          # signed short = int16
    for s in samples:
        val = int(max(-32768.0, min(32767.0, s * scale)))
        buf.append(val)   # canal L
        buf.append(val)   # canal R

    return pygame.mixer.Sound(buffer=buf)


# ── Classe principale ─────────────────────────────────────────────────────────

class EngineSound:
    """Son moteur procédural pour une voiture.

    Utilise deux canaux pygame en cross-fade (A ↔ B) pour des transitions
    fluides sans artefacts audio lors des changements de RPM.

    Paramètres
    ----------
    max_rpm  : RPM limite du moteur (issu de car.max_rpm)
    cat      : catégorie voiture ('JDM', 'EURO', 'MUSCLE')
    channels : (id_canal_A, id_canal_B) – deux canaux pygame dédiés

    Utilisation typique
    -------------------
    es = EngineSound(car.max_rpm, cat=car.data['cat'], channels=(2, 3))
    es.start()                               # au départ de la course
    # boucle :
    es.update(car.rpm, car.is_shifting, dt)
    # fin :
    es.stop()
    """

    def __init__(self, max_rpm: int, cat: str = 'JDM', channels: tuple = (2, 3)):
        self._ok = False
        try:
            if not pygame.mixer.get_init():
                return

            self._etype    = 'v8' if cat == 'MUSCLE' else '4cyl'
            self._ch_a     = pygame.mixer.Channel(channels[0])
            self._ch_b     = pygame.mixer.Channel(channels[1])
            self._active   = self._ch_a
            self._inactive = self._ch_b

            self._level    = 1000
            self._fading   = False
            self._fade_t   = 0.0
            self._started  = False
            self._fadeout       = False   # True pendant le fondu final d'arrivée
            self._fadeout_t     = 0.0
            self._fadeout_dur   = 1.0
            self._sounds: dict[int, pygame.mixer.Sound] = {}

            self._bake(max_rpm)
            self._ok = True
        except Exception as exc:
            print(f"[EngineSound] init failed: {exc}")

    def _bake(self, max_rpm: int) -> None:
        """Pré-bake des waveforms pour chaque palier de RPM."""
        sr  = _mixer_sr()
        rpm = 1000
        while rpm <= max_rpm + _RPM_STEP:
            self._sounds[rpm] = _make_sound(float(rpm), self._etype, sr, 1.0)
            rpm += _RPM_STEP
        self._max = rpm - _RPM_STEP

    def _nearest(self, rpm: float) -> int:
        """Arrondit un RPM au palier le plus proche de la bibliothèque."""
        target = max(1000.0, min(float(self._max), rpm))
        level  = int(round(target / _RPM_STEP) * _RPM_STEP)
        level  = max(1000, min(self._max, level))
        # Garde-fou : si la clé n'existe pas (ne devrait pas arriver avec
        # _RPM_STEP diviseur de 1000), on cherche la plus proche.
        if level not in self._sounds:
            level = min(self._sounds, key=lambda k: abs(k - target))
        return level

    # ── API publique ──────────────────────────────────────────────────────────

    def start(self) -> None:
        """Démarre le son de ralenti. Appeler quand la course commence."""
        if not self._ok:
            return
        snd = self._sounds.get(self._nearest(1000.0))
        if snd:
            self._active.play(snd, loops=-1)
            self._active.set_volume(_BASE_VOL)
        self._started = True

    def update(self, rpm: float, is_shifting: bool, dt: float) -> None:
        """Mettre à jour chaque frame : adapte le son au RPM courant."""
        if not self._ok or not self._started:
            return

        # ── Fondu final d'arrivée (prioritaire sur tout le reste) ─────────────
        if self._fadeout:
            self._fadeout_t += dt
            p = min(1.0, self._fadeout_t / self._fadeout_dur)
            vol = _BASE_VOL * (1.0 - p)
            self._active.set_volume(vol)
            self._inactive.set_volume(0.0)   # couper l'autre canal proprement
            if p >= 1.0:
                self.stop()
            return

        level = self._nearest(rpm)

        # Déclencher un cross-fade si le palier change et qu'on n'est pas
        # déjà en train de fader (le niveau cible sera rattrapé après)
        if level != self._level and not self._fading:
            snd = self._sounds.get(level)
            if snd:
                self._inactive.play(snd, loops=-1)
                self._inactive.set_volume(0.0)
                self._fading = True
                self._fade_t = 0.0
                self._level  = level

        # Volume cible : légèrement réduit pendant le changement de rapport
        vol = _BASE_VOL * (_SHIFT_VOL if is_shifting else 1.0)

        if self._fading:
            self._fade_t += dt
            p = min(1.0, self._fade_t / _FADE_DUR)
            self._active.set_volume((1.0 - p) * vol)
            self._inactive.set_volume(p * vol)
            if p >= 1.0:
                self._active.stop()
                self._active, self._inactive = self._inactive, self._active
                self._fading = False
        else:
            self._active.set_volume(vol)

    def fade_out(self, duration: float = 1.2) -> None:
        """Décroissance progressive du son moteur (arrivée en course).
        Après `duration` secondes le son s'arrête complètement.
        """
        if not self._ok or not self._started or self._fadeout:
            return
        self._fadeout     = True
        self._fadeout_t   = 0.0
        self._fadeout_dur = max(0.1, duration)
        # Annuler un éventuel cross-fade en cours pour partir d'un niveau propre
        self._fading = False
        self._inactive.set_volume(0.0)

    def stop(self) -> None:
        """Stoppe tous les canaux. Appeler en quittant la scène."""
        if not self._ok:
            return
        self._ch_a.stop()
        self._ch_b.stop()
        self._started = False
