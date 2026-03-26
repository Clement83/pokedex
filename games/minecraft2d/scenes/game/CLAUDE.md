# scenes/game — Module de jeu Minecraft 2D

Point d'entrée : `from scenes.game import run` (exporté par `__init__.py` depuis `loop.py`).

## Structure

| Fichier | Contenu |
|---|---|
| `loop.py` | Boucle principale : init, input, physique, mobs, split-screen, rendu, sauvegarde DB |
| `player.py` | Classe `Player` + fonctions collision (`solid`, `move_x`, `move_y`, `eject_from_blocks`, `in_lava`, `in_water`, `on_ice`) |
| `inventory.py` | Classe `Inventory` (5 slots : outil, ressources, tête, corps, pieds) + navigation |
| `controls.py` | Lecture inputs clavier/manette (`get_dir_p1`, `get_dir_p2`, `get_cursor`, `joy_btn`) |
| `camera.py` | Classe `Camera` (suivi, conversion coords) + `ChunkCache` (rendu tuiles pré-calculé en thread) |
| `actions.py` | Actions joueur : minage, placement, épée, arc, canne à pêche, drapeau, torche |
| `sky.py` | Cycle jour/nuit : interpolation couleur ciel, overlay nuit, HUD soleil/lune |
| `craft.py` | `CraftMenu` : 4 tiers de table (bois/fer/or/diamant), recettes, consommation ressources |
| `trade.py` | `TradeMenu` : échange d'items entre les 2 joueurs |
| `projectiles.py` | `ProjectileManager` : flèches avec physique parabolique, collision mobs |
| `renderer_world.py` | Rendu monde (chunks blittés), curseur animé, drapeaux |
| `renderer_player.py` | Rendu sprite joueur (pixel-art), équipements, halo torche, fumée |
| `renderer_hud.py` | Hotbar (5 slots), icônes outils/équipements pixel-art, nom item actif |

## Notes

- Tous les fichiers importent les constantes depuis `config.py` (racine minecraft2d).
- `_write_loop.py` est un script utilitaire legacy, non utilisé en jeu.
- Le jeu est 2 joueurs split-screen (une manette, J1=joystick J2=boutons ABXY).
