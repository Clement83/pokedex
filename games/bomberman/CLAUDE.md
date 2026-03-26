# Bomberman

Bomberman classique 4 joueurs : 2 humains (J1/J2) + 2 IA. Grille 15x9, premier à survivre gagne.

## Structure

```
main.py           – Point d'entrée, splash screen animé, boucle partie/résultat
config.py         – Constantes (grille 15x9, cellules 30px, 60 FPS, contrôles)
scene_game.py     – Logique de jeu complète (entités, IA, physique, rendu) ~1084 lignes
scene_result.py   – Podium des résultats
sound_manager.py  – Synthèse audio procédurale (5 SFX, aucun fichier audio)
```

## Entités (scene_game.py)

- **Player** : position grille, alive, couleur, cooldowns, stats bonus
- **Bomb** : timer 3s, range, owner, réactions en chaîne
- **Explosion** : cells touchées, durée 0.6s
- **Bonus** : BOMB (+1 bombe max), RANGE (+1 portée), SPEED (-0.025s cooldown)

## Mécanique

- **5 layouts procéduraux** : Classic, Labyrinth, Arena, Tunnels, Cross (choix aléatoire)
- **Bombes** : posées sur case vide, explosion en croix (4 directions), chaîne si bombe touchée
- **Bonus** : 60% de chance au bloc détruit. Max : 4 bombes, 6 range, 0.05s move
- **Mort subite** : après 90s, pluie de bombes aléatoires (intervalle décroissant)
- **10 thèmes visuels** : Classic, Neon, Forest, Lava, Girly, Pastel...

## IA (3 états)

- **SEEK** : BFS vers cibles bombardables, priorité bonus proches
- **FLEE** : BFS vers zone safe après pose de bombe
- **WAIT_SAFE** : attente en sécurité, opportunisme si cible adjacente

## Contrôles

- J1 : Z/Q/S/D + E (bombe) | Hat/Axes manette + btn 12
- J2 : O/K/L/M + P (bombe) | ABXY manette + btn 17
