from backend.app.services.scoring import (
    address_similarity,
    exact_match,
    normalize_address,
    normalize_pin,
    normalize_text,
    normalized_contains,
    pin_matches,
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


class TestAddress:
    def test_normalize_drops_filler_words(self):
        n = normalize_address("Shop No. 12, Main Road, Near Bus Stand, Ludhiana, Punjab")
        assert "SHOP" not in n and "ROAD" not in n and "PUNJAB" not in n
        assert "LUDHIANA" in n or "BUS" in n or "STAND" in n

    def test_similarity_matches_reworded_same_address(self):
        a = "Plot 42, Focal Point Phase 3, Ludhiana, Punjab"
        b = "PLOT 42 FOCAL POINT PH 3 LUDHIANA"
        assert address_similarity(a, b) > 0.8

    def test_similarity_low_for_different_addresses(self):
        assert address_similarity(
            "Plot 42, Focal Point, Ludhiana",
            "Shop 9, Grain Market, Mohali",
        ) < 0.5

    def test_similarity_zero_on_missing(self):
        assert address_similarity(None, "Plot 42") == 0.0


class TestPin:
    def test_normalize_extracts_six_digits(self):
        assert normalize_pin(" 141 001 ") == "141001"
        assert normalize_pin("PIN-160055") == "160055"

    def test_normalize_rejects_wrong_length(self):
        assert normalize_pin("14100") == ""
        assert normalize_pin("1410012") == ""
        assert normalize_pin(None) == ""

    def test_pin_matches(self):
        assert pin_matches("141001", "141 001") is True
        assert pin_matches("141001", "141002") is False
        assert pin_matches("", "141001") is False
