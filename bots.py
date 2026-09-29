"""Bot personalities, word selection and pattern-based letter strategy."""

from __future__ import annotations

import random
import unicodedata
from dataclasses import dataclass
from typing import Iterable

from words import CATALOG, choose_word, normalize_word


@dataclass(frozen=True)
class Bot:
    id: str
    name: str
    difficulty: str
    description: str
    mistake_rate: float
    delay_seconds: tuple[float, float]
    taunts: tuple[str, ...]


BOTS = {
    "beginner": Bot(
        "beginner",
        "Léo Lapsus",
        "easy",
        "Débutant — mots courts et très courants",
        0.22,
        (1.4, 2.8),
        (
            "J’ai choisi un mot… enfin, je crois.",
            "Mon cerveau vient de faire une petite sieste.",
            "Même mon grille-pain aurait trouvé ça !",
            "Je réfléchis très fort. Ça se voit ?",
            "Oups, j’ai peut-être cliqué avec mon coude.",
        ),
    ),
    "clever": Bot(
        "clever",
        "Mina Maligne",
        "medium",
        "Malin — vocabulaire varié et stratégie correcte",
        0.12,
        (1.1, 2.3),
        (
            "J’ai un plan. Il est écrit sur un post-it.",
            "Tu ne trouveras jamais… enfin, probablement.",
            "Je garde mon meilleur mot pour la fin.",
            "Les voyelles me racontent tout.",
            "J’ai révisé dans un dictionnaire. Presque.",
        ),
    ),
    "expert": Bot(
        "expert",
        "Professeur Phosphore",
        "hard",
        "Expert — mots longs et vocabulaire soutenu",
        0.07,
        (0.9, 1.9),
        (
            "Une excellente hypothèse, mais non.",
            "La lexicographie est mon sport préféré.",
            "Je sens une consonne se cacher.",
            "Ce mot est parfaitement raisonnable. Pour moi.",
            "Petit indice : j’ai choisi avec beaucoup trop de soin.",
        ),
    ),
    "nightmare": Bot(
        "nightmare",
        "Docteure Panique",
        "nightmare",
        "Cauchemar — mots rares et lettres piégeuses",
        0.035,
        (0.8, 1.7),
        (
            "J’espère que tu aimes les lettres silencieuses.",
            "Ce mot a demandé un permis de sortie du dictionnaire.",
            "Une lettre rare ? Je n’en vois aucune. Enfin, presque.",
            "J’ai choisi ce mot en riant. Un peu.",
            "Respire. Le dictionnaire, lui, ne le fera pas.",
        ),
    ),
    "boss": Bot(
        "boss",
        "Le Grand Lexicobot",
        "nightmare",
        "Boss final — piège surprise tous les 10 duels",
        0.015,
        (0.65, 1.45),
        (
            "Le dictionnaire m’a confié ses secrets.",
            "Dixième duel ? J’ai justement un petit piège.",
            "Je ne triche pas. Je suis juste très bien entraîné.",
            "Ce silence ? C’est le bruit de ta stratégie qui chauffe.",
            "Un mot, huit erreurs possibles, zéro pitié… ludique !",
        ),
    ),
}

FRENCH_LETTER_FREQUENCY = "esaitnrulodcmpvgbfqhjxyzkw"
RARE_ERROR_LETTERS = "kwxyzjq"
ALPHABET = "abcdefghijklmnopqrstuvwxyz"


def available_bots() -> list[dict]:
    return [
        {
            "id": bot.id,
            "name": bot.name,
            "difficulty": bot.difficulty,
            "description": bot.description,
        }
        for bot in BOTS.values()
    ]


def _graphemes(word: str) -> list[str]:
    """Split NFC French text into letter clusters so œ stays one game position."""
    result: list[str] = []
    for character in unicodedata.normalize("NFC", word):
        if unicodedata.category(character).startswith("M") and result:
            result[-1] += character
        else:
            result.append(character)
    return result


def grapheme_key(grapheme: str) -> str:
    return normalize_word(grapheme)


