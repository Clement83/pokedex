# Minecraft 2D – Feuille de route : Loot, Mobs & Progression

> État actuel condensé pour référence rapide

| Domaine | Ce qui existe |
|---|---|
| **Outils** | Main / Pioche / Canon / Épée / Drapeau |
| **Matériaux** | Bois (0) · Fer (1) · Or (2) |
| **Blocs** | Air, Terre, Pierre, Herbe, Sable, Bois, Charbon, Brique, Coffre, Obsidienne, Vitre |
| **Mobs agressifs** | Slime (2 PV) · Zombie (3 PV) · Golem (5 PV) |
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
Craft Pioche/Épée Diamant → end game
```

---

## 9. Ordre de priorité suggéré

| Priorité | Fonctionnalité | Complexité | Impact |
|---|---|---|---|
| ⭐⭐⭐ | Tier pioche requis par bloc | Faible | Très fort |
| ⭐⭐⭐ | Drop de ressource par mob | Faible | Fort |
| ⭐⭐⭐ | Mob immunisé (tier épée) | Faible | Très fort |
| ⭐⭐ | Minerais (Fer, Or, Diamant) dans world.py | Moyen | Fort |
| ⭐⭐ | Nouveau mob : Araignée | Moyen | Moyen |
| ⭐⭐ | Nouveau mob : Squelette (projectile) | Moyen | Moyen |
| ⭐⭐ | Craft minimal (menu simple) | Moyen | Très fort |
| ⭐⭐ | Matériau Diamant + MAT_DIAMOND | Moyen | Fort |
| ⭐ | Loot coffre contextualisé par structure | Faible | Moyen |
| ⭐ | Nouveau mob : Démon (boss léger) | Élevé | Fort |
| ⭐ | Boss Liche | Très élevé | Très fort |
| ⭐ | Durabilité des outils | Moyen | Moyen |
