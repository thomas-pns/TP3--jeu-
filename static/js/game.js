import { CHARACTER_LIST, characterQuote } from "./characters.js";
import { botAvatarSvg } from "./bots.js";
import { audio } from "./audio.js";
import {
    $,
    appendChat,
    celebrate,
    clearChat,
    closeDialogs,
    renderAttempts,
    renderBotOptions,
    renderCharacter,
    renderCharacters,
    renderHeroCharacter,
    renderKeyboard,
    renderLeaderboard,
    renderMask,
    renderAchievements,
    selectBotOption,
    setProfileSetup,
    setView,
    showDialog,
    showResult,
    showToast,
    updateProfile,
} from "./ui.js";

const PROFILE_TOKEN_KEY = "motus-maximus-profile";
const DIFFICULTY_LABELS = {
    easy: "FACILE",
    medium: "MOYEN",
    hard: "DIFFICILE",
    nightmare: "CAUCHEMAR",
};
const socket = window.io();
let profile = null;
let gameData = { bots: [], characters: [], badges: {} };
let selectedBot = "beginner";
let selectedCharacter = "pirate";
let hasConnectedBefore = false;
let reconnecting = false;
let volatileToken = null;
let game = {
    kind: null,
    mode: null,
    roomId: null,
    playerId: null,
    botId: null,
    botName: null,
    round: 0,
    errors: 0,
    guessed: new Set(),
    correct: new Set(),
    enabled: false,
    localTurn: false,
    finished: false,
    lastProfileMatch: null,
};

function token() {
    try {
        return localStorage.getItem(PROFILE_TOKEN_KEY) || volatileToken;
    } catch {
        return volatileToken;
    }
}

function saveToken(value) {
    volatileToken = value;
    try {
        localStorage.setItem(PROFILE_TOKEN_KEY, value);
    } catch {
        showToast("Le navigateur ne peut pas mémoriser le profil sur cet appareil.", "error");
    }
}

function removeToken() {
    volatileToken = null;
    try {
        localStorage.removeItem(PROFILE_TOKEN_KEY);
    } catch {
        // A fresh profile can still be created for this page session.
    }
}

