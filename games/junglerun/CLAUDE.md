# Jungle Run

Runner 2 joueurs en split-screen vertical, mode survie. Chaque joueur n'a
qu'**un seul bouton** (saut + double saut). Le dernier en vie gagne ; en cas
d'égalité de mort, c'est la distance la plus longue qui départage.

## Structure

```
main.py          – Boucle partie/résultat
config.py        – Constantes (écran, physique, génération, contrôles)
scene_game.py    – Compte à rebours + boucle 2-mondes (split-screen 480x160)
scene_result.py  – Annonce gagnant + distances finales + replay
world.py         – Player, Platform, World : physique, génération procédurale,
                   plateformes pourries, plumes, séismes
renderer.py      – Dessin d'une viewport (ciel, parallax, plateformes,
                   pickups, joueur, HUD, overlay mort)
```

## Flux

`main.py` → `scene_game.run()` (3-2-1-GO + course) → `(winner, dist_j1, dist_j2)`
→ `scene_result.run()` → replay ou retour launcher.

## Contrôles

- **J1** : n'importe quel bouton du D-pad (8-11), hat ou axes du joystick.
  Au clavier : flèche du haut ou espace.
- **J2** : n'importe quel bouton de face (0=B, 1=A, 2=X, 3=Y).
  Au clavier : N ou Entrée.
- **Quitter** : combo SELECT+START maintenu 3s (cf. `quit_combo.py`).

## Mécaniques

- **Saut + double saut** : 1 saut au sol, 1 second saut en l'air. Reset au contact.
- **Plateformes pourries** : prennent une teinte plus claire et s'effondrent
  300 ms après le piétinement.
- **Lianes** : plateformes décorées de feuillage vert qui rebondissent le
  joueur (trampoline auto, +1 saut "gratuit").
- **Rochers** : posés sur une plateforme, tuent au contact.
- **Branches basses** : suspendues au-dessus de la plateforme. Tuent si on
  saute → forcent à *ne pas* sauter dessous.
- **Plumes** : pickup doré qui donne 1 bouclier (annule la prochaine mort,
  petit boost vertical pour s'extraire).
- **Séismes** : tous les 18-32 s, écran tremble et la vitesse de scroll
  monte 1.5× pendant 4.5 s ; quelques plateformes à venir deviennent pourries.

## Difficulté

- Vitesse de départ : 180 px/s
- Augmentation : +4 px/s par seconde de jeu, plafond 420 px/s
- Génération : seed différent par joueur (parité de challenge mais variations
  perso → pas de mémorisation possible)
