# Le Pendu Multijoueur Web

Une version en ligne du jeu du pendu avec multijoueur en temps réel, responsive et animée.

## Fonctionnalités
- ✅ Multijoueur en temps réel via WebSocket (Socket.IO)
- ✅ Interface responsive (mobile, tablette, desktop)
- ✅ Animations du bonhomme pendue
- ✅ Salle de jeu avec identifiants
- ✅ Chat intégré (via événements Socket.IO)
- ✅ Gestion des scores
- ✅ Design moderne et dégradé animé

## Prérequis
- Python 3.7+
- pip
- (Optionnel) virtualenv

## Installation
1. Clonez ce dépôt ou copiez le dossier `TP3_web` sur votre machine.
2. Accédez au dossier :
   ```bash
   cd TP3_web
   ```
3. Installez les dépendances Python :
   ```bash
   pip install flask flask-socketio
   ```
4. (Optionnel) Créez un environnement virtuel pour éviter les conflits de dépendances.

## Lancer l'application
```bash
python app.py
```
L'application sera accessible à l'adresse : http://localhost:5000

Pour y accéder depuis d'autres appareils sur le même réseau WiFi :
1. Trouvez l'adresse IP de votre machine (ex: `ipconfig` sur Windows, `ifconfig` sur Mac/Linux).
2. Depuis un autre appareil, allez à `http://<VOTRE_IP>:5000` dans le navigateur.

## Structure du projet
```
TP3_web/
├── app.py                 # Serveur Flask-SocketIO
├── templates/
│   └── index.html         # Page principale
├── static/
│   ├── css/
│   │   └── style.css      # Styles et animations
│   ├── js/
│   │   └── game.js        # Logique client Socket.IO
│   └── images/            # Images du bonhomme (bonhomme1.gif à bonhomme8.gif)
└── mots.json              # Liste de mots par longueur (réutilisé du TP3 original)
```

## Comment jouer
1. Ouvrez l'application dans votre navigateur.
2. Entrez votre nom et éventuellement un ID de salle (laissez vide pour créer une nouvelle salle).
3. Partagez l'ID de la salle avec votre adversaire pour qu'il puisse vous rejoindre.
4. Une fois deux joueurs connectés, l'un sera désigné aléatoirement pour choisir un mot.
5. Le joueur qui choisit le mot doit entrer un mot valide (lettres uniquement, longueur ≥ 3).
6. L'autre joueur tente de deviner le mot lettre par lettre.
7. Le jeu continue jusqu'à ce que le mot soit trouvé ou que le bonhomme soit complet.
8. À la fin de la partie, vous pouvez choisir de rejouer ou de quitter la salle.

## Personnalisation
- Pour modifier la liste des mots, éditez `mots.json` (même format que l'original).
- Pour changer les images du bonhomme, remplacez les fichiers dans `static/images/` en conservant le nommage `bonhomme1.gif` à `bonhomme8.gif`.
- Pour ajuster le style, éditez `static/css/style.css`.
- Pour modifier la logique du jeu côté client, éditez `static/js/game.js`.
- Pour modifier la logique du serveur, éditez `app.py`.

## Déploiement en production
Pour un déploiement sérieux, considérez :
- Utiliser un serveur WSGI comme Gunicorn avec worker gevent: `gunicorn -k gevent -w 1 app:app`
- Mettre derrière un reverse proxy (Nginx, Apache) pour le SSL et la gestion des ports.
- Configurer les variables d'environnement pour la clé secrète.
- Utiliser une base de données pour persister les scores et les historiques.

## Remarques légales
Ce projet est destiné à un usage éducatif et personnel. Les images utilisées proviennent du TP3 original et sont supposées libres de droits dans ce contexte.
