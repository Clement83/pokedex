# Shifter 🏎️

Un jeu de drag racing multi-joueurs (2-8 joueurs) inspiré de Need for Speed Underground, développé en HTML5/JavaScript avec Phaser.js.

## 🎮 Comment jouer

### Lancer le jeu

Le jeu nécessite un serveur web local pour fonctionner correctement (à cause des modules ES6).

**Option 1 : Avec Python**
```bash
# Python 3
python -m http.server 8000

# Ouvrir dans le navigateur : http://localhost:8000
```

**Option 2 : Avec Node.js (http-server)**
```bash
# Installer http-server si nécessaire
npm install -g http-server

# Lancer le serveur
http-server -p 8000

# Ouvrir dans le navigateur : http://localhost:8000
```

**Option 3 : Avec l'extension VS Code "Live Server"**
```
1. Installer l'extension "Live Server" dans VS Code
2. Clic droit sur index.html
3. Sélectionner "Open with Live Server"
```

### Règles du jeu

1. **Sélection** : Choisissez le nombre de joueurs (2 à 8)
2. **Choix des voitures** : Chaque joueur sélectionne sa voiture
3. **Course** : Au feu vert, changez les vitesses au bon moment !
4. **Objectif** : Parcourir 400m le plus rapidement possible

### Contrôles

#### Clavier (8 joueurs possibles)
- **Joueur 1** : `A` (monter) / `Q` (descendre)
- **Joueur 2** : `$` (monter) / `*` (descendre)
- **Joueur 3** : `E` (monter) / `D` (descendre)
- **Joueur 4** : `T` (monter) / `G` (descendre)
- **Joueur 5** : `U` (monter) / `J` (descendre)
- **Joueur 6** : `O` (monter) / `L` (descendre)
- **Joueur 7** : `X` (monter) / `C` (descendre)
- **Joueur 8** : `,` (monter) / `;` (descendre)

### Système de changement de vitesse

Le timing est crucial ! Surveillez le compte-tours :

- 🟢 **Zone Verte (PERFECT)** : ±200 RPM du point optimal → +5% de puissance
- 🟡 **Zone Jaune (GOOD)** : ±500 RPM du point optimal → Aucun bonus/pénalité
- 🔴 **Zone Rouge (BAD)** : En dehors de la zone → -10% de puissance

**Conseils :**
- Chaque voiture a un point de changement de vitesse optimal différent
- Les muscle cars changent à ~5500 RPM (4 vitesses)
- Les JDM montent plus haut : ~7000-8500 RPM (5-6 vitesses)
- Ne tapez pas le limiteur (zone rouge) !

## 🚗 Voitures disponibles

### Catégorie Tuner
- **Shadow Racer** (Noire) - Équilibrée, idéale pour débuter
- **Green Machine** (Verte) - Turbo lag mais très puissante
- **White Ghost** (Blanche) - Équilibrée et précise

### Catégorie JDM
- **Blue Lightning** (Bleue) - Accélération rapide, monte très haut
- **Red Devil** (Rouge) - Légère et nerveuse, 9000 RPM!

### Catégorie Muscle
- **Yellow Thunder** (Jaune) - Couple énorme, peu de vitesses

## 🎯 Fonctionnalités

### Phase MVP (Actuel)
- ✅ Menu de sélection du nombre de joueurs (2-8)
- ✅ Sélection de voitures avec stats
- ✅ Split-screen adaptatif (2-8 joueurs)
- ✅ Physique de course simplifiée mais réaliste
- ✅ Système de changement de vitesse avec zones Perfect/Good/Bad
- ✅ Compte-tours visuel avec zones colorées
- ✅ Séquence de départ avec feux (rouge/orange/vert)
- ✅ Interface complète (vitesse, distance, temps, position)
- ✅ Écran de résultats avec classement et statistiques
- ✅ Support clavier pour 8 joueurs simultanés

### À venir
- [ ] Support des manettes (Gamepad API)
- [ ] Sons de moteur et effets sonores
- [ ] Effets visuels (fumée, flammes)
- [ ] Plus de voitures (12+)
- [ ] Mode tournoi
- [ ] Replay système

## 📁 Structure du projet

```
shifter/
├── index.html              # Point d'entrée
├── style.css              # Styles globaux
├── asset/
│   ├── data/
│   │   └── cars.json      # Données des voitures
│   └── keny-racing/       # Assets Kenney (sprites)
├── src/
│   ├── main.js           # Configuration Phaser
│   ├── config.js         # Constantes du jeu
│   ├── entities/
│   │   ├── Car.js        # Classe véhicule
│   │   └── Player.js     # Classe joueur
│   ├── systems/
│   │   └── InputManager.js  # Gestion des inputs
│   └── scenes/
│       ├── MenuScene.js       # Menu principal
│       ├── CarSelectScene.js  # Sélection des voitures
│       ├── RaceScene.js       # Course
│       └── ResultScene.js     # Résultats
├── specification.md       # Spécifications complètes
├── ASSETS.md             # Guide des ressources
├── CREDITS.md            # Crédits des assets
└── README.md             # Ce fichier
```

## 🛠️ Technologies

- **Phaser 3.70.0** - Framework de jeu HTML5
- **JavaScript ES6+** - Modules, classes
- **HTML5 Canvas** - Rendu graphique
- **Kenney Assets** - Sprites gratuits (CC0)

## 🎨 Crédits

Voir [CREDITS.md](CREDITS.md) pour les attributions complètes.

## 📝 Licence

Ce projet est créé à des fins éducatives et de démonstration.
Les assets utilisés sont sous licence CC0 (domaine public).

---

**Développé avec ❤️ pour les fans de Fast & Furious et NFS Underground**

Bon drag ! 🏁
