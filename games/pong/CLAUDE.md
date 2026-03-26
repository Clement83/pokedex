# Pong

Pong classique 2 joueurs local. Premier à 7 points gagne. Esthétique rétro CRT avec trail phosphore.

## Structure

```
main.py          – Point d'entrée, splash screen (démo IA vs IA + scanlines CRT), boucle partie/résultat
config.py        – Constantes (écran 480x320, 60 FPS, couleurs, physique, contrôles)
scene_game.py    – Boucle de jeu : input, physique raquettes, update balle, scoring, rendu
scene_result.py  – Écran victoire (nom gagnant pulsé, bouton rejouer)
engine/
  input.py       – is_held() : abstraction clavier + manette (axes, hat, boutons, deadzone 0.3)
  ball.py        – reset/update balle, rebonds murs, collisions raquettes (angle selon position hit)
  renderer.py    – Frame complète : fond, filet, raquettes, balle + trail 14 frames, scores, flash
```

## Flux

`main.py` → splash (IA auto) → `scene_game.run()` → gagnant (0/1) ou None (quit) → `scene_result.run()` → replay ou quit.

## Physique balle

- Vitesse initiale : 210 px/s horizontal, 160 px/s vertical
- Angle de rebond : dépend de la position d'impact sur la raquette (±56° max)
- Accélération : x1.06 par hit de raquette (cap 480 px/s)
- Pause 0.85s après chaque point marqué

## Contrôles

- J1 : Haut/Bas (flèches, hat, axe 1)
- J2 : M (monter) / N (descendre) (boutons manette 0/1)
- Définis dans `config.py` → dict `CTRL`
