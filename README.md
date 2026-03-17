# Arcade Multi-Jeux

Console d'arcade multi-jeux tournant sur un **Odroid Go Advance** (écran 480×320, manette intégrée). Deux jeux sont disponibles depuis un launcher commun.

## Fonctionnel

**Launcher** : écran d'accueil avec tuiles de sélection (image de couverture par jeu). Navigation clavier et joystick.

**Jeux disponibles :**
- `pokedex/` — Pokédex interactif avec chasse aux Pokémon, mini-jeux de combat et capture, progression par régions (Kanto → Paldea).
- `shifter/` — Drag race 1/4 mile en split-screen 2 joueurs, physique moteur complète, 6 voitures.

**POC web :** `poc/shifter/` — prototype Phaser.js de Shifter (jusqu'à 8 joueurs), sert de référence de conception.

## Technique

```
main.py          ← Point d'entrée universel (pygame)
launcher.py      ← UI menu de sélection (classe Launcher)
games/
  pokedex/       ← Jeu Pokédex (voir games/pokedex/README.md)
  shifter/       ← Jeu Shifter  (voir games/shifter/README.md)
poc/shifter/     ← Prototype web Phaser.js
```

- **Runtime :** Python 3, pygame
- **Lancement :** `python main.py` (active le venv si présent)
- **Isolation des jeux :** `main.py` utilise `importlib` + `chdir` pour charger chaque jeu dans son propre contexte, puis nettoie `sys.modules` au retour.
- **Cible matérielle :** Odroid Go Advance — 480×320 px, 1 joystick analogique + boutons ABXY + Select/Start.

## Sources & Disclaimer
Sprites/données Pokémon : [Tyradex](https://tyradex.vercel.app/) / [Poképédia](https://www.pokepedia.fr/). Audio : [Pokémon Showdown](https://play.pokemonshowdown.com/). Assets voitures : Kenny Racing Pack. Projet non officiel, usage éducatif uniquement.

