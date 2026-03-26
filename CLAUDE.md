# Pokedex — Arcade Multi-Jeux

Console arcade multi-jeux pour **Odroid GO Advance** (480x320, manette integrée). Python 3.10 + Pygame 2.6.

## Structure

```
main.py           – Point d'entrée, lance le launcher et charge les jeux via importlib
launcher.py       – Carousel de sélection (5 jeux, navigation manette/clavier)
music_player.py   – Lecteur musique singleton (shuffle, volume, mute)
quit_combo.py     – Combo SELECT+START (3s) pour revenir au launcher
logger.py         – Logs dual console+fichier (debug.log)
games/            – Chaque sous-dossier = un jeu autonome avec son main.py
  pokedex/        – Pokédex interactif + chasse/capture
  shifter/        – Drag racing 2 joueurs
  pong/           – Pong classique 2 joueurs
  bomberman/      – Bomberman 4 joueurs (2 humains + 2 IA)
  minecraft2d/    – Sandbox 2D 2 joueurs split-screen
poc/shifter/      – Version web JS/Phaser du jeu Shifter (POC)
music/            – Musiques du launcher (mp3)
```

## Architecture

- **Isolation des jeux** : `importlib.import_module()` + `os.chdir()` + nettoyage `sys.modules` apres chaque retour au launcher
- **Modules partagés** : `music_player`, `quit_combo`, `logger` utilisés par tous les jeux
- **Combo manette** : boutons 12+13 tenus 5s = git pull + restart (dev remote)

## Controles Odroid

Voir `CONTROLLERS.md` pour le mapping complet des boutons/axes. Chaque jeu a son propre mapping défini dans son `config.py`.

## Deps

```
pygame==2.6.1
numpy==1.24.4
requests
beautifulsoup4
```