async function fetchJson(url, options = {}) {
    const response = await fetch(url, {
        headers: { "Content-Type": "application/json", ...(options.headers || {}) },
        ...options,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        const error = new Error(data.error || `Erreur ${response.status}`);
        error.status = response.status;
        throw error;
    }
    return data;
}

function applyProfile(nextProfile) {
    profile = nextProfile;
    selectedCharacter = profile?.selected_character || "pirate";
    updateProfile(profile);
    renderHeroCharacter(selectedCharacter);
    $("start-bot-btn").disabled = !profile || !selectedBot;
    $("start-duel-btn").disabled = !profile || !selectedBot;
    $("join-room-btn").disabled = !profile;
}

async function loadProfile() {
    const savedToken = token();
    if (!savedToken) {
        setProfileSetup(true);
        return;
    }
    try {
        const data = await fetchJson("/api/profile", {
            method: "POST",
            body: JSON.stringify({ token: savedToken }),
        });
        applyProfile(data.profile);
        setProfileSetup(false);
    } catch (error) {
        if (error.status === 401) {
            removeToken();
            setProfileSetup(true);
            showToast("Ton ancien profil n’a pas été retrouvé. Crée-en un nouveau.", "error");
            return;
        }
        $("profile-setup").hidden = true;
        $("start-bot-btn").disabled = true;
        $("start-duel-btn").disabled = true;
        $("join-room-btn").disabled = true;
        showToast("Impossible de joindre le serveur pour vérifier ton profil. Réessaie plus tard.", "error");
    }
}

async function loadGameData() {
    try {
        gameData = await fetchJson("/api/game-data");
        selectedBot = gameData.bots[0]?.id || "beginner";
        renderBotOptions(gameData.bots, selectedBot, (botId) => {
            selectedBot = botId;
            selectBotOption(botId);
        });
        if (profile) {
            renderCharacters(gameData, profile, chooseCharacter);
            renderAchievements(gameData, profile);
        }
    } catch (error) {
        showToast(`Impossible de charger le jeu : ${error.message}`, "error");
    }
}

function requireProfile() {
    if (profile) return true;
    setProfileSetup(true);
    $("profile-setup").scrollIntoView({ behavior: "smooth", block: "center" });
    showToast("Choisis d’abord ton nom de légende.");
    return false;
}

function resetRoundState() {
    game.errors = 0;
    game.guessed = new Set();
    game.correct = new Set();
    game.enabled = false;
    game.localTurn = false;
    game.finished = false;
    game.lastProfileMatch = null;
    renderMask("");
    renderAttempts(0);
    renderKeyboard([], [], false, onGuess);
    $("round-message").textContent = "Préparation du défi…";
    $("guessed-letters").textContent = "";
    $("secret-word-form").hidden = true;
    $("duel-word-form").hidden = true;
    $("hint-btn").hidden = true;
    $("bot-progress-box").hidden = true;
    $("chat-form").hidden = true;
    clearChat();
    renderCharacter(selectedCharacter, 0, "idle", characterQuote(selectedCharacter, "idle"));
}

function beginBotGame(mode) {
    if (!requireProfile()) return;
    game = {
        kind: "bot",
        mode,
        roomId: null,
        playerId: null,
        botId: selectedBot,
        botName: "",
        round: 0,
        errors: 0,
        guessed: new Set(),
        correct: new Set(),
        enabled: false,
        localTurn: false,
        finished: false,
        lastProfileMatch: null,
    };
    resetRoundState();
    setView("game");
    $("game-mode-label").textContent = mode === "duel" ? "DUEL BOT" : "SOLO VS BOT";
    $("room-code-label").hidden = true;
    $("game-title").textContent = mode === "duel" ? "Deux mots. Un seul vainqueur." : "Garde ton sang-froid";
    $("game-eyebrow").textContent = mode === "duel" ? "FACE-À-FACE" : "LE MOT MYSTÈRE";
    $("round-message").textContent = "Le bot prépare son meilleur mot…";
    socket.emit("start_bot_game", { token: token(), bot_id: selectedBot, mode });
}

function joinMultiplayerRoom() {
    if (!requireProfile()) return;
    game = {
        kind: "multiplayer",
        mode: "multiplayer",
        roomId: null,
        playerId: null,
        botId: null,
        botName: null,
        round: 0,
        errors: 0,
        guessed: new Set(),
        correct: new Set(),
        enabled: false,
        localTurn: false,
        finished: false,
        lastProfileMatch: null,
    };
    resetRoundState();
    setView("game");
    $("game-mode-label").textContent = "DUEL PRIVÉ";
    $("game-title").textContent = "La salle se prépare…";
    $("game-eyebrow").textContent = "MULTIJOUEUR";
    $("game-category").textContent = "Mot choisi par ton ami";
    $("game-difficulty").textContent = "SURPRISE";
    $("round-message").textContent = "Connexion à la salle en cours…";
    $("opponent-name").textContent = "En attente…";
    $("opponent-description").textContent = "Partage le code avec ton ami";
    $("room-code-label").hidden = true;
    socket.emit("join_game", {
        name: profile.nickname,
        token: token(),
        room_id: $("room-input").value.trim() || null,
    });
}

function leaveGame() {
    if (game.kind === "multiplayer" && game.roomId) {
        socket.emit("leave_room", { room_id: game.roomId });
    } else if (game.kind === "bot") {
        socket.emit("leave_bot_game");
    }
    closeDialogs();
    game = { ...game, kind: null, mode: null, enabled: false, finished: false };
    setView("home");
}

function nextRound() {
    closeDialogs();
    if (game.kind === "multiplayer" && game.roomId) {
        $("round-message").textContent = "En attente de la revanche…";
        $("next-round-btn").disabled = true;
        socket.emit("play_again", { room_id: game.roomId });
    } else if (game.kind === "bot") {
        beginBotGame(game.mode || "guess");
    }
}

function onGuess(letter) {
    if (!game.enabled || game.finished || !/^[a-z]$/.test(letter)) return;
    game.enabled = false;
    renderKeyboard([...game.guessed], [...game.correct], false, onGuess);
    if (game.kind === "multiplayer") {
        socket.emit("guess_letter", { room_id: game.roomId, letter });
    } else if (game.kind === "bot" && game.mode === "duel") {
        socket.emit("bot_duel_guess", { letter });
    } else if (game.kind === "bot") {
        socket.emit("bot_guess_letter", { letter });
    }
    audio.play("key");
}

function setGuessing(enabled) {
    game.enabled = enabled && !game.finished;
    renderKeyboard([...game.guessed], [...game.correct], game.enabled, onGuess);
}

function updateGuesses(guessed, correct = [...game.correct]) {
    game.guessed = new Set(guessed || []);
    game.correct = new Set(correct || []);
    $("guessed-letters").textContent = game.guessed.size
        ? `DÉJÀ JOUÉ : ${[...game.guessed].join(" · ").toUpperCase()}`
        : "";
    renderKeyboard([...game.guessed], [...game.correct], game.enabled, onGuess);
}

function setOpponent(botId, name, description = "Adversaire redoutable") {
    $("opponent-name").textContent = name;
    $("opponent-description").textContent = description;
    $("opponent-avatar").innerHTML = botId
        ? botAvatarSvg(botId, true)
        : [...(name || "?")][0]?.toLocaleUpperCase("fr") || "?";
}

function showChatLine(name, message, player = false) {
    if (message) appendChat(name, message, player);
}

function openLeaderboard() {
    fetchJson("/api/leaderboard")
        .then((data) => renderLeaderboard(data.players))
        .catch((error) => showToast(error.message, "error"));
    showDialog("leaderboard-dialog");
}

function openCharacters() {
    if (profile) renderCharacters(gameData, profile, chooseCharacter);
    showDialog("characters-dialog");
}

function openAchievements() {
    if (profile) renderAchievements(gameData, profile);
    showDialog("achievements-dialog");
}

async function chooseCharacter(characterId) {
    if (!requireProfile()) return;
    try {
        const data = await fetchJson("/api/profile/character", {
            method: "POST",
            body: JSON.stringify({ token: token(), character_id: characterId }),
        });
        applyProfile(data.profile);
        renderCharacters(gameData, profile, chooseCharacter);
        renderCharacter(selectedCharacter, game.errors, "idle");
        showToast(`${CHARACTER_LIST.find((item) => item.id === characterId)?.name || "Personnage"} rejoint l’aventure !`);
    } catch (error) {
        showToast(error.message, "error");
    }
}

function updateRoundDisplay(data) {
    renderMask(data.masked || "");
    game.errors = Number(data.errors) || 0;
    renderAttempts(game.errors);
    updateGuesses(data.guessed_letters || [], [...game.correct]);
}

function handleProfileResult(nextProfile, match) {
    const previousStreak = profile?.current_streak || 0;
    const previousBadges = new Set(profile?.badges || []);
    applyProfile(nextProfile);
    game.lastProfileMatch = match || null;
    if ((nextProfile?.current_streak || 0) > previousStreak && nextProfile.current_streak >= 2) {
        audio.play("streak");
    }
    const newBadge = (nextProfile?.badges || []).find((badge) => !previousBadges.has(badge));
    if (newBadge) {
        const label = gameData.badges?.[newBadge] || "Nouveau succès";
        showToast(`Badge débloqué : ${label} !`);
    }
}

function showHumanResult(data) {
    game.finished = true;
    setGuessing(false);
    const won = data.winner === game.playerId;
    renderCharacter(selectedCharacter, game.errors, won ? "victory" : "defeat");
    audio.play(won ? "win" : "lose");
    const match = game.lastProfileMatch;
    showResult(
        {
            won,
            mode: "multiplayer",
            word: data.word,
            bot_name: data.winner_name,
            match,
            category: "Mot choisi par ton ami",
        },
        profile,
        celebrate,
    );
    $("result-title").textContent = won ? "Tu l’as trouvé !" : `${data.winner_name || "Ton ami"} remporte la manche`;
    $("result-subtitle").textContent = won
        ? "Ton instinct de devineur fait des merveilles."
        : "La revanche n’attend que vous deux.";
    $("next-round-btn").hidden = false;
    $("next-round-btn").textContent = "Demander la revanche";
}

async function createProfile(event) {
    event.preventDefault();
    const nickname = $("nickname-input").value.trim();
    try {
        const data = await fetchJson("/api/profile", {
            method: "POST",
            body: JSON.stringify({ nickname }),
        });
        saveToken(data.token);
        applyProfile(data.profile);
        setProfileSetup(false);
        renderCharacters(gameData, profile, chooseCharacter);
        renderAchievements(gameData, profile);
        showToast(`Bienvenue, ${profile.nickname} ! Ta légende commence.`);
    } catch (error) {
        showToast(error.message, "error");
        $("nickname-input").focus();
    }
}

function clearRoundForServerStart() {
    resetRoundState();
    $("next-round-btn").disabled = false;
}

$("profile-form").addEventListener("submit", createProfile);
$("start-bot-btn").addEventListener("click", () => beginBotGame("guess"));
$("start-duel-btn").addEventListener("click", () => beginBotGame("duel"));
$("join-room-btn").addEventListener("click", joinMultiplayerRoom);
$("leave-game-btn").addEventListener("click", leaveGame);
$("next-round-btn").addEventListener("click", nextRound);
$("result-home-btn").addEventListener("click", leaveGame);
$("copy-room-btn").addEventListener("click", async () => {
    const code = game.roomId || "";
    try {
        await navigator.clipboard.writeText(code);
    } catch {
        const field = document.createElement("textarea");
        field.value = code;
        document.body.append(field);
        field.select();
        document.execCommand("copy");
        field.remove();
    }
    showToast("Code de salle copié !");
});
$("hint-btn").addEventListener("click", () => {
    if (game.enabled && game.kind === "multiplayer" && game.localTurn) {
        setGuessing(false);
        socket.emit("use_hint", { room_id: game.roomId });
    } else if (game.kind === "bot" && game.mode === "guess" && game.enabled) {
        setGuessing(false);
        socket.emit("bot_hint");
    }
});
$("sound-toggle").addEventListener("click", () => {
    const muted = audio.toggle();
    $("sound-toggle").classList.toggle("sound-muted", muted);
    $("sound-toggle").setAttribute("aria-label", muted ? "Activer le son" : "Désactiver le son");
    if (!muted) audio.play("key");
});
$("volume-slider").value = String(Math.round(audio.volume * 100));
$("volume-slider").addEventListener("input", (event) => {
    audio.setVolume(Number(event.currentTarget.value) / 100);
    const muted = audio.muted;
    $("sound-toggle").classList.toggle("sound-muted", muted);
    $("sound-toggle").setAttribute("aria-label", muted ? "Activer le son" : "Désactiver le son");
    if (!muted) audio.play("key");
});
$("secret-word-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const word = $("secret-word-input").value.trim();
    if (game.kind === "multiplayer") {
        socket.emit("submit_word", { room_id: game.roomId, word });
    }
    $("secret-word-input").value = "";
});
$("duel-word-form").addEventListener("submit", (event) => {
    event.preventDefault();
    socket.emit("submit_bot_word", { word: $("duel-word-input").value.trim() });
    $("duel-word-input").value = "";
    $("round-message").textContent = "Le bot prépare ses calculs…";
});
$("chat-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const message = $("chat-input").value.trim();
    if (!message || game.kind !== "multiplayer" || !game.roomId) return;
    socket.emit("chat_message", { room_id: game.roomId, message });
    $("chat-input").value = "";
});
document.querySelectorAll("[data-close-dialog]").forEach((button) => {
    button.addEventListener("click", () => button.closest("dialog")?.close());
});
document.querySelectorAll("[data-open-panel]").forEach((button) => {
    button.addEventListener("click", () => {
        const panel = button.dataset.openPanel;
        if (panel === "home") {
            closeDialogs();
            if (game.kind) leaveGame();
            else setView("home");
            window.scrollTo({
                top: 0,
                behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
            });
        } else if (panel === "leaderboard") openLeaderboard();
        else if (panel === "characters" || panel === "profile") openCharacters();
        else if (panel === "achievements") openAchievements();
    });
});
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") return;
    if (event.ctrlKey || event.metaKey || event.altKey) return;
    const target = event.target;
    if (target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement || target?.isContentEditable) return;
    if (game.kind && game.enabled && /^[a-z]$/i.test(event.key)) {
        event.preventDefault();
        onGuess(event.key.toLocaleLowerCase("fr"));
    }
});
window.addEventListener("storage", (event) => {
    if (event.key === PROFILE_TOKEN_KEY) window.location.reload();
});

