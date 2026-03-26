# Minecraft 2D – Game Design Document

> Dernière mise à jour : 2026-03-24

---

## Légende des statuts

| Icône | Signification |
|---|---|
| ✅ | Implémenté et fonctionnel |
| 🔧 | Partiellement implémenté |
| ❌ | Pas encore implémenté |
| 💡 | Nouvelle idée (proposition) |

---

## 1. Vue d'ensemble du jeu

Un jeu de survie/exploration 2D inspiré de Minecraft en local splitscreen (2 joueurs).
Le joueur mine des blocs, craft des outils/armures, explore des structures et combat des mobs dans un monde généré procéduralement.

### Progression cible

```
Départ (mains vides)
  ↓ Miner Bois/Terre à la main
Craft Pioche Bois (Table Tier 1)
  ↓ Miner Pierre, Charbon, Minerai de Fer
Craft Épée Bois → tuer Slimes, Araignées, Zombies
  ↓ Craft Table Tier 2 (Fer)
Craft Pioche Fer → miner Brique, Vitre, Minerai d'Or
Craft Épée Fer → tuer Golems, Trolls
  ↓ Craft Table Tier 3 (Or)
Craft Pioche Or → miner Obsidienne, Minerai de Diamant
Craft Épée Or → tuer Démons, Spectres
  ↓ Craft Table Tier 4 (Diamant)
Craft Pioche/Épée Diamant → tuer Vrille (boss final) → endgame
```

---

## 2. Blocs & Matériaux

### 2.1 Blocs existants ✅

| ID | Bloc | Couleur | Tier pioche requis | Temps de minage |
|---|---|---|---|---|
| 0 | Air | Bleu ciel | – | – |
| 1 | Terre | Marron | 0 (main) | 0.4s |
| 2 | Pierre | Gris | 1 (Bois) | 0.9s |
| 3 | Herbe | Vert | 0 (main) | 0.4s |
| 4 | Sable | Beige | 0 (main) | 0.3s |
| 5 | Bois | Brun | 0 (main) | 0.5s |
| 6 | Charbon | Noir | 1 (Bois) | 0.8s |
| 7 | Brique | Rouge | 2 (Fer) | 1.2s |
| 8 | Coffre | Brun-or | – | 0.3s |
| 9 | Obsidienne | Violet foncé | 3 (Or) | 3.0s |
| 10 | Vitre | Bleu clair | 1 (Bois) | 0.3s |
| 11 | Minerai de Fer | Gris-rouille | 1 (Bois) | 1.2s |
| 12 | Minerai d'Or | Jaune-pierre | 2 (Fer) | 1.8s |
| 13 | Minerai de Diamant | Cyan | 3 (Or) | 2.5s |

### 2.2 Matériaux (tiers) ✅

| Tier | Matériau | Valeur |
|---|---|---|
| 0 | Main | – |
| 1 | Bois | `MAT_WOOD` |
| 2 | Fer | `MAT_IRON` |
| 3 | Or | `MAT_GOLD` |
| 4 | Diamant | `MAT_DIAMOND` |

### 2.3 Nouveaux blocs proposés 💡

| Bloc | Couleur | Tier | Effet | Priorité |
|---|---|---|---|---|
| Lave | Orange `(220,80,0)` | Indestructible | Dégâts au contact, éclairage | ⭐⭐⭐ |
| Glace | Bleu-blanc `(180,220,255)` | 1 (Bois) | Le joueur glisse dessus | ⭐⭐ |
| Mousse | Vert foncé `(50,120,60)` | 0 (main) | Décor, herbe profonde | ⭐ |
| Eau | Bleu `(50,100,200)` | – | Physique de fluide, coule, nage, noyade (voir §9.3) | ⭐⭐⭐ |
| Bedrock | Gris foncé | Indestructible | Fond du monde, inminable | ⭐⭐ |
| Feuillage | Vert clair | 0 (main) | Traverse, décoration d'arbre | ⭐ |
| Échelle | Brun | 0 (main) | Permet de grimper verticalement | ⭐⭐ |
| Torche (bloc) | Jaune | – | Éclaire la zone (rayon 5 blocs) | ⭐⭐⭐ |

---

## 3. Outils & Armes

### 3.1 Outils existants ✅

| ID | Outil | Fonction |
|---|---|---|
| 0 | Main | Outil de base, ouvre les coffres, lance les trades |
| 1 | Pioche | Mine les blocs (selon tier) |
| 2 | Canon (Placer) | Place des blocs depuis l'inventaire |
| 3 | Épée | Attaque les mobs (dégâts selon matériau) |
| 4 | Drapeau | Place un point de respawn |
| 5 | Table de Craft | Ouvre le menu de craft |

### 3.2 Dégâts des épées ✅

| Matériau | Dégâts |
|---|---|
| Bois | 1 |
| Fer | 2 |
| Or | 3 |
| Diamant | 5 |

### 3.3 Nouvelles armes & outils proposés 💡

