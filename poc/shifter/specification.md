# Spécifications - Shifter

## 1. Vue d'ensemble

**Shifter** est un jeu de course en drag racing pour 2 à 8 joueurs en local, inspiré du mode drag race de Need for Speed Underground. Le défi principal consiste à maîtriser le timing des changements de vitesse pour optimiser l'accélération et franchir la ligne d'arrivée en premier.

## 2. Concept de jeu

### 2.1 Gameplay principal
- Course en ligne droite sur une distance fixe (ex: 400m ou 1/4 mile)
- Chaque joueur contrôle sa voiture uniquement via le changement de vitesses
- Le timing du changement de vitesse est crucial : trop tôt = perte de puissance, trop tard = limiteur/surégime
- La zone optimale de changement de vitesse est indiquée visuellement sur le compte-tours

### 2.2 Objectif
Être le premier à franchir la ligne d'arrivée en optimisant ses changements de vitesse selon la courbe de puissance de son moteur.

## 3. Fonctionnalités

### 3.1 Écran de sélection du nombre de joueurs
- Écran permettant de choisir le nombre de joueurs (2 à 8)
- Affichage des contrôles disponibles (clavier + manettes détectées)
- Validation et passage à la sélection des véhicules

### 3.2 Écran de sélection des véhicules (Split-screen)
- Écran divisé en autant de zones que de joueurs
- Layout adaptatif :
  - 2 joueurs : split horizontal (50% / 50%)
  - 3-4 joueurs : grid 2x2
  - 5-6 joueurs : grid 2x3
  - 7-8 joueurs : grid 2x4
- Chaque joueur navigue dans le garage pour sélectionner sa voiture
- Affichage des caractéristiques de chaque véhicule :
  - Nom et modèle
  - Puissance (chevaux)
  - Couple moteur
  - Poids
  - Graphique de la courbe de puissance (simplifié si > 4 joueurs)
  - Nombre de vitesses
  - Zone de régime optimale (RPM)
- Indicateur visuel de "Prêt" pour chaque joueur

### 3.3 Écran de course (Split-screen adaptatif)
- Vue isométrique 2D de la piste
- Layout adaptatif selon le nombre de joueurs :
  - **2 joueurs** : split horizontal (50% / 50%)
  - **3 joueurs** : 1 en haut (100%), 2 en bas (50% / 50%)
  - **4 joueurs** : grid 2x2 (25% chacun)
  - **5-6 joueurs** : grid 2x3 (zones plus compactes)
  - **7-8 joueurs** : grid 2x4 (interface minimale)
- Chaque zone d'écran affiche :
  - La voiture du joueur sur sa piste
  - Le compte-tours avec zone verte (optimal), jaune (acceptable), rouge (mauvais)
  - La vitesse actuelle (km/h)
  - Le rapport de vitesse engagé (1, 2, 3, 4, 5, 6)
  - La distance parcourue / distance restante
  - Un chronomètre
  - Classement en temps réel (position)
- Séquence de départ :
  - Feu rouge (3 secondes)
  - Feu orange (1 seconde)
  - Feu vert (GO!)
  - Départ anticipé = pénalité
- Mini-classement latéral optionnel montrant la position de tous les joueurs

### 3.4 Écran de résultats
- Podium avec classement complet de tous les joueurs
- Affichage du gagnant avec animation
- Pour chaque joueur :
  - Position finale
  - Temps réalisé
  - Vitesse de pointe atteinte
  - Nombre de changements de vitesse ratés/parfaits
  - Score de performance
- Statistiques globales de la course
- Options : rejouer, retourner à la sélection, changer le nombre de joueurs

## 4. Spécifications techniques

### 4.1 Stack technique proposée

**Option 1 : Web (HTML5/JavaScript)**
- **Frontend** : HTML5 Canvas + JavaScript (Vanilla ou TypeScript)
- **Framework graphique** : Phaser.js ou PixiJS
- **Avantages** : 
  - Multi-plateforme (navigateur)
  - Facile à déployer
  - Bon support pour les graphismes 2D
  - Système d'input simple

