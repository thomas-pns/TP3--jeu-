# Le Pendu — multijoueur web

Application Flask + Socket.IO responsive, avec des salles de deux joueurs, choix de mot, score par manche et revanche.

## Lancer en local

Python 3.13.5 est indiqué dans `.python-version`.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Ouvrir ensuite <http://localhost:5000>. Le point de contrôle de santé est `/healthz`.

Lancer les tests :

```powershell
python -m unittest discover -s tests -v
```

## Déployer sur Render

Les fichiers web (`app.py`, `templates/`, `static/`) sont à la racine du dépôt. Dans les paramètres du service Render, laisser **Root Directory** vide.

- **Build Command** : `pip install -r requirements.txt`
- **Start Command** :

  ```bash
  gunicorn --worker-class gthread --workers 1 --threads 100 --bind 0.0.0.0:$PORT app:app
  ```

Le dépôt fournit aussi un `render.yaml` avec ces réglages et un contrôle de santé. `.python-version` sélectionne Python 3.13.5. Flask-SocketIO est explicitement configuré en mode `threading`; `simple-websocket` permet la prise en charge WebSocket avec Gunicorn. **Ne remettez pas `eventlet` ou `gevent` dans `requirements.txt`** : leurs versions précédentes échouaient à l’installation sur le runtime Python 3.14.

Si le service Render existe déjà, vérifiez/modifiez sa commande de démarrage dans **Settings → Build & Deploy → Start Command**, puis lancez un déploiement après avoir poussé les changements. Ajoutez une variable `SECRET_KEY` dans Render (valeur aléatoire longue) si le service n’est pas créé depuis `render.yaml`.

Après le déploiement, ouvrez l’URL Render sur deux appareils, créez une salle sur le premier puis rejoignez-la avec son identifiant sur le second.

## Structure

```text
app.py
requirements.txt
.python-version
render.yaml
templates/index.html
static/css/style.css
static/js/game.js
static/images/bonhomme1.gif … bonhomme8.gif
tests/test_app.py
```