| Outil | Fonction | Craft | Priorité |
|---|---|---|---|
| **Arc** | Attaque à distance (projectile) | Bois ×2 + Fil d'araignée ×1 | ⭐⭐⭐ |
| **Flèches** | Munitions pour l'arc | Bois ×1 + Pierre ×1 (donne ×8) | ⭐⭐⭐ |
| **Torche** | Éclaire la zone quand tenue/placée | Bois ×1 + Charbon ×1 | ⭐⭐⭐ |
| **Bouclier** | Réduit les dégâts frontaux (bloque) | Fer ×3 | ⭐⭐ |
| **Hache** | Mine le bois plus vite, dégâts moyens | Bois/Fer/Or/Diamant ×2 | ⭐⭐ |
| **Canne à pêche** | Pêche dans l'eau (nourriture) | Bois ×2 + Fil ×1 | ⭐ |
| **Grappin** | Se propulse vers un bloc à distance | Fer ×3 + Fil ×2 | ⭐ |

---

## 4. Équipement & Armure

### 4.1 Armures existantes ✅

Chaque pièce existe en 4 matériaux (Bois, Fer, Or, Diamant).

| Slot | Pièce | Effet |
|---|---|---|
| 2 | Casque | -10% touche, -35% crit |
| 3 | Plastron | -30% touche |
| 4 | Bottes | -10% touche |

L'efficacité de l'armure diminue si le tier de l'armure < tier du mob (pénalité 1/4^diff).

### 4.2 Défense par matériau ✅

| Matériau | Défense par pièce |
|---|---|
| Bois | 0 |
| Fer | 1 |
| Or | 1 |
| Diamant | 2 |

### 4.3 Interaction spéciale ✅
- **Armure en Or** : les Sangliers (MOB_BOAR) n'attaquent pas les joueurs portant de l'or

### 4.4 Améliorations proposées 💡

| Idée | Description | Priorité |
|---|---|---|
| **Durabilité des outils** | Chaque outil a un nombre d'usages (Bois=30, Fer=80, Or=50, Diamant=200). À 0, l'outil casse | ⭐⭐ |
| **Enchantements** | Bonus aléatoire sur équipement trouvé dans les donjons (ex: +vitesse, +dégâts, regen) | ⭐ |
| **Armure spéciale Vrille** | Craftée avec Cœur de Vrille, bonus unique (regen ou résistance poison) | ⭐ |

---

## 5. Système de craft

### 5.1 Table de craft à 4 niveaux ✅

La table se craft/upgrade progressivement. Chaque tier débloque de nouvelles recettes.

| Tier | Nom | Couleur |
|---|---|---|
| 1 | Table Bois | Marron |
| 2 | Table Fer | Gris |
| 3 | Table Or | Jaune |
| 4 | Table Diamant | Cyan |

### 5.2 Recettes implémentées ✅

**Tier 1 (Bois) :**
| Résultat | Ingrédients |
|---|---|
| Pioche Bois | Bois ×3 |
| Épée Bois | Bois ×2 |
| Upgrade → Tier 2 | Bois ×5 + Minerai Fer ×3 |

**Tier 2 (Fer) :**
| Résultat | Ingrédients |
|---|---|
| Pioche Fer | Minerai Fer ×3 |
| Épée Fer | Minerai Fer ×2 |
| Casque Fer | Minerai Fer ×3 |
| Plastron Fer | Minerai Fer ×5 |
| Bottes Fer | Minerai Fer ×3 |
| Upgrade → Tier 3 | Minerai Fer ×5 + Minerai Or ×3 |

**Tier 3 (Or) :**
| Résultat | Ingrédients |
|---|---|
| Pioche Or | Minerai Or ×3 |
| Épée Or | Minerai Or ×2 |
| Casque Or | Minerai Or ×2 |
| Plastron Or | Minerai Or ×5 |
| Bottes Or | Minerai Or ×2 |
| Upgrade → Tier 4 | Minerai Or ×5 + Minerai Diamant ×3 |

**Tier 4 (Diamant) :**
| Résultat | Ingrédients |
|---|---|
| Pioche Diamant | Minerai Diamant ×3 |
| Épée Diamant | Minerai Diamant ×2 |
| Casque Diamant | Minerai Diamant ×2 |
| Plastron Diamant | Minerai Diamant ×5 |
| Bottes Diamant | Minerai Diamant ×2 |

### 5.3 Nouvelles recettes proposées 💡

| Résultat | Ingrédients | Tier requis | Priorité |
|---|---|---|---|
| **Torche ×4** | Bois ×1 + Charbon ×1 | 1 | ⭐⭐⭐ |
| **Arc** | Bois ×2 + Fil d'araignée ×1 | 1 | ⭐⭐⭐ |
| **Flèches ×8** | Bois ×1 + Pierre ×1 | 1 | ⭐⭐⭐ |
| **Brique ×4** | Pierre ×2 | 1 | ⭐⭐ |
| **Vitre ×2** | Sable ×3 | 2 | ⭐⭐ |
| **Bouclier** | Fer ×3 | 2 | ⭐⭐ |
| **Échelle ×4** | Bois ×3 | 1 | ⭐⭐ |
| **Grappin** | Fer ×3 + Fil ×2 | 3 | ⭐ |
| **Armure Vrille** | Cœur de Vrille ×1 + Diamant ×3 | 4 | ⭐ |

