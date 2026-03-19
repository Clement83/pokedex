# Référence manettes – Odroid GO Advance (OGA)

> Ce fichier récapitule le mapping pygame de tous les boutons physiques de la console.  
> À consulter avant d'écrire les contrôles d'un nouveau jeu.

---

## Architecture pygame sur OGA

L'OGA expose **deux joysticks séparés** via pygame :

| Index pygame | Côté physique | Utilisé pour |
|---|---|---|
| `joystick 0` | Gauche (croix directionnelle, L1/L2, SELECT) | J1 / joueur solo |
| `joystick 1` | Droit (boutons A/B/X/Y, R1, START) | J2 dans les jeux 2 joueurs |

---

## Joystick 0 – côté gauche

### Boutons (`get_button`)

| Index | Physique | Rôle typique |
|---|---|---|
| `8`  | L2 (gâchette arrière gauche) | Action principale J1 |
| `9`  | R2 (gâchette arrière droite) | Action secondaire J1 |
| `10` | D-pad ← | — |
| `11` | D-pad → | — |
| `12` | SELECT | Modifier / menu J1 |

> ⚠️ Sur certains firmwares le D-pad arrive en **hat** ou en **axes** plutôt qu'en boutons.  
> Préférer la combinaison hat + axes + boutons (voir ci-dessous).

### Hat (`get_hat(0)`)

Renvoie un tuple `(x, y)` :

| x | y | Direction |
|---|---|---|
| `0`  | `1`  | Haut  |
| `0`  | `-1` | Bas   |
| `-1` | `0`  | Gauche |
| `1`  | `0`  | Droite |

### Axes (`get_axis`)

| Axe | Valeur | Direction |
|---|---|---|
| Axe `0` | `< -dead` | Gauche |
| Axe `0` | `> +dead` | Droite |
| Axe `1` | `< -dead` | Haut   |
| Axe `1` | `> +dead` | Bas    |

Deadzone recommandée : **0.4** (jeux action) · **0.7** (menus / shifter)

---

## Joystick 1 – côté droit

### Boutons (`get_button`) – **VÉRIFIÉ en jeu**

| Index | Physique | Direction / action |
|---|---|---|
| `0` | **A** | Bas            |
| `1` | **B** | Droite         |
| `2` | **X** | Haut           |
| `3` | **Y** | Gauche         |
| `13` | L1 / R1 | Action principale J2 |
| `16` | — | Action libre J2 |
| `17` | START | Modifier / menu J2 |

> Le mapping A/B/X/Y ci-dessus est **confirmé** après tests sur console.  
> Mnémotechnique : disposition en croix = bas · droite · haut · gauche (sens antihoraire depuis A).

---

## Boutons communs (joystick 0, jeux solo)

| Index | Physique | Rôle dans pokedex |
|---|---|---|
| `0`  | A | CONFIRM |
| `1`  | B | CANCEL  |
| `8`  | Haut D-pad  | UP    |
| `9`  | Bas D-pad   | DOWN  |
| `10` | Gauche D-pad | LEFT |
| `11` | Droite D-pad | RIGHT |
| `14` | Volume –    | VOLUME_DOWN |
| `15` | Volume +    | VOLUME_UP   |
| `17` | START       | GIT_PULL / menu |

---

## Récapitulatif par jeu

| Jeu | J1 directions | J2 directions | Bomb / action |
|---|---|---|---|
| **Bomberman** | Hat + axes (joystick 0) | A/B/X/Y (joystick 1) | J1=btn 12 · J2=btn 17 |
| **Minecraft 2D** | Hat + axes (joystick 0) | A/B/X/Y (joystick 1) | J1=L2(8) · J2=L1(13) |
| **Shifter** | Hat + axes + dpad-btns 8-11 | A/B/X/Y (joystick 1) | — |
| **Pokédex** | Axes + dpad-btns 8-11 | — | A(0)=confirm · B(1)=cancel |

---

## Template – nouveau jeu 2 joueurs

```python
# ── Contrôles manette ─────────────────────────────────────────────────────────
AXIS_DEAD = 0.4

# J1 – joystick 0 (croix / joystick gauche)
#   → utiliser hat(0) + axes 0/1 pour les directions

# J2 – joystick 1 (boutons face)
BTN_A = 0   # bas
BTN_B = 1   # droite
BTN_X = 2   # haut
BTN_Y = 3   # gauche
```