socket.on("connect", () => {
    $("sound-toggle").classList.toggle("sound-muted", audio.muted);
    if (hasConnectedBefore && reconnecting) {
        reconnecting = false;
        if (game.kind === "multiplayer" && game.roomId && profile) {
            socket.emit("join_game", {
                name: profile.nickname,
                token: token(),
                room_id: game.roomId,
            });
            showToast("Connexion rétablie. Tu rejoins ta salle…");
        } else if (game.kind === "bot") {
            game.kind = null;
            game.mode = null;
            setView("home");
            showToast("La manche solo a été interrompue. Relance un défi.");
        }
    }
    hasConnectedBefore = true;
});

socket.on("disconnect", () => {
    if (!hasConnectedBefore) return;
    reconnecting = true;
    showToast("Connexion perdue… nouvelle tentative en cours.", "error");
});

socket.on("connect_error", () => showToast("Le serveur est momentanément injoignable.", "error"));

socket.on("joined_game", (data) => {
    game.roomId = data.room_id;
    game.playerId = data.player_id;
    $("room-code").textContent = data.room_id;
    $("room-code-label").hidden = false;
    $("chat-form").hidden = false;
    $("game-title").textContent = "La salle est à toi";
    $("round-message").textContent = data.players?.length === 2
        ? "Les deux joueurs sont là. Que le meilleur devine !"
        : "Partage le code et attends ton adversaire…";
    const opponent = data.players?.find((player) => player.id !== data.player_id);
    setOpponent(null, opponent?.name || "En attente…", data.players?.length === 2 ? "Adversaire connecté" : "Partage le code de salle");
});

