// Game client logic
let socket = io();
let playerId = null;
let roomId = null;
let isChooser = false;
let currentState = '';

// DOM elements
const loginScreen = document.getElementById('login-screen');
const gameScreen = document.getElementById('game-screen');
const waitingDiv = document.getElementById('waiting');
const chooseWordDiv = document.getElementById('choose-word');
const playingDiv = document.getElementById('playing');
const gameOverDiv = document.getElementById('game-over');
const usernameInput = document.getElementById('username');
const roomIdInput = document.getElementById('room-id');
const joinBtn = document.getElementById('join-btn');
const roomDisplay = document.getElementById('room-display');
const wordInput = document.getElementById('word-input');
const submitWordBtn = document.getElementById('submit-word');
const letterInput = document.getElementById('letter-input');
const guessBtn = document.getElementById('guess-btn');
const hangmanImg = document.getElementById('hangman-img');
const wordDisplay = document.getElementById('word-display');
const guessedLettersDiv = document.getElementById('guessed-letters');
const remainingAttemptsDiv = document.getElementById('remaining-attempts');
const messageDiv = document.getElementById('message');
const gameOverTitle = document.getElementById('game-over-title');
const gameOverWord = document.getElementById('game-over-word');
const scoresSpan = document.getElementById('scores');
const playAgainBtn = document.getElementById('play-again');
const leaveRoomBtn = document.getElementById('leave-room');

// Event listeners
joinBtn.addEventListener('click', joinGame);
submitWordBtn.addEventListener('click', submitWord);
guessBtn.addEventListener('click', guessLetter);
playAgainBtn.addEventListener('click', playAgain);
leaveRoomBtn.addEventListener('click', leaveRoom);
letterInput.addEventListener('keypress', e => {
    if (e.key === 'Enter') guessLetter();
});

function joinGame() {
    const username = usernameInput.value.trim();
    if (!username) {
        alert('Veuillez entrer un nom');
        return;
    }
    const room = roomIdInput.value.trim() || null;
    socket.emit('join_game', { name: username, room_id: room });
}

function submitWord() {
    const word = wordInput.value.trim();
    if (!word) {
        alert('Veuillez entrer un mot');
        return;
    }
    socket.emit('submit_word', { room_id: roomId, word: word });
    wordInput.value = '';
}

function guessLetter() {
    const letter = letterInput.value.toLowerCase();
    if (!letter) {
        alert('Veuillez entrer une lettre');
        return;
    }
    socket.emit('guess_letter', { room_id: roomId, letter: letter });
    letterInput.value = '';
}

function playAgain() {
    socket.emit('play_again', { room_id: roomId });
    playAgainBtn.disabled = true;
    playAgainBtn.textContent = 'En attente…';
}

function leaveRoom() {
    socket.emit('leave_room', { room_id: roomId });
    resetGame();
    showLoginScreen();
}

// Socket event handlers
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('joined_game', data => {
    playerId = data.player_id;
    roomId = data.room_id;
    roomDisplay.textContent = roomId;
    showGameScreen();
    showWaiting();
});

socket.on('player_joined', data => {
    showWaiting(`${data.name} a rejoint la salle. Préparation de la manche…`);
});

socket.on('game_full', () => {
    alert('Cette salle contient déjà deux joueurs.');
});

socket.on('your_turn_choose_word', () => {
    isChooser = true;
    resetGame();
    showChooseWord();
});

socket.on('waiting_for_opponent_word', data => {
    isChooser = false;
    resetGame();
    showWaiting(`${data?.name || 'Votre adversaire'} choisit un mot…`);
});

socket.on('word_set', data => {
    updateWordDisplay(data.masked);
    guessedLettersDiv.textContent = (data.guessed_letters || []).join(', ');
    updateRemainingAttempts(data.errors || 0);
    updateHangmanImage(data.errors || 0);
    showPlaying();
    setGuessingEnabled(false);
    messageDiv.textContent = 'Au tour de l\'adversaire de deviner...';
});

socket.on('your_turn_guess', () => {
    setGuessingEnabled(true);
    messageDiv.textContent = 'À vous de deviner une lettre';
    letterInput.focus();
});

socket.on('opponent_turn', () => {
    setGuessingEnabled(false);
    messageDiv.textContent = 'Au tour de l\'adversaire...';
});

socket.on('correct_guess', data => {
    updateWordDisplay(data.masked);
    guessedLettersDiv.textContent = (data.guessed_letters || []).join(', ');
    messageDiv.textContent = `Bonne lettre ! ${data.letter}`;
});

