# Module Hunt

Orchestre le flux complet d'une "chasse" Pokémon : sélection de région → rencontre → combat → capture → stabilisation → résultat.

## Fonctionnel

Une chasse se déroule en séquence linéaire :

1. **Sélection de région** : grille de régions, verrouillées selon progression. Animation de déverrouillage si une nouvelle région vient d'être atteinte. Skippée à la toute première chasse (starter Kanto imposé).
2. **Rencontre** : préparation des assets visuels (sprite Pokémon, fond stade, sprite dresseur dos), transition spirale vers l'écran de combat.
3. **Combat** : l'un des 3 mini-jeux est choisi aléatoirement (QTE / Dodge / Memory). En cas de victoire → animation déplétion HP. En cas de défaite → transition de perte, le Pokémon s'est enfui.
4. **Capture** : mini-jeu de lancer de Pokéball (3 tentatives max).
5. **Stabilisation** : animation de capture dans la Pokéball (peut être skippée si `catch_rate > 60`).
6. **Résultat** : mise à jour BDD, vérification des jalons de progression, redirection vers la vue détail du Pokémon capturé.

**Cas particulier :** première chasse = starter Kanto (Bulbizarre, Salamèche ou Carapuce), sans sélection de région.

## Technique

```
__init__.py          ← Re-exporte hunt.run()
manager.py           ← HuntManager : machine à états REGION_SELECTION → ENCOUNTER → COMBAT → CATCHING → STABILIZING → SUCCESS/FLED
encounter.py         ← EncounterHandler : charge sprites + fond stade, joue transition spirale
combat.py            ← CombatHandler : sélection aléatoire mini-jeu, dispatch, animations HP
catching.py          ← CatchingHandler : délègue à catch_game.run(), normalise retour
stabilizing.py       ← StabilizingHandler : décide skip ou non, délègue à stabilize_game
region_selection.py  ← RegionSelectionHandler : grille régions, verrous, anim déverrouillage
result.py            ← ResultHandler : write BDD, jalons génération, redirect vue détail
```

**Dépendances :** `db`, `config`, `transitions`, tous les mini-jeux (`catch_game`, `combat_*_game`, `stabilize_game`).

**Difficulté adaptative :** la vitesse/durée des mini-jeux varie selon le `catch_rate` du Pokémon (normal / rare ×1.5 / légendaire ×2).
