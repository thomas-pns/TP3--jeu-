import { CHARACTER_LIST, characterQuote, characterSvg } from "./characters.js";
import { botAvatarSvg } from "./bots.js";

export const $ = (id) => document.getElementById(id);

export function setView(name) {
    const home = $("home-view");
    const game = $("game-view");
    const isGame = name === "game";
    home.hidden = isGame;
    game.hidden = !isGame;
    home.classList.toggle("active", !isGame);
    game.classList.toggle("active", isGame);
    document.querySelectorAll(".nav-button").forEach((button) => {
        button.classList.toggle("active", button.dataset.openPanel === "home" && !isGame);
    });
    if (isGame) {
        const behavior = matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
        window.scrollTo({ top: 0, behavior });
    }
}

export function showToast(message, kind = "info") {
    const region = $("toast-region");
    const item = document.createElement("div");
    item.className = `toast ${kind === "error" ? "error" : ""}`;
    item.textContent = message;
    region.append(item);
    window.setTimeout(() => item.remove(), 3600);
}

export function setProfileSetup(show) {
    $("profile-setup").hidden = !show;
    $("start-bot-btn").disabled = show;
    $("start-duel-btn").disabled = show;
    $("join-room-btn").disabled = show;
    if (show) window.setTimeout(() => $("nickname-input").focus(), 100);
}

export function updateProfile(profile) {
    if (!profile) return;
    const rank = profile.rank || {};
    const next = rank.xp_next;
    $("profile-name").textContent = profile.nickname;
    $("profile-avatar").textContent = [...profile.nickname][0]?.toLocaleUpperCase("fr") || "?";
    $("profile-rank").textContent = rank.name || "Apprenti";
    $("hero-caption-name").textContent =
        CHARACTER_LIST.find((character) => character.id === profile.selected_character)?.name || "Capitaine Moustache";
    $("rank-title").textContent = rank.name || "Apprenti";
    $("rank-next").textContent = next === null ? "Rang maximum" : `Prochain : ${rank.next_name}`;
    $("xp-current").textContent = `${profile.xp || 0} XP`;
    $("xp-target").textContent = next === null ? "MAX" : `${next} XP`;
    $("xp-progress").style.width = `${Math.round((rank.progress || 0) * 100)}%`;
    $("best-streak").textContent = profile.best_streak || 0;
    $("total-score").textContent = profile.total_score || 0;
    $("total-wins").textContent = profile.wins || 0;

    const streak = $("streak-flame");
    if (profile.current_streak > 0) {
        streak.hidden = false;
        $("streak-count").textContent = `×${profile.current_streak}`;
        const flameScale = 1 + Math.min(profile.current_streak, 12) * 0.025;
        streak.style.setProperty("--flame-grow", String(flameScale));
        if (profile.current_streak >= 5) streak.classList.add("streak-hot");
        else streak.classList.remove("streak-hot");
    } else {
        streak.hidden = true;
    }
}

export function renderHeroCharacter(characterId) {
    $("hero-character").innerHTML = characterSvg(characterId, { mood: "idle" });
}

export function renderCharacter(characterId, errors, mood = "idle", message = null, stageError = false) {
    const stage = $("character-stage");
    stage.dataset.errors = String(errors);
    stage.dataset.mood = mood;
    const character = CHARACTER_LIST.find((item) => item.id === characterId) || CHARACTER_LIST[0];
    $("character-art").innerHTML = characterSvg(character.id, {
        errors,
        mood,
        withGallows: true,
        stageError,
    });
    $("character-bubble").textContent = message || characterQuote(character.id, mood);

    if (stageError) {
        stage.classList.remove("is-shaking");
        void stage.offsetWidth;
        stage.classList.add("is-shaking");
        window.setTimeout(() => stage.classList.remove("is-shaking"), 400);
    }
}

export function renderMask(masked) {
    const word = $("word-mask");
    word.replaceChildren();
    const letters = String(masked || "").trim().split(/\s+/).filter(Boolean);
    $("word-length-label").textContent = `${letters.length} LETTRE${letters.length === 1 ? "" : "S"}`;
    word.setAttribute("aria-label", letters.map((letter) => letter === "_" ? "lettre cachée" : letter).join(" "));
    letters.forEach((letter, index) => {
        const span = document.createElement("span");
        span.className = `word-letter ${letter === "_" ? "is-hidden" : "is-revealed"}`;
        span.textContent = letter === "_" ? "•" : letter;
        span.setAttribute("aria-hidden", "true");
        span.style.animationDelay = `${Math.min(index, 12) * 18}ms`;
        word.append(span);
    });
}

