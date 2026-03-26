# Pokedex — Jeu de chasse et collection Pokemon

Pokédex interactif avec système de chasse, mini-jeux de combat et capture. Progression par générations débloquées selon le nombre de captures.

## Structure

```
main.py              – Boucle principale (60 FPS), routing d'états, gestion inputs
config.py            – Constantes (écran, touches, régions, seuils génération, playlists)
state.py             – GameState : état global (écran, DB, sprites, sélection, stats)
game_logic.py        – Chargement sprites (cache multi-clé), animations, dispatch rendu
input_handler.py     – Gestion clavier (navigation, accélération au maintien)
controls.py          – Conversion manette → événements clavier synthétiques
db.py                – SQLite : tables pokemon + user_preferences (caught, shiny, seen)
sprites.py           – Chargement/cache images, pokéballs, icônes types, silhouettes
ui.py                – Rendu liste (14 items + sprite), détail (radar stats, talents, évolutions)
dresseur_selection.py – Sélection du dresseur (face/dos, persisté en DB)
transitions.py       – Transition spirale de cubes, fondu de défaite
debug_actions.py     – Git pull, reset save, saut au prochain palier

hunt/                – Sous-système de chasse complet
  manager.py         – Machine à états : REGION → ENCOUNTER → COMBAT → CATCHING → RESULT
  region_selection.py – Grille de régions (verrouillées par seuil de captures)
  encounter.py       – Chargement assets + transition spirale
  combat.py          – Choix aléatoire d'1 mini-jeu parmi 3
  combat_qte_game.py – QTE rythmique (flèches/boutons, 10 hits pour gagner)
  combat_dodge_game.py – Bullet hell (esquive projectiles, survie chronométrée)
  combat_memory_game.py – Simon Says (séquence de boutons à reproduire)
  catching.py        – Lancer de pokéball (angle + puissance, 3 essais)
  stabilizing.py     – Pokélock (zone cible qui rétrécit, timing)
  result.py          – Sauvegarde capture, vérification déblocage région
```

## Flux

```
init → dresseur_selection → list ↔ detail
                              ↓
                        hunt/manager.py
                    (région → rencontre → combat → capture → résultat)
```

## Données

- **DB SQLite** : `pokemon` (id, noms, sprites, caught, shiny, seen, raw_json) + `user_preferences`
- **Sprites** : `app/data/sprites/`, `app/data/assets/` (dresseurs, stades, types, attaques)
- **Audio** : `pokemon_audio/cries/`, `audio/menu_*.mp3`, `audio/win_*.mp3`
- **Shiny** : 1% de chance par rencontre
- **Déblocage régions** : 0/1/50/100/150/200/250/300/350/400 captures

## Difficulté mini-jeux

Basée sur le `catch_rate` du Pokemon :
- < 45 (légendaire) : séquences longues, vitesse x2
- < 100 (rare) : intermédiaire, vitesse x1.5
- >= 100 (commun) : facile, vitesse x1