### 5.4 Drops de mobs utilisables en craft 💡

Pour que les nouvelles recettes fonctionnent, les mobs doivent dropper des matériaux uniques.
Ces drops sont à ajouter dans `mobs/drops.py`.

| Drop | Mob source | Probabilité | Qté | Utilisation |
|---|---|---|---|---|
| **Fil d'araignée** | Araignée | 80% | ×1-2 | Arc, Canne à pêche, Grappin, Toile-piège |
| **Os** | Squelette | 90% | ×1-2 | Farine d'os (fertilisant), Potion de Soin |
| **Plume** | Poule, Vautour | 70% | ×1-2 | Flèches améliorées, Lit |
| **Viande crue** | Sanglier, Poule | 90% / 60% | ×1-2 | Nourriture, cuisson au Four |
| **Cuir** | Sanglier, Loup | 50% | ×1 | Palmes, Cape, armures légères |
| **Glu de Slime** | Slime | 70% | ×1 | Colle, Potion de Vitesse, pièges |
| **Carapace** | Crabe, Scorpion | 60% | ×1 | Amulette de Résistance, Trident |
| **Dard** | Scorpion | 40% | ×1 | Flèches Envenimées |
| **Fragment d'Âme** | Démon | 40% | ×1 | Potion de Force, Épée du Chaos |
| **Ectoplasme** | Spectre | 60% | ×1-2 | Potion de Vision nocturne, Arc du Néant, Cape de l'Ombre |
| **Cœur de Vrille** | Vrille (boss) | 100% | ×1 | Armure Vrille |

### 5.5 Recettes étendues par thème 💡

#### Éclairage & Environnement

| Résultat | Ingrédients | Tier | Notes |
|---|---|---|---|
| **Torche ×4** | Bois ×1 + Charbon ×1 | 1 | Éclaire rayon 5 blocs quand tenue ou placée |
| **Lanterne** | Vitre ×4 + Charbon ×2 | 2 | Éclaire rayon 7 blocs, s'éteint pas dans l'eau |
| **Lampe à Lave** | Obsidienne ×1 + Vitre ×2 | 3 | Éclaire rayon 9 blocs, indestructible |

#### Armes à distance

| Résultat | Ingrédients | Tier | Notes |
|---|---|---|---|
| **Arc** | Bois ×2 + Fil d'araignée ×1 | 1 | 2 dégâts de base, drop Araignée |
| **Flèches ×8** | Bois ×1 + Pierre ×1 | 1 | Munitions standard |
| **Flèches de Feu ×4** | Flèches ×4 + Charbon ×1 | 1 | Applique Brûlure 3s |
| **Flèches Envenimées ×4** | Flèches ×4 + Dard ×1 | 2 | Applique Poison 5s, drop Scorpion |
| **Flèches de Glace ×4** | Flèches ×4 + Glace ×1 | 3 | Applique Lenteur 3s, drop biome Glace |
| **Arc en Fer** | Minerai Fer ×2 + Fil ×1 | 2 | 3 dégâts, portée +2 blocs |
| **Arc du Néant** | Diamant ×2 + Ectoplasme ×2 | 4 | 5 dégâts, projectile traversant, drop Spectre |

#### Défense & Protection

| Résultat | Ingrédients | Tier | Notes |
|---|---|---|---|
| **Bouclier Bois** | Bois ×3 | 1 | -20% dégâts frontaux, bloque les projectiles |
| **Bouclier Fer** | Minerai Fer ×3 | 2 | -40% dégâts frontaux |
| **Bouclier Or** | Minerai Or ×3 | 3 | -40% dégâts + les Sangliers n'attaquent pas |
| **Amulette de Résistance** | Carapace ×2 + Minerai Or ×1 | 3 | -1 dégât reçu en permanence |
| **Armure Vrille** | Cœur de Vrille ×1 + Diamant ×3 | 4 | Regen passive +1 PV/10s |

#### Utilitaires & Mobilité

| Résultat | Ingrédients | Tier | Notes |
|---|---|---|---|
| **Échelle ×4** | Bois ×3 | 1 | Grimpe verticale sur les murs |
| **Canne à pêche** | Bois ×2 + Fil ×1 | 1 | Pêcher dans l'eau (si biome Eau dispo) |
| **Boussole** | Minerai Fer ×2 + Pierre ×1 | 2 | Indique la direction du point de spawn |
| **Grappin** | Minerai Fer ×3 + Fil ×2 | 2 | Se propulse vers un bloc ciblé |
| **Masque de plongée** | Vitre ×2 + Minerai Fer ×1 | 2 | Jauge d'oxygène ×2 sous l'eau |
| **Palmes** | Cuir ×2 | 2 | Vitesse de nage ×1.5, drop Sanglier/Loup |

#### Blocs craftables