**Option 2 : Python**
- **Framework** : Pygame
- **Avantages** :
  - Prototypage rapide
  - Bonne documentation
  - Gestion native des inputs multiples

**Recommandation : HTML5/JavaScript avec Phaser.js** pour la flexibilité et la facilité de distribution.

### 4.2 Architecture logicielle

```
shifter/
├── assets/
│   ├── sprites/
│   │   ├── cars/          # Sprites des voitures
│   │   ├── track/         # Éléments de la piste
│   │   └── ui/            # Éléments d'interface
│   ├── sounds/
│   │   ├── engines/       # Sons de moteur par voiture
│   │   └── sfx/           # Effets sonores
│   └── data/
│       └── cars.json      # Données des voitures
├── src/
│   ├── main.js           # Point d'entrée
│   ├── scenes/
│   │   ├── MenuScene.js      # Écran titre
│   │   ├── CarSelectScene.js # Sélection des voitures
│   │   ├── RaceScene.js      # Course
│   │   └── ResultScene.js    # Résultats
│   ├── entities/
│   │   ├── Car.js            # Classe véhicule
│   │   └── Player.js         # Contrôleur joueur
│   ├── systems/
│   │   ├── PhysicsEngine.js  # Physique simplifiée
│   │   ├── InputManager.js   # Gestion des inputs (clavier + manettes)
│   │   ├── GamepadManager.js # Détection et gestion des manettes
│   │   └── AudioManager.js   # Gestion audio
│   └── ui/
│       ├── Tachometer.js     # Compte-tours
│       ├── Speedometer.js    # Compteur de vitesse
│       └── StartLights.js    # Feux de départ
├── index.html
├── style.css
└── README.md
```

### 4.3 Contrôles

#### Option A : Clavier seul (jusqu'à 8 joueurs)

**Joueur 1 :**
- Monter : `A` | Descendre : `Q`

**Joueur 2 :**
- Monter : `$` | Descendre : `*`

**Joueur 3 :**
- Monter : `E` | Descendre : `D`

**Joueur 4 :**
- Monter : `T` | Descendre : `G`

**Joueur 5 :**
- Monter : `U` | Descendre : `J`

**Joueur 6 :**
- Monter : `O` | Descendre : `L`

**Joueur 7 :**
- Monter : `X` | Descendre : `C`

**Joueur 8 :**
- Monter : `,` | Descendre : `;`

#### Option B : Manettes (recommandé pour 3+ joueurs)

**Tous les joueurs avec manette :**
- Monter la vitesse : `Bouton A` ou `Gâchette droite (RT)`
- Descendre la vitesse : `Bouton B` ou `Gâchette gauche (LT)`

**Mode hybride :** Combinaison possible de joueurs au clavier et à la manette

## 5. Système de physique et mécanique de jeu

### 5.1 Modèle de physique simplifié

```javascript
// Pseudo-code du système de physique
class Car {
  constructor(carData) {
    this.rpm = 1000;              // Tours/minute
    this.speed = 0;               // km/h
    this.gear = 1;                // Vitesse engagée (1-6)
    this.position = 0;            // Position sur la piste (mètres)
    this.powerCurve = carData.powerCurve; // Points de puissance par RPM
    this.gearRatios = carData.gearRatios;
    this.weight = carData.weight;
    this.maxRPM = carData.maxRPM;
  }
  
  update(deltaTime) {
    // Calculer la puissance actuelle selon RPM et courbe
    let power = this.getPowerAtRPM(this.rpm);
    
    // Calculer l'accélération
    let acceleration = (power / this.weight) * this.gearRatios[this.gear];
    
    // Mettre à jour la vitesse
    this.speed += acceleration * deltaTime;
    
    // Mettre à jour les RPM en fonction de la vitesse et du rapport
    this.rpm = this.calculateRPM(this.speed, this.gear);
    
    // Limiteur de régime
    if (this.rpm > this.maxRPM) {
      this.rpm = this.maxRPM;
      // Réduction de puissance
      power *= 0.5;
    }
    
    // Mettre à jour la position
    this.position += (this.speed / 3.6) * deltaTime; // conversion km/h -> m/s
  }
  
  shiftUp() {
    if (this.gear < 6) {
      this.gear++;
      // Chute de RPM lors du changement de vitesse
      this.rpm = this.rpm * 0.7; // Approximation
    }
  }
  
  shiftDown() {
    if (this.gear > 1) {
      this.gear--;
      // Montée de RPM lors de la rétrogradation
      this.rpm = Math.min(this.rpm * 1.4, this.maxRPM);
    }
  }
}
```

