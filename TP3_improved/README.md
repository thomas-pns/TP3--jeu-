# TP3 Amélioré - Le Pendu

Cette version améliorée du jeu du pendu inclut :

## Fonctionnalités ajoutées
- **Mode multijoueur local** : Un joueur choisit un mot, l'autre essaie de le deviner.
- **Système de points** : Les séries de victoires (streak) sont enregistrées pour chaque joueur.
- **Interface améliorée** : Fenêtre redimensionnable, indications claires, séparateur visuel.
- **Validation des entrées** : Vérification que l'entrée est une seule lettre alphabétique.
- **Effacement d'écran simulé** entre les tours en multijoueur pour cacher le mot choisi.

## Comment jouer
1. Lancez le jeu avec `python jeu_improved.py`.
2. Entrez votre identifiant.
3. Choisissez le mode :
   - **Solo** : Vous jouez contre l'ordinateur qui choisit un mot parmi la liste.
   - **Multijoueur** : 
     - Joueur 1 entre un mot à faire deviner (lettres uniquement, longueur ≥ 3).
     - L'écran est effacé (simulé) et le Joueur 2 tente de deviner le lettre par lettre.
     - Après chaque partie, vous pouvez choisir de rejouer ou quitter.

## Fichiers
- `jeu_improved.py` : Point d'entrée du jeu.
- `interface_improved.py` : Interface graphique Tkinter avec les deux modes.
- `fonctions_improved.py` : Gestion des données (mots, joueurs, statistiques).
- `mots.json` : Liste de mots par longueur.
- `bdd.json` : Base de données des joueurs et leurs statistiques.
- `images PENDU-20260929/` : Images du bonhomme pour chaque nombre d'erreurs.

## Remarques
- Le jeu respecte les règles classiques du pendu avec 8 tentatives maximum.
- En multijoueur, le mot choisi doit contenir uniquement des lettres et avoir au moins 3 caractères.
- Les historiques de parties sont sauvegardés dans `bdd.json`.
