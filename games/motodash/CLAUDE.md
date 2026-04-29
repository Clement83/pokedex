# Motodash

Trials 2D solo (BETA). Pilote une moto sur 3 niveaux fixes, chrono + médailles or/argent/bronze.

## Structure

```
main.py            – Splash, init pygame, state machine select → game → result
config.py          – Constantes (écran, physique, contrôles, médailles)
levels.py          – 3 niveaux fixes (terrain polyligne, départ, arrivée, checkpoints, temps cibles)
scores.py          – I/O JSON ~/.config/pokedex/motodash.json
bike.py            – Corps rigide + intégration Euler semi-implicite
terrain.py         – Polyligne sol, hauteur/pente par x, rendu polygone
scene_select.py    – Menu : 3 tuiles, meilleur temps + médaille par niveau
scene_game.py      – Boucle de jeu : input → physique → rendu, HUD chrono
scene_result.py    – Écran fin : temps, médaille, retry/menu
```

## Physique

- Moto = un seul corps rigide. Roues = positions dérivées de (pos, angle).
- Intégration Euler semi-implicite à 60 FPS.
- Collisions par roue contre la polyligne du terrain (binary search sur les x).
- Crash si l'inclinaison dépasse ±110° → reset au dernier checkpoint passé après 0.6s.

## Contrôles

- J1 : A=accélérer · B=frein · D-pad/hat=pencher · X=reset · combo SELECT+START 3s=quitter
- Clavier : ↑=accélérer · ↓=frein · ←→=pencher · R=reset · Échap=quitter

## Tuning

Si la sensation de pilotage est bizarre, agis sur `config.py` :
- `THROTTLE_FORCE` / `BRAKE_FORCE` — punch d'accélération et freinage
- `LEAN_TORQUE` — réactivité de l'inclinaison
- `ANGULAR_DRAG` — amortissement rotation (plus haut = moto stable mais peu réactive)
- `GROUND_FRICTION` — accroche au sol (1 = collante, 0.5 = patine)