### 5.2 Détails de la courbe de puissance

Chaque voiture possède une courbe de puissance unique définie par des points :

```json
{
  "name": "Honda Civic Type R",
  "powerCurve": [
    { "rpm": 1000, "power": 50 },
    { "rpm": 2000, "power": 120 },
    { "rpm": 3000, "power": 180 },
    { "rpm": 4000, "power": 220 },
    { "rpm": 5000, "power": 250 },
    { "rpm": 6000, "power": 280 },
    { "rpm": 7000, "power": 300 },
    { "rpm": 8000, "power": 290 },
    { "rpm": 8500, "power": 250 }
  ],
  "optimalShiftRPM": 7200,
  "maxRPM": 8500,
  "gearRatios": [3.5, 2.2, 1.6, 1.2, 0.95, 0.75],
  "weight": 1320
}
```

### 5.3 Zones de changement de vitesse

- **Zone verte (Perfect)** : ±200 RPM autour du point optimal
  - Bonus : +5% de puissance pendant 0.5s
  
- **Zone jaune (Good)** : ±500 RPM autour du point optimal
  - Pas de bonus ni pénalité
  
- **Zone rouge (Bad)** : En dehors de la zone jaune
  - Pénalité : -10% de puissance pendant 0.3s

## 6. Catalogue de véhicules (Style Fast & Furious 1-2)

### 6.1 Catégories proposées

**Catégorie A - JDM Legends** (voitures japonaises iconiques)
1. **Toyota Supra MK IV** - La légende orange de Brian
   - Puissance élevée, couple massif
   - 6 vitesses, optimal à 6800 RPM
2. **Nissan Skyline GT-R R34** - Icône JDM ultime
   - Équilibrée, accélération rapide
   - 6 vitesses, optimal à 7500 RPM
3. **Mazda RX-7 FD** - Moteur rotatif unique
   - Léger, montée en régime rapide
   - 5 vitesses, optimal à 8000 RPM
4. **Honda S2000** - VTEC qui kick in
   - Légère, rev très haut
   - 6 vitesses, optimal à 8500 RPM

**Catégorie B - Tuner Imports** (voitures modifiées accessibles)
1. **Mitsubishi Eclipse GSX** - La voiture verte de Brian
   - Bonne accélération, facile
   - 5 vitesses, optimal à 6500 RPM
2. **Honda Civic EG/EK** - Compact tunée
   - Très légère, technique
   - 5 vitesses, optimal à 7800 RPM
3. **Nissan 240SX / Silvia S14** - Drift queen
   - Équilibrée, progressive
   - 5 vitesses, optimal à 7000 RPM
4. **Acura NSX** - Supercar japonaise
   - Puissante et équilibrée
   - 6 vitesses, optimal à 7500 RPM

**Catégorie C - American Muscle** (puissance brute)
1. **Dodge Charger R/T 70** - Le muscle de Toretto
   - Couple énorme, lourde
   - 4 vitesses, optimal à 5500 RPM
2. **Chevrolet Chevelle SS** - Muscle classique
   - Très puissante, brutale
   - 4 vitesses, optimal à 5800 RPM
3. **Ford Mustang** - Icône américaine
   - Puissance élevée
   - 5 vitesses, optimal à 6200 RPM
4. **Plymouth Road Runner** - Old school power
   - Couple massif, poids lourd
   - 4 vitesses, optimal à 5400 RPM

### 6.2 Différenciation des véhicules

