# mobs/ — Systeme de mobs Minecraft 2D

22 types de mobs avec IA, physique, combat, loot et familiers.

## Structure

```
base.py      – Classe Mob + constantes des 22 types (taille, HP, dégâts, couleur, tier immunité)
manager.py   – MobManager : spawn budgété (10/joueur, rayon 35 tiles), despawn 80 tiles, cooldown 45s
ai.py        – IA par type : chase (LOS + distance), wander, vol sinusoidal, mobs profonds
physics.py   – Mouvement + collision terrain (gravité, saut, vol)
armor.py     – Calcul défense armure joueur, dégâts contact mob→joueur
renderer.py  – Dessin pixel-art (rectangles colorés, taille par type)
deep.py      – Mobs de grottes profondes : Troll (lent, tank), Worm (traverse terrain), Wraith (vol), Tendril (boss statique)
drops.py     – Tables de loot : Zombie→fer, Golem→pierre+fer, Demon→or+diamant, Tendril→diamant garanti
familiar.py  – Familiers : apprivoisement (Main+action), suivi joueur, loup=combat, chat=déco, poule=oeufs
```

## Types principaux

**Agressifs** (tier = épée minimum pour infliger des dégâts) :
- Slime (0), Zombie (1), Golem (2), Spider (6), Skeleton (7), Crab (9)
- Demon (10, tier 3 = or+), Boar (11, neutre si armure or), Polar Bear (17), Scorpion (18)
- Deep : Troll (12), Worm (13), Wraith (14), Tendril (15, boss tier 3)

**Passifs** : Chicken (3), Frog (4), Seagull (5), Bat (8), Penguin (16), Vulture (19), Cat (21)

**Domesticables** : Chicken (3, gratuit), Wolf (20, poisson), Cat (21, poisson)
- Wolf : neutre en surface, attaque en meute si frappé
- 1 familier max par joueur, sauvegardé en DB

## Spawn

Table déclarative `_SPAWN_RULES` dans `manager.py` : hash check, contrainte biome, mode (surface/underground/flying), plage de profondeur.
