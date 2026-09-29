import pytest

from bots import (
    BOTS,
    bot_delay,
    bot_line,
    choose_bot_word,
    choose_guess,
)


class PredictableRandom:
    def __init__(self, *, mistake_roll=1.0):
        self.mistake_roll = mistake_roll

    def random(self):
        return self.mistake_roll

    def choice(self, values):
        return values[0]

    def uniform(self, low, high):
        return (low + high) / 2


def entry(word, normalized=None, difficulty="easy", trap=False):
    return {
        "word": word,
        "normalized": normalized or word,
        "difficulty": difficulty,
        "category": "Test",
        "trap": trap,
    }


def test_five_bots_have_increasing_difficulty_and_french_taunts():
    assert list(BOTS) == ["beginner", "clever", "expert", "nightmare", "boss"]
    assert [bot.difficulty for bot in BOTS.values()] == [
        "easy",
        "medium",
        "hard",
        "nightmare",
        "nightmare",
    ]
    assert all(len(bot.taunts) >= 5 for bot in BOTS.values())


@pytest.mark.parametrize(
    ("bot_id", "difficulty"),
    [
        ("beginner", "easy"),
        ("clever", "medium"),
        ("expert", "hard"),
        ("nightmare", "nightmare"),
    ],
)
def test_bot_word_matches_its_level_and_skips_recent_words(bot_id, difficulty):
    catalog = [
        entry("chat", difficulty=difficulty),
        entry("chien", difficulty=difficulty),
    ]
    first = choose_bot_word(bot_id, catalog=catalog, rng=PredictableRandom())
    second = choose_bot_word(
        bot_id,
        recent_words=[first["word"]],
        catalog=catalog,
        rng=PredictableRandom(),
    )
    assert first["difficulty"] == second["difficulty"] == difficulty
    assert first["normalized"] != second["normalized"]


def test_boss_uses_an_unseen_trap_on_every_tenth_duel():
    catalog = [
        entry("chat", difficulty="nightmare"),
        entry("xylophage", difficulty="nightmare", trap=True),
        entry("sphygmomanometre", difficulty="nightmare", trap=True),
    ]
    assert choose_bot_word(
        "boss", duel_count=10, catalog=catalog, rng=PredictableRandom()
    )["word"] == "xylophage"
    assert choose_bot_word(
        "boss",
        duel_count=10,
        recent_words=["xylophage"],
        catalog=catalog,
        rng=PredictableRandom(),
    )["word"] == "sphygmomanometre"
    assert choose_bot_word(
        "boss", duel_count=9, catalog=catalog, rng=PredictableRandom()
    )["word"] == "chat"


def test_only_the_boss_uses_reserved_trap_words():
    catalog = [
        entry("xylophage", difficulty="nightmare", trap=True),
        entry("abstrus", difficulty="nightmare"),
    ]
    chosen = choose_bot_word(
        "nightmare", catalog=catalog, rng=PredictableRandom()
    )
    assert chosen["word"] == "abstrus"


def test_bot_filters_candidates_and_uses_letter_frequency():
    catalog = [entry("chat"), entry("char")]
    guess = choose_guess(
        ["c", "h", "a", None],
        guessed_letters=["c", "h", "a"],
        bot_id="expert",
        catalog=catalog,
        rng=PredictableRandom(),
    )
    assert guess == "t"


def test_strategy_keeps_ligature_as_one_mask_position():
    guess = choose_guess(
        [None, None, None, None],
        bot_id="expert",
        catalog=[entry("cœur", normalized="coeur", difficulty="hard")],
        rng=PredictableRandom(),
    )
    assert guess in {"o", "e"}


def test_bot_avoids_repeated_guesses_and_can_make_a_personality_mistake():
    catalog = [entry("chat"), entry("chien")]
    guess = choose_guess(
        [None, None, None, None],
        guessed_letters=["a", "e", "i", "o", "u"],
        bot_id="beginner",
        catalog=catalog,
        rng=PredictableRandom(mistake_roll=0),
    )
    assert guess == "k"


def test_bot_replies_and_human_like_delay_are_available():
    rng = PredictableRandom()
    assert bot_line("boss", rng=rng) in BOTS["boss"].taunts
    assert bot_delay("boss", rng=rng) == sum(BOTS["boss"].delay_seconds) / 2
