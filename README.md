# Motus Maximus — le pendu qui a du répondant

Une application de pendu multijoueur et solo construite avec Flask, Flask-SocketIO et JavaScript vanilla. Les personnages sont dessinés en SVG/CSS, les effets sonores sont générés avec Web Audio et aucun framework ni asset graphique externe n’est requis.

## Fonctionnalités

- **Solo contre cinq bots** : du débutant au Boss, avec choix de mots adaptés, punchlines, temps de réflexion et stratégie de devinette par filtrage de motifs/fréquence des lettres.
- **Mode Duel** : le joueur et le bot devinent chacun un mot ; la première personne à trouver gagne.
- **Multijoueur humain** : salles privées à deux joueurs, mot secret, manches alternées, revanche et chat en temps réel.
- **Six personnages cartoon** : SVG expressifs, répliques en français, réactions à chaque lettre et personnages à débloquer avec les meilleurs streaks.
- **Progression persistante** : profils pseudo + token, XP, rangs, score, streak, badges, personnage choisi et classement global dans SQLite.
- **1 038 mots français uniques** classés par difficulté et catégorie ; saisie et comparaison insensibles aux accents, accents conservés à l’affichage.
- **Score de manche** : difficulté, vitesse, sans-faute, multiplicateurs de streak et joker pénalisé.
- **Clavier virtuel et physique**, animations de victoire/défaite, confettis, effets sonores Web Audio, contrôle du volume et prise en charge de `prefers-reduced-motion`.
- Interface responsive téléphone, tablette et ordinateur.

## Installation et lancement local

Python 3.13.5 est indiqué dans `.python-version`.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Ouvre ensuite <http://localhost:5000>. Pour jouer depuis un autre appareil sur le même réseau, ouvre l’adresse IPv4 de l’ordinateur serveur avec `:5000` (par exemple `http://192.168.1.25:5000`) et autorise Python dans le pare-feu Windows.

La base SQLite est créée automatiquement dans `instance/pendu.sqlite3`. Tu peux définir `DATABASE_PATH` pour choisir un autre emplacement et `SECRET_KEY` pour configurer la clé Flask.

## Tests

```powershell
python -m pytest -q
```

Les tests couvrent le catalogue et la normalisation, les règles de score/streak, la persistance SQLite, la stratégie des bots, la confidentialité du mot secret, les salles/chat multijoueur et le contrat de l’interface.

## Déploiement sur Render

Le dépôt conserve sa configuration Render à la racine. Dans les paramètres du service, laisse **Root Directory** vide.

- **Build Command** : `pip install -r requirements.txt`
- **Start Command** :

  ```bash
  gunicorn --worker-class gthread --workers 1 --threads 100 --bind 0.0.0.0:$PORT app:app
  ```

Le serveur Socket.IO utilise explicitement le mode `threading` et `simple-websocket`; n’ajoute ni `eventlet` ni `gevent`. Configure une valeur secrète via `SECRET_KEY`. Pour conserver les profils après un redéploiement, configure `DATABASE_PATH` vers un stockage persistant fourni par l’hébergeur.

Le code source du client Socket.IO est livré localement dans `static/vendor/` avec sa licence. Aucun script, police, image ou feuille de style n’est téléchargé depuis un CDN au chargement du site.

## Structure

```text
app.py                         routes Flask, API et événements Socket.IO
bots.py                        personnalités, sélection de mots, stratégie de devinette
db.py                          profils, historique récent, progression et classement SQLite
scoring.py                     score, bonus de streak et rangs
words.py                       catalogue, validation et normalisation des mots français
mots.json                      mots par difficulté/catégorie, pièges et définitions
templates/index.html           menu, plateau et dialogues accessibles
static/css/style.css           thème responsive, scènes et animations
static/js/game.js              orchestration du client et Socket.IO
static/js/ui.js                rendu de l’interface, progression et chat
static/js/characters.js        six personnages SVG et leurs répliques
static/js/bots.js              avatars vectoriels des bots
static/js/audio.js             effets Web Audio, volume et mute persistés
static/vendor/                 client Socket.IO local et licence
tests/                         tests pytest serveur et contrat frontend
```
