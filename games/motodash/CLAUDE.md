# Motodash

Trials 2D solo. Pilote une moto sur 15 niveaux (5 biomes × 3), chrono + médailles or/argent/bronze. Difficulté croissante : grass → desert → canyon → ice → volcano.

## Structure

```
main.py            – Splash, init pygame, state machine select → game → result
config.py          – Constantes (écran, physique, contrôles, palettes biomes, BIOME_EFFECTS)
levels.py          – 15 niveaux générés procéduralement (1 generator par biome) + MEDALS
scores.py          – I/O JSON ~/.config/pokedex/motodash.json
bike.py            – Corps rigide + intégration Euler semi-implicite
terrain.py         – Polyligne sol, hauteur/pente par x, rendu polygone
hazards.py         – HazardManager : kill_zones, obstacles, slow_zones, ice_patch, updraft, geyser, falling_rock, kill_floor
particles.py       – ParticleSystem : neige, cendres, braises, papillons, poussière (selon biome)
scene_select.py    – Menu carrousel : meilleur temps + médaille, déverrouillage progressif
scene_game.py      – Boucle de jeu : input → physique → hazards → rendu (terrain → hazards → bike → particules → sky pulse)
scene_result.py    – Écran fin : temps, médaille, retry/menu
calibrate_medals.py – Bot déterministe pour mesurer un temps de référence par niveau
```

## Biomes & hazards

Chaque biome a un boss hazard signature + 1-2 secondaires :

| Biome   | Boss hazard          | Secondaires            | Particules | Ambiance       |
|---------|----------------------|------------------------|------------|----------------|
| grass   | (aucun, tutoriel)    | mares de boue          | papillons  | calme          |
| desert  | quicksand (kill_zone)| (aucun)                | poussière  | soleil orange  |
| canyon  | kill_floor (rivière) | cassures profondes, falling_rock, updraft | poussière  | falaises rouges|
| ice     | crevasse (kill_zone) | ice_patch              | neige      | bleu froid     |
| volcano | lave (kill_zone)     | geyser, braises        | braise+ash | sky pulse rouge + screen shake |

`BIOME_EFFECTS` dans `config.py` contrôle particules/sky_pulse/shake par biome.

Hazards sont des dicts data-driven (kind, subkind, rect/x/period/...). Le `HazardManager.update(bike, dt)` applique les effets ; `render(...)` dessine.

## Niveaux

15 niveaux générés à la volée par seed/length/density. Cache lazy (`levels._CACHE`). `LEVELS` est une vue stub (id/name/biome/medals) pour le menu — le terrain n'est construit qu'à `levels.get(id)`.

Déverrouillage : il faut décrocher au moins une médaille (bronze) sur le niveau `n-1` pour débloquer `n`.

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
