# Minecraft 2D

Sandbox 2D 2 joueurs split-screen. Monde infini procédural, minage, craft, mobs, persistance SQLite.

## Structure

```
main.py            – Splash screen, init DB
config.py          – Constantes (39 tuiles, 9 outils, 3 biomes, physique, craft, équipements)
db.py              – SQLite : worlds, blocks (deltas seulement), players (pos + inventaire JSON)
world.py           – Génération procédurale par hash déterministe (terrain, grottes, minerais)
world_builders.py  – Structures : châteaux, pyramides, bateaux pirates, igloos, donjons
sounds.py          – Synthèse audio procédurale (mine, place, coffre, saut, épée...)
scenes/
  select.py        – Menu sélection/création de monde (4 slots)
  game/            – Module de jeu (voir CLAUDE.md dédié dans scenes/game/)
mobs/
  base.py          – 20 types de mobs, constantes (taille, couleur, HP, dégâts, tier)
  manager.py       – Spawn budgété (10/joueur), despawn à 80 tiles, cooldown 45s
  ai.py            – IA par type : chase, wander, flying, deep cave, spécial
  physics.py       – Collision et mouvement des mobs
  armor.py         – Défense armure + dégâts contact
  renderer.py      – Dessin des mobs (rectangles colorés pixel-art)
  deep.py          – Mobs de grottes profondes (Troll, Worm, Wraith, Tendril)
  drops.py         – Tables de loot par type de mob
```

## Monde

- **Infini horizontal**, 120 tuiles de haut. Seed déterministe (hash)
- **3 biomes** : Forest (arbres, cabanes), Desert (pyramides, dunes), Ice (igloos, icebergs)
- **Sous-sol** : grottes (Perlin > 0.67), minerais par profondeur (charbon→fer→or→diamant)
- **Liquides** : lava/water coulent, eau+lave = obsidienne
- **Structures** : châteaux, navires pirates, grandes pyramides, donjons (coffres + loot)
- **Stockage delta** : seules les modifications joueur sont en DB

## Gameplay

- **Physique** : gravité 28 t/s², saut -9.5 t/s, escalade murs 4.5 t/s, friction glace
- **Inventaire** : 5 slots (outil, ressources, tête, corps, pieds)
- **Craft** : 4 tiers (bois→fer→or→diamant), 24 recettes
- **Combat** : épée (cooldown 0.35s, dégâts par matériau), arc (flèches paraboliques)
- **Minage** : temps variable par bloc (0.2-3s), tier de pioche requis
- **Mobs** : 20 types (agressifs avec tier d'immunité, passifs, boss)
- **Cycle jour/nuit** : 20 min, zombies au crépuscule, brûlent à l'aube
- **Split-screen** : 2 viewports quand joueurs éloignés (>88px), caméra partagée sinon

## Rendu

- **ChunkCache** : pré-rendu 320x320px par thread, cache invalidé sur modification
- **Pas de fichiers assets** : tout est dessiné (rectangles colorés, pixel-art procédural)
- **30 FPS** cible, sauvegarde DB toutes les 2s

## Contrôles

- J1 : Analogique/D-Pad + L2 (miner) + SELECT (modificateur)
- J2 : ABXY + R2 (miner) + START (modificateur)
- Clavier debug : WASD/Flèches + E/RCtrl + R/Enter
