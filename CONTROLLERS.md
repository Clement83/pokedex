# Référence manettes – Odroid GO Advance (OGA)

> Ce fichier récapitule le mapping pygame de tous les boutons physiques de la console.  
> À consulter avant d'écrire les contrôles d'un nouveau jeu.

---

## Architecture pygame sur OGA

L'OGA est vu par pygame comme **un seul joystick (index 0)** qui expose tous les boutons, axes et hat.

---

## Tous les boutons (`get_button`) – joystick 0

### Boutons de face (droite) – layout Switch

```
        X (2)
Y (3)         A (1)
        B (0)
```

| Index | Physique | Position | Direction |
|---|---|---|---|
| `0` | **B** | Bas     | bas     |
| `1` | **A** | Droite  | droite  |
| `2` | **X** | Haut    | haut    |
| `3` | **Y** | Gauche  | gauche  |

> ⚠️ Les indices pygame ne correspondent **pas** aux lettres : B=0, A=1, X=2, Y=3.  
> Les constantes dans le code (`BTN_A`, `BTN_B`…) suivent les indices pygame, pas les lettres physiques.

### Gâchettes

| Index | Physique | Rôle typique |
|---|---|---|
| `4`  | R2 (gâchette avant droite) | Action |
| `5`  | R  (gâchette épaule droite) | Action |
| `6`  | L2 (gâchette avant gauche)  | Action |
| `7`  | L  (gâchette épaule gauche)  | Action |

### D-pad

| Index | Physique | Rôle typique |
|---|---|---|
| `8`  | D-pad ↑ | Haut J1 |
| `9`  | D-pad ↓ | Bas J1 |
| `10` | D-pad ← | Gauche J1 |
| `11` | D-pad → | Droite J1 |

> ⚠️ Le D-pad peut aussi arriver en **hat** ou **axes** selon le firmware.  
> Préférer la combinaison hat + axes + boutons pour couvrir tous les cas.

### Boutons du bas (sérigraphiés en chiffres romains)

| Index | Sérigraphie | Rôle typique |
|---|---|---|
| `12` | **I**   | SELECT / Modifier |
| `13` | **II**  | — |
| `14` | **III** | Volume – |
| `15` | **IV**  | Volume + |
| `16` | **V**   | — |
| `17` | **VI**  | START / menu |

---

## Hat et axes (joystick gauche)

### Hat (`get_hat(0)`)

Renvoie un tuple `(x, y)` :

| x | y | Direction |
|---|---|---|
| `0`  | `1`  | Haut   |
| `0`  | `-1` | Bas    |
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

## Récapitulatif par jeu

| Jeu | J1 directions | J2 directions | Actions |
|---|---|---|---|
| **Bomberman** | Hat + axes | Boutons A/B/X/Y | J1=btn I(12) · J2=btn VI(17) |
| **Minecraft 2D** | Hat + axes + dpad 8-11 | Boutons A/B/X/Y | J1=L2(6)/R2(4) · J2=btn II(13)/III(14) |
| **Shifter** | Hat + axes + dpad 8-11 | Boutons A/B/X/Y | — |
| **Pokédex** | Axes + dpad 8-11 | — | A(0)=confirm · B(1)=cancel |

---

## Template – nouveau jeu 2 joueurs

```python
# ── Contrôles manette ─────────────────────────────────────────────────────────
# Une seule manette (joystick 0) partagée entre les deux joueurs :
#   J1 = joystick gauche (axes/hat) + D-pad (btns 8-11)
#   J2 = boutons de face (btns 0-3)
#
# ATTENTION : indices pygame ≠ lettres physiques !
#   btn 0 = B (bas)    btn 1 = A (droite)
#   btn 2 = X (haut)   btn 3 = Y (gauche)
AXIS_DEAD = 0.4

# Boutons de face – J2 (indices pygame)
BTN_B = 0   # physique B → bas
BTN_A = 1   # physique A → droite
BTN_X = 2   # physique X → haut
BTN_Y = 3   # physique Y → gauche

# Gâchettes
BTN_R2 = 4
BTN_R  = 5
BTN_L2 = 6
BTN_L  = 7

# D-pad – J1
BTN_UP    =  8
BTN_DOWN  =  9
BTN_LEFT  = 10
BTN_RIGHT = 11

# Boutons du bas
BTN_I   = 12  # I
BTN_II  = 13  # II
BTN_III = 14  # III – Volume –
BTN_IV  = 15  # IV  – Volume +
BTN_V   = 16  # V
BTN_VI  = 17  # VI  – START
```
