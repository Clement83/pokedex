# Minecraft 2D – Feuille de route : Loot, Mobs & Progression

> État actuel condensé pour référence rapide

| Domaine | Ce qui existe |
|---|---|
| **Outils** | Main / Pioche / Canon / Épée / Drapeau |
| **Matériaux** | Bois (0) · Fer (1) · Or (2) · **Diamant (3)** |
| **Blocs** | Air, Terre, Pierre, Herbe, Sable, Bois, Charbon, Brique, Coffre, Obsidienne, Vitre |
| **Mobs agressifs** | Slime (2 PV) · Zombie (3 PV) · Golem (5 PV) · **Vrille (25 PV, boss souterrain)** |
| **Mobs passifs** | Poule · Grenouille · Mouette |
| **Loot coffre** | Épée/Pioche/Casque/Plastron/Bottes — Bois 65 % · Fer 28 % · Or 7 % |
| **Dégâts épée** | Bois = 1 · Fer = 2 · Or = 3 |

---

## 1. Tier de pioche requis par bloc

### Idée centrale
Introduire un attribut `TILE_PICKAXE_TIER` : le tier **minimum** de pioche nécessaire pour miner un bloc.  
Frapper un bloc avec une pioche insuffisante ne le détruira pas (ou le détruira sans loot).

### Tiers proposés
| Tier | Pioche | Valeur |
|---|---|---|
| 0 | Main / N'importe quelle pioche | tous matériaux |
| 1 | Pioche Bois minimum | `MAT_WOOD` |
| 2 | Pioche Fer minimum | `MAT_IRON` |
| 3 | Pioche Or minimum | `MAT_GOLD` |
| 4 | *(futur) Pioche Diamant* | `MAT_DIAMOND` |

### Assignation des blocs actuels
| Bloc | Tier requis | Justification |
|---|---|---|
| Terre / Herbe / Sable | 0 | ramassable à la main |
| Pierre | 1 (Bois) | bloc de base |
| Charbon | 1 (Bois) | drop de charbon |
| Bois | 1 (Bois) | les arbres, hache dans le futur |
| Brique | 2 (Fer) | structures construites |
| Vitre | 2 (Fer) | fragile mais "craftée" |
| Obsidienne | 3 (Or) | fond des donjons, très dur |

### Nouveaux blocs à ajouter (voir §3)
| Nouveau bloc | Tier requis |
|---|---|
| Minerai de Fer | 2 (Fer) |
| Minerai d'Or | 2 (Fer) |
| Minerai de Diamant | 3 (Or) |
| Roc infernal / Bedrock | Non minable |

### Implémentation (résumé technique)

```python
# config.py – à ajouter
TILE_PICKAXE_TIER = {
    TILE_DIRT:     0,
    TILE_GRASS:    0,
    TILE_SAND:     0,
    TILE_WOOD:     1,
    TILE_COAL:     1,
    TILE_STONE:    1,
    TILE_BRICK:    2,
    TILE_GLASS:    2,
    TILE_OBSIDIAN: 3,
    # nouveaux blocs :
    TILE_IRON_ORE:    2,
    TILE_GOLD_ORE:    2,
    TILE_DIAMOND_ORE: 3,
}

MAT_TIER = {MAT_WOOD: 1, MAT_IRON: 2, MAT_GOLD: 3}  # (MAT_DIAMOND: 4)
```

Dans `scenes/game/loop.py` (ou `scene_game.py`), lors du break d'un bloc :
- Si `player.inventory.pickaxe_mat is None` → tier = 0
- Sinon `tier = MAT_TIER[pickaxe_mat]`
- Si `tier < TILE_PICKAXE_TIER.get(tile, 0)` → ne pas accorder le loot (bloc résistant)

---

## 2. Mobs avec résistance à certaines épées

