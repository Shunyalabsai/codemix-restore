"""Tests for the dictionary lookup module."""

from codemix_restore.dictionary_lookup import Confidence, DictionaryLookup


class TestDictionaryLookup:
    def setup_method(self):
        self.lookup = DictionaryLookup()

    def test_hindi_meeting(self):
        result = self.lookup.lookup("मीटिंग", "hi", "Devanagari")
        assert result.english_match == "meeting"
        assert result.confidence == Confidence.HIGH

    def test_hindi_native_word_excluded(self):
        result = self.lookup.lookup("है", "hi", "Devanagari")
        assert result.confidence == Confidence.LOW
        assert result.english_match is None

    def test_telugu_report(self):
        result = self.lookup.lookup("రిపోర్ట్", "te", "Telugu")
        assert result.english_match == "report"
        assert result.confidence == Confidence.HIGH

    def test_kannada_please(self):
        result = self.lookup.lookup("ಪ್ಲೀಸ್", "kn", "Kannada")
        assert result.english_match == "please"

    def test_bengali_native_excluded(self):
        result = self.lookup.lookup("আমি", "bn", "Bengali")
        assert result.confidence == Confidence.LOW

    def test_romanize_caches(self):
        r1 = self.lookup.romanize("मीटिंग", "Devanagari")
        r2 = self.lookup.romanize("मीटिंग", "Devanagari")
        assert r1 == r2

    def test_batch_lookup(self):
        words = [("मीटिंग", "hi", "Devanagari"), ("है", "hi", "Devanagari")]
        results = self.lookup.batch_lookup(words)
        assert len(results) == 2
        assert results[0].english_match == "meeting"
        assert results[1].english_match is None
