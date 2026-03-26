# Instructions Copilot

## Règle obligatoire : CLAUDE.md

Avant de travailler sur un dossier ou un module, **tu dois impérativement lire le fichier `CLAUDE.md`** s'il en existe un dans le dossier courant ou ses parents. Ces fichiers contiennent la documentation technique et fonctionnelle du projet et de chaque sous-module. Ne jamais les ignorer.

Emplacements connus :
- `CLAUDE.md` (racine) — architecture globale, deps, modules partagés
- `games/pokedex/CLAUDE.md` — jeu Pokédex (chasse, capture, mini-jeux)
- `games/pong/CLAUDE.md` — jeu Pong
- `games/bomberman/CLAUDE.md` — jeu Bomberman
- `games/shifter/CLAUDE.md` — jeu Shifter (drag racing)
- `games/minecraft2d/CLAUDE.md` — jeu Minecraft 2D
- `games/minecraft2d/mobs/CLAUDE.md` — système de mobs
- `games/minecraft2d/scenes/game/CLAUDE.md` — module de jeu (boucle, rendu, craft)
- `poc/shifter/CLAUDE.md` — version web JS/Phaser du Shifter

## Contexte projet

Console arcade multi-jeux pour Odroid GO Advance (480x320). Python 3.10 + Pygame 2.6. Chaque jeu est un module isolé dans `games/`. Voir le `CLAUDE.md` racine pour les détails.