### Idée centrale
Chaque mob possède un `min_sword_mat` : tier d'épée **minimum** pour infliger des dégâts.  
En dessous du seuil, les coups font 0 dégât (l'épée rebondit, feedback visuel/sonore).

### Table proposée
| Mob | PV actuels | Tier épée min | Raison narrative |
|---|---|---|---|
| Slime | 2 | 0 (Main ok) | mob de base |
| Zombie | 3 | 1 (Bois) | chair morte, résiste aux poings |
| **Araignée** *(nouveau)* | 3 | 1 (Bois) | carapace chitineuse |
| Golem | 5 | 2 (Fer) | armure de pierre |
| **Squelette** *(nouveau)* | 4 | 1 (Bois) | os solides |
| **Démon** *(nouveau)* | 8 | 3 (Or) | créature magique, immunisée fer |
| **Boss Liche** *(nouveau)* | 20 | 3 (Or) | boss de donjon |

### Implémentation (résumé technique)

```python
# mobs/base.py – à ajouter
_MOB_MIN_SWORD_TIER = {
    MOB_SLIME:    0,
    MOB_ZOMBIE:   1,
    MOB_GOLEM:    2,
    MOB_SPIDER:   1,   # nouveau
    MOB_SKELETON: 1,   # nouveau
    MOB_DEMON:    3,   # nouveau
    MOB_LICHE:    3,   # boss
}
```

Dans la logique de hit (scene_game / loop) :
```python
player_tier = MAT_TIER.get(player.inventory.sword_mat, 0)
mob_min_tier = _MOB_MIN_SWORD_TIER.get(mob.mob_type, 0)
if player_tier < mob_min_tier:
    dmg = 0   # feedback "IMMUNE" affiché
else:
    dmg = _SWORD_DMG[player.inventory.sword_mat]
```

---

## 3. Nouveaux blocs et minerais

| ID | Nom | Couleur | Tier requis | Drop |
|---|---|---|---|---|
| `TILE_IRON_ORE` | Minerai de Fer | gris-rouille `(120,100,90)` | 2 | Lingot de Fer |
| `TILE_GOLD_ORE` | Minerai d'Or | jaune-pierre `(180,155,60)` | 2 | Lingot d'Or |
| `TILE_DIAMOND_ORE` | Minerai de Diamant | bleu glacier `(80,210,220)` | 3 | Gemme de Diamant |
| `TILE_LAVA` | Lave | orange `(220,80,0)` | – (indestructible) | dégâts si touché |
| `TILE_ICE` | Glace | bleu-blanc `(180,220,255)` | 1 | glisse le joueur |
| `TILE_MOSS` | Mousse | vert foncé `(50,120,60)` | 0 | décor / herbe profonde |
| `TILE_CRATE` | Caisse en bois | brun clair `(160,120,70)` | 1 | loot de surface (nourriture, bois) |

### Génération dans `world.py`
- **Minerai de Fer** : entre `surface + 10` et `surface + 30`, probabilité ~12 % par colonne
- **Minerai d'Or** : entre `surface + 25` et `surface + 55`, probabilité ~6 %
- **Minerai de Diamant** : entre `surface + 50` et `ROWS - 5`, probabilité ~2 %
- **Lave** : poches aléatoires très profondes (`surface + 60+`), petits lacs 3-5 blocs
- **Glace** : biome "froid" (colonnes avec seed tendant vers `hash > 0.7`), remplace eau/surface

---

## 4. Système de drop de ressources par mob

### Loot table des mobs
| Mob | Drop |
|---|---|
| Slime | Slime gel (nouvelle ressource cosmétique) |
| Zombie | Lingot de Fer (20 %) |
| Golem | Pierre × 3, Fer (50 %) |
| Poule | Plume (décoration, future flèche) |
| Grenouille | Rien |
| **Araignée** | Fil d'araignée (future corde/filet) |
| **Squelette** | Os × 1–2, Arc (rarement) |
| **Démon** | Gemme de Diamant (30 %) |
| **Boss Liche** | Équipement Or garanti + clé de portail |

### Implémentation

```python
# mobs/base.py
_MOB_DROPS = {
    MOB_SLIME:   [(ITEM_SLIME_GEL, 1, 1.0)],
    MOB_ZOMBIE:  [(TILE_IRON_ORE,  1, 0.2)],
    MOB_GOLEM:   [(TILE_STONE, 3, 1.0), (TILE_IRON_ORE, 1, 0.5)],
    MOB_CHICKEN: [(ITEM_FEATHER,   1, 0.8)],
    MOB_SPIDER:  [(ITEM_SILK,      1, 0.9)],
    # ...
}
# (item_id, quantité, probabilité)
```

---

## 5. Système de craft minimal (sans interface lourde)

### Principe : recettes automatiques à l'inventaire
Le joueur accède à un menu de craft "simple" :  
**bouton MODIFIER + bas** → ouvre un panneau de 4 recettes disponibles.

### Recettes de base
| Résultat | Ingrédients |
|---|---|
| Pioche Bois | Bois × 3 |
| Pioche Fer | Lingot Fer × 3 |
| Pioche Or | Lingot Or × 3 |
| **Pioche Diamant** | Gemme Diamant × 3 |
| Épée Bois | Bois × 2 |
| Épée Fer | Lingot Fer × 2 |
| Épée Or | Lingot Or × 2 |
| **Épée Diamant** | Gemme Diamant × 2 |
| Torche | Bois × 1 + Charbon × 1 |
| Brique | Pierre × 2 |

> Actuellement les équipements sont trouvés **uniquement** dans les coffres. Ajouter le craft permet de les fabriquer avec les minerais récoltés — ce qui donne enfin un sens au minage !

---

## 6. Nouveaux mobs

### 6.1 Araignée (`MOB_SPIDER`)
- Spawn : forêts, arbres, caves peu profondes (surface + 5 à + 20)
- Comportement : escalade les murs (pas de gravité contre les murs)
- PV : 3 · Dégâts : 1 · Tier min épée : Bois
- Spécial : peut tirer un fil qui **ralentit** le joueur 1 s

### 6.2 Squelette (`MOB_SKELETON`)
- Spawn : caves profondes (surface + 20+), nuit uniquement
- Comportement : maintient sa distance, tire des **flèches** (projectile)
- PV : 4 · Dégâts flèche : 1 à distance · Tier min épée : Bois
- Drop : Os, rarement un Arc

### 6.3 Chauve-souris (`MOB_BAT`)
- Spawn : caves, toujours actives (jour/nuit)
- Comportement : vol erratique, passive mais fonce sur le joueur la nuit
- PV : 1 · Dégâts : 0 (distraction) · Tier min épée : 0

### 6.4 Crabe (`MOB_CRAB`)
- Spawn : plages (sable + proche de la surface)
- Comportement : marche latéralement, charge courte
- PV : 3 · Dégâts : 1 · Tier min épée : Bois
- Drop : Pince de crabe (ressource de craft future)

### 6.5 Démon (`MOB_DEMON`)
- Spawn : zones profondes (surface + 60+), près de la lave
- Comportement : vole lentement, lance des boules de feu (projectile)
- PV : 8 · Dégâts : 2 · **Immunisé aux épées Bois et Fer**
- Drop : Gemme de Diamant (30 %)

### 6.6 Boss Liche (`MOB_LICHE`) — boss de donjon
- Spawn : unique, généré dans un donjon spécial (1 par monde)
- Comportement : invoque des squelettes, projectiles multiples
- PV : 20 · Dégâts : 3 · Tier min épée : Or
- Drop : **Équipement Or garanti × 3** + clé de portail

---

## 7. Améliorations diverses

### 7.1 Loot contextualisé par structure
| Structure | Loot coffre (modificateurs) |
|---|---|
| Château | +chances Fer/Or, peut contenir Épée Fer garantie |
| Donjon | +chances Or, peut contenir Pioche Or ou Épée Or |
| Bateau pirate | Matériaux nautiques (futur), carte au trésor |
| Pyramide | +chances Or, peut contenir artefact unique |
| Cabane | Bois/Nourriture uniquement |

### 7.2 Matériau Diamant (4e tier)
- Nouveau `MAT_DIAMOND = 3` (décalage de `MAT_GOLD` vers 2 déjà en place)
- Pioche Diamant : mine **tout** (obsidienne, roc)
- Épée Diamant : tue tout mob, dégâts = 5
- Se craft avec Gemme de Diamant (drop démon / minerai profond)

### 7.3 Feedback visuel "tier insuffisant"
- Bloc résistant : animation de **rebond** + particule rouge "trop dur !"
- Mob immunisé : flash blanc + texte flottant **"IMMUNE"** pendant 0.5 s

### 7.4 Barre de durabilité des outils (optionnel)
- Chaque outil a un nombre d'usages (Bois=30, Fer=80, Or=50 "mais rapide", Diamant=200)
- Quand durabilité = 0, l'outil disparaît de l'inventaire
- Incite à crafter et à progresser dans les tiers

### 7.5 Coffres de niveaux
Actuellement tous les coffres ont le même pool de loot. Proposer :
- `CHEST_SURFACE` → bois/fer uniquement
- `CHEST_CAVE` → fer/or
- `CHEST_DUNGEON` → or/diamant (post-boss)

Implémentation : stocker la **profondeur** du coffre au moment de la génération de la structure, et passer ce context à `chest_loot()`.

---

## 8. Résumé de la progression cible

```
Départ (mains vides)
  ↓ Miner Bois/Terre à la main
Craft Pioche Bois
  ↓ Miner Pierre, Charbon
Craft Épée Bois → tuer Zombies, Araignées
  ↓ Trouver/obtenir Lingot Fer (coffre ou drop zombie)
Craft Pioche Fer → miner Brique, Vitre, Minerai de Fer
  ↓ Miner Minerai d'Or
Craft Épée Fer → tuer Golems, Squelettes
Craft Pioche Or → miner Obsidienne, Minerai de Diamant
  ↓ Drop Démon ou minage profond → Gemme Diamant
Craft Épée Or → tuer Démons, Liche
Craft Pioche/Épée Diamant → tuer Vrille (boss final souterrain) → end game
```

---

## 9. Ordre de priorité suggéré

| Priorité | Fonctionnalité | Complexité | Impact |
|---|---|---|---|
| ⭐⭐⭐ | Tier pioche requis par bloc | Faible | Très fort |
| ⭐⭐⭐ | Drop de ressource par mob | Faible | Fort |
| ⭐⭐⭐ | Mob immunisé (tier épée) | Faible | Très fort |
| ⭐⭐⭐ | **Armure Diamant + outils Diamant** | Faible | Fort |
| ⭐⭐⭐ | **Système de troc P1 ↔ P2** | Moyen | Fort |
| ⭐⭐⭐ | **Fix : fantômes / mobs à travers murs** | Faible | Fort |
| ⭐⭐⭐ | **Zombies nocturnes (surface)** | Faible | Fort |
| ⭐⭐ | Minerais (Fer, Or, Diamant) dans world.py | Moyen | Fort |
| ⭐⭐ | Nouveau mob : Araignée | Moyen | Moyen |
| ⭐⭐ | Nouveau mob : Squelette (projectile) | Moyen | Moyen |
| ⭐⭐ | Craft minimal (menu simple) | Moyen | Très fort |
| ⭐⭐ | Matériau Diamant + MAT_DIAMOND | Moyen | Fort |
| ⭐⭐ | **Boss Vrille (végétal souterrain)** | Élevé | Très fort |
| ⭐⭐ | **Loot coffres amélioré (plus de matériaux)** | Faible | Fort |
| ⭐ | Loot coffre contextualisé par structure | Faible | Moyen |
| ⭐ | Nouveau mob : Démon (boss léger) | Élevé | Fort |
| ⭐ | Boss Liche | Très élevé | Très fort |
| ⭐ | Durabilité des outils | Moyen | Moyen |

---

## 10. Armure et outils Diamant (tier 4)

### Nouveaux équipements
| Item | Tier | Craft | Stats |
|---|---|---|---|
| Pioche Diamant | 4 | Gemme Diamant × 3 | Mine **tout** sans exception, rapidité max |
| Épée Diamant | 4 | Gemme Diamant × 2 | Dégâts = 5, tue tout mob |
| Casque Diamant | 4 | Gemme Diamant × 2 | Défense = 3 |
| Plastron Diamant | 4 | Gemme Diamant × 4 | Défense = 5 |
| Bottes Diamant | 4 | Gemme Diamant × 2 | Défense = 2 |

### Mise à jour `config.py`
```python
MAT_DIAMOND = 3           # nouveau tier le plus haut

# Dégâts épée mis à jour
_SWORD_DMG = {
    MAT_WOOD:    1,
    MAT_IRON:    2,
    MAT_GOLD:    3,
    MAT_DIAMOND: 5,        # ← nouveau
}

# Défense armure
_ARMOR_DEF = {
    MAT_WOOD:    1,
    MAT_IRON:    3,
    MAT_GOLD:    4,
    MAT_DIAMOND: 10,       # set complet
}
```

### Densité de coffres par zone

**Règle générale : moins de coffres en surface, toujours plus intéressants en profondeur.**

| Zone | Fréquence de spawn |
|---|---|
| Surface / Cabane | Très rare — 1 coffre max par structure |
| Cave (tier 1) | Rare — 1 coffre par 3–4 salles |
| Cave profonde (tier 2) | Modéré — 1 coffre par 2 salles |
| Donjon | Garanti — 2–3 coffres par donjon |

### Loot coffres — répartition matériaux vs équipement

> **Philosophie** : les coffres donnent principalement des **matériaux bruts** pour alimenter le craft.  
> L'équipement tout fait est **rare** et réservé aux profondeurs. En surface, on ne trouve presque rien d'utile — ce qui pousse à descendre.

| Niveau coffre | Matériaux bruts | Équipement tout fait |
|---|---|---|
| Surface | Bois ×2–4 (70 %), Charbon ×1–2 (25 %), Pierre ×2–3 (20 %) | Outil Bois (5 %) — très rare |
| Cave tier 1 | Lingot Fer ×1–2 (60 %), Charbon ×2 (40 %), Pierre ×3 (30 %) | Outil/Armure Bois (15 %), Fer (5 %) |
| Cave tier 2 | Lingot Fer ×2–3 (70 %), Lingot Or ×1 (30 %), Charbon ×3 (30 %) | Outil/Armure Fer (20 %), Or (5 %) |
| Donjon | Lingot Or ×2–4 (80 %), Gemme Diamant ×1–2 (25 %) | Outil/Armure Or (30 %), Diamant (8 %) |

**Résumé des changements vs l'ancien système :**
- Coffres de surface : **fréquence divisée par ~3**, contenu quasi exclusivement en bois/pierre
- Équipement Bois/Fer en coffre surface : quasi supprimé (5 % max)
- Matériaux bruts augmentés à tous les niveaux (lingots, gemmes)
- Équipement Diamant : uniquement dans les donjons, probabilité faible (8 %)

Règle : **plus le coffre est profond, plus son contenu est intéressant** (système existant conservé et renforcé).

---

## 11. Système de troc entre joueurs

### Déclenchement
- **Outil actif : Main** · Joueur 1 appuie sur **Action** en étant adjacent à Joueur 2  
- Un menu de troc s'ouvre au centre de l'écran  
- Les deux joueurs sont figés (mouvements désactivés) pendant la transaction

### Interface
```
┌─────────────────────────────────────────┐
│           ── TROC ──                    │
│  [J1]               [J2]               │
│  ┌──────┐           ┌──────┐           │
│  │  [X] │◄──────   │  [ ] │           │
│  │  [ ] │           │  [X] │           │
│  │  [ ] │   ─────►  │  [ ] │           │
│  │  [ ] │           │  [ ] │           │
│  │  [ ] │           │  [ ] │           │
│  └──────┘           └──────┘           │
│   ↑↓ : sélectionner  Action : donner   │
│   Alt : annuler et quitter             │
└─────────────────────────────────────────┘
```

### Règles
- Chaque joueur voit **sa propre colonne** d'inventaire (5 slots visibles, scroll ↑↓)
- **Flèches haut/bas** : déplacer le curseur sur un item de son propre inventaire
- **Action** : transférer l'item sélectionné vers l'inventaire de l'autre joueur
  - Si l'inventaire destinataire est plein → refus avec feedback « INVENTAIRE PLEIN »
- **Touche Alternative** (Alt / bouton B) : l'un ou l'autre peut quitter → fermeture immédiate, aucun échange forcé
- Chaque joueur ne peut donner que **depuis son propre inventaire** (pas de vol)

### Implémentation (résumé technique)

```python
# Nouvel état de jeu
STATE_TRADE = "trade"

# Ouverture du troc (dans scenes/game/controls.py ou actions.py)
def try_open_trade(player_src, player_dst):
    if player_src.tool == TOOL_HAND and is_adjacent(player_src, player_dst):
        game_state.mode = STATE_TRADE
        trade_state.p1 = player_src
        trade_state.p2 = player_dst
        trade_state.cursor_p1 = 0
        trade_state.cursor_p2 = 0

# Loop de troc (nouvelle fonction dans loop.py)
def update_trade(inputs_p1, inputs_p2):
    for player, inputs, cursor_attr in [(p1, inputs_p1, 'cursor_p1'), ...]:
        if inputs.up:   trade_state[cursor_attr] = max(0, cursor - 1)
        if inputs.down: trade_state[cursor_attr] = min(len(inv)-1, cursor + 1)
        if inputs.action:
            item = player.inventory[cursor]
            transfer_item(item, player, other_player)
        if inputs.alt:
            game_state.mode = STATE_GAME   # fermeture propre

# Rendu (dans renderer_hud.py)
def draw_trade_menu(surface, trade_state):
    # Panneau centré semi-transparent
    # Colonne gauche : inventaire J1 avec curseur ▶
    # Colonne droite : inventaire J2 avec curseur ▶
    # Flèches centrales indiquant le sens du transfert possible
    ...
```

> L'interface suit le même modèle que le craft : `MODIFIER + Alt` pour quitter, touches directionnelles pour naviguer.

---

## 12. Nouveau boss : La Vrille (`MOB_TENDRIL`)

### Direction artistique
Inspirée des créatures végétales de Half-Life 1 — une masse de racines, lianes et filaments lumineux vert-noir qui pousse dans les profondeurs.  
Elle ne se déplace **jamais** : elle est **ancrée au sol/plafond** et attaque à portée.  
Elle détecte les joueurs à la **vibration** (mouvement dans un rayon, pas le son).

### Caractéristiques
| Attribut | Valeur |
|---|---|
| PV | 25 |
| Dégâts (tentacule) | 3 par touche |
| Portée d'attaque | 6 blocs |
| Portée de détection | 10 blocs |
| Tier épée min | 3 (Or) — résiste à tout le reste |
| Spawn | `surface + 70+`, max **1 par monde** (boss unique) |
| Spawn rate | Très rare (~0.5 % à la génération de monde) |
| Immunité | Projectiles (flèches, boules de feu) — seule l'épée directe blesse |

### Comportement
1. **Dormante** : visible sous forme de racines entrelacées au plafond/sol, inerte
2. **Activée** (joueur à < 10 blocs dans son axe vertical) : tentacules qui s'étendent lentement
3. **Attaque** : 3 tentacules ciblent le joueur, dégâts si contact
4. **Rage** (< 10 PV) : portée +2, vitesse d'extension ×1.5, tentacules supplémentaires
5. **Mort** : animation de décomposition lente (3 secondes), drop garanti

### Drop
- **Cœur de Vrille** (item unique) × 1 — ressource de craft future (ex : armure végétale)
- Gemme de Diamant × 2–4
- Lingot d'Or × 3–6

### Génération
```python
# world.py — à la fin de la génération
if random.random() < 0.005:   # ~0.5 % de chance par monde
    col = random.randint(COLS // 4, 3 * COLS // 4)
    row = random.randint(surface[col] + 70, ROWS - 10)
    spawn_tendril(world, col, row)
```

### Implémentation mob
```python
# mobs/base.py
MOB_TENDRIL = "tendril"

_MOB_MIN_SWORD_TIER[MOB_TENDRIL] = 3      # Or minimum
_MOB_DROPS[MOB_TENDRIL] = [
    (ITEM_TENDRIL_HEART, 1, 1.0),          # toujours
    (ITEM_DIAMOND_GEM,  3, 1.0),           # 2–4 gemmes
    (ITEM_GOLD_INGOT,   5, 1.0),           # 3–6 lingots
]

# Pas de déplacement → pas de physique gravitationnelle
# Logique dans mobs/ai.py : TendrilAI — gestion des tentacules comme sous-entités
```

---

## 13. Corrections & améliorations comportement mobs

### 13.1 Mobs traversant les murs — Fix

**Problème** : certains mobs (notamment les types "fantôme" ou les slimes à haute vitesse) traversent les blocs solides.

**Solution proposée** :
- **Supprimer le type fantôme** (`MOB_GHOST` / mob immatériel) s'il existe — trop problématique et peu cohérent avec la DA
- Pour tous les mobs terrestres : forcer la résolution de collision **tile par tile** (pas de saut de position entre deux frames)
- Limiter la vitesse max des mobs à `MAX_MOB_SPEED = 0.4 * TILE_SIZE / frame` pour éviter le tunnel effect
- Ajouter un flag `solid_collision = True` sur tous les mobs non-volants

```python
# mobs/physics.py — à ajouter
MAX_MOB_SPEED = 0.4   # fraction de TILE_SIZE par frame

def clamp_mob_velocity(mob):
    """Évite le tunnel effect à haute vitesse."""
    speed = math.hypot(mob.vx, mob.vy)
    if speed > MAX_MOB_SPEED:
        factor = MAX_MOB_SPEED / speed
        mob.vx *= factor
        mob.vy *= factor
```

### 13.2 Zombies nocturnes — Cycle jour/nuit

**Comportement** :
- **Nuit** (cycle `sky.is_night == True`) : spawn de 1–3 zombies à la surface, dans des zones sombres
- **Aube** (transition nuit → jour) : les zombies de surface **prennent feu** et meurent (`hp → 0` en 3 secondes)
- Les zombies dans les caves ne sont pas affectés par la lumière du jour

```python
# scenes/game/loop.py (ou sky.py)
def update_zombie_cycle(world, mobs, sky):
    if sky.just_became_night():
        for _ in range(random.randint(1, 3)):
            col = random.randint(0, COLS - 1)
            row = world.surface_at(col)
            spawn_mob(mobs, MOB_ZOMBIE, col, row - 1)

    if sky.just_became_day():
        for mob in mobs:
            if mob.mob_type == MOB_ZOMBIE and mob.y < world.surface_avg:
                mob.burning = True   # animation feu + dégâts continus
                mob.burn_timer = 3.0  # secondes avant mort
```

**Feedback visuel** : animation de brûlure (clignotement orange/rouge) quand `burning == True`.