socket.on('wrong_guess', data => {
    guessedLettersDiv.textContent = (data.guessed_letters || []).join(', ');
    updateRemainingAttempts(data.errors);
    messageDiv.textContent = `Mauvaise lettre ! Il reste ${8 - data.errors} tentatives`;
    updateHangmanImage(data.errors);
});

socket.on('game_over', data => {
    setGuessingEnabled(false);
    showGameOver(data);
});

socket.on('rematch_waiting', () => {
    gameOverTitle.textContent = 'Revanche demandée !';
    gameOverWord.textContent = 'En attente de la réponse de votre adversaire…';
});

socket.on('opponent_wants_rematch', data => {
    gameOverWord.textContent = `${data.name} souhaite rejouer. Cliquez sur « Rejouer » pour accepter.`;
    playAgainBtn.disabled = false;
    playAgainBtn.textContent = 'Accepter la revanche';
});

socket.on('opponent_left', () => {
    resetGame();
    showWaiting('Votre adversaire a quitté la salle. En attente d’un nouveau joueur…');
});

socket.on('error', data => {
    playAgainBtn.disabled = false;
    playAgainBtn.textContent = 'Rejouer';
    alert(data.msg);
});

socket.on('disconnect', () => {
    alert('Déconnecté du serveur');
    showLoginScreen();
});

// UI update functions
function showLoginScreen() {
    loginScreen.style.display = 'flex';
    gameScreen.style.display = 'none';
    resetUI();
}

function showGameScreen() {
    loginScreen.style.display = 'none';
    gameScreen.style.display = 'block';
}

function showWaiting(message = 'En attente d’un autre joueur…') {
    waitingDiv.style.display = 'block';
    chooseWordDiv.style.display = 'none';
    playingDiv.style.display = 'none';
    gameOverDiv.style.display = 'none';
    waitingDiv.querySelector('p').textContent = message;
    currentState = 'waiting';
}

function showChooseWord() {
    waitingDiv.style.display = 'none';
    chooseWordDiv.style.display = 'block';
    playingDiv.style.display = 'none';
    gameOverDiv.style.display = 'none';
    currentState = 'choosing';
    submitWordBtn.disabled = false;
    wordInput.value = '';
    wordInput.focus();
}

function showPlaying() {
    waitingDiv.style.display = 'none';
    chooseWordDiv.style.display = 'none';
    playingDiv.style.display = 'block';
    gameOverDiv.style.display = 'none';
    currentState = 'playing';
}

function setGuessingEnabled(enabled) {
    letterInput.disabled = !enabled;
    guessBtn.disabled = !enabled;
}

function showGameOver(data) {
    waitingDiv.style.display = 'none';
    chooseWordDiv.style.display = 'none';
    playingDiv.style.display = 'none';
    gameOverDiv.style.display = 'block';
    currentState = 'gameover';
    gameOverTitle.textContent = data.winner === playerId
        ? 'Vous avez gagné !'
        : `${data.winner_name || 'Votre adversaire'} a gagné !`;
    gameOverWord.textContent = `Le mot était : ${data.word}`;
    const scoresObj = data.scores;
    scoresSpan.textContent = Object.entries(scoresObj)
        .map(([id, score]) => `${data.player_names?.[id] || 'Joueur'} : ${score}`)
        .join(' · ');
    playAgainBtn.disabled = false;
    playAgainBtn.textContent = 'Rejouer';
}

function resetGame() {
    isChooser = false;
    currentState = '';
    // clear displays
    wordDisplay.textContent = '';
    guessedLettersDiv.textContent = '';
    remainingAttemptsDiv.textContent = '';
    messageDiv.textContent = '';
    hangmanImg.innerHTML = '';
}

function resetUI() {
    usernameInput.value = '';
    roomIdInput.value = '';
    wordInput.value = '';
    letterInput.value = '';
}

function updateWordDisplay(masked) {
    wordDisplay.textContent = masked;
}

function updateGuessedLetters(letter) {
    const current = guessedLettersDiv.textContent;
    guessedLettersDiv.textContent = current ? `${current}, ${letter}` : letter;
}

function updateRemainingAttempts(errors) {
    remainingAttemptsDiv.textContent = `Tentatives restantes : ${8 - errors}`;
}

function updateHangmanImage(errors) {
    if (errors === 0) {
        hangmanImg.innerHTML = '<div style="color:#666;">Le dessin apparaîtra ici</div>';
        return;
    }
    const img = document.createElement('img');
    img.src = `/static/images/bonhomme${errors}.gif`;
    img.alt = `Étape ${errors}`;
    img.style.maxWidth = '100%';
    img.style.maxHeight = '100%';
    hangmanImg.innerHTML = '';
    hangmanImg.appendChild(img);
}