| Résultat | Ingrédients | Tier | Notes |
|---|---|---|---|
| **Brique ×4** | Pierre ×2 | 1 | Bloc de construction résistant |
| **Vitre ×4** | Sable ×3 | 1 | Fenêtres transparentes |
| **Coffre** | Bois ×4 | 1 | Stockage supplémentaire (16 slots) |
| **Lit** | Bois ×2 + Plume ×3 | 1 | Passer la nuit, réinitialise le point de spawn |
| **Four** | Pierre ×5 | 2 | Cuire la nourriture crue |
| **Alambic** | Pierre ×4 + Vitre ×2 | 2 | Brasser des potions |
| **Toile-piège** | Fil ×3 + Bois ×1 | 1 | Ralentit les mobs qui marchent dessus (3s) |
| **Piège à ressort** | Minerai Fer ×2 + Pierre ×1 | 2 | 1 dégât aux mobs qui marchent dessus |

#### Nourriture & Survie

| Résultat | Ingrédients | Tier | Notes |
|---|---|---|---|
| **Viande rôtie** | Viande crue ×1 (au Four) | 2 | Restaure 5 faim, drop Sanglier/Poule |
| **Soupe de Crapaud** | Bois ×1 + Pierre ×1 | 1 | Restaure 2 faim + Regen 5s, blague |
| **Galette de Sable** | Sable ×2 + Charbon ×1 | 1 | Restaure 1 faim, biome Désert |
| **Pain ×2** | Blé ×3 (système farming) | 1 | Restaure 3 faim |

#### Potions (nécessitent un Alambic)

| Résultat | Ingrédients | Tier | Effet |
|---|---|---|---|
| **Potion de Soin** | Os ×2 + Glu de Slime ×1 | 2 | +3 PV instantané |
| **Potion de Vitesse** | Glu de Slime ×2 + Plume ×1 | 2 | Vitesse ×1.5 pendant 10s |
| **Potion de Force** | Fragment d'Âme ×1 + Minerai Or ×2 | 3 | Dégâts ×1.5 pendant 15s |
| **Potion de Vision nocturne** | Ectoplasme ×1 + Charbon ×2 | 3 | Voir dans le noir complet pendant 20s |
| **Potion de Respiration** | Ectoplasme ×1 + Vitre ×2 | 3 | Pas de jauge d'oxygène pendant 30s |
| **Potion Anti-Poison** | Os ×1 + Pierre ×2 | 2 | Immunisé au Poison pendant 60s |

#### Armes & équipements spéciaux (drops rares)

| Résultat | Ingrédients | Tier | Notes |
|---|---|---|---|
| **Trident** | Minerai Fer ×2 + Carapace ×1 | 2 | Mêlée + lancer, dégâts ×2 sous l'eau |
| **Cape de l'Ombre** | Ectoplasme ×3 + Cuir ×2 | 3 | Invisibilité 5s (cooldown 30s), drop Spectre |
| **Épée du Chaos** | Diamant ×2 + Fragment d'Âme ×2 | 4 | 10% chance d'éliminer un mob non-boss |
| **Armure d'Écaille** | Écaille ×5 (drop Serpent de mer) | 3 | Respiration illimitée sous l'eau |

---

## 6. Mobs

### 6.1 Mobs passifs ✅

| Mob | PV | Spawn | Biome | Comportement |
|---|---|---|---|---|
| Poule | 1 | Surface | Tous | Marche aléatoire |
| Grenouille | 1 | Surface | Forêt uniquement | Saute, marche aléatoire |
| Mouette | 1 | Survol surface | Forêt, Désert | Vol, côtier |
| Pingouin | 2 | Surface | **Glace uniquement** | Marche, glisse, fuit le joueur |

### 6.2 Mobs agressifs ✅

| Mob | PV | Dégâts | Tier épée min | Zone de spawn | Biome | Comportement spécial |
|---|---|---|---|---|---|---|
| Slime | 2 | 1 | 0 (main) | Surface +5 à +40 | Tous | Saute pour chasser |
| Chauve-souris | 1 | 1 | 0 (main) | Grottes partout | Tous | Passive de jour, agressive la nuit |
| Zombie | 3 | 1 | 1 (Bois) | Surface +10 à +60 | Tous | Spawn nocturne, brûle à l'aube |
| Araignée | 3 | 1 | 1 (Bois) | Surface +5 à +20 | Forêt, Glace | Escalade les murs, rapide |
| Squelette | 4 | 1 (dist) | 1 (Bois) | Grottes +20 | Tous | Maintient distance, attaque à distance |
| Crabe | 3 | 1 | 1 (Bois) | Surface sable | Désert, Forêt (rare) | Marche latérale, charge |
| Sanglier | 4 | 1 | 1 (Bois) | Surface herbe | Forêt uniquement | Ignore joueurs en Or |
| Scorpion | 3 | 2 | 1 (Bois) | Surface | **Désert uniquement** | Rapide, charge directe |
| Vautour | 3 | 1 | 0 (main) | Survol surface | **Désert uniquement** | Volant, plonge sur le joueur |
| Ours polaire | 8 | 3 | 2 (Fer) | Surface | **Glace uniquement** | Tanky, charge puissante |
| Troll | 6 | 2 | 1 (Bois) | Profondeur +20 à +45 | Tous | Lent, saute, détection 9 blocs |
| Golem | 5 | 4 (perce) | 2 (Fer) | Cabanes (50%) | Forêt, Glace | Gardien de structure |
| Ver | 9 | 3 | 2 (Fer) | Profondeur +45 à +65 | Tous | Traverse terrain, charge en ligne |
| Démon | 8 | 6 | 3 (Or) | Profondeur +60+ | Tous | Volant, attaque à distance |
| Spectre | 12 | 4 | 3 (Or) | Profondeur +65+ | Tous | Volant, détection 20 blocs |