Chaque voiture se différencie par :
- **Courbe de puissance unique** : 
  - JDM : montée progressive, puissance haute dans les tours
  - Muscle : couple énorme bas, chute en haut régime
  - Tuner : courbes variables selon le setup
- **Zone RPM optimale différente** :
  - Muscle (4 vitesses) : shifts à 5000-6000 RPM
  - JDM/Tuner (5-6 vitesses) : shifts à 6500-8500 RPM
- **Nombre de vitesses** : 4 (muscle) à 6 (JDM moderne)
- **Temps de passage de vitesse** : 
  - Rapide (0.11s) : Civic, S2000
  - Moyen (0.14-0.16s) : Supra, Skyline
  - Lent (0.20-0.22s) : Muscle cars
- **Sonorité du moteur** :
  - V8 muscle : grave, grondant
  - Rotary (RX-7) : aigu, unique
  - 4-cylindres turbo : sifflement turbo
  - 6-cylindres : son équilibré

## 7. Interface utilisateur détaillée

### 7.1 Compte-tours (Tachometer)

```
     8000 RPM
    ┌─────────┐
  7 │    ╱    │ 9
    │   █     │
  5 │  ▓▓▓    │ 11
    │ ░░░▓▓   │
  3 │░░░░░▓▓  │ 13
    └─────────┘
     GEAR: 4
```

- Affichage circulaire ou semi-circulaire
- Couleurs :
  - Vert : zone optimale (6000-7500)
  - Jaune : zone acceptable (5500-6000, 7500-8000)
  - Rouge : zone dangereuse (8000+)
- Indicateur animé du RPM actuel
- Affichage du rapport engagé au centre

### 7.2 Layout de la course

**Layout 2 joueurs (split horizontal) :**
```
┌─────────────────────────────────────────────────┐
│              PLAYER 1 ZONE                      │
│  ┌──────────┐  [🏎️]──────────────> 245m/400m  │
│  │   TACHO  │  Speed: 156 km/h    Time: 8.2s   │
│  │  ░▓▓▓█   │  Gear: 4/6          Pos: 1st     │
│  └──────────┘                                    │
├─────────────────────────────────────────────────┤
│              PLAYER 2 ZONE                      │
│  ┌──────────┐  [🏎️]──────────────> 238m/400m  │
│  │   TACHO  │  Speed: 149 km/h    Time: 8.2s   │
│  │  ░░▓▓█   │  Gear: 3/6          Pos: 2nd     │
│  └──────────┘                                    │
└─────────────────────────────────────────────────┘
```

**Layout 4 joueurs (grid 2x2) :**
```
┌────────────────────┬────────────────────┐
│   PLAYER 1 (1st)   │   PLAYER 2 (3rd)   │
│ ┌────┐ [🏎️]→ 245m │ ┌────┐ [🏎️]→ 220m │
│ │TACH│ 156km/h G:4│ │TACH│ 142km/h G:3│
│ └────┘ 8.2s       │ └────┘ 8.5s       │
├────────────────────┼────────────────────┤
│   PLAYER 3 (2nd)   │   PLAYER 4 (4th)   │
│ ┌────┐ [🏎️]→ 238m │ ┌────┐ [🏎️]→ 215m │
│ │TACH│ 149km/h G:3│ │TACH│ 138km/h G:3│
│ └────┘ 8.3s       │ └────┘ 8.6s       │
└────────────────────┴────────────────────┘
```

**Layout 8 joueurs (grid 2x4) :**
- Interface ultra compacte
- Compte-tours simplifié (barre ou arc)
- Informations essentielles uniquement (vitesse, rapport, position)
- Vue de la piste en miniature

## 8. Phases de développement

### Phase 1 : Prototype de base (MVP)
- [ ] Menu simple avec sélection du nombre de joueurs
- [ ] Sélection de 2-4 voitures basiques
- [ ] Course fonctionnelle avec physique simplifiée
- [ ] Système de changement de vitesse
- [ ] Support clavier pour 2-4 joueurs
- [ ] Split-screen adaptatif (2-4 joueurs)
- [ ] Détection de ligne d'arrivée
- [ ] Écran de résultat avec classement

