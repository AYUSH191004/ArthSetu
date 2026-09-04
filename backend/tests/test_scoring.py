from backend.app.services.scoring import (
    exact_match,
    normalize_text,
    normalized_contains,
    similarity,
)


class TestNormalizeText:
    def test_handles_none_and_empty(self):
        assert normalize_text(None) == ""
        assert normalize_text("") == ""
        assert normalize_text("   ") == ""

    def test_uppercases_and_strips_punctuation(self):
        assert normalize_text("M/s Acme-Steel  Works.") == "M S ACME STEEL WORKS"

    def test_collapses_whitespace(self):
        assert normalize_text("a   b\t c") == "A B C"


class TestSimilarity:
    def test_identical_after_normalization(self):
        assert similarity("Acme Steel Works", "ACME  STEEL WORKS") == 1.0

    def test_token_order_insensitive(self):
        assert similarity("Steel Works Acme", "Acme Steel Works") > 0.95

    def test_missing_input_is_zero(self):
        assert similarity(None, "Acme") == 0.0
        assert similarity("Acme", "") == 0.0

    def test_dissimilar_is_low(self):
        assert similarity("Acme Steel", "Zephyr Logistics") < 0.4


def test_exact_match():
    assert exact_match("Acme Ltd", "acme  ltd") is True
    assert exact_match("Acme", "Beta") is False
    assert exact_match(None, None) is False


def test_normalized_contains():
    assert normalized_contains("Acme", "M/S ACME STEEL") is True
    assert normalized_contains("Acme Steel Works", "Acme") is True
    assert normalized_contains("Acme", "Beta") is False
    assert normalized_contains(None, "Acme") is False