### 6.3 Boss ✅

| Boss | PV | Dégâts | Tier épée min | Spawn | Comportement |
|---|---|---|---|---|---|
| **Vrille** | 25 | 3 (tentacule) | 3 (Or) | Profondeur +70+, max 1/monde, 0.5% chance | Stationnaire, portée 6 blocs, détection 10 blocs, immunisée projectiles |

**Drops Vrille :** Minerai Diamant ×2-4 (garanti), Minerai Or ×3-6 (garanti)

### 6.4 Nouveaux mobs proposés 💡

| Mob | PV | Dégâts | Tier épée | Zone | Comportement | Priorité |
|---|---|---|---|---|---|---|
| **Liche** (boss donjon) | 20 | 3 | 3 (Or) | Donjon spécial, 1/monde | Invoque des squelettes, projectiles multiples | ⭐⭐ |
| **Loup** ✅ | 4 | 1 | 0 | Forêts surface | Neutre, attaque en meute si on frappe un loup. Apprivoisable (Poisson) → compagnon de combat | ⭐⭐ |
| **Chat sauvage** ✅ | 2 | 0 | 0 | Surface (hors glace) | Passif, fuit. Apprivoisable (Poisson) → familier décoratif | ⭐⭐ |
| **Poisson** | 1 | 0 | 0 | Eau | Passif, pêchable pour nourriture | ⭐ |
| **Fantôme** | 5 | 2 | 2 (Fer) | Surface la nuit | Volant, apparaît si le joueur n'a pas dormi | ⭐ |
| **Mimic** | 6 | 2 | 1 (Bois) | Donjons | Ressemble à un coffre, attaque quand on l'ouvre | ⭐⭐⭐ |

---

## 7. Monde & Génération

### 7.1 Terrain ✅
- Monde infini horizontalement, 120 blocs de hauteur
- Génération par seed (32 bits)
- Surface : bruit de Perlin (fréquence 0.07)
- Biomes : Sable (7% des colonnes), Herbe (défaut)
- Arbres : 6% de chance, 2-3 blocs de haut

### 7.2 Grottes ✅
- Automate cellulaire (bruit 2D > 0.67)
- Spawn sous la couche de pierre (profondeur > 8)

### 7.3 Minerais ✅
| Minerai | Profondeur | Probabilité |
|---|---|---|
| Charbon | 10+ | Variable |
| Fer | 10 à 45 | ~12% |
| Or | 28 à 65 | ~6% |
| Diamant | 58+ | ~2% |

### 7.4 Structures ✅
| Structure | Taille | Fréquence | Espacement min |
|---|---|---|---|
| Cabane | 5 large | 2.5% / ~40 cols | – |
| Château | 11×9 | 0.3% | 120 cols |
| Bateau pirate | 14×8 | 0.4% | 100 cols |
| Pyramide | 11×6 | 0.3% | 110 cols |
| Donjon | 9×5 | 0.6% | 90 cols |

### 7.5 Loot des coffres par profondeur ✅
| Zone | Matériaux | Équipement |
|---|---|---|
| Surface (<20) | Bois ×2-4 (70%), Charbon (25%), Pierre (20%) | Outil Bois (5%) |
| Grotte (20-50) | Minerai Fer ×1-2 (70%), Charbon (40%) | Bois (15%), Fer (5%) |
| Profond (50+) | Minerai Or ×2-4 (80%), Diamant (25%) | Or (30%), Diamant (8%) |

### 7.6 Améliorations monde proposées 💡

| Idée | Description | Priorité |
|---|---|---|
| **Biomes variés** | Forêt dense, désert, toundra (neige/glace), marais, volcan — chacun avec mobs et ressources spécifiques | ⭐⭐⭐ |
| **Lave en profondeur** | Poches de lave à profondeur 60+, dégâts au contact, éclairage ambiant | ⭐⭐⭐ |
| **Eau & physique fluide** | Rivières en surface, lacs souterrains, le joueur nage/ralentit | ⭐⭐ |
| **Villages PNJ** | Petits villages avec PNJ marchands (acheter/vendre ressources) | ⭐⭐ |
| **Portails** | Structures spéciales menant à une dimension alternative (Nether-like) | ⭐ |
| **Grottes améliorées** | Stalactites, stalagmites, grottes de cristal, biomes souterrains | ⭐⭐ |
| **Fond du monde (Bedrock)** | Couche indestructible à la profondeur max | ⭐⭐ |

---

## 8. Systèmes de jeu

### 8.1 Cycle jour/nuit ✅
- Système de ciel avec transitions de couleur
- Icônes soleil/lune
- Overlay sombre la nuit
- Zombies spawn en surface la nuit, brûlent à l'aube