### Phase 2 : Gameplay complet
- [ ] Support des manettes (Gamepad API)
- [ ] Mode hybride clavier + manettes
- [ ] Support 5-8 joueurs
- [ ] Compte-tours visuel avec zones colorées
- [ ] 6-8 voitures avec courbes différentes
- [ ] Système de Perfect/Good/Bad shift
- [ ] Séquence de départ avec feux
- [ ] Sons de moteur basiques
- [ ] Détection automatique des contrôleurs

### Phase 3 : Polish et contenu
- [ ] 12+ voitures
- [ ] Effets visuels (fumée des pneus, flammes d'échappement)
- [ ] Sons de moteur spécifiques par voiture
- [ ] Animations améliorées
- [ ] Statistiques détaillées
- [ ] Système de replay

### Phase 4 : Fonctionnalités avancées
- [ ] Mode tournoi
- [ ] Déblocage de voitures
- [ ] Tuning des voitures
- [ ] Différentes pistes (nuit, jour, ville, désert)
- [ ] Mode entraînement avec ghost

## 9. Considérations techniques

### 9.1 Performance
- Ciblage : 60 FPS constant
- Optimisation des rendus sprites
- Système de pooling pour les particules

### 9.2 Responsive design
- Résolution de base : 1920x1080
- Support du mode fenêtré et plein écran
- Mise à l'échelle proportionnelle des éléments UI
- Interface adaptative selon le nombre de joueurs :
  - 2 joueurs : UI complète et détaillée
  - 3-4 joueurs : UI standard
  - 5-8 joueurs : UI compacte et simplifiée

### 9.3 Sauvegarde
- LocalStorage pour sauvegarder :
  - Paramètres audio
  - Meilleurs temps (par nombre de joueurs)
  - Configuration des contrôles préférée
  - Voitures débloquées (si système de progression)

### 9.4 Gestion des manettes
- Utilisation de la Gamepad API (standard web)
- Détection à chaud des manettes connectées/déconnectées
- Support des contrôleurs courants :
  - Xbox (One, Series, 360)
  - PlayStation (DualShock 4, DualSense)
  - Nintendo Switch Pro Controller
  - Contrôleurs génériques
- Mapping personnalisable des boutons
- Calibration automatique des gâchettes analogiques

## 10. Exemple de données de voiture

```json
{
  "cars": [
    {
      "id": "supra_mk4",
      "name": "Toyota Supra MK IV",
      "category": "jdm",
      "description": "La légende orange de Brian - 2JZ power",
      "stats": {
        "power": 500,
        "weight": 1570,
        "gears": 6,
        "maxRPM": 7500,
        "optimalShiftRPM": 6800,
        "shiftTime": 0.16
      },
      "powerCurve": [
        [1000, 100], [2000, 200], [3000, 320],
        [4000, 420], [5000, 480], [6000, 500],
        [6800, 500], [7500, 470]
      ],
      "gearRatios": [3.83, 2.36, 1.69, 1.31, 1.00, 0.79],
      "sound": "assets/sounds/engines/supra_2jz.mp3",
      "sprite": "assets/sprites/cars/supra_orange.png"
    },
    {
      "id": "skyline_r34",
      "name": "Nissan Skyline GT-R R34",
      "category": "jdm",
      "description": "Godzilla - RB26DETT twin-turbo",
      "stats": {
        "power": 480,
        "weight": 1560,
        "gears": 6,
        "maxRPM": 8000,
        "optimalShiftRPM": 7500,
        "shiftTime": 0.14
      },
      "powerCurve": [
        [1000, 90], [2000, 180], [3000, 290],
        [4000, 380], [5000, 440], [6000, 470],
        [7000, 480], [7500, 480], [8000, 460]
      ],
      "gearRatios": [3.83, 2.36, 1.69, 1.31, 1.00, 0.79],
      "sound": "assets/sounds/engines/rb26dett.mp3",
      "sprite": "assets/sprites/cars/r34_blue.png"
    },
    {
      "id": "rx7_fd",
      "name": "Mazda RX-7 FD",
      "category": "jdm",
      "description": "Rotary power - 13B-REW",
      "stats": {
        "power": 380,
        "weight": 1280,
        "gears": 5,
        "maxRPM": 8500,
        "optimalShiftRPM": 8000,
        "shiftTime": 0.12
      },
      "powerCurve": [
        [1000, 60], [2000, 120], [3000, 180],
        [4000, 240], [5000, 300], [6000, 340],
        [7000, 370], [8000, 380], [8500, 360]
      ],
      "gearRatios": [3.48, 2.01, 1.39, 1.00, 0.72],
      "sound": "assets/sounds/engines/rotary_13b.mp3",
      "sprite": "assets/sprites/cars/rx7_red.png"
    },
    {
      "id": "charger_70",
      "name": "Dodge Charger R/T 1970",
      "category": "muscle",
      "description": "Dom's ride - V8 440 Magnum",
      "stats": {
        "power": 550,
        "weight": 1850,
        "gears": 4,
        "maxRPM": 6000,
        "optimalShiftRPM": 5500,
        "shiftTime": 0.22
      },
      "powerCurve": [
        [1000, 200], [2000, 350], [3000, 480],
        [4000, 540], [5000, 550], [5500, 550],
        [6000, 520]
      ],
      "gearRatios": [2.76, 1.92, 1.40, 1.00],
      "sound": "assets/sounds/engines/v8_muscle.mp3",
      "sprite": "assets/sprites/cars/charger_black.png"
    },
    {
      "id": "eclipse_gsx",
      "name": "Mitsubishi Eclipse GSX",
      "category": "tuner",
      "description": "Green machine - 4G63T turbo",
      "stats": {
        "power": 380,
        "weight": 1420,
        "gears": 5,
        "maxRPM": 7500,
        "optimalShiftRPM": 6500,
        "shiftTime": 0.15
      },
      "powerCurve": [
        [1000, 80], [2000, 160], [3000, 250],
        [4000, 330], [5000, 370], [6000, 380],
        [6500, 380], [7500, 350]
      ],
      "gearRatios": [3.42, 2.05, 1.48, 1.09, 0.84],
      "sound": "assets/sounds/engines/4g63t.mp3",
      "sprite": "assets/sprites/cars/eclipse_green.png"
    },
    {
      "id": "civic_ek",
      "name": "Honda Civic EK (tuned)",
      "category": "tuner",
      "description": "VTEC kicked in yo! - B18C swap",
      "stats": {
        "power": 280,
        "weight": 1050,
        "gears": 5,
        "maxRPM": 8800,
        "optimalShiftRPM": 7800,
        "shiftTime": 0.11
      },
      "powerCurve": [
        [1000, 50], [2000, 100], [3000, 140],
        [4000, 180], [5000, 220], [6000, 260],
        [7000, 280], [7800, 280], [8800, 260]
      ],
      "gearRatios": [3.23, 1.90, 1.36, 1.03, 0.81],
      "sound": "assets/sounds/engines/vtec_b18.mp3",
      "sprite": "assets/sprites/cars/civic_yellow.png"
    }
  ]
}
```

## 11. Roadmap et estimations

| Phase | Fonctionnalités | Temps estimé |
|-------|----------------|--------------|
| 1 | MVP fonctionnel | 2-3 jours |
| 2 | Gameplay complet | 3-4 jours |
| 3 | Polish et contenu | 4-5 jours |
| 4 | Fonctionnalités avancées | 5-7 jours |

**Total estimé : 14-19 jours de développement**

## 12. Prochaines étapes

1. ✅ Validation des spécifications
2. Configuration du projet (choix de la stack)
3. Création des assets de base (sprites, sons)
4. Développement du MVP
5. Tests et itérations
6. Ajout de contenu
7. Polish final

---

**Document créé le :** 16 mars 2026  
**Version :** 1.0  
**Auteur :** Shifter Team
