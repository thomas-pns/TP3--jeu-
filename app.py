"""Flask and Socket.IO server for the multiplayer and bot hangman game."""

from __future__ import annotations

import os
import re
import secrets
import threading
import time
import unicodedata
from functools import wraps

from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room

from bots import (
    BOTS,
    available_bots,
    bot_delay,
    bot_line,
    choose_bot_word,
    choose_guess,
)
from db import BADGES, CHARACTERS, database
from words import normalize_word, validate_word


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))
socketio = SocketIO(app, async_mode="threading")

MAX_ERRORS = 8
MAX_WORD_LENGTH = 30
games = {}
bot_games = {}
state_lock = threading.RLock()
database.init()


def synchronized(handler):
    @wraps(handler)
    def wrapper(*args, **kwargs):
        with state_lock:
            return handler(*args, **kwargs)

    return wrapper


def _word_graphemes(word: str) -> list[str]:
    """Keep precomposed accents and œ as one position in the game mask."""
    result = []
    for character in unicodedata.normalize("NFC", word):
        if unicodedata.category(character).startswith("M") and result:
            result[-1] += character
        else:
            result.append(character)
    return result


def _word_keys(word: str) -> list[str]:
    return [normalize_word(letter) for letter in _word_graphemes(word)]


def _masked_text(masked: list[str | None]) -> str:
    return " ".join(letter if letter is not None else "_" for letter in masked)


