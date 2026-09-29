import os
import re
import secrets

from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))

# gthread + simple-websocket is the production setup configured for Render.
# Explicit threading mode prevents Flask-SocketIO from auto-selecting gevent/eventlet.
socketio = SocketIO(app, async_mode="threading")

MAX_ERRORS = 8
MAX_WORD_LENGTH = 30
games = {}


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/healthz")
def health_check():
    return jsonify(status="ok")


def _players_payload(game):
    return [
        {"id": sid, "name": player["name"], "score": player["score"]}
        for sid, player in game["players"].items()
    ]


def _new_room_id():
    room_id = secrets.token_urlsafe(6)
    while room_id in games:
        room_id = secrets.token_urlsafe(6)
    return room_id


def _reset_round(game):
    game.update(
        state="waiting",
        word=None,
        masked=[],
        guessed_letters=set(),
        errors=0,
        chooser=None,
        guesser=None,
        rematch_votes=set(),
    )


def _start_round(room_id, game, chooser_sid):
    player_ids = list(game["players"])
    if len(player_ids) != 2 or chooser_sid not in game["players"]:
        _reset_round(game)
        return

    guesser_sid = next(sid for sid in player_ids if sid != chooser_sid)
    game.update(
        state="choosing",
        word=None,
        masked=[],
        guessed_letters=set(),
        errors=0,
        chooser=chooser_sid,
        guesser=guesser_sid,
        rematch_votes=set(),
        round=game.get("round", 0) + 1,
    )
    socketio.emit(
        "round_started",
        {"round": game["round"], "players": _players_payload(game)},
        to=room_id,
    )
    socketio.emit("your_turn_choose_word", {"room_id": room_id}, to=chooser_sid)
    socketio.emit(
        "waiting_for_opponent_word",
        {"name": game["players"][chooser_sid]["name"]},
        to=guesser_sid,
    )


def _finish_round(room_id, game, winner_sid):
    if game["state"] != "playing" or winner_sid not in game["players"]:
        return

    game["state"] = "finished"
    game["winner"] = winner_sid
    game["players"][winner_sid]["score"] += 1
    socketio.emit(
        "game_over",
        {
            "winner": winner_sid,
            "winner_name": game["players"][winner_sid]["name"],
            "word": game["word"],
            "scores": {
                sid: player["score"] for sid, player in game["players"].items()
            },
            "player_names": {
                sid: player["name"] for sid, player in game["players"].items()
            },
        },
        to=room_id,
    )


def _remove_player(room_id, sid):
    game = games.get(room_id)
    if not game or sid not in game["players"]:
        return

    del game["players"][sid]
    remaining_players = list(game["players"])
    if not remaining_players:
        games.pop(room_id, None)
        return

    _reset_round(game)
    socketio.emit("opponent_left", to=remaining_players[0])


@socketio.on("connect")
def handle_connect(auth=None):
    emit("connected", {"sid": request.sid})


@socketio.on("disconnect")
def handle_disconnect(reason=None):
    sid = request.sid
    for room_id, game in list(games.items()):
        if sid in game["players"]:
            _remove_player(room_id, sid)
            break


@socketio.on("join_game")
def handle_join_game(data):
    if not isinstance(data, dict):
        emit("error", {"msg": "Données de connexion invalides."})
        return

    sid = request.sid
    # A socket may belong to only one game room at a time.
    if any(sid in game["players"] for game in games.values()):
        emit("error", {"msg": "Vous êtes déjà dans une salle."})
        return

    name = str(data.get("name", "Anonyme")).strip()[:20] or "Anonyme"
    requested_room = str(data.get("room_id") or "").strip()
    if requested_room and not re.fullmatch(r"[A-Za-z0-9_-]{3,50}", requested_room):
        emit("error", {"msg": "L'identifiant de salle doit contenir 3 à 50 lettres, chiffres, tirets ou _."})
        return

    room_id = requested_room or _new_room_id()
    game = games.get(room_id)
    if game and len(game["players"]) >= 2:
        emit("game_full")
        return

    if game is None:
        game = {
            "players": {},
            "round": 0,
            "state": "waiting",
            "rematch_votes": set(),
        }
        games[room_id] = game

    join_room(room_id)
    game["players"][sid] = {"name": name, "score": 0}
    emit(
        "joined_game",
        {
            "room_id": room_id,
            "player_id": sid,
            "players": _players_payload(game),
        },
        to=sid,
    )
    socketio.emit(
        "player_joined",
        {"id": sid, "name": name, "players": _players_payload(game)},
        to=room_id,
        skip_sid=sid,
    )

    if len(game["players"]) == 2:
        chooser_sid = secrets.choice(list(game["players"]))
        _start_round(room_id, game, chooser_sid)