socket.on("player_joined", (data) => {
    setOpponent(null, data.name, "Prêt·e à jouer");
    showToast(`${data.name} a rejoint la salle !`);
});

socket.on("game_full", () => showToast("Cette salle contient déjà deux joueurs.", "error"));
socket.on("round_started", (data) => {
    closeDialogs();
    game.round = data.round;
    $("round-number").textContent = `MANCHE ${String(data.round).padStart(2, "0")}`;
    clearRoundForServerStart();
});

socket.on("your_turn_choose_word", () => {
    game.enabled = false;
    $("game-title").textContent = "Choisis un mot secret";
    $("round-message").textContent = "Choisis un mot malin, mais garde-le pour toi.";
    $("secret-word-form").hidden = false;
    $("secret-word-input").focus();
});
socket.on("waiting_for_opponent_word", (data) => {
    $("game-title").textContent = "Ton adversaire choisit un mot";
    $("round-message").textContent = `${data.name || "Ton ami"} prépare un défi…`;
});
socket.on("word_set", (data) => {
    $("secret-word-form").hidden = true;
    $("game-title").textContent = "Garde ton sang-froid";
    $("game-category").textContent = "Mot choisi par ton ami";
    updateRoundDisplay(data);
    $("round-message").textContent = "Devine le mot avant la dernière erreur !";
    renderCharacter(selectedCharacter, 0, "idle");
});
socket.on("your_turn_guess", () => {
    game.localTurn = true;
    setGuessing(true);
    $("hint-btn").hidden = false;
    $("round-message").textContent = "À toi : choisis une lettre.";
});
socket.on("opponent_turn", () => {
    game.localTurn = false;
    setGuessing(false);
    $("hint-btn").hidden = true;
    $("round-message").textContent = "Ton adversaire réfléchit à une lettre…";
});
socket.on("correct_guess", (data) => {
    game.correct.add(data.letter);
    updateRoundDisplay(data);
    renderCharacter(selectedCharacter, game.errors, "good");
    $("round-message").textContent = `Bien vu ! La lettre ${data.letter.toLocaleUpperCase("fr")} est dans le mot.`;
    audio.play("good");
    setGuessing(game.kind !== "multiplayer" || game.localTurn);
});
socket.on("hint_used", (data) => {
    game.correct.add(data.letter);
    updateRoundDisplay(data);
    renderCharacter(selectedCharacter, game.errors, "good", "Joker utilisé ! Le streak ne progresse pas.");
    audio.play("hint");
    $("round-message").textContent = `Joker : la lettre ${data.letter.toLocaleUpperCase("fr")} est révélée.`;
    setGuessing(game.kind !== "multiplayer" || game.localTurn);
});
socket.on("wrong_guess", (data) => {
    updateRoundDisplay(data);
    const mood = game.errors >= 7 ? "panic" : "wrong";
    renderCharacter(selectedCharacter, game.errors, mood, null, true);
    $("round-message").textContent = game.errors >= 7
        ? "Dernière chance ! Trouve la lettre qui sauvera la manche."
        : "Oups ! Essaie une autre lettre.";
    audio.play("wrong");
    setGuessing(game.kind !== "multiplayer" || game.localTurn);
});
socket.on("game_over", (data) => showHumanResult(data));
socket.on("profile_updated", (data) => handleProfileResult(data.profile, data.match));
socket.on("rematch_waiting", () => {
    $("next-round-btn").disabled = true;
    $("round-message").textContent = "En attente de la réponse de ton adversaire…";
    showToast("Demande de revanche envoyée.");
});
socket.on("opponent_wants_rematch", (data) => {
    $("next-round-btn").disabled = false;
    $("result-subtitle").textContent = `${data.name} veut sa revanche. À toi d’accepter !`;
    $("next-round-btn").textContent = "Accepter la revanche";
});
socket.on("opponent_left", () => {
    game.enabled = false;
    $("opponent-name").textContent = "En attente…";
    $("opponent-description").textContent = "L’adversaire a quitté la salle";
    $("game-title").textContent = "La salle est toujours ouverte";
    $("round-message").textContent = "Ton adversaire est parti. Un ami peut rejoindre avec le même code.";
    renderKeyboard([...game.guessed], [...game.correct], false, onGuess);
    showToast("Ton adversaire a quitté la salle.");
});

