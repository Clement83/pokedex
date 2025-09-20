# Pokédex Pi Zero

Ce projet est une application Pokédex développée en Python avec Pygame, conçue pour fonctionner sur un Raspberry Pi Zero.

## Fonctionnalités
- Affichage d'une liste de Pokémon avec sprites
- Vue détail avec statistiques, types, talents et évolutions
- Affichage radar des statistiques
- Navigation au clavier (flèches, entrée, échappement)
- Utilisation d'une base de données SQLite pour les données Pokémon

## Installation
1. Clonez le dépôt :
   ```sh
   git clone https://github.com/Clement83/pokedex.git
   ```
2. Installez les dépendances Python :
   ```sh
   pip install pygame
   ```
3. Placez le fichier `pokedex.db` et le dossier `app/data/sprites/` dans le dossier du projet.

## Utilisation
Lancez l'application avec :
```sh
python main.py
```

## Structure du projet
- `main.py` : Application principale
- `pokedex.db` : Base de données SQLite
- `app/data/sprites/` : Sprites des Pokémon
- `.gitignore` : Fichiers à ignorer par git

## Contrôles
- Flèche haut/bas : Naviguer dans la liste
- Entrée : Afficher le détail du Pokémon sélectionné
- Échap : Retour ou quitter

## Sources
Les assets (sprites, données) proviennent du site [Tyradex](https://tyradex.vercel.app/), qui récupère ses données de [Poképédia](https://www.pokepedia.fr/).
Les assets audio proviennent du site [Pokemon Showdown](https://play.pokemonshowdown.com/). Tous les droits leur sont réservés.

## Disclaimer
Ce projet est non officiel et n'est pas affilié à The Pokémon Company, Nintendo ou Game Freak. Les noms, images et données Pokémon sont la propriété de leurs détenteurs respectifs et sont utilisés ici à des fins éducatives et non commerciales.

