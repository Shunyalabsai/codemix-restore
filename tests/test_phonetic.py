"""Tests for the phonetic matching engine."""

from codemix_restore.phonetic.engine import PhoneticMatcher


class TestPhoneticMatcher:
    def setup_method(self):
        self.matcher = PhoneticMatcher()

    def test_exact_match(self):
        results = self.matcher.lookup("meeting")
        assert results
        assert results[0].english_word == "meeting"
        assert results[0].score == 1.0
        assert results[0].match_type == "exact"

    def test_translit_variant_match(self):
        results = self.matcher.lookup("chek")
        assert results
        assert results[0].english_word == "check"
        assert results[0].match_type == "translit_variant"

    def test_translit_variant_at(self):
        results = self.matcher.lookup("aat")
        assert results
        assert results[0].english_word == "at"

    def test_no_match_for_gibberish(self):
        results = self.matcher.lookup("xyzqwk")
        assert not results

    def test_is_english_positive(self):
        is_eng, match = self.matcher.is_english("report")
        assert is_eng
        assert match is not None
        assert match.english_word == "report"

    def test_is_english_negative(self):
        is_eng, match = self.matcher.is_english("xyzqwk")
        assert not is_eng
        assert match is None

    def test_vocab_size(self):
        assert self.matcher.vocab_size > 100

    def test_empty_input(self):
        assert self.matcher.lookup("") == []
