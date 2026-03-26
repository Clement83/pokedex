# Pong

Jeu Pong 2 joueurs local. Lancé via `main.py`.

## Structure

```
main.py          – Point d'entrée, splash screen, boucle partie/résultat
config.py        – Constantes (écran, couleurs, contrôles, physique)
scene_game.py    – Boucle de jeu principale (orchestre engine/)
scene_result.py  – Écran de victoire
engine/
  input.py       – is_held() : lecture clavier + manette
  ball.py        – reset/update balle, collisions raquettes, scoring
  renderer.py    – Dessin complet d'une frame (fond, filet, raquettes, balle, scores, flash)
```

## Flux

`main.py` → splash → `scene_game.run()` → retourne le gagnant (0/1) ou None (quit) → `scene_result.run()` → replay ou quit.

## Contrôles

- J1 : flèches haut/bas (+ hat/axe manette)
- J2 : M=monter, N=descendre (+ boutons manette 0/1)
- Définis dans `config.py` → dict `CTRL`