socket.on("bot_game_started", (data) => {
    game.botId = data.bot_id;
    game.botName = data.bot_name;
    game.round = data.round;
    $("round-number").textContent = `MANCHE ${String(data.round).padStart(2, "0")}`;
    $("game-mode-label").textContent = data.mode === "duel" ? "DUEL BOT" : "SOLO VS BOT";
    $("game-category").textContent = data.category;
    $("game-difficulty").textContent = DIFFICULTY_LABELS[data.difficulty] || "SURPRISE";
    $("game-title").textContent = data.mode === "duel" ? "Deux mots. Un seul vainqueur." : "Garde ton sang-froid";
    setOpponent(data.bot_id, data.bot_name, gameData.bots.find((bot) => bot.id === data.bot_id)?.description);
    showChatLine(data.bot_name, data.chat);
    renderCharacter(selectedCharacter, 0, "idle");
    if (data.mode === "guess") {
        updateRoundDisplay(data);
        game.localTurn = true;
        game.enabled = true;
        $("hint-btn").hidden = false;
        $("round-message").textContent = "Le mot est secret. Fais parler ton instinct.";
        setGuessing(true);
    } else {
        $("duel-word-form").hidden = true;
        $("round-message").textContent = "Choisis le mot que le bot devra deviner.";
        $("keyboard").setAttribute("aria-disabled", "true");
    }
});
socket.on("bot_word_required", () => {
    $("duel-word-form").hidden = false;
    $("duel-word-input").focus();
});
socket.on("bot_duel_started", (data) => {
    $("duel-word-form").hidden = true;
    $("bot-progress-box").hidden = false;
    $("bot-word-mask").textContent = data.bot_mask;
    $("bot-errors-label").textContent = "8 essais";
    updateRoundDisplay(data);
    showChatLine(game.botName, data.chat);
    $("round-message").textContent = "Devine son mot avant que le bot trouve le tien !";
    game.localTurn = true;
    setGuessing(true);
});
socket.on("bot_guess_result", (data) => {
    if (data.correct) game.correct.add(data.letter);
    updateRoundDisplay(data);
    game.enabled = true;
    renderCharacter(selectedCharacter, game.errors, data.correct ? "good" : game.errors >= 7 ? "panic" : "wrong", null, !data.correct);
    $("round-message").textContent = data.correct ? "Bonne pioche ! Continue." : "Raté ! Une chance en moins.";
    showChatLine(game.botName, data.chat);
    audio.play(data.correct ? "good" : "wrong");
    setGuessing(true);
});
socket.on("bot_hint_result", (data) => {
    game.correct.add(data.letter);
    updateRoundDisplay(data);
    game.enabled = true;
    $("round-message").textContent = `Joker utilisé : la lettre ${data.letter.toLocaleUpperCase("fr")} est révélée.`;
    renderCharacter(selectedCharacter, game.errors, "good", "Joker activé ! Le streak repart à zéro.");
    audio.play("hint");
    setGuessing(true);
});
socket.on("bot_duel_player_guess", (data) => {
    if (data.correct) game.correct.add(data.letter);
    updateRoundDisplay(data);
    game.enabled = false;
    renderCharacter(selectedCharacter, game.errors, data.correct ? "good" : game.errors >= 7 ? "panic" : "wrong", null, !data.correct);
    $("round-message").textContent = data.correct ? "Bonne lettre ! Le bot se prépare à répondre…" : "Raté ! Le bot joue son tour…";
    audio.play(data.correct ? "good" : "wrong");
    renderKeyboard([...game.guessed], [...game.correct], false, onGuess);
});
socket.on("bot_duel_update", (data) => {
    $("bot-word-mask").textContent = data.bot_mask;
    $("bot-errors-label").textContent = `${Math.max(0, 8 - data.bot_errors)} essais`;
    showChatLine(game.botName, `${data.chat} (${data.letter.toUpperCase()})`);
    audio.play(data.correct ? "good" : "wrong");
    $("round-message").textContent = "À toi de jouer !";
    setGuessing(true);
});
socket.on("bot_game_over", (data) => {
    game.finished = true;
    game.enabled = false;
    if (data.profile) handleProfileResult(data.profile, data.match);
    const won = Boolean(data.won);
    renderCharacter(selectedCharacter, game.errors, won ? "victory" : "defeat");
    $("hint-btn").hidden = true;
    audio.play(won ? "win" : "lose");
    showChatLine(data.bot_name, data.chat);
    showResult(data, profile, celebrate);
});