@socketio.on("submit_word")
def handle_submit_word(data):
    if not isinstance(data, dict):
        emit("error", {"msg": "Données de mot invalides."})
        return

    sid = request.sid
    room_id = str(data.get("room_id", ""))
    game = games.get(room_id)
    raw_word = data.get("word", "")
    if not game or sid not in game["players"]:
        emit("error", {"msg": "Salle introuvable."})
        return
    if game["state"] != "choosing" or sid != game.get("chooser"):
        emit("error", {"msg": "Ce n'est pas à vous de choisir le mot."})
        return
    if not isinstance(raw_word, str):
        emit("error", {"msg": "Le mot doit contenir uniquement des lettres."})
        return

    word = raw_word.strip().lower()
    if not (3 <= len(word) <= MAX_WORD_LENGTH) or not word.isalpha():
        emit(
            "error",
            {"msg": f"Choisissez un mot de 3 à {MAX_WORD_LENGTH} lettres, sans espace ni chiffre."},
        )
        return

    game.update(
        state="playing",
        word=word,
        masked=["_"] * len(word),
        guessed_letters=set(),
        errors=0,
    )
    socketio.emit(
        "word_set",
        {"masked": " ".join(game["masked"]), "errors": 0, "guessed_letters": []},
        to=room_id,
    )
    socketio.emit("your_turn_guess", to=game["guesser"])
    socketio.emit("opponent_turn", to=game["chooser"])


@socketio.on("guess_letter")
def handle_guess_letter(data):
    if not isinstance(data, dict):
        emit("error", {"msg": "Données de lettre invalides."})
        return

    sid = request.sid
    room_id = str(data.get("room_id", ""))
    game = games.get(room_id)
    raw_letter = data.get("letter", "")
    if not game or sid not in game["players"]:
        emit("error", {"msg": "Salle introuvable."})
        return
    if game["state"] != "playing":
        emit("error", {"msg": "La partie n'est pas en cours."})
        return
    if sid != game.get("guesser"):
        emit("error", {"msg": "Ce n'est pas à vous de deviner."})
        return
    if not isinstance(raw_letter, str):
        emit("error", {"msg": "Saisissez une seule lettre."})
        return

    letter = raw_letter.strip().lower()
    if len(letter) != 1 or not letter.isalpha():
        emit("error", {"msg": "Saisissez une seule lettre."})
        return
    if letter in game["guessed_letters"]:
        emit("error", {"msg": f"La lettre « {letter} » a déjà été proposée."})
        return

    game["guessed_letters"].add(letter)
    if letter in game["word"]:
        for index, character in enumerate(game["word"]):
            if character == letter:
                game["masked"][index] = letter
        socketio.emit(
            "correct_guess",
            {
                "letter": letter,
                "masked": " ".join(game["masked"]),
                "guessed_letters": sorted(game["guessed_letters"]),
            },
            to=room_id,
        )
        if "_" not in game["masked"]:
            _finish_round(room_id, game, game["guesser"])
        return

    game["errors"] += 1
    socketio.emit(
        "wrong_guess",
        {
            "letter": letter,
            "errors": game["errors"],
            "guessed_letters": sorted(game["guessed_letters"]),
        },
        to=room_id,
    )
    if game["errors"] >= MAX_ERRORS:
        _finish_round(room_id, game, game["chooser"])


@socketio.on("play_again")
def handle_play_again(data):
    if not isinstance(data, dict):
        emit("error", {"msg": "Données de revanche invalides."})
        return

    sid = request.sid
    room_id = str(data.get("room_id", ""))
    game = games.get(room_id)
    if not game or sid not in game["players"] or game["state"] != "finished":
        emit("error", {"msg": "La revanche n'est pas disponible."})
        return

    game["rematch_votes"].add(sid)
    if len(game["rematch_votes"]) < 2:
        emit("rematch_waiting", to=sid)
        opponent_sid = next(player_sid for player_sid in game["players"] if player_sid != sid)
        socketio.emit(
            "opponent_wants_rematch",
            {"name": game["players"][sid]["name"]},
            to=opponent_sid,
        )
        return

    # Alternate the roles: the previous guesser chooses the next word.
    next_chooser = game["guesser"]
    _start_round(room_id, game, next_chooser)


@socketio.on("leave_room")
def handle_leave_room(data):
    if not isinstance(data, dict):
        return
    room_id = str(data.get("room_id", ""))
    sid = request.sid
    if room_id and sid in games.get(room_id, {}).get("players", {}):
        leave_room(room_id)
        _remove_player(room_id, sid)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    socketio.run(
        app,
        host="0.0.0.0",
        port=port,
        debug=False,
        allow_unsafe_werkzeug=True,
    )
