"""Tests for the Unicode-aware tokenizer."""

from codemix_restore.tokenizer import ScriptType, Token, detokenize, tokenize


class TestTokenize:
    def test_simple_devanagari(self):
        tokens = tokenize("नमस्ते दुनिया")
        word_tokens = [t for t in tokens if t.script_type == ScriptType.INDIC]
        assert len(word_tokens) == 2
        assert word_tokens[0].text == "नमस्ते"
        assert word_tokens[0].script_name == "Devanagari"

    def test_preserves_whitespace(self):
        tokens = tokenize("एक दो")
        assert any(t.script_type == ScriptType.WHITESPACE for t in tokens)

    def test_separates_punctuation(self):
        tokens = tokenize("हेल्लो,")
        types = [t.script_type for t in tokens]
        assert ScriptType.PUNCTUATION in types

    def test_detokenize_roundtrip(self):
        text = "धन्यवाद फॉर योर हेल्प"
        tokens = tokenize(text)
        assert detokenize(tokens) == text

    def test_empty_input(self):
        assert tokenize("") == []

    def test_latin_tokens(self):
        tokens = tokenize("hello world")
        word_tokens = [t for t in tokens if t.script_type == ScriptType.LATIN]
        assert len(word_tokens) == 2

    def test_mixed_script_detection(self):
        tokens = tokenize("நாளைக்கு மீட்டிங்")
        indic = [t for t in tokens if t.script_type == ScriptType.INDIC]
        assert all(t.script_name == "Tamil" for t in indic)

    def test_purna_viram_is_punctuation(self):
        tokens = tokenize("वाक्य।")
        assert any(t.text == "।" and t.script_type == ScriptType.PUNCTUATION for t in tokens)
