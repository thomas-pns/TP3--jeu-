import pytest

from words import CATALOG, choose_word, normalize_word, validate_word, words_for


def test_catalog_has_at_least_600_unique_words_and_150_nightmare_words():
    normalized = [entry["normalized"] for entry in CATALOG]
    assert len(CATALOG) >= 600
    assert len(set(normalized)) == len(normalized)
    assert len(words_for("nightmare")) >= 150
    assert all(entry["category"] for entry in CATALOG)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("ÉLÉPHANT", "elephant"),
        ("garçon", "garcon"),
        ("forêt", "foret"),
        ("cœur", "coeur"),
    ],
)
def test_accents_are_normalized_for_comparison(source, expected):
    assert normalize_word(source) == expected


def test_word_display_keeps_french_accents():
    assert validate_word("  éléphant ") == "éléphant"


@pytest.mark.parametrize("invalid", ["", "ab", "mot composé", "mot2", "a-b", "é🙂"])
def test_word_validation_rejects_non_letters(invalid):
    with pytest.raises(ValueError):
        validate_word(invalid)


def test_word_picker_does_not_repeat_a_recent_word():
    easy_words = words_for("easy")
    first = choose_word("easy", rng=type("Fixed", (), {"choice": lambda _, values: values[0]})())
    second = choose_word(
        "easy",
        recent_words=[first["word"]],
        rng=type("Fixed", (), {"choice": lambda _, values: values[0]})(),
    )
    assert second["normalized"] != first["normalized"]
    assert len(easy_words) > 1


def test_word_picker_reports_exhaustion_instead_of_repeating():
    tiny = [
        {
            "word": "chat",
            "normalized": "chat",
            "difficulty": "easy",
            "category": "Animaux",
        }
    ]
    with pytest.raises(LookupError):
        choose_word("easy", ["chat"], catalog=tiny)
