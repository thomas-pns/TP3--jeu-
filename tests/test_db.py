import sqlite3

import pytest

from db import Database, validate_nickname


@pytest.fixture
def store(tmp_path):
    database = Database(tmp_path / "profiles.sqlite3")
    database.init()
    return database


def test_profile_token_persists_profile_without_storing_plain_token(store):
    token, profile = store.create_profile("  Zoé   du-42 ")

    assert profile["nickname"] == "Zoé du-42"
    assert profile["selected_character"] == "pirate"
    assert profile["unlocked_characters"] == ["pirate"]
    assert store.get_profile(token)["id"] == profile["id"]
    assert store.get_profile("not-a-real-token") is None

    with sqlite3.connect(store.path) as connection:
        stored_hash = connection.execute(
            "SELECT token_hash FROM players WHERE id = ?", (profile["id"],)
        ).fetchone()[0]
    assert stored_hash != token


@pytest.mark.parametrize("nickname", ["", "  ", "this name is much too long", "Zoé!"])
def test_invalid_nickname_is_rejected(nickname):
    with pytest.raises(ValueError):
        validate_nickname(nickname)


def test_match_updates_score_streak_badges_and_unlocks(store):
    token, _ = store.create_profile("Devineur")

    result = None
    for _ in range(10):
        result = store.record_match(
            token,
            difficulty="nightmare",
            errors=0,
            elapsed_seconds=10,
            won=True,
        )

    profile = result["profile"]
    assert result["match"]["streak"] == 10
    assert profile["current_streak"] == profile["best_streak"] == 10
    assert profile["total_score"] > 0
    assert profile["xp"] == profile["total_score"]
    assert set(profile["unlocked_characters"]) == {
        "pirate",
        "chef",
        "mummy",
        "astronaut",
        "robot",
        "knight",
    }
    assert {"first_win", "ten_wins", "streak_10", "nightmare_perfect"} <= set(
        profile["badges"]
    )


def test_hint_breaks_streak_and_character_selection_is_persisted(store):
    token, _ = store.create_profile("Joueur")
    store.record_match(
        token, difficulty="easy", errors=0, elapsed_seconds=12, won=True
    )
    after_hint = store.record_match(
        token,
        difficulty="easy",
        errors=1,
        elapsed_seconds=30,
        won=True,
        hints_used=1,
    )

    assert after_hint["profile"]["current_streak"] == 0
    with pytest.raises(ValueError, match="pas encore débloqué"):
        store.set_character(token, "astronaut")

    for _ in range(5):
        store.record_match(
            token, difficulty="easy", errors=0, elapsed_seconds=10, won=True
        )
    selected = store.set_character(token, "astronaut")
    assert selected["selected_character"] == "astronaut"
    assert store.get_profile(token)["selected_character"] == "astronaut"


def test_losses_reset_streak_and_leaderboard_is_ranked(store):
    top_token, _ = store.create_profile("Top")
    other_token, _ = store.create_profile("Second")
    for _ in range(3):
        store.record_match(
            top_token, difficulty="medium", errors=0, elapsed_seconds=10, won=True
        )
    store.record_match(
        top_token, difficulty="hard", errors=8, elapsed_seconds=70, won=False
    )
    store.record_match(
        other_token, difficulty="nightmare", errors=0, elapsed_seconds=10, won=True
    )

    assert store.get_profile(top_token)["current_streak"] == 0
    assert store.get_profile(top_token)["best_streak"] == 3
    assert [entry["nickname"] for entry in store.leaderboard()] == ["Top", "Second"]
