# Jeu Pokédex

Pokédex interactif avec système de chasse aux Pokémon. Le joueur parcourt les régions, combat des Pokémon via des mini-jeux, les capture et complète son Pokédex.

## Fonctionnel

**Flux principal :**
1. Sélection du dresseur (Ethan, Leaf, Lucas, Lyra…)
2. Vue liste : navigation dans le Pokédex, Pokémon non vus masqués en silhouette
3. Vue détail : stats, types, évolutions, radar hexagonal
4. Lancement d'une **chasse** depuis n'importe quel Pokémon → module `hunt/`

**Progression :**
- Régions débloquées en attrapant un seuil de Pokémon (ex. 10 vus → Johto, 30 → Hoenn…)
- Pokémon shiny (1 % par défaut), compteurs globaux (capturés / vus / shinies / régions)
- Mew débloqué après 150 Pokémon Kanto capturés

**Mini-jeux de combat** (1 choisi aléatoirement) :
- **QTE** : flèches défilantes, viser la zone centrale
- **Dodge** : éviter les projectiles pendant X secondes
- **Memory** : reproduire une séquence de directions (Simon-like)

**Mini-jeu de capture** : lancer balistique de Pokéball avec angle + puissance.

**Mini-jeu de stabilisation** : animation de capture (tremblements), skippé si `catch_rate > 60`.

## Technique

```
main.py             ← Machine à états (init → dresseur_selection → list/detail → quit)
config.py           ← Toutes les constantes (résolution, KEY_MAPPINGS, REGIONS, SHINY_RATE…)
state.py            ← GameState : état global, connexion SQLite, cache sprites, gestion musique
db.py               ← Couche SQLite (pokedex.db) : migrations, lecture/écriture Pokémon, préférences
game_logic.py       ← Rendu et animations (sprites avec cache, texte défilant, dispatch vues)
ui.py               ← Toutes les fonctions de dessin pygame (list/detail view, radar, barres)
sprites.py          ← Chargement / cache images, silhouette (apply_shadow_effect)
controls.py         ← Traduit events joystick → faux events clavier pygame (deadzone, combos debug)
input_handler.py    ← Gestion clavier états list/detail (navigation, accélération, git pull, debug)
transitions.py      ← Animations : spirale de cubes, fondu désaturation
dresseur_selection.py ← Écran choix dresseur (sprites face/dos)
debug_actions.py    ← Outils dev : git pull + restart, reset BDD, avance rapide jalons
catch_game.py       ← Mini-jeu Pokéball (balistique, 3 tentatives)
combat_qte_game.py  ← Mini-jeu QTE rythmique
combat_dodge_game.py ← Mini-jeu dodge projectiles
combat_memory_game.py ← Mini-jeu séquence mémoire
stabilize_game.py   ← Animation capture + victoire/échec
hunt/               ← Orchestration complète d'une chasse (voir hunt/README.md)
```

**Assets :**
- `app/data/sprites/` : sprites PNG des Pokémon (normal + shiny)
- `app/data/assets/dresseurs/<Nom>/` : `face.png`, `dos.png`
- `app/data/assets/type/` : icônes de types
- `app/data/assets/<region>/stadium/` : fonds de combat
- `app/data/assets/attacks/` : sprites de projectiles (combat dodge)
- `audio/` : musiques MP3 (`menu_*.mp3`, `win_*.mp3`)

**BDD SQLite (`pokedex.db`) :** table `pokemon` avec colonnes `caught`, `is_shiny`, `times_caught`, `seen` + table `user_preferences` (clé/valeur).

**Résolution cible :** 480×320 px (Odroid Go Advance). Tous les rendus sont dimensionnés en dur.