### 8.2 Système de combat ✅
- Attaque au corps-à-corps avec épée
- Dégâts selon matériau de l'épée
- Résistance des mobs par tier d'épée (feedback "IMMUNE")
- Système de touche/critique (80% touche, 40% crit, ×2 multiplicateur)
- Armure réduit les chances d'être touché et les crits

### 8.3 Système de minage ✅
- Hold-to-mine avec barre de progression
- Temps de minage différent par bloc
- Tier de pioche requis par bloc

### 8.4 Système de placement ✅
- Outil Canon place des blocs depuis l'inventaire
- Collision avec le joueur empêche le placement
- Cooldown de 0.4s

### 8.5 Inventaire ✅
- 5 slots : Outils (0), Ressources (1), Casque (2), Plastron (3), Bottes (4)
- Navigation haut/bas/gauche/droite
- Compteur de ressources

### 8.6 Trading P2P ✅
- Activé main + action quand adjacent à l'autre joueur
- Menu avec les 2 inventaires côte à côte
- Transfert d'items entre joueurs
- Alt pour fermer

### 8.7 Respawn ✅
- Placement de drapeau pour définir le point de respawn
- 6 PV max, flash rouge quand touché

### 8.8 Sauvegarde ✅
- Base de données pour sauvegarder le monde et l'inventaire
- Modifications du monde persistées entre sessions

---

## 9. Nouvelles features proposées 💡

### 9.1 Éclairage & Torches ⭐⭐⭐
**Impact : IMMERSION**

Actuellement les grottes sont uniformément sombres. Ajouter un système d'éclairage dynamique :
- **Torche tenue** : éclaire un rayon de ~5 blocs autour du joueur
- **Torche placée** : bloc lumineux permanent, rayon de 5 blocs
- **Lave** : source de lumière naturelle (rayon 4)
- Les mobs agressifs spawnent plus dans l'obscurité
- Craft : Bois ×1 + Charbon ×1 → Torche ×4

### 9.2 Arc & Combat à distance ⭐⭐⭐
**Impact : GAMEPLAY**

- **Arc** : arme à distance, tire des flèches en arc de cercle
- **Flèches** : consommables, craft facile (Bois + Pierre → ×8)
- Permet de combattre les Squelettes et Démons à leur propre jeu
- Dégâts de base : 2 (comparable épée Fer)
- Variantes possibles : Flèches de feu (+ Charbon), Flèches de glace (+ Glace)

### 9.3 Eau & Monde aquatique ⭐⭐⭐
**Impact : IMMERSION / EXPLORATION / SURVIE**

Système d'eau complet avec physique de fluide et contenu aquatique.

