# Motodash + Beta Toggle — Design

**Date :** 2026-04-28
**Statut :** approuvé, prêt pour implémentation

## Objectif

Ajouter au pokedex arcade :

1. **Motodash** — un nouveau jeu de moto 2D solo, style *Trials*, physique réaliste, 3 niveaux fixes, médailles bronze/argent/or sur le chrono.
2. **Toggle beta dans le launcher** — masquer par défaut les jeux instables (`motodash` + `doom`), révélables via la touche `F4` sur PC. Aucun raccourci manette : sur l'Odroid les jeux beta restent toujours masqués.

## Périmètre

**Inclus**
- Jeu motodash complet (menu, jeu, écran de fin) en physique hand-rolled, rendu procédural.
- 3 niveaux fixes (easy/medium/hard) avec terrain en polyligne et checkpoints.
- Persistance des meilleurs temps + médailles en JSON.
- Champ `beta` sur chaque entrée de `GAMES` dans `main.py` (racine).
- Filtrage de la liste affichée par le launcher selon un drapeau `show_beta`.
- Bascule `F4` clavier dans le launcher pour activer/désactiver l'affichage des beta.
- Badge visuel "BETA" sur les tuiles concernées quand visibles.
- Ajout de `doom` et `motodash` à `GAMES` avec `beta=True`.

**Exclus (potentiel futur)**
- Adversaires IA / fantômes (pas dans le MVP).
- Endless mode / niveaux procéduraux.
- Sprites pixel-art (rendu reste 100% procédural).
- Mode 2 joueurs.
- Persistance du toggle beta entre sessions (volontaire — non persistant).

## Architecture

### Modifications hors `games/motodash/`