def _normalized_letter(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("Saisissez une seule lettre.")
    letter = normalize_word(value.strip())
    if len(letter) != 1 or not letter.isalpha():
        raise ValueError("Saisissez une seule lettre.")
    return letter


def _difficulty_for_word(word: str) -> str:
    length = len(_word_graphemes(word))
    if length <= 5:
        return "easy"
    if length <= 8:
        return "medium"
    if length <= 12:
        return "hard"
    return "nightmare"


def _record_profile_result(
    player: dict,
    *,
    won: bool,
    difficulty: str,
    errors: int,
    started_at: float,
    hints_used: int = 0,
):
    token = player.get("token")
    if not token:
        return None
    return database.record_match(
        token,
        difficulty=difficulty,
        errors=errors,
        elapsed_seconds=max(0, time.time() - started_at),
        won=won,
        hints_used=hints_used,
    )


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
        word_keys=[],
        masked=[],
        guessed_letters=set(),
        errors=0,
        chooser=None,
        guesser=None,
        started_at=None,
        hints_used=0,
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
        word_keys=[],
        masked=[],
        guessed_letters=set(),
        errors=0,
        chooser=chooser_sid,
        guesser=guesser_sid,
        started_at=None,
        hints_used=0,
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
    difficulty = _difficulty_for_word(game["word"])
    started_at = game.get("started_at") or time.time()
    for sid, player in game["players"].items():
        result = _record_profile_result(
            player,
            won=(sid == winner_sid),
            difficulty=difficulty,
            errors=game["errors"],
            started_at=started_at,
            hints_used=game["hints_used"] if sid == game["guesser"] else 0,
        )
        if result:
            socketio.emit(
                "profile_updated",
                {"profile": result["profile"], "match": result["match"]},
                to=sid,
            )

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


def _error(message: str):
    emit("error", {"msg": message})


def _token_from(data: dict) -> str | None:
    token = data.get("token")
    return token if isinstance(token, str) and len(token) <= 200 else None


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/healthz")
def health_check():
    return jsonify(status="ok")


@app.post("/api/profile")
def profile_api():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Données de profil invalides."), 400

    token = data.get("token")
    if token:
        profile = database.get_profile(token)
        if profile is None:
            return jsonify(error="Profil introuvable. Créez un nouveau profil."), 401
        return jsonify(profile=profile)

    try:
        token, profile = database.create_profile(data.get("nickname", ""))
    except ValueError as error:
        return jsonify(error=str(error)), 400
    return jsonify(token=token, profile=profile), 201


@app.post("/api/profile/character")
def character_api():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Données invalides."), 400
    try:
        profile = database.set_character(data.get("token"), data.get("character_id"))
    except ValueError as error:
        return jsonify(error=str(error)), 400
    if profile is None:
        return jsonify(error="Profil introuvable."), 401
    return jsonify(profile=profile)


@app.get("/api/leaderboard")
def leaderboard_api():
    return jsonify(players=database.leaderboard())


@app.get("/api/game-data")
def game_data_api():
    return jsonify(
        bots=available_bots(),
        characters=[
            {
                **character,
                "unlocked_at_start": character["streak_required"] == 0,
            }
            for character in CHARACTERS
        ],
        badges=BADGES,
    )


@socketio.on("connect")
def handle_connect(auth=None):
    emit("connected", {"sid": request.sid})


@socketio.on("disconnect")
@synchronized
def handle_disconnect(reason=None):
    sid = request.sid
    with state_lock:
        bot_games.pop(sid, None)
        for room_id, game in list(games.items()):
            if sid in game["players"]:
                _remove_player(room_id, sid)
                break


@socketio.on("join_game")
@synchronized
def handle_join_game(data):
    if not isinstance(data, dict):
        _error("Données de connexion invalides.")
        return

    sid = request.sid
    with state_lock:
        if sid in bot_games or any(sid in game["players"] for game in games.values()):
            _error("Vous êtes déjà dans une partie.")
            return

    token = _token_from(data)
    profile = database.get_profile(token) if token else None
    if token and not profile:
        _error("Profil invalide. Rechargez la page puis reconnectez-vous.")
        return
    name = profile["nickname"] if profile else str(data.get("name", "Anonyme")).strip()[:20]
    name = name or "Anonyme"
    requested_room = str(data.get("room_id") or "").strip()
    if requested_room and not re.fullmatch(r"[A-Za-z0-9_-]{3,50}", requested_room):
        _error("L'identifiant de salle doit contenir 3 à 50 lettres, chiffres, tirets ou _.")
        return

    with state_lock:
        room_id = requested_room or _new_room_id()
        game = games.get(room_id)
        resumed_player = None
        stale_sid = None
        if game and token:
            stale_sid = next(
                (
                    player_sid
                    for player_sid, player in game["players"].items()
                    if player.get("token") == token
                ),
                None,
            )
            if stale_sid:
                resumed_player = game["players"].pop(stale_sid)
                leave_room(room_id, sid=stale_sid)
                _reset_round(game)
                remaining = next(iter(game["players"]), None)
                if remaining:
                    socketio.emit("opponent_left", to=remaining)
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
        game["players"][sid] = resumed_player or {
            "name": name,
            "score": 0,
            "token": token,
            "last_chat_at": 0.0,
        }
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
@synchronized
def handle_submit_word(data):
    if not isinstance(data, dict):
        _error("Données de mot invalides.")
        return

    sid = request.sid
    room_id = str(data.get("room_id", ""))
    game = games.get(room_id)
    if not game or sid not in game["players"]:
        _error("Salle introuvable.")
        return
    if game["state"] != "choosing" or sid != game.get("chooser"):
        _error("Ce n'est pas à vous de choisir le mot.")
        return

    try:
        word = validate_word(data.get("word", ""))
    except ValueError as error:
        _error(str(error))
        return
    if len(_word_graphemes(word)) < 3:
        _error("Choisissez un mot d'au moins 3 lettres.")
        return

    game.update(
        state="playing",
        word=word,
        word_keys=_word_keys(word),
        masked=[None] * len(_word_graphemes(word)),
        guessed_letters=set(),
        errors=0,
        started_at=time.time(),
        hints_used=0,
    )
    socketio.emit(
        "word_set",
        {"masked": _masked_text(game["masked"]), "errors": 0, "guessed_letters": []},
        to=room_id,
    )
    socketio.emit("your_turn_guess", to=game["guesser"])
    socketio.emit("opponent_turn", to=game["chooser"])


@socketio.on("guess_letter")
@synchronized
def handle_guess_letter(data):
    if not isinstance(data, dict):
        _error("Données de lettre invalides.")
        return

    sid = request.sid
    room_id = str(data.get("room_id", ""))
    game = games.get(room_id)
    if not game or sid not in game["players"]:
        _error("Salle introuvable.")
        return
    if game["state"] != "playing":
        _error("La partie n'est pas en cours.")
        return
    if sid != game.get("guesser"):
        _error("Ce n'est pas à vous de deviner.")
        return
    try:
        letter = _normalized_letter(data.get("letter", ""))
    except ValueError as error:
        _error(str(error))
        return
    if letter in game["guessed_letters"]:
        _error(f"La lettre « {letter} » a déjà été proposée.")
        return

    game["guessed_letters"].add(letter)
    matches = [
        index for index, key in enumerate(game["word_keys"]) if letter in key
    ]
    if matches:
        for index in matches:
            game["masked"][index] = _word_graphemes(game["word"])[index]
        socketio.emit(
            "correct_guess",
            {
                "letter": letter,
                "masked": _masked_text(game["masked"]),
                "guessed_letters": sorted(game["guessed_letters"]),
            },
            to=room_id,
        )
        if all(game["masked"]):
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


@socketio.on("use_hint")
@synchronized
def handle_use_hint(data):
    if not isinstance(data, dict):
        _error("Données de joker invalides.")
        return
    sid = request.sid
    room_id = str(data.get("room_id", ""))
    game = games.get(room_id)
    if not game or sid not in game["players"]:
        _error("Salle introuvable.")
        return
    if game["state"] != "playing" or sid != game.get("guesser"):
        _error("Le joker est disponible uniquement pendant ton tour.")
        return

    hidden_letters = {
        character
        for index, key in enumerate(game["word_keys"])
        if game["masked"][index] is None
        for character in key
        if len(character) == 1 and character not in game["guessed_letters"]
    }
    if not hidden_letters:
        _error("Il ne reste aucune lettre à révéler.")
        return
    letter = secrets.choice(sorted(hidden_letters))
    game["guessed_letters"].add(letter)
    game["hints_used"] += 1
    graphemes = _word_graphemes(game["word"])
    for index, key in enumerate(game["word_keys"]):
        if letter in key:
            game["masked"][index] = graphemes[index]
    socketio.emit(
        "hint_used",
        {
            "letter": letter,
            "masked": _masked_text(game["masked"]),
            "errors": game["errors"],
            "guessed_letters": sorted(game["guessed_letters"]),
            "hints_used": game["hints_used"],
        },
        to=room_id,
    )
    if all(game["masked"]):
        _finish_round(room_id, game, game["guesser"])


@socketio.on("play_again")
@synchronized
def handle_play_again(data):
    if not isinstance(data, dict):
        _error("Données de revanche invalides.")
        return

    sid = request.sid
    room_id = str(data.get("room_id", ""))
    game = games.get(room_id)
    if not game or sid not in game["players"] or game["state"] != "finished":
        _error("La revanche n'est pas disponible.")
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

    _start_round(room_id, game, game["guesser"])


@socketio.on("leave_room")
@synchronized
def handle_leave_room(data):
    if not isinstance(data, dict):
        return
    room_id = str(data.get("room_id", ""))
    sid = request.sid
    if room_id and sid in games.get(room_id, {}).get("players", {}):
        leave_room(room_id)
        _remove_player(room_id, sid)


@socketio.on("chat_message")
@synchronized
def handle_chat_message(data):
    if not isinstance(data, dict):
        return
    sid = request.sid
    room_id = str(data.get("room_id", ""))
    game = games.get(room_id)
    player = game.get("players", {}).get(sid) if game else None
    message = data.get("message")
    if not player or not isinstance(message, str):
        _error("Tu ne peux pas écrire dans cette salle.")
        return
    message = " ".join(message.split())
    if not message or len(message) > 140:
        _error("Le message doit contenir de 1 à 140 caractères.")
        return
    now = time.monotonic()
    if now - player["last_chat_at"] < 0.45:
        return
    player["last_chat_at"] = now
    socketio.emit(
        "chat_message",
        {"name": player["name"], "message": message},
        to=room_id,
    )


def _create_bot_match(sid: str, data: dict) -> tuple[dict | None, str | None]:
    token = _token_from(data)
    profile = database.get_profile(token) if token else None
    if profile is None:
        return None, "Créez d'abord votre profil pour lancer une partie."

    bot_id = data.get("bot_id")
    if not isinstance(bot_id, str) or bot_id not in BOTS:
        return None, "Bot inconnu."
    mode = data.get("mode", "guess")
    if mode not in ("guess", "duel"):
        return None, "Mode de jeu inconnu."

    with state_lock:
        if sid in bot_games or any(sid in game["players"] for game in games.values()):
            return None, "Quittez votre partie actuelle avant d'en commencer une autre."

        duel_count = database.bot_duel_count(token, bot_id)
        recent_words = database.recent_bot_words(token, bot_id)
        try:
            secret = choose_bot_word(
                bot_id,
                duel_count=duel_count + 1,
                recent_words=recent_words,
            )
        except LookupError as error:
            return None, str(error)
        database.remember_bot_word(token, bot_id, secret["normalized"])

        game = {
            "bot_id": bot_id,
            "bot": BOTS[bot_id],
            "token": token,
            "nickname": profile["nickname"],
            "mode": mode,
            "state": "playing" if mode == "guess" else "choosing",
            "entry": secret,
            "word": secret["word"],
            "word_keys": _word_keys(secret["word"]),
            "masked": [None] * len(_word_graphemes(secret["word"])),
            "guessed_letters": set(),
            "errors": 0,
            "hints_used": 0,
            "started_at": time.time(),
            "duel_count": duel_count + 1,
            "bot_mask": [],
            "bot_guessed_letters": set(),
            "bot_errors": 0,
            "bot_turn_pending": False,
        }
        bot_games[sid] = game
    return game, None


@socketio.on("start_bot_game")
@synchronized
def handle_start_bot_game(data):
    if not isinstance(data, dict):
        _error("Données de partie invalides.")
        return
    game, error = _create_bot_match(request.sid, data)
    if error:
        _error(error)
        return

    payload = {
        "bot_id": game["bot_id"],
        "bot_name": game["bot"].name,
        "mode": game["mode"],
        "difficulty": game["entry"]["difficulty"],
        "category": game["entry"]["category"],
        "round": game["duel_count"],
        "chat": bot_line(game["bot_id"]),
    }
    if game["mode"] == "guess":
        payload.update(masked=_masked_text(game["masked"]), errors=0)
    socketio.emit("bot_game_started", payload, to=request.sid)
    if game["mode"] == "duel":
        socketio.emit(
            "bot_word_required",
            {"min_length": 3, "max_length": MAX_WORD_LENGTH},
            to=request.sid,
        )


@socketio.on("submit_bot_word")
@synchronized
def handle_submit_bot_word(data):
    if not isinstance(data, dict):
        _error("Données de mot invalides.")
        return
    sid = request.sid
    game = bot_games.get(sid)
    if not game or game["mode"] != "duel" or game["state"] != "choosing":
        _error("Aucun mot n'est attendu.")
        return
    try:
        word = validate_word(data.get("word", ""))
    except ValueError as error:
        _error(str(error))
        return
    graphemes = _word_graphemes(word)
    if len(graphemes) < 3:
        _error("Choisissez un mot d'au moins 3 lettres.")
        return

    game.update(
        state="playing",
        player_word=word,
        player_word_keys=[normalize_word(letter) for letter in graphemes],
        bot_mask=[None] * len(graphemes),
        bot_guessed_letters=set(),
        bot_errors=0,
        masked=[None] * len(game["word_keys"]),
        guessed_letters=set(),
        errors=0,
        started_at=time.time(),
    )
    socketio.emit(
        "bot_duel_started",
        {
            "masked": _masked_text(game["masked"]),
            "errors": 0,
            "bot_mask": _masked_text(game["bot_mask"]),
            "bot_errors": 0,
            "chat": bot_line(game["bot_id"]),
        },
        to=sid,
    )


def _finish_bot_game(sid: str, won: bool):
    game = bot_games.get(sid)
    if not game or game["state"] == "finished":
        return
    game["state"] = "finished"
    result = database.record_match(
        game["token"],
        difficulty=game["entry"]["difficulty"],
        errors=game["errors"],
        elapsed_seconds=max(0, time.time() - game["started_at"]),
        won=won,
        hints_used=game["hints_used"],
    )
    payload = {
        "won": won,
        "bot_id": game["bot_id"],
        "bot_name": game["bot"].name,
        "mode": game["mode"],
        "word": game["entry"]["word"],
        "player_word": game.get("player_word"),
        "category": game["entry"]["category"],
        "difficulty": game["entry"]["difficulty"],
        "definition": game["entry"].get("definition"),
        "errors": game["errors"],
        "bot_errors": game["bot_errors"],
        "chat": bot_line(game["bot_id"]),
    }
    if result:
        payload.update(profile=result["profile"], match=result["match"])
    socketio.emit("bot_game_over", payload, to=sid)


@socketio.on("bot_guess_letter")
@synchronized
def handle_bot_guess_letter(data):
    if not isinstance(data, dict):
        _error("Données de lettre invalides.")
        return
    sid = request.sid
    game = bot_games.get(sid)
    if not game or game["mode"] != "guess" or game["state"] != "playing":
        _error("Aucune partie solo n'est en cours.")
        return
    try:
        letter = _normalized_letter(data.get("letter", ""))
    except ValueError as error:
        _error(str(error))
        return
    if letter in game["guessed_letters"]:
        _error(f"La lettre « {letter} » a déjà été proposée.")
        return

    game["guessed_letters"].add(letter)
    matches = [
        index for index, key in enumerate(game["word_keys"]) if letter in key
    ]
    if matches:
        graphemes = _word_graphemes(game["word"])
        for index in matches:
            game["masked"][index] = graphemes[index]
        socketio.emit(
            "bot_guess_result",
            {
                "correct": True,
                "letter": letter,
                "masked": _masked_text(game["masked"]),
                "errors": game["errors"],
                "guessed_letters": sorted(game["guessed_letters"]),
                "chat": bot_line(game["bot_id"]),
            },
            to=sid,
        )
        if all(game["masked"]):
            _finish_bot_game(sid, True)
        return

    game["errors"] += 1
    socketio.emit(
        "bot_guess_result",
        {
            "correct": False,
            "letter": letter,
            "masked": _masked_text(game["masked"]),
            "errors": game["errors"],
            "guessed_letters": sorted(game["guessed_letters"]),
            "chat": bot_line(game["bot_id"]),
        },
        to=sid,
    )
    if game["errors"] >= MAX_ERRORS:
        _finish_bot_game(sid, False)


@socketio.on("bot_hint")
@synchronized
def handle_bot_hint(data):
    sid = request.sid
    game = bot_games.get(sid)
    if not game or game["mode"] != "guess" or game["state"] != "playing":
        _error("Le joker n'est pas disponible.")
        return
    hidden_letters = set()
    for index, key in enumerate(game["word_keys"]):
        if game["masked"][index] is not None:
            continue
        hidden_letters.update(
            character
            for character in key
            if len(character) == 1 and character not in game["guessed_letters"]
        )
    if not hidden_letters:
        _error("Il ne reste aucune lettre à révéler.")
        return
    letter = secrets.choice(sorted(hidden_letters))
    game["hints_used"] += 1
    game["guessed_letters"].add(letter)
    graphemes = _word_graphemes(game["word"])
    for index, key in enumerate(game["word_keys"]):
        if letter in key:
            game["masked"][index] = graphemes[index]
    socketio.emit(
        "bot_hint_result",
        {
            "letter": letter,
            "masked": _masked_text(game["masked"]),
            "errors": game["errors"],
            "guessed_letters": sorted(game["guessed_letters"]),
            "hints_used": game["hints_used"],
        },
        to=sid,
    )
    if all(game["masked"]):
        _finish_bot_game(sid, True)


@socketio.on("bot_duel_guess")
@synchronized
def handle_bot_duel_guess(data):
    if not isinstance(data, dict):
        _error("Données de lettre invalides.")
        return
    sid = request.sid
    game = bot_games.get(sid)
    if (
        not game
        or game["mode"] != "duel"
        or game["state"] != "playing"
        or game["bot_turn_pending"]
    ):
        _error("Ce n'est pas votre tour.")
        return
    try:
        letter = _normalized_letter(data.get("letter", ""))
    except ValueError as error:
        _error(str(error))
        return
    if letter in game["guessed_letters"]:
        _error(f"La lettre « {letter} » a déjà été proposée.")
        return

    game["guessed_letters"].add(letter)
    matches = [
        index for index, key in enumerate(game["word_keys"]) if letter in key
    ]
    if matches:
        graphemes = _word_graphemes(game["word"])
        for index in matches:
            game["masked"][index] = graphemes[index]
        correct = True
    else:
        game["errors"] += 1
        correct = False

    socketio.emit(
        "bot_duel_player_guess",
        {
            "letter": letter,
            "correct": correct,
            "masked": _masked_text(game["masked"]),
            "errors": game["errors"],
            "guessed_letters": sorted(game["guessed_letters"]),
        },
        to=sid,
    )
    if all(game["masked"]):
        _finish_bot_game(sid, True)
    elif game["errors"] >= MAX_ERRORS:
        _finish_bot_game(sid, False)
    else:
        game["bot_turn_pending"] = True
        socketio.start_background_task(_run_bot_duel_turn, sid)


def _run_bot_duel_turn(sid: str):
    game = bot_games.get(sid)
    if not game:
        return
    socketio.sleep(bot_delay(game["bot_id"]))

    with state_lock:
        game = bot_games.get(sid)
        if (
            not game
            or game["state"] != "playing"
            or not game["bot_turn_pending"]
        ):
            return
        pattern = game["bot_mask"]
        guessed = game["bot_guessed_letters"]
        letter = choose_guess(
            pattern,
            guessed,
            bot_id=game["bot_id"],
        )
        guessed.add(letter)
        correct = False
        for index, key in enumerate(game["player_word_keys"]):
            if letter in key:
                game["bot_mask"][index] = _word_graphemes(game["player_word"])[index]
                correct = True
        if not correct:
            game["bot_errors"] += 1
        game["bot_turn_pending"] = False

        socketio.emit(
            "bot_duel_update",
            {
                "letter": letter,
                "correct": correct,
                "bot_mask": _masked_text(game["bot_mask"]),
                "bot_errors": game["bot_errors"],
                "bot_guessed_letters": sorted(guessed),
                "chat": bot_line(game["bot_id"]),
            },
            to=sid,
        )
        if all(game["bot_mask"]) or game["bot_errors"] >= MAX_ERRORS:
            _finish_bot_game(sid, False)


@socketio.on("leave_bot_game")
@synchronized
def handle_leave_bot_game():
    bot_games.pop(request.sid, None)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    socketio.run(
        app,
        host="0.0.0.0",
        port=port,
        debug=False,
        allow_unsafe_werkzeug=True,
    )
