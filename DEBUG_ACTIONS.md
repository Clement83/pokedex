# Actions de Debug

Ce fichier documente les actions de debug disponibles dans le jeu Pokédex et comment les utiliser.

## ⚠️ Sécurité

Pour éviter les déclenchements accidentels, toutes les actions de debug nécessitent de **maintenir une combinaison de touches pendant 5 secondes**. Une barre de progression s'affichera à l'écran pour indiquer le temps restant.

## Actions Disponibles

### 1. Git Pull & Restart

**Fonction :** Met à jour le jeu via `git pull` et redémarre l'application.

**Combinaisons :**

- **Manette (Odroid Go Advance) :** `Select (bouton 12) + F10 (bouton 13)`
- **Clavier :** `F1 + F2`

**Utilisation :** Maintenir les deux touches simultanément pendant 5 secondes.

---

### 2. Reset Game

**Fonction :** Réinitialise complètement le jeu :

- Tous les Pokémon sont marqués comme non-capturés et non-vus
- Les préférences utilisateur sont supprimées
- Une sauvegarde horodatée de la base de données est automatiquement créée

**Combinaisons :**

- **Manette (Odroid Go Advance) :** `Select (bouton 12) + PageDown (bouton 14)`
- **Clavier :** `F1 + F3`

**Utilisation :** Maintenir les deux touches simultanément pendant 5 secondes.

**⚠️ Attention :** Cette action est irréversible (même si une sauvegarde est créée).

---

### 3. Next Milestone

**Fonction :** Marque automatiquement des Pokémon comme "vus" jusqu'à un Pokémon avant le prochain seuil de déverrouillage de génération.

**Caractéristiques :**

- Ne sélectionne que des Pokémon de la génération/région actuellement débloquée
- S'arrête à `unlock_count - 1` pour permettre de débloquer manuellement la prochaine génération

**Combinaisons :**

- **Manette (Odroid Go Advance) :** `Select (bouton 12) + PageUp (bouton 15)`
- **Clavier :** `F1 + F4`

**Utilisation :** Maintenir les deux touches simultanément pendant 5 secondes.

---

## Barre de Progression

Lorsque vous maintenez une combinaison de touches :

1. Une barre jaune/orange apparaît en bas de l'écran
2. Un texte indique l'action qui sera déclenchée
3. La barre se remplit progressivement pendant 5 secondes
4. L'action s'exécute automatiquement une fois la barre pleine

**Pour annuler :** Relâchez simplement les touches avant que la barre soit complète.

---

## Mapping des Boutons (Odroid Go Advance)

```
Bouton 12 = Select
Bouton 13 = F10 mapping
Bouton 14 = PageDown (Volume Down)
Bouton 15 = PageUp (Volume Up)
```

---

## Notes Techniques

- Les actions de debug sont définies dans `debug_actions.py`
- La logique de détection des combinaisons se trouve dans `controls.py` (manette) et `input_handler.py` (clavier)
- Le temps de maintien requis est défini par `DEBUG_HOLD_DURATION = 5000` (millisecondes)
- Les vérifications sont effectuées dans la boucle principale du jeu (`main.py`)

---

## Dépannage

**La barre de progression n'apparaît pas :**

- Vérifiez que vous êtes dans l'état "list" ou "detail" du jeu
- Assurez-vous de maintenir les deux touches en même temps

**L'action ne se déclenche pas :**

- Maintenez les touches pendant toute la durée (5 secondes complètes)
- Vérifiez que vous utilisez la bonne combinaison de touches

**L'action se déclenche accidentellement :**

- C'est très peu probable avec le système de maintien de 5 secondes
- Si nécessaire, augmentez `DEBUG_HOLD_DURATION` dans `controls.py` et `input_handler.py`