socket.on("chat_message", (data) => showChatLine(data.name || "Joueur", data.message, data.name === profile?.nickname));
socket.on("bot_chat", (data) => showChatLine(data.name || game.botName, data.message));
socket.on("error", (data) => {
    showToast(data?.msg || "Une erreur est survenue.", "error");
    if (game.kind === "bot" && !game.finished && game.mode === "guess") {
        setGuessing(true);
    } else if (game.kind === "bot" && !game.finished && game.mode === "duel" && !reconnecting) {
        setGuessing(true);
    } else if (game.kind === "multiplayer" && !game.finished && game.localTurn) {
        setGuessing(true);
    }
    if (game.kind === "bot" && !game.round) setView("home");
});

const savedMuted = localStorage.getItem("motus-maximus-muted") === "true";
$("sound-toggle").classList.toggle("sound-muted", savedMuted || audio.volume === 0);
$("sound-toggle").setAttribute("aria-label", savedMuted || audio.volume === 0 ? "Activer le son" : "Désactiver le son");
renderCharacter("pirate", 0, "idle", "Le dictionnaire tremble déjà.");
renderHeroCharacter("pirate");
renderAttempts(0);
loadGameData().then(() => {
    if (profile) {
        renderCharacters(gameData, profile, chooseCharacter);
        renderAchievements(gameData, profile);
    }
});
loadProfile().then(() => {
    if (profile) {
        renderCharacters(gameData, profile, chooseCharacter);
        renderAchievements(gameData, profile);
    }
});
