# Shifter — Drag Racing

Jeu de drag racing 2 joueurs. Course de 400m où le timing des passages de vitesse détermine la victoire.

## Structure

```
main.py            – Point d'entrée, splash 8s, boucle select→race→result
config.py          – 18 voitures (3 tiers x 6), contrôles, physique, zones de shift
car.py             – Classe Car : physique moteur, RPM, vitesses, surchauffe, bonus shift
scene_select.py    – Sélection split-screen (ActionDetector pour nav manette)
scene_race.py      – Course split-screen, tachymètre, HUD, feux de départ
scene_result.py    – Podium, stats (temps, vitesse max, qualité shifts)
ui.py              – Sprites voitures, TrackBackground, cockpits, feux, effets visuels
engine_sound.py    – Synthèse sonore moteur (Fourier, crossfade RPM, types 4cyl/V8)
asset/             – Spritesheets véhicules
```

## Physique

- **Force** = Puissance(RPM) / Vitesse - (résistance air + roulement)
- **RPM** = Vitesse x Rapport x 45.0, clampé [1000, maxRPM]
- **Shift zones** : PERFECT (+-200 RPM opt → +20% puissance 0.5s), GOOD (+-500 → neutre), BAD (hors zone → -10%)
- **Surchauffe** : 3s en zone rouge → -45% puissance, 5s hors zone pour récupérer

## 18 voitures (3 tiers)

- **Tier 1** (Street) : 300-400ch — Civic, GTI, S14, 200SX, Eclipse, Integra
- **Tier 2** (Quarter Mile) : 390-520ch — Supra, R34, Accord, RX-8, Eclipse GTS, S2000
- **Tier 3** (Built) : 520-850ch — RX-7, Evo VIII, Challenger, GT86, Barracuda, Supra MkIV

## Contrôles

- J1 : Haut/Bas (hat/axe/dpad) pour shift up/down, Gauche/Droite pour sélection
- J2 : X (shift up) / A (shift down), Y/A pour sélection

## Version web (poc/shifter/)

POC JS/Phaser 3 en 1920x1080, 2-8 joueurs clavier. Même physique, pas d'audio. Voir `poc/shifter/`.