def _rng_choice(rng, choices):
    return rng.choice(choices)


def choose_bot_word(
    bot_id: str,
    duel_count: int = 1,
    recent_words: Iterable[str] = (),
    *,
    rng=random,
    catalog: Iterable[dict] = CATALOG,
) -> dict:
    """Choose a difficulty-matched secret; the boss uses a trap every 10 duels."""
    bot = BOTS.get(bot_id)
    if bot is None:
        raise ValueError("Bot inconnu.")
    catalog = list(catalog)
    recent = {normalize_word(word) for word in recent_words}

    if bot_id == "boss" and duel_count > 0 and duel_count % 10 == 0:
        traps = [
            entry
            for entry in catalog
            if entry.get("trap")
            and entry["difficulty"] == "nightmare"
            and entry["normalized"] not in recent
        ]
        if traps:
            return _rng_choice(rng, traps)
    elif bot_id == "boss":
        catalog = [entry for entry in catalog if not entry.get("trap")]

    return choose_word(
        bot.difficulty,
        recent_words=recent,
        rng=rng,
        catalog=catalog,
    )


def _candidate_graphemes(
    entry: dict,
    pattern: list[str | None],
    guessed: set[str],
) -> list[str] | None:
    letters = _graphemes(entry["word"])
    if len(letters) != len(pattern):
        return None

    keys = [grapheme_key(letter) for letter in letters]
    for index, shown in enumerate(pattern):
        if shown is not None:
            if keys[index] != grapheme_key(shown):
                return None
        elif any(letter in keys[index] for letter in guessed):
            return None
    return keys


def choose_guess(
    pattern: list[str | None],
    guessed_letters: Iterable[str] = (),
    *,
    bot_id: str = "expert",
    rng=random,
    catalog: Iterable[dict] = CATALOG,
) -> str:
    """Filter dictionary candidates by visible pattern, then use letter frequency."""
    bot = BOTS.get(bot_id)
    if bot is None:
        raise ValueError("Bot inconnu.")
    guessed = {normalize_word(letter) for letter in guessed_letters}
    guessed = {letter for letter in guessed if len(letter) == 1}
    normalized_pattern = [
        None if letter is None or letter == "_" else grapheme_key(letter)
        for letter in pattern
    ]

    candidates = []
    for entry in catalog:
        keys = _candidate_graphemes(entry, normalized_pattern, guessed)
        if keys is not None:
            candidates.append(keys)

    possible = set(ALPHABET) - guessed
    if not possible:
        raise LookupError("Le bot a épuisé les lettres disponibles.")

    # A deliberate occasional mistake chooses a rare but still untried letter.
    if rng.random() < bot.mistake_rate:
        rare = [letter for letter in RARE_ERROR_LETTERS if letter in possible]
        return _rng_choice(rng, rare or sorted(possible))

    counts = {letter: 0 for letter in possible}
    for word in candidates:
        for key in word:
            for letter in key:
                if letter in counts:
                    counts[letter] += 1

    best_count = max(counts.values(), default=0)
    if best_count == 0:
        # No matching dictionary entry: fall back to broad French frequencies.
        ranked = [letter for letter in FRENCH_LETTER_FREQUENCY if letter in possible]
        return ranked[0] if ranked else sorted(possible)[0]
    best = [letter for letter, count in counts.items() if count == best_count]
    order = {letter: index for index, letter in enumerate(FRENCH_LETTER_FREQUENCY)}
    best.sort(key=lambda letter: order.get(letter, len(order)))
    return best[0]


def bot_delay(bot_id: str, *, rng=random) -> float:
    bot = BOTS.get(bot_id)
    if bot is None:
        raise ValueError("Bot inconnu.")
    return rng.uniform(*bot.delay_seconds)


def bot_line(bot_id: str, *, rng=random) -> str:
    bot = BOTS.get(bot_id)
    if bot is None:
        raise ValueError("Bot inconnu.")
    return _rng_choice(rng, bot.taunts)