export function renderAttempts(errors, maxErrors = 8) {
    const left = Math.max(0, maxErrors - errors);
    $("attempts-label").textContent = `${left} ${left === 1 ? "chance" : "chances"} restante${left === 1 ? "" : "s"}`;
    $("attempt-pips").setAttribute("aria-label", `${left} tentatives restantes`);
    $("attempt-pips").replaceChildren(
        ...Array.from({ length: maxErrors }, (_, index) => {
            const pip = document.createElement("span");
            pip.className = `attempt-pip ${index >= left ? "spent" : ""}`;
            pip.setAttribute("aria-hidden", "true");
            return pip;
        }),
    );
}

export function renderKeyboard(guessed = [], correct = [], enabled = false, onGuess = () => {}) {
    const keyboard = $("keyboard");
    const guessedSet = new Set(guessed);
    const correctSet = new Set(correct);
    keyboard.replaceChildren();
    for (const letter of "abcdefghijklmnopqrstuvwxyz") {
        const button = document.createElement("button");
        button.type = "button";
        button.className = `key-button ${correctSet.has(letter) ? "correct" : guessedSet.has(letter) ? "wrong" : ""}`;
        button.textContent = letter;
        button.setAttribute("aria-label", `Proposer la lettre ${letter}`);
        button.disabled = !enabled || guessedSet.has(letter);
        button.addEventListener("click", () => onGuess(letter));
        keyboard.append(button);
    }
}

export function renderBotOptions(bots, selectedId, onSelect) {
    const grid = $("bot-grid");
    grid.replaceChildren();
    bots.forEach((bot) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = `bot-option ${bot.id === selectedId ? "selected" : ""}`;
        button.dataset.botId = bot.id;
        button.setAttribute("aria-pressed", String(bot.id === selectedId));
        button.setAttribute("aria-label", `${bot.name}. ${bot.description}`);
        button.innerHTML = `${botAvatarSvg(bot.id, true)}<strong></strong><small></small><span class="bot-selected-check" aria-hidden="true">✓</span>`;
        button.querySelector("strong").textContent = bot.name;
        button.querySelector("small").textContent = bot.id === "boss"
            ? "BOSS FINAL"
            : ({ easy: "DOUCEUR", medium: "MALIN", hard: "EXPERT", nightmare: "CAUCHEMAR" })[bot.difficulty] || "BOSS";
        button.title = bot.description;
        button.addEventListener("click", () => onSelect(bot.id));
        grid.append(button);
    });
}

export function selectBotOption(botId) {
    document.querySelectorAll(".bot-option").forEach((button) => {
        const selected = button.dataset.botId === botId;
        button.classList.toggle("selected", selected);
        button.setAttribute("aria-pressed", String(selected));
    });
}

export function renderCharacters(gameData, profile, onChoose) {
    const collection = $("character-collection");
    collection.replaceChildren();
    const unlocked = new Set(profile?.unlocked_characters || ["pirate"]);
    for (const character of gameData.characters || []) {
        const isUnlocked = unlocked.has(character.id);
        const card = document.createElement("article");
        card.className = `character-card ${isUnlocked ? "" : "locked"} ${profile?.selected_character === character.id ? "selected" : ""}`;
        card.innerHTML = `${characterSvg(character.id, { mood: "idle" })}<strong></strong><small></small><button type="button"></button>`;
        card.querySelector("strong").textContent = character.name;
        card.querySelector("small").textContent = isUnlocked
            ? (CHARACTER_LIST.find((item) => item.id === character.id)?.title || "Personnage")
            : `À débloquer : série de ${character.streak_required} victoires`;
        const button = card.querySelector("button");
        button.textContent = isUnlocked
            ? (profile?.selected_character === character.id ? "Sélectionné ✓" : "Choisir")
            : "Verrouillé";
        button.disabled = !isUnlocked || profile?.selected_character === character.id;
        button.addEventListener("click", () => onChoose(character.id));
        collection.append(card);
    }
}

const ACHIEVEMENT_INFO = {
    first_win: ["🏁", "Ta première victoire", "Remporte une manche, quel que soit le mode."],
    ten_wins: ["🏆", "Collectionneur de victoires", "Gagne dix manches."],
    streak_10: ["🔥", "Inarrêtable", "Enchaîne dix victoires sans perdre."],
    nightmare_perfect: ["🧠", "Cauchemar sans faute", "Trouve un mot cauchemar sans erreur ni joker."],
    last_chance: ["😅", "À un cheveu du pendu", "Gagne avec une seule chance restante."],
};

