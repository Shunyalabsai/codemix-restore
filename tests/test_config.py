"""Tests for the language configuration registry."""

import pytest

from codemix_restore.config import (
    LANGUAGE_CONFIGS,
    SCRIPT_TO_LANGS,
    detect_lang_from_script,
    detect_script,
    get_config,
)


class TestLanguageConfigs:
    def test_all_22_languages_present(self):
        assert len(LANGUAGE_CONFIGS) == 22

    def test_get_config_valid(self):
        cfg = get_config("hi")
        assert cfg.lang_name == "Hindi"
        assert cfg.script_name == "Devanagari"

    def test_get_config_invalid_raises(self):
        with pytest.raises(KeyError, match="Unsupported language"):
            get_config("xx")

    def test_all_configs_have_unicode_ranges(self):
        for code, cfg in LANGUAGE_CONFIGS.items():
            assert cfg.unicode_ranges, f"{code} has no unicode ranges"

    def test_script_to_langs_populated(self):
        assert "Devanagari" in SCRIPT_TO_LANGS
        assert "hi" in SCRIPT_TO_LANGS["Devanagari"]


class TestScriptDetection:
    def test_detect_devanagari(self):
        assert detect_script("क") == "Devanagari"

    def test_detect_tamil(self):
        assert detect_script("க") == "Tamil"

    def test_detect_bengali(self):
        assert detect_script("ক") == "Bengali"

    def test_detect_latin_returns_none(self):
        assert detect_script("a") is None

    def test_detect_lang_from_devanagari_text(self):
        lang = detect_lang_from_script("धन्यवाद फॉर योर हेल्प")
        assert lang == "hi"

    def test_detect_lang_from_tamil_text(self):
        lang = detect_lang_from_script("நாளைக்கு மீட்டிங்")
        assert lang == "ta"

    def test_detect_lang_from_latin_only_returns_none(self):
        assert detect_lang_from_script("hello world") is None
