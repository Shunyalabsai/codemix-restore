"""Tests for suffix stripping (deagglutination) in dictionary lookup."""

import pytest

from codemix_restore.dictionary_lookup import Confidence, DictionaryLookup


@pytest.fixture(scope="module")
def dl():
    return DictionaryLookup()


class TestSuffixStripping:
    """Test that English loanwords with native suffixes are correctly identified."""

    def test_marathi_office_madhye(self, dl):
        """ऑफिसमध्ये = office + मध्ये (locative)"""
        result = dl.lookup("ऑफिसमध्ये", "mr", "Devanagari")
        assert result.english_match == "office"
        assert result.confidence == Confidence.HIGH

    def test_bengali_team_ke(self, dl):
        """টিমকে = team + কে (dative)"""
        result = dl.lookup("টিমকে", "bn", "Bengali")
        assert result.english_match == "team"
        assert result.confidence == Confidence.HIGH

    def test_tamil_office_la(self, dl):
        """ஆபிஸ்ல = office + ல (locative)"""
        result = dl.lookup("ஆபிஸ்ல", "ta", "Tamil")
        assert result.english_match is not None
        assert result.confidence == Confidence.HIGH

    def test_telugu_office_lo(self, dl):
        """ఆఫీస్లో = office + లో (locative)"""
        result = dl.lookup("ఆఫీస్లో", "te", "Telugu")
        assert result.english_match is not None
        assert result.confidence == Confidence.HIGH

    def test_gujarati_office_maan(self, dl):
        """ઓફિસમાં = office + માં (locative)"""
        result = dl.lookup("ઓફિસમાં", "gu", "Gujarati")
        assert result.english_match is not None
        assert result.confidence == Confidence.HIGH

    def test_tamil_team_kitta(self, dl):
        """டீம்கிட்ட = team + கிட்ட (dative)"""
        result = dl.lookup("டீம்கிட்ட", "ta", "Tamil")
        assert result.english_match == "team"
        assert result.confidence == Confidence.HIGH

    def test_hindi_office_mein(self, dl):
        """ऑफिसमें = office + में (locative)"""
        result = dl.lookup("ऑफिसमें", "hi", "Devanagari")
        assert result.english_match == "office"
        assert result.confidence == Confidence.HIGH

    def test_no_false_positive_on_native_word(self, dl):
        """Native words ending in suffix-like strings should NOT be stripped."""
        # कल (kal = yesterday/tomorrow) ends with ल but should not match
        result = dl.lookup("कल", "hi", "Devanagari")
        # Should not be HIGH confidence English
        assert result.confidence != Confidence.HIGH or result.english_match is None

    def test_short_stem_rejected(self, dl):
        """Stems shorter than 2 base chars should be rejected."""
        # A single-char stem with suffix should not match
        result = dl.lookup("कमें", "hi", "Devanagari")
        # Even if "k" could match something, stem too short
        assert result.confidence != Confidence.HIGH