export function renderAchievements(gameData, profile) {
    const list = $("achievement-list");
    list.replaceChildren();
    const unlocked = new Set(profile?.badges || []);
    for (const [id, label] of Object.entries(gameData.badges || {})) {
        const [icon, title, description] = ACHIEVEMENT_INFO[id] || ["✦", label, "Un exploit à découvrir."];
        const item = document.createElement("div");
        item.className = `achievement-item ${unlocked.has(id) ? "" : "locked"}`;
        item.innerHTML = `<span class="achievement-icon"></span><span><strong></strong><small></small></span><span class="achievement-status"></span>`;
        item.querySelector(".achievement-icon").textContent = icon;
        item.querySelector("strong").textContent = title || label;
        item.querySelector("small").textContent = description;
        item.querySelector(".achievement-status").textContent = unlocked.has(id) ? "OBTENU" : "À DÉBLOQUER";
        list.append(item);
    }
}

export function renderLeaderboard(players) {
    const list = $("leaderboard-list");
    list.replaceChildren();
    if (!players?.length) {
        const empty = document.createElement("li");
        empty.className = "empty-state";
        empty.textContent = "Pas encore de légendes. Le trône est à prendre !";
        list.append(empty);
        return;
    }
    players.forEach((player, index) => {
        const row = document.createElement("li");
        row.className = "leaderboard-row";
        row.innerHTML = `<span class="leader-rank"></span><strong class="leader-name"></strong><span class="leader-streak"></span><span class="leader-score"></span>`;
        row.querySelector(".leader-rank").textContent = ["①", "②", "③"][index] || String(index + 1);
        row.querySelector(".leader-name").textContent = player.nickname;
        row.querySelector(".leader-streak").textContent = `🔥 ${player.best_streak}`;
        row.querySelector(".leader-score").textContent = `${player.total_score} pts`;
        list.append(row);
    });
}

export function appendChat(author, message, player = false) {
    const log = $("chat-log");
    log.querySelector(".chat-empty")?.remove();
    const line = document.createElement("div");
    line.className = `chat-line ${player ? "player-line" : ""}`;
    const name = document.createElement("strong");
    name.textContent = author;
    const text = document.createElement("span");
    text.textContent = message;
    line.append(name, text);
    log.append(line);
    while (log.children.length > 35) log.firstElementChild.remove();
    $("chat-count").textContent = String(log.children.length);
    log.scrollTop = log.scrollHeight;
}

export function clearChat() {
    const log = $("chat-log");
    log.innerHTML = `<p class="chat-empty">Les meilleures punchlines arrivent…</p>`;
    $("chat-count").textContent = "0";
}

export function showDialog(id) {
    const dialog = $(id);
    if (dialog && !dialog.open) dialog.showModal();
}

export function closeDialogs() {
    document.querySelectorAll("dialog[open]").forEach((dialog) => dialog.close());
}

export function showResult(data, profile, onConfetti = () => {}) {
    const dialog = $("result-dialog");
    const won = Boolean(data.won);
    dialog.classList.toggle("loss", !won);
    $("result-icon").textContent = won ? "✦" : "☁";
    $("result-kicker").textContent = won ? "VICTOIRE !" : "MANCHE TERMINÉE";
    $("result-title").textContent = won ? "Quel talent !" : "Bien tenté !";
    $("result-subtitle").textContent = data.bot_name
        ? (won ? `${data.bot_name} est impressionné·e. La légende grandit !` : `${data.bot_name} garde le sourire. La revanche t’attend.`)
        : (won ? "Ton adversaire n’a rien vu venir." : "Une manche de plus pour aiguiser ton instinct.");
    $("result-word").textContent = data.word || "—";
    $("result-definition").textContent = data.definition || (data.category ? `Catégorie : ${data.category}` : "");
    $("result-points").textContent = `+${data.match?.score || 0}`;
    $("result-streak").textContent = profile?.current_streak ?? data.match?.streak ?? 0;
    $("result-rank").textContent = profile?.rank?.name || "Apprenti";
    $("next-round-btn").hidden = false;
    $("next-round-btn").textContent = data.mode === "multiplayer"
        ? "Demander la revanche"
        : data.mode === "duel" ? "Rejouer le duel" : "Manche suivante";
    if (!dialog.open) dialog.showModal();
    if (won) onConfetti();
}

export function celebrate() {
    const holder = $("result-dialog").querySelector(".result-confetti");
    holder.replaceChildren();
    const colors = ["#a68bff", "#7ee7db", "#ffc970", "#ff8aa8", "#f7f4ff"];
    for (let index = 0; index < 42; index += 1) {
        const bit = document.createElement("span");
        bit.className = "confetti-bit";
        bit.style.left = `${Math.random() * 100}%`;
        bit.style.background = colors[index % colors.length];
        bit.style.animationDelay = `${Math.random() * .8}s`;
        bit.style.setProperty("--drift", `${Math.round(Math.random() * 120 - 60)}px`);
        holder.append(bit);
    }
}
