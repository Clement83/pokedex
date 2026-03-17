# Jeu Shifter

Drag race 1/4 mile en split-screen 2 joueurs. Le gameplay repose entièrement sur le **timing des changements de vitesse** : shift au bon RPM pour maximiser la puissance.

## Fonctionnel

**Flux :** Écran titre → Sélection voitures → Course → Résultats → (rejouer ou quitter)

**Sélection :** chaque joueur choisit sa voiture indépendamment (navigation ←/→). Affiche stats, courbe de puissance, catégorie. Les deux doivent confirmer "Prêt" pour lancer.

**Course :** split-screen vertical (2×240 px). Feux de départ animés (rouge → vert). La voiture accélère tant que le joueur maintient la touche gaz. Changer de rapport au bon moment donne un bonus de puissance (`PERFECT` +5 %, `GOOD` ±0, `BAD` −10 %). Rester trop longtemps en zone rouge surchauffe le moteur (malus progressif + fumée visuelle).

**Résultats :** temps, vitesse max, classement des shifts (parfaits / bons / ratés).

**6 voitures :** chacune a ses propres courbes de puissance, ratios de boîte, poids et caractéristiques moteur.

## Technique

```
main.py          ← Point d'entrée, boucle scènes, écran titre animé (splash 8 s)
config.py        ← Constantes : specs 6 voitures, courbes puissance, zones shift, physique, contrôles
car.py           ← Classe Car : physique complète (force tractrice, air/roll résistance, surchauffe)
scene_race.py    ← Scène de course : boucle principale, feux de départ, inputs, HUD cockpit
scene_select.py  ← Sélection voitures split-screen avec ActionDetector et animation "bob"
scene_result.py  ← Écran résultats : vainqueur, tableau de bord, stats de shifts
ui.py            ← Utilitaires : sprites voitures, fond scrollant (TrackBackground), StartLights, draw_cockpit, draw_smoke
```

**Physique (`car.py`) :**
- RPM recalculé à chaque frame depuis la vitesse et le rapport engagé
- Force = `power_at_rpm()` (interpolation linéaire) × multiplicateur shift
- Résistances : aérodynamique (`v²`) + roulement (constante)
- Surchauffe : compteur en zone rouge, multiplicateur de puissance réduit au-delà du seuil

**Contrôles (`config.py → CTRL`) :**
| Joueur | Clavier | Joystick |
|--------|---------|----------|
| J1 | ↑ gaz, ↓ frein, ← shift–, → shift+ | Croix directionnelle |
| J2 | W/S gaz/frein, A shift–, D shift+ | Boutons ABXY |

**POC de référence :** `poc/shifter/` (Phaser.js) — même physique, sert de spec et de prototype.
