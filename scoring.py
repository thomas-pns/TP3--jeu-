"""Pure scoring and rank rules, kept separate for easy testing."""

BASE_POINTS = {
    "easy": 50,
    "medium": 100,
    "hard": 175,
    "nightmare": 275,
}

RANKS = (
    (0, "Apprenti"),
    (250, "Devineur"),
    (800, "Maître des mots"),
    (2000, "Légende"),
)


def streak_multiplier(streak: int) -> float:
    if streak >= 10:
        return 10.0
    if streak >= 5:
        return 5.0
    if streak >= 3:
        return 3.0
    if streak >= 2:
        return 2.0
    return 1.0


def rank_for_xp(xp: int) -> dict:
    current_index = max(
        index for index, (minimum, _) in enumerate(RANKS) if xp >= minimum
    )
    minimum, name = RANKS[current_index]
    if current_index + 1 < len(RANKS):
        next_minimum, next_name = RANKS[current_index + 1]
        progress = (xp - minimum) / (next_minimum - minimum)
    else:
        next_minimum, next_name, progress = None, None, 1.0
    return {
        "name": name,
        "next_name": next_name,
        "xp": xp,
        "xp_floor": minimum,
        "xp_next": next_minimum,
        "progress": max(0.0, min(1.0, progress)),
    }


def calculate_score(
    difficulty: str,
    errors: int,
    elapsed_seconds: float,
    *,
    current_streak: int = 0,
    hints_used: int = 0,
    won: bool = True,
) -> dict:
    if difficulty not in BASE_POINTS:
        raise ValueError(f"Difficulté inconnue : {difficulty}")
    errors = max(0, errors)
    hints_used = max(0, hints_used)
    streak = current_streak + 1 if won and hints_used == 0 else 0

    speed_bonus = (
        max(0, 50 - int(max(0.0, elapsed_seconds) / 3))
        if won
        else 0
    )
    flawless_bonus = 35 if won and errors == 0 and hints_used == 0 else 0
    hint_penalty = hints_used * 30
    base = BASE_POINTS[difficulty] if won else 0
    multiplier = streak_multiplier(streak)
    subtotal = max(0, base + speed_bonus + flawless_bonus - hint_penalty)
    score = round(subtotal * multiplier) if won else 0

    return {
        "score": score,
        "base": base,
        "speed_bonus": speed_bonus,
        "flawless_bonus": flawless_bonus,
        "hint_penalty": hint_penalty,
        "multiplier": multiplier,
        "streak": streak,
        "won": bool(won),
    }
