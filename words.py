"""French word catalogue, validation and accent-insensitive lookup helpers."""

from __future__ import annotations

import json
import random
import unicodedata
from pathlib import Path
from typing import Iterable


CATALOG_PATH = Path(__file__).with_name("mots.json")
DIFFICULTIES = ("easy", "medium", "hard", "nightmare")
DIFFICULTY_LABELS = {
    "easy": "Facile",
    "medium": "Moyen",
    "hard": "Difficile",
    "nightmare": "Cauchemar",
}
MIN_WORD_LENGTH = 3
MAX_WORD_LENGTH = 30


def normalize_word(value: str) -> str:
    """Fold French accents for matching while keeping the displayed word intact."""
    if not isinstance(value, str):
        return ""
    folded = value.casefold().replace("œ", "oe").replace("æ", "ae")
    decomposed = unicodedata.normalize("NFKD", folded)
    return "".join(
        character
        for character in decomposed
        if not unicodedata.category(character).startswith("M")
    )


def validate_word(value: str) -> str:
    """Return a cleaned NFC display form, or raise ValueError for invalid input."""
    if not isinstance(value, str):
        raise ValueError("Le mot doit être une chaîne de caractères.")
    word = unicodedata.normalize("NFC", value.strip())
    if not MIN_WORD_LENGTH <= len(word) <= MAX_WORD_LENGTH:
        raise ValueError(
            f"Le mot doit contenir de {MIN_WORD_LENGTH} à {MAX_WORD_LENGTH} lettres."
        )
    for character in word:
        if not unicodedata.category(character).startswith("L"):
            raise ValueError("Utilise uniquement des lettres, sans espace ni chiffre.")
        if "LATIN" not in unicodedata.name(character, ""):
            raise ValueError("Seules les lettres de l’alphabet latin sont acceptées.")
    return word


def _as_words(raw_words: str | list[str]) -> list[str]:
    if isinstance(raw_words, str):
        return raw_words.split()
    if isinstance(raw_words, list) and all(isinstance(word, str) for word in raw_words):
        return raw_words
    raise ValueError("Une catégorie doit contenir une liste de mots.")


def load_catalog(path: Path | str = CATALOG_PATH) -> list[dict]:
    """Flatten mots.json into unique, validated word records."""
    source = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    definitions = source.get("definitions", {})
    traps = {normalize_word(word) for word in source.get("trap_words", [])}
    levels = source.get("levels")
    if not isinstance(levels, dict):
        raise ValueError("mots.json doit contenir l’objet « levels ».")

    catalog = []
    seen = set()
    for difficulty in DIFFICULTIES:
        level = levels.get(difficulty, {})
        for category, raw_words in level.get("categories", {}).items():
            for raw_word in _as_words(raw_words):
                word = validate_word(raw_word)
                normalized = normalize_word(word)
                if normalized in seen:
                    continue
                seen.add(normalized)
                catalog.append(
                    {
                        "word": word,
                        "normalized": normalized,
                        "difficulty": difficulty,
                        "category": category,
                        "definition": definitions.get(normalized)
                        or definitions.get(word.casefold()),
                        "trap": normalized in traps,
                    }
                )

    if not catalog:
        raise ValueError("Le dictionnaire français est vide.")
    return catalog


CATALOG = load_catalog()


def words_for(
    difficulty: str | None = None,
    category: str | None = None,
    *,
    catalog: Iterable[dict] = CATALOG,
) -> list[dict]:
    return [
        entry
        for entry in catalog
        if (difficulty is None or entry["difficulty"] == difficulty)
        and (category is None or entry["category"] == category)
    ]


def choose_word(
    difficulty: str,
    recent_words: Iterable[str] = (),
    category: str | None = None,
    *,
    rng=random,
    catalog: Iterable[dict] = CATALOG,
) -> dict:
    """Pick an unused word at a requested level; never silently repeat a recent one."""
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"Difficulté inconnue : {difficulty}")
    recent = {normalize_word(word) for word in recent_words}
    candidates = [
        entry
        for entry in catalog
        if entry["difficulty"] == difficulty
        and (category is None or entry["category"] == category)
        and entry["normalized"] not in recent
    ]
    if not candidates:
        raise LookupError("Tous les mots de cette difficulté ont été joués récemment.")
    return rng.choice(candidates)