#### Bloc d'eau — physique de fluide
- **TILE_WATER** : nouveau type de bloc, bleu semi-transparent `(50, 100, 200, 160)`
- **Gravité de l'eau** : l'eau coule vers le bas si l'espace en dessous est libre (Air)
  - Vitesse : **1 bloc toutes les ~2 secondes** (tick d'eau)
  - L'eau se propage aussi latéralement si elle ne peut plus descendre (remplissage en U)
  - On peut **vider un réservoir** en cassant un bloc en dessous → l'eau s'écoule progressivement
  - On peut **créer un barrage** en plaçant des blocs pour contenir l'eau
- **Génération** :
  - Lacs souterrains : poches d'eau dans les grottes (profondeur 15-50), 3-10 blocs de large
  - Rivières de surface : rares, coulent dans des dépressions naturelles
  - Réservoirs dans les structures (Bateau pirate rempli d'eau de cale, pyramide inondée)

#### Physique du joueur dans l'eau
- **Nage** : le joueur se déplace plus lentement dans l'eau (vitesse ×0.5)
- **Gravité réduite** : chute ralentie, possibilité de remonter en appuyant sur saut
- **Jauge d'oxygène** : 10 secondes d'air sous l'eau
  - Barre d'oxygène affichée dans le HUD (bulles)
  - À 0, le joueur perd **1 PV/seconde** (noyade)
  - Se recharge instantanément à la surface
- **Minage sous l'eau** : vitesse de minage ×0.5 (sauf avec enchantement futur)

#### Mobs aquatiques 💡
| Mob | PV | Dégâts | Tier épée | Comportement | Drop |
|---|---|---|---|---|---|
| **Poisson** | 1 | 0 | 0 | Passif, nage dans l'eau, fuit le joueur | Poisson cru (nourriture) |
| **Méduse** | 2 | 1 (poison) | 0 | Flotte dans l'eau, inflige poison au contact (3s) | Gel lumineux |
| **Piranha** | 2 | 1 | 1 (Bois) | Agressif en banc (3-5), rapide dans l'eau | Dent (craft) |
| **Serpent de mer** | 8 | 3 | 2 (Fer) | Mini-boss aquatique, charge sous l'eau, détection 12 blocs | Écaille (craft armure aqua) |
| **Kraken** (boss) | 30 | 4 | 3 (Or) | Boss aquatique, tentacules, crée des vagues, max 1/monde | Cœur de Kraken + Diamant ×3-5 |

#### Équipement aquatique 💡
| Item | Craft | Effet |
|---|---|---|
| **Masque de plongée** | Vitre ×2 + Fer ×1 | Oxygène ×2 (20 secondes) |
| **Palmes** | Cuir ×2 (ou Écaille ×1) | Vitesse nage ×1.5 |
| **Armure d'écaille** | Écaille ×5 (drop Serpent de mer) | Respiration sous l'eau illimitée + vitesse nage normale |
| **Trident** | Fer ×2 + Écaille ×1 | Arme de mêlée/lancer, dégâts ×2 sous l'eau |

#### Interactions eau & autres systèmes
- **Eau + Lave** = Obsidienne (quand l'eau touche la lave, le bloc de lave se transforme)
- **Eau + Torche** = la torche s'éteint (ne peut pas placer de torche dans l'eau)
- **Mobs terrestres dans l'eau** : ralentis, certains ne savent pas nager et coulent
- **Zombies dans l'eau** : deviennent des "Noyés" (variante, même stats mais nagent)

### 9.4 Système de faim / nourriture ⭐⭐
**Impact : SURVIE / IMMERSION**

- Barre de faim (10 points) qui diminue lentement
- À 0, le joueur perd des PV
- Sources de nourriture :
  - Pommes (drop des arbres)
  - Viande crue (drop mobs : Poule, Sanglier)
  - Viande cuite (cuisson au feu/four)
  - Poisson (pêche)
- Craft : **Four** (Pierre ×5) pour cuire la nourriture
- Manger restaure de la faim + petite regen de PV

### 9.5 Système de lumière des grottes ⭐⭐⭐
**Impact : IMMERSION / EXPLORATION**

- Dégradé de luminosité en fonction de la profondeur
- Plus on descend, plus c'est sombre (déjà partiellement fait visuellement)
- Les torches deviennent essentielles en profondeur
- Les mobs profonds pourraient avoir un avantage dans le noir

### 9.6 Musique & Sons ⭐⭐
**Impact : IMMERSION**

- Musique d'ambiance (calme en surface, tendue en profondeur)
- Sons de minage, combat, craft
- Son d'ambiance dans les grottes (gouttes d'eau, vent)
- Sons aquatiques sous l'eau (bulles, courant)
- Musique de boss

### 9.7 Mini-map ⭐⭐
**Impact : NAVIGATION**

- Petite carte dans un coin montrant :
  - Terrain environnant
  - Position du joueur
  - Position de l'autre joueur
  - Structures découvertes

### 9.8 Système d'XP & Niveaux ⭐⭐
**Impact : PROGRESSION**

- Gagner de l'XP en minant et tuant des mobs
- Monter de niveau débloque :
  - Plus de PV max
  - Vitesse de minage améliorée
  - Nouveaux emplacements d'inventaire
- Barre d'XP dans le HUD

### 9.9 Effets de statut ⭐⭐
**Impact : GAMEPLAY**

| Effet | Source | Durée | Description |
|---|---|---|---|
| Poison | Araignée, Méduse | 5s | -1 PV/2s |
| Brûlure | Lave, Démon | 3s | -1 PV/s |
| Lenteur | Toile d'araignée, Glace, Eau | 3s | Vitesse /2 |
| Noyade | Sous l'eau sans air | Continu | -1 PV/s |
| Régénération | Nourriture, potion | 10s | +1 PV/3s |
| Force | Potion | 15s | Dégâts ×1.5 |

### 9.10 Potions ⭐
**Impact : GAMEPLAY AVANCÉ**

- Craftées avec des ingrédients rares (Gel de slime, Yeux d'araignée, Gel lumineux, etc.)
- Nécessite un **Alambic** (craft : Pierre ×4 + Vitre ×2)
- Types : Soin, Régénération, Force, Vitesse, Vision nocturne, **Respiration aquatique**

### 9.11 Animaux domesticables ✅
**Impact : IMMERSION**

Chaque joueur peut avoir **un seul familier** à la fois. Apprivoisement avec **TOOL_HAND + action** près de l'animal.

| Animal | Item requis | Comportement familier |
|---|---|---|
| **Poule** | Gratuit | Suit le joueur, pond un Oeuf toutes les 60s (ajouté à l'inventaire) |
| **Loup** | Poisson ×1 | Suit le joueur, attaque les mobs hostiles proches (2 dmg, cd 1.5s) |
| **Chat** | Poisson ×1 | Suit le joueur, ne fait rien (comme dans la vraie vie) |

- Familier se téléporte si distance > 20 tuiles du joueur
- Loup familier donne les drops au joueur quand il tue un mob
- Poule familière produit TILE_EGG (nouvel item)
- Sauvegardé en DB (type + HP + timer oeuf)
- Coeur rouge pixel-art affiché au-dessus du familier

### 9.12 Système de farming ⭐
**Impact : SURVIE**

- Planter des graines sur de la terre
- Cultiver : Blé, Carottes, Citrouilles
- Nécessite de l'eau à proximité
- Récolte pour nourriture ou craft

---

## 10. Améliorations techniques proposées 💡

| Amélioration | Description | Priorité |
|---|---|---|
| **Particules** | Effet visuel lors du minage, combat, mort de mob, torche | ⭐⭐⭐ |
| **Animations des mobs** | Sprites animés au lieu de rectangles colorés | ⭐⭐ |
| **Sprites du joueur** | Animation de marche, minage, attaque | ⭐⭐ |
| **Écran de mort** | Écran "Game Over" avec stats et option respawn | ⭐⭐ |
| **Menu principal** | Titre, Nouvelle partie, Charger, Options | ⭐⭐ |
| **Keybinding configurable** | Permettre de remapper les touches | ⭐ |
| **Optimisation rendu** | Frustum culling amélioré, chunk loading async | ⭐ |
| **Tutoriel intégré** | Premiers pas guidés pour les nouveaux joueurs | ⭐⭐ |

---

## 11. Priorités recommandées

### Priorité haute ⭐⭐⭐ — Impact immédiat sur l'immersion et le gameplay

| # | Feature | Type | Complexité |
|---|---|---|---|
| 1 | **Eau & monde aquatique** (physique fluide, nage, oxygène, mobs aquatiques) | Monde/Survie | Élevée |
| 2 | **Torches & éclairage** | Immersion | Moyenne |
| 3 | **Arc & flèches** | Gameplay | Moyenne |
| 4 | **Lave** (+ interaction Eau→Obsidienne) | Monde/Danger | Faible |
| 5 | **Mob Mimic** (coffre piégé) | Fun/Surprise | Faible |
| 6 | **Particules** (minage, combat) | Polish | Faible |
| 7 | **Biomes variés** | Exploration | Élevée |

### Priorité moyenne ⭐⭐ — Enrichit le jeu significativement

| # | Feature | Type | Complexité |
|---|---|---|---|
| 8 | Système de faim/nourriture | Survie | Moyenne |
| 9 | Effets de statut (poison, noyade, brûlure...) | Combat | Moyenne |
| 10 | Mini-map | Navigation | Moyenne |
| 11 | Durabilité des outils | Progression | Faible |
| 12 | Boss Liche | Combat | Élevée |
| 13 | Boss Kraken (aquatique) | Combat/Eau | Élevée |
| 14 | ~~Loups (meute + domestication)~~ ✅ | Immersion | Moyenne |
| 15 | Sons & musique | Immersion | Moyenne |

### Priorité basse ⭐ — Nice to have, quand le reste est solide

| # | Feature | Type | Complexité |
|---|---|---|---|
| 16 | Potions & alambic (dont Respiration aquatique) | Gameplay | Élevée |
| 17 | Farming (nécessite eau) | Survie | Moyenne |
| 18 | Villages PNJ | Monde | Très élevée |
| 19 | Portails/dimensions | Monde | Très élevée |
| 20 | Enchantements | Progression | Élevée |
| 21 | ~~Animaux domesticables~~ ✅ | Immersion | Moyenne |

---

## 12. Résumé : Ce qui existe vs ce qui reste à faire

### ✅ Implémenté (complet)
- **Système de biomes** : 3 biomes (Forêt, Désert, Glace) avec bruit lent, sols/ciel/mobs/structures différents
- Minage avec tiers de pioche
- Craft avec table à 4 niveaux (Bois → Fer → Or → Diamant)
- 20 mobs (5 passifs, 14 agressifs, 1 boss) dont 4 mobs de biome (Pingouin, Ours polaire, Scorpion, Vautour)
- Combat au corps-à-corps avec épée (4 tiers)
- Armure complète (4 tiers × 3 pièces)
- Minerais (Fer, Or, Diamant) avec génération par profondeur
- 5 structures (Cabane, Château, Bateau, Pyramide, Donjon)
- Loot de coffres contextualisé par profondeur
- Cycle jour/nuit avec zombies nocturnes
- Trading P2P (2 joueurs)
- Boss Vrille (souterrain, unique)
- Placement de blocs
- Système de drapeau/respawn
- Sauvegarde monde/inventaire

### ❌ Pas encore implémenté (du design original)
- Boss Liche
- Durabilité des outils
- Lave, Glace, Mousse (nouveaux blocs)
- Items spéciaux de craft (Fil d'araignée, Os, Gel de slime — en tant que ressource utilisable)
- Drop de mob en tant que ressources de craft (les mobs drop des minerais mais pas d'items uniques craftables)

### 💡 Nouvelles idées (pas dans le design original)
- **Eau & monde aquatique** — physique de fluide (coule 1 bloc/2s), nage, jauge d'oxygène, mobs aquatiques (Poisson, Méduse, Piranha, Serpent de mer, boss Kraken), équipement de plongée, interaction Eau+Lave=Obsidienne
- Torches & éclairage dynamique
- Arc & combat à distance
- ~~Biomes variés~~ ✅ Implémenté (Forêt, Désert, Glace)
- Effets de statut (poison, brûlure, noyade, etc.)
- Potions (dont Respiration aquatique)
- Farming (nécessite eau à proximité)
- PNJ marchands
- Animaux domesticables
- Particules visuelles
- Sons & musique
