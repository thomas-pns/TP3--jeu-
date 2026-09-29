import pytest

from scoring import calculate_score, rank_for_xp, streak_multiplier


@pytest.mark.parametrize(
    ("streak", "expected"),
    [(0, 1.0), (1, 1.0), (2, 2.0), (3, 3.0), (5, 5.0), (10, 10.0)],
)
def test_streak_multipliers(streak, expected):
    assert streak_multiplier(streak) == expected


def test_win_awards_difficulty_speed_perfect_and_streak_bonuses():
    result = calculate_score(
        "hard", errors=0, elapsed_seconds=15, current_streak=2
    )
    assert result["base"] == 175
    assert result["flawless_bonus"] == 35
    assert result["streak"] == 3
    assert result["multiplier"] == 3.0
    assert result["score"] > result["base"]


def test_hint_costs_points_and_breaks_the_streak():
    result = calculate_score(
        "medium",
        errors=1,
        elapsed_seconds=45,
        current_streak=6,
        hints_used=1,
    )
    assert result["hint_penalty"] == 30
    assert result["streak"] == 0
    assert result["multiplier"] == 1.0


def test_loss_resets_streak_and_awards_no_points():
    result = calculate_score(
        "nightmare", errors=8, elapsed_seconds=80, current_streak=7, won=False
    )
    assert result["score"] == 0
    assert result["streak"] == 0


@pytest.mark.parametrize(
    ("xp", "rank"),
    [(0, "Apprenti"), (250, "Devineur"), (800, "Maître des mots"), (2000, "Légende")],
)
def test_rank_thresholds(xp, rank):
    assert rank_for_xp(xp)["name"] == rank
