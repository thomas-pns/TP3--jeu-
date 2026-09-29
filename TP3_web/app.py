from flask import Flask, render_template, session, copy_current_request_context, request
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
import json
import random
from pathlib import Path
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

BASE_DIR = Path(__file__).resolve().parent
with open(BASE_DIR / "mots.json", encoding="utf-8") as f:
    mots = json.load(f)

# Game state per room
games = {}

def get_random_word(length=None):
    if length is None:
        length = random.choice(list(mots.keys()))
    return random.choice(mots[str(length)]).lower()

def init_game(room_id, player1_sid, word=None):
    if word is None:
        word = get_random_word()
    games[room_id] = {
        'word': word,
        'masked': ['_' if i != 0 else word[0] for i in range(len(word))],  # reveal first letter
        'guessed_letters': set(),
        'errors': 0,
        'max_errors': 8,
        'players': {player1_sid: {'name': f'Joueur1', 'score': 0}},
        'current_turn': player1_sid,  # who guesses? In multiplayer, one chooses, other guesses. We'll handle via events.
        'state': 'waiting_for_word',  # waiting_for_word, playing, finished
        'winner': None
    }
    return games[room_id]

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected:', request.sid)
    emit('connected', {'sid': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected:', request.sid)
    # Clean up games where this sid is involved
    for room_id, game in list(games.items()):
        if request.sid in game['players']:
            leave_room(room_id)
            # If only one player left, end game
            if len(game['players']) == 1:
                # Notify remaining player
                remaining_sid = [sid for sid in game['players'] if sid != request.sid][0]
                emit('opponent_left', room=remaining_sid)
                del games[room_id]
            else:
                # Remove player
                del game['players'][request.sid]
                if game['current_turn'] == request.sid:
                    # pass turn to other
                    next_sid = [sid for sid in game['players'] if sid != request.sid][0]
                    game['current_turn'] = next_sid
                    emit('turn_change', {'sid': next_sid}, room=room_id)
            break

@socketio.on('join_game')
def handle_join_game(data):
    sid = request.sid
    player_name = data.get('name', 'Anonyme')
    room_id = data.get('room_id')
    if not room_id:
        # create new room
        import uuid
        room_id = str(uuid.uuid4())
    join_room(room_id)
    if room_id not in games:
        init_game(room_id, sid)
        games[room_id]['players'][sid] = {'name': player_name, 'score': 0}
        emit('joined_game', {'room_id': room_id, 'player_id': sid, 'players': [{'id': sid, 'name': player_name}]}, room=sid)
    else:
        game = games[room_id]
        if len(game['players']) >= 2:
            emit('game_full', room=sid)
            leave_room(room_id)
            return
        game['players'][sid] = {'name': player_name, 'score': 0}
        emit('joined_game', {'room_id': room_id, 'player_id': sid, 'players': [{'id': k, 'name': v['name']} for k, v in game['players'].items()]}, room=sid)
        # notify others
        emit('player_joined', {'id': sid, 'name': player_name}, room=room_id, include_self=False)
        # if now two players, start waiting for word
        if len(game['players']) == 2:
            game['state'] = 'waiting_for_word'
            # randomly choose who chooses word
            chooser = random.choice(list(game['players'].keys()))
            game['chooser'] = chooser
            emitter = [sid for sid in game['players'] if sid != chooser][0]
            emit('your_turn_choose_word', room=chooser)
            emit('waiting_for_opponent_word', room=emitter)

@socketio.on('submit_word')
def handle_submit_word(data):
    sid = request.sid
    room_id = data.get('room_id')
    word = data.get('word', '').strip().lower()
    if not room_id or room_id not in games:
        emit('error', {'msg': 'Invalid room'}, room=sid)
        return
    game = games[room_id]
    if sid != game.get('chooser'):
        emit('error', {'msg': 'Not your turn'}, room=sid)
        return
    if not word.isalpha() or len(word) < 3:
        emit('error', {'msg': 'Word must be letters only and at least 3 chars'}, room=sid)
        return
    game['word'] = word
    game['masked'] = ['_' if i != 0 else word[0] for i in range(len(word))]
    game['guessed_letters'] = set()
    game['errors'] = 0
    game['state'] = 'playing'
    # notify both
    emitter = [s for s in game['players'] if s != sid][0]
    emit('word_set', {'masked': ' '.join(game['masked'])}, room=room_id)
    emit('your_turn_guess', room=emitter)
    emit('opponent_turn', room=sid)

@socketio.on('guess_letter')
def handle_guess_letter(data):
    sid = request.sid
    room_id = data.get('room_id')
    letter = data.get('letter', '').lower()
    if not room_id or room_id not in games:
        emit('error', {'msg': 'Invalid room'}, room=sid)
        return
    game = games[room_id]
    if game['state'] != 'playing':
        emit('error', {'msg': 'Game not playing'}, room=sid)
        return
    # determine whose turn it is (the guesser)
    guesser = [s for s in game['players'] if s != game.get('chooser')][0]
    if sid != guesser:
        emit('error', {'msg': 'Not your turn to guess'}, room=sid)
        return
    if len(letter) != 1 or not letter.isalpha():
        emit('error', {'msg': 'Invalid letter'}, room=sid)
        return
    if letter in game['guessed_letters']:
        emit('error', {'msg': 'Letter already guessed'}, room=sid)
        return
    game['guessed_letters'].add(letter)
    if letter in game['word']:
        for i, c in enumerate(game['word']):
            if c == letter:
                game['masked'][i] = letter
        emit('correct_guess', {'letter': letter, 'masked': ' '.join(game['masked'])}, room=room_id)
        if '_' not in game['masked']:
            game['state'] = 'finished'
            game['winner'] = guesser
            game['players'][guesser]['score'] += 1
            emit('game_over', {'winner': guesser, 'word': game['word'], 'scores': {k: v['score'] for k, v in game['players'].items()}}, room=room_id)
    else:
        game['errors'] += 1
        emit('wrong_guess', {'letter': letter, 'errors': game['errors']}, room=room_id)
        if game['errors'] >= game['max_errors']:
            game['state'] = 'finished'
            game['winner'] = game.get('chooser')  # the chooser wins if guesser fails
            game['players'][game['winner']]['score'] += 1
            emit('game_over', {'winner': game['winner'], 'word': game['word'], 'scores': {k: v['score'] for k, v in game['players'].items()}}, room=room_id)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
