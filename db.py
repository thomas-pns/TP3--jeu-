"""SQLite-backed player profiles, progression, achievements and leaderboard."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from scoring import calculate_score, rank_for_xp


DEFAULT_DB_PATH = Path(
    os.environ.get(
        "DATABASE_PATH",
        Path(__file__).with_name("instance") / "pendu.sqlite3",
    )
)

CHARACTERS = (
    {"id": "pirate", "name": "Capitaine Moustache", "streak_required": 0},
    {"id": "chef", "name": "Chef Patatras", "streak_required": 2},
    {"id": "mummy", "name": "Momie Biscotte", "streak_required": 3},
    {"id": "astronaut", "name": "Astro-Biscuit", "streak_required": 5},
    {"id": "robot", "name": "Bip le robot", "streak_required": 7},
    {"id": "knight", "name": "Sir Gribouille", "streak_required": 10},
)

BADGES = {
    "first_win": "Première victoire",
    "ten_wins": "Collectionneur de victoires",
    "streak_10": "Inarrêtable",
    "nightmare_perfect": "Cauchemar sans faute",
    "last_chance": "À un cheveu du pendu",
}


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def validate_nickname(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("Le pseudo doit être du texte.")
    nickname = " ".join(value.split())
    if not 1 <= len(nickname) <= 20:
        raise ValueError("Le pseudo doit contenir entre 1 et 20 caractères.")
    if any(not (character.isalnum() or character in " _-") for character in nickname):
        raise ValueError("Le pseudo contient un caractère non autorisé.")
    return nickname


class Database:
    """Small connection-per-operation SQLite store; suitable for one app worker."""

    def __init__(self, path: str | Path = DEFAULT_DB_PATH):
        self.path = Path(path)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def init(self) -> None:
        with self._connection() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_hash TEXT NOT NULL UNIQUE,
                    nickname TEXT NOT NULL,
                    xp INTEGER NOT NULL DEFAULT 0,
                    total_score INTEGER NOT NULL DEFAULT 0,
                    matches INTEGER NOT NULL DEFAULT 0,
                    wins INTEGER NOT NULL DEFAULT 0,
                    current_streak INTEGER NOT NULL DEFAULT 0,
                    best_streak INTEGER NOT NULL DEFAULT 0,
                    badges_json TEXT NOT NULL DEFAULT '[]',
                    unlocked_json TEXT NOT NULL DEFAULT '["pirate"]',
                    selected_character TEXT NOT NULL DEFAULT 'pirate',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(players)")
            }
            if "matches" not in columns:
                connection.execute(
                    "ALTER TABLE players ADD COLUMN matches INTEGER NOT NULL DEFAULT 0"
                )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS players_leaderboard "
                "ON players(best_streak DESC, total_score DESC)"
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS bot_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
                    bot_id TEXT NOT NULL,
                    normalized_word TEXT NOT NULL,
                    played_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS bot_history_recent "
                "ON bot_history(player_id, bot_id, id DESC)"
            )

    @staticmethod
    def _public_profile(row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
            "nickname": row["nickname"],
            "xp": row["xp"],
            "total_score": row["total_score"],
            "matches": row["matches"],
            "wins": row["wins"],
            "current_streak": row["current_streak"],
            "best_streak": row["best_streak"],
            "badges": json.loads(row["badges_json"]),
            "unlocked_characters": json.loads(row["unlocked_json"]),
            "selected_character": row["selected_character"],
            "rank": rank_for_xp(row["xp"]),
        }

    def create_profile(self, nickname: object) -> tuple[str, dict]:
        clean_nickname = validate_nickname(nickname)
        token = secrets.token_urlsafe(32)
        with self._connection() as connection:
            cursor = connection.execute(
                "INSERT INTO players(token_hash, nickname) VALUES (?, ?)",
                (_token_hash(token), clean_nickname),
            )
            row = connection.execute(
                "SELECT * FROM players WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return token, self._public_profile(row)

    def get_profile(self, token: object) -> dict | None:
        if not isinstance(token, str) or not 20 <= len(token) <= 200:
            return None
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM players WHERE token_hash = ?", (_token_hash(token),)
            ).fetchone()
        return self._public_profile(row) if row else None

    def recent_bot_words(
        self, token: object, bot_id: str | None = None, limit: int = 20
    ) -> list[str]:
        if not isinstance(token, str) or (bot_id is not None and not isinstance(bot_id, str)):
            return []
        limit = max(1, min(int(limit), 100))
        bot_filter = " AND history.bot_id = ?" if bot_id is not None else ""
        parameters = (
            (_token_hash(token), bot_id, limit)
            if bot_id is not None
            else (_token_hash(token), limit)
        )
        with self._connection() as connection:
            rows = connection.execute(
                f"""
                SELECT history.normalized_word
                FROM bot_history AS history
                JOIN players ON players.id = history.player_id
                WHERE players.token_hash = ?{bot_filter}
                ORDER BY history.id DESC
                LIMIT ?
                """,
                parameters,
            ).fetchall()
        return [row["normalized_word"] for row in rows]

    def bot_duel_count(self, token: object, bot_id: str) -> int:
        if not isinstance(token, str) or not isinstance(bot_id, str):
            return 0
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM bot_history AS history
                JOIN players ON players.id = history.player_id
                WHERE players.token_hash = ? AND history.bot_id = ?
                """,
                (_token_hash(token), bot_id),
            ).fetchone()
        return row["total"]

    def remember_bot_word(
        self, token: object, bot_id: str, normalized_word: str
    ) -> bool:
        if (
            not isinstance(token, str)
            or not isinstance(bot_id, str)
            or not isinstance(normalized_word, str)
        ):
            return False
        with self._connection() as connection:
            row = connection.execute(
                "SELECT id FROM players WHERE token_hash = ?", (_token_hash(token),)
            ).fetchone()
            if row is None:
                return False
            connection.execute(
                """
                INSERT INTO bot_history(player_id, bot_id, normalized_word)
                VALUES (?, ?, ?)
                """,
                (row["id"], bot_id, normalized_word),
            )
        return True

    def set_character(self, token: object, character_id: object) -> dict | None:
        if not isinstance(token, str) or not isinstance(character_id, str):
            return None
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM players WHERE token_hash = ?", (_token_hash(token),)
            ).fetchone()
            if row is None:
                return None
            unlocked = json.loads(row["unlocked_json"])
            if character_id not in unlocked:
                raise ValueError("Ce personnage n'est pas encore débloqué.")
            if character_id not in {character["id"] for character in CHARACTERS}:
                raise ValueError("Personnage inconnu.")
            connection.execute(
                "UPDATE players SET selected_character = ?, updated_at = CURRENT_TIMESTAMP "
                "WHERE id = ?",
                (character_id, row["id"]),
            )
            updated = connection.execute(
                "SELECT * FROM players WHERE id = ?", (row["id"],)
            ).fetchone()
        return self._public_profile(updated)

    def record_match(
        self,
        token: object,
        *,
        difficulty: str,
        errors: int,
        elapsed_seconds: float,
        won: bool,
        hints_used: int = 0,
    ) -> dict | None:
        if not isinstance(token, str):
            return None

        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM players WHERE token_hash = ?", (_token_hash(token),)
            ).fetchone()
            if row is None:
                return None

            outcome = calculate_score(
                difficulty,
                errors,
                elapsed_seconds,
                current_streak=row["current_streak"],
                hints_used=hints_used,
                won=won,
            )
            wins = row["wins"] + int(bool(won))
            current_streak = outcome["streak"]
            best_streak = max(row["best_streak"], current_streak)
            xp = row["xp"] + outcome["score"]
            badges = set(json.loads(row["badges_json"]))
            unlocked = set(json.loads(row["unlocked_json"]))

            if wins >= 1:
                badges.add("first_win")
            if wins >= 10:
                badges.add("ten_wins")
            if best_streak >= 10:
                badges.add("streak_10")
            if won and difficulty == "nightmare" and errors == 0 and hints_used == 0:
                badges.add("nightmare_perfect")
            if won and errors >= 7:
                badges.add("last_chance")
            for character in CHARACTERS:
                if best_streak >= character["streak_required"]:
                    unlocked.add(character["id"])

            connection.execute(
                """
                UPDATE players
                SET xp = ?, total_score = total_score + ?, matches = matches + 1,
                    wins = ?,
                    current_streak = ?, best_streak = ?, badges_json = ?,
                    unlocked_json = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    xp,
                    outcome["score"],
                    wins,
                    current_streak,
                    best_streak,
                    json.dumps(sorted(badges)),
                    json.dumps(
                        [
                            character["id"]
                            for character in CHARACTERS
                            if character["id"] in unlocked
                        ]
                    ),
                    row["id"],
                ),
            )
            updated = connection.execute(
                "SELECT * FROM players WHERE id = ?", (row["id"],)
            ).fetchone()

        return {"profile": self._public_profile(updated), "match": outcome}

    def leaderboard(self, limit: int = 20) -> list[dict]:
        limit = max(1, min(int(limit), 100))
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT nickname, total_score, best_streak, wins
                FROM players
                ORDER BY best_streak DESC, total_score DESC, wins DESC, id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]


database = Database()