**`main.py` (racine du projet)**
- Chaque entrée de `GAMES` reçoit un champ optionnel `beta: bool` (défaut `False` quand absent).
- Ajout de deux entrées :
  - `Doom` (beta=True), pointant vers `games/doom/` (déjà existant sur disque, jamais référencé jusqu'ici).
  - `Motodash` (beta=True), pointant vers `games/motodash/`.
- Passe la liste complète à `Launcher`. Le filtrage est fait côté launcher.

**`launcher.py`**
- `Launcher.__init__` accepte la liste complète et conserve un drapeau `self.show_beta = False`.
- Une propriété `self.visible_games` recalcule à chaque toggle la liste filtrée :
  - `show_beta = False` → uniquement les jeux non-beta.
  - `show_beta = True` → tous les jeux.
- Les attributs `self.images` / `self.bg_images` deviennent des **dictionnaires indexés par identifiant de jeu** (le titre suffit, ils sont uniques) au lieu de listes parallèles à `self.games`. Ça évite les bugs d'indices désynchronisés quand la liste filtrée change de taille.
- `handle_event` :
  - `K_F4` → toggle `show_beta`, recalcul `visible_games`, `selected = 0`.
  - Toutes les autres touches/boutons opèrent sur `visible_games` au lieu de `games`.
- `render` : pour chaque tuile dans `visible_games`, si `game.get("beta")`, dessiner un petit badge `BETA` jaune (~32×12 px) dans le coin haut-droit de la tuile.
- L'index retourné par `handle_event` (jeu sélectionné) **doit être un index dans la liste complète d'origine**, pas dans `visible_games`. Sinon `main.py` lance le mauvais jeu après un toggle. Solution : retourner directement le dict du jeu sélectionné, pas un index. Le `main.py` actuel passe l'index à `GAMES[result]` — il faut adapter pour utiliser le dict directement, ou résoudre l'index via une recherche.
  - **Choix retenu** : `handle_event` retourne le dict du jeu (ou `-1` pour quitter, `None` sinon). `main.py` passe directement ce dict à `launch_game`. Plus simple et plus robuste.

### Nouveau dossier `games/motodash/`

```
games/motodash/
  main.py            – Entry point : init pygame si absent, splash, boucle de scènes
  config.py          – Constantes : écran, physique, contrôles, paramètres médailles
  cover.png          – Cover 480×320 pour le carousel (placeholder procédural OK pour le MVP)
  scene_select.py    – Menu de sélection des niveaux (3 tuiles, médailles, meilleurs temps)
  scene_game.py      – Boucle de jeu : input, physique, rendu, chrono, checkpoints
  scene_result.py    – Écran fin : temps, médaille gagnée, retour menu
  bike.py            – Modèle moto + intégration physique
  terrain.py         – Polyligne du sol + collisions roue/sol + rendu
  levels.py          – Données des 3 niveaux (points terrain, départ, arrivée, checkpoints, temps cibles)
  scores.py          – I/O JSON des best times (~/.config/pokedex/motodash.json)
  CLAUDE.md          – Doc interne (cohérent avec les autres jeux)
```

### Modules partagés réutilisés
- `music_player` (racine) — musique de fond du menu motodash.
- `quit_combo` (racine) — combo SELECT+START 3s pour retour launcher.
- `logger` (racine) — logs unifiés.

## Modèle physique (motodash)

La moto est un **corps rigide unique** ; les deux roues sont calculées comme positions dérivées de `(pos, angle)`.

```
Bike state:
  pos          (vec2)        – centre du châssis
  vel          (vec2)
  angle        (float, rad)  – inclinaison globale
  angular_vel  (float)
  on_ground    (bool)
  throttle     (0.0 ou 1.0 — input binaire bouton/touche)
  brake        (0.0 ou 1.0 — input binaire bouton/touche)
```

**Constantes (config.py)** — valeurs initiales à régler par essai :
```
GRAVITY        = 1200 px/s²
THROTTLE_FORCE = 800   N-équiv (impulsion par seconde, le long de l'axe châssis)
BRAKE_FORCE    = 1500
LEAN_TORQUE    = 6.0   rad/s², appliqué chaque frame tant que l'input gauche/droite est tenu
AIR_DRAG       = 0.5
WHEEL_RADIUS   = 8 px
WHEELBASE      = 28 px
SUSPENSION_K   = 1500  raideur ressort vertical
SUSPENSION_C   = 30    amortissement
CRASH_ANGLE    = 110°  au-delà → reset checkpoint
```

**Pas d'intégration par frame** (Euler semi-implicite) :
1. Forces : gravité + (si `on_ground` et `throttle>0`) poussée le long de l'axe châssis ; (si `brake`) friction supplémentaire ; `LEAN_TORQUE * input_lean` sur `angular_vel`.
2. Intégration : `vel += accel*dt`, `pos += vel*dt`, idem rotation.
3. Pour chaque roue (avant et arrière), position monde = `pos ± R(angle) * (WHEELBASE/2, 0)` plus offset de suspension.
4. Test contre la polyligne : trouver le segment du terrain sous la roue (binary search sur la liste de points triés par x), distance signée roue → segment.
5. Si pénétration : correction de position (remonter le centre de masse) + impulsion normale ; couple résultant sur le châssis (force tangentielle × bras de levier) → la moto pivote vers la pente.
6. Friction tangentielle proportionnelle à la composante normale et à la vitesse relative au sol.
7. `on_ground = True` si au moins une roue touche.
8. **Crash** : si `|angle normalisé| > CRASH_ANGLE` → marquer crash, déclencher reset checkpoint à la frame suivante (animation courte de chute, ~0.6s). Au reset : `pos = position du dernier checkpoint franchi (ou départ)`, `vel = (0,0)`, `angle = 0`, `angular_vel = 0`. Le chrono ne s'interrompt pas.

**Caméra** : centrée sur la moto, `look_x = bike.pos.x + clamp(bike.vel.x * 0.3, -80, 80)`, lerp 8.0 par seconde. Y bornée à `bike.pos.y ± 60` pour limiter le mal de mer.

## Niveaux & médailles

**Format `levels.py`** (data only, pas de logique) :
```python
LEVELS = [
    {
        "id": "easy",
        "name": "Premiers tours",
        "terrain": [(0, 240), (200, 240), (400, 220), ...],  # liste (x, y), triée par x
        "start": (50, 220),
        "finish_x": 1800,
        "checkpoints": [600, 1200],   # abscisses
        "gold":   25.0,
        "silver": 35.0,
        "bronze": 50.0,
    },
    { "id": "medium", ... },
    { "id": "hard",   ... },
]
```

**Médaille calculée** depuis le temps final :
- `t <= gold`   → or
- `t <= silver` → argent
- `t <= bronze` → bronze
- sinon → aucune (le niveau est validé mais sans médaille)

**Persistance** :
- Fichier : `~/.config/pokedex/motodash.json`
- Schéma :
  ```json
  {
    "best_times": {
      "easy":   { "time": 27.34, "medal": "silver" },
      "medium": null,
      "hard":   null
    }
  }
  ```
- Création silencieuse du dossier au premier write. Lecture tolérante (fichier manquant ou JSON corrompu → repart à zéro sans crasher).

**Affichage menu de sélection** :
- 3 tuiles côte à côte (480×320 → 3 tuiles de ~140 de large + gaps).
- Chaque tuile : nom du niveau + meilleur temps en mm:ss.cc + icône médaille colorée si obtenue, "—" sinon.

## Contrôles

| Action | Manette (Odroid) | Clavier (PC) |
|---|---|---|
| Accélérer | A (btn 1) | ↑ |
| Freiner | B (btn 0) | ↓ |
| Pencher gauche | hat/axe gauche, dpad btn 10 | ← |
| Pencher droite | hat/axe droite, dpad btn 11 | → |
| Reset checkpoint | X (btn 2) | R |
| Quitter vers menu motodash | combo SELECT+START 3s (`quit_combo`) | Échap |

Mêmes deadzones que minecraft2d (axe 0.4).

## Toggle beta — UX précise

- Au démarrage du launcher : `show_beta = False`, seuls les jeux non-beta sont affichés (5 actuels).
- Appui sur `F4` (clavier uniquement, code `pygame.K_F4`) :
  - Toggle `show_beta`.
  - Recalcul de `visible_games`.
  - `selected = 0` (sécurité au cas où l'index courant n'existe plus).
  - Re-render immédiat.
- Tuile beta visible : un rectangle jaune `(245, 200, 60)` de 40×14 px en `(tile_x + TILE_W - 44, tile_y + 4)`, avec le texte `BETA` en noir bold 10pt centré dedans. Coins arrondis 3 px.
- Aucun feedback texte hors le badge — discret par design.

## Gestion d'erreurs

- **Motodash** : si `~/.config/pokedex/motodash.json` est corrompu, on logue `WARNING` via `logger.log` et on repart sur un état vide. Pas de crash.
- **Launcher** : si la liste filtrée est vide (théoriquement impossible — il y aura toujours au moins les jeux stables), afficher un message "Aucun jeu disponible". Cas paranoïaque.
- **Niveaux malformés** (devraient être impossibles puisque c'est du code) : si chargement de niveau échoue, retour au menu motodash avec un log d'erreur.

## Testing

Pas de framework de test côté projet. Validation par :
- **Manuelle au clavier** sur PC : jouer chaque niveau, vérifier la physique, médailles, sauvegarde, F4 toggle, badge BETA.
- **Manuelle manette** sur Odroid : vérifier que les jeux beta restent invisibles (F4 absent), que les contrôles répondent, que `quit_combo` ramène au launcher.
- **Robustesse JSON** : supprimer le fichier de scores pendant une partie → le jeu doit le recréer sans broncher au prochain résultat.

## Fichiers à créer

- `games/motodash/main.py`
- `games/motodash/config.py`
- `games/motodash/cover.png` (placeholder procédural)
- `games/motodash/scene_select.py`
- `games/motodash/scene_game.py`
- `games/motodash/scene_result.py`
- `games/motodash/bike.py`
- `games/motodash/terrain.py`
- `games/motodash/levels.py`
- `games/motodash/scores.py`
- `games/motodash/CLAUDE.md`
- `docs/superpowers/specs/2026-04-28-motodash-beta-toggle-design.md` (ce fichier)

## Fichiers à modifier

- `main.py` (racine) — ajouter motodash + doom à `GAMES`, ajouter le champ `beta`, adapter la signature de `launch_game` pour accepter un dict (pas un index).
- `launcher.py` — refactor `images`/`bg_images` en dicts, ajouter `show_beta` + filtrage, gestion `K_F4`, badge BETA, retour de `handle_event` en dict de jeu.

## Risques & inconnues

- **Tuning physique** : la sensation moto Trials est délicate. Premier passage = constantes raisonnables ; itération nécessaire après essai. Pas bloquant pour le draft mais à prévoir.
- **Performances Odroid** : 60 FPS visé, 1 seul corps physique simple — confortable. Le rendu de la polyligne peut devenir coûteux si trop de points ; limiter à ~200 points par niveau et ne dessiner que la fenêtre visible (clipping par x).
- **Refactor `images`/`bg_images`** : changement structurel dans `launcher.py`. Bien tester que les 5 jeux existants se chargent toujours après le passage en dict.
