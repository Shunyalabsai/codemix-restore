"""Stage 3: Word-level language identification for ambiguous tokens.

Determines whether a word in Indic script is actually English (transliterated)
or a native language word. Uses character n-gram features, subword patterns,
dictionary signals, and context.
"""

from __future__ import annotations

import logging
import unicodedata
from dataclasses import dataclass
from codemix_restore.dictionary_lookup import Confidence, LookupResult

logger = logging.getLogger(__name__)


@dataclass
class LIDResult:
    """Language identification result for a single word."""
    is_english: bool
    probability: float  # P(english) in [0.0, 1.0]
    signals: dict[str, float]  # Individual signal scores for debugging


# Common English transliteration suffixes in Devanagari and other scripts
# These are phonetic patterns that strongly suggest English origin
_ENGLISH_SUFFIX_PATTERNS = {
    # Devanagari
    "Devanagari": [
        "मेंट",  # -ment (document, management)
        "शन",   # -tion/-sion (station, commission)
        "इंग",   # -ing (meeting, working)
        "ली",    # -ly (actually, really)
        "नेस",   # -ness (business, happiness)
        "टी",    # -ty/-tee (party, committee)
        "बल",   # -ble (possible, available)
        "फुल",   # -ful (helpful, beautiful)
        "लेस",   # -less (useless, careless)
        "एबल",   # -able (available, comfortable)
    ],
    # Bengali
    "Bengali": [
        "মেন্ট",  # -ment
        "শন",    # -tion
        "ইং",    # -ing
        "লি",    # -ly
        "নেস",   # -ness
    ],
    # Tamil
    "Tamil": [
        "மென்ட்",  # -ment
        "ஷன்",    # -tion
        "இங்",    # -ing
        "லி",     # -ly
    ],
    # Telugu
    "Telugu": [
        "మెంట్",  # -ment
        "షన్",   # -tion
        "ఇంగ్",  # -ing
    ],
    # Kannada
    "Kannada": [
        "ಮೆಂಟ್",  # -ment
        "ಷನ್",   # -tion
        "ಇಂಗ್",  # -ing
    ],
    # Gujarati
    "Gujarati": [
        "મેન્ટ",  # -ment
        "શન",    # -tion
        "ઇંગ",   # -ing
    ],
    # Gurmukhi (Punjabi)
    "Gurmukhi": [
        "ਮੈਂਟ",  # -ment
        "ਸ਼ਨ",   # -tion
        "ਇੰਗ",  # -ing
    ],
}

# Common English transliteration prefixes
_ENGLISH_PREFIX_PATTERNS = {
    "Devanagari": [
        "प्री",   # pre-
        "रि",    # re-
        "अन",    # un-
        "डिस",   # dis-
        "मिस",   # mis-
        "ओवर",   # over-
    ],
}


class WordLanguageIdentifier:
    """Classifies ambiguous words as English or native language.

    Uses a feature-based approach with multiple signals:
    1. Dictionary confidence score (from Stage 2), match-type aware
    2. Character n-gram analysis
    3. Subword suffix/prefix patterns
    4. Word length heuristics
    5. Context from neighboring words
    6. Native word list membership

    This is a lightweight rule-based classifier. For production use with
    higher accuracy, train a logistic regression or BiLSTM model using
    the features computed here.
    """

    def __init__(
        self,
        english_threshold: float = 0.65,
        native_threshold: float = 0.35,
        native_word_lists: dict[str, set[str]] | None = None,
    ):
        self._english_threshold = english_threshold
        self._native_threshold = native_threshold
        self._native_word_lists = native_word_lists or {}

    def classify(
        self,
        word: str,
        script_name: str,
        lookup_result: LookupResult | None = None,
        context_prev: str | None = None,
        context_next: str | None = None,
        prev_is_english: bool | None = None,
        next_is_english: bool | None = None,
        lang_code: str | None = None,
    ) -> LIDResult:
        """Classify a word as English or native.

        Args:
            word: The Indic-script word to classify.
            script_name: Script name (e.g., "Devanagari").
            lookup_result: Result from dictionary lookup (Stage 2).
            context_prev: Previous word (for context signal).
            context_next: Next word (for context signal).
            prev_is_english: Whether previous word was classified as English.
            next_is_english: Whether next word was classified as English.
            lang_code: Language code for native word list lookup.

        Returns:
            LIDResult with classification and probability.
        """
        signals: dict[str, float] = {}

        # Signal 1: Dictionary confidence (strongest signal), match-type aware
        dict_score = self._dictionary_signal(lookup_result)
        signals["dictionary"] = dict_score

        # Signal 2: Suffix pattern matching
        suffix_score = self._suffix_signal(word, script_name)
        signals["suffix"] = suffix_score

        # Signal 3: Prefix pattern matching
        prefix_score = self._prefix_signal(word, script_name)
        signals["prefix"] = prefix_score

        # Signal 4: Word length heuristic
        length_score = self._length_signal(word, script_name)
        signals["length"] = length_score

        # Signal 5: Character composition analysis
        char_score = self._char_composition_signal(word, script_name)
        signals["char_composition"] = char_score

        # Signal 6: Context (code-switching span awareness)
        context_score = self._context_signal(prev_is_english, next_is_english)
        signals["context"] = context_score

        # Signal 7: Native word list membership
        native_score = self._native_word_list_signal(word, lang_code)
        signals["native_list"] = native_score

        # Weighted combination — dictionary is strongest, context reduced
        # to prevent cascade errors from false positives
        weights = {
            "dictionary": 0.40,
            "suffix": 0.12,
            "prefix": 0.05,
            "length": 0.10,
            "char_composition": 0.13,
            "context": 0.10,
            "native_list": 0.10,
        }

        probability = sum(signals[k] * weights[k] for k in weights)
        probability = max(0.0, min(1.0, probability))

        is_english = probability >= self._english_threshold

        return LIDResult(
            is_english=is_english,
            probability=probability,
            signals=signals,
        )

    def _dictionary_signal(self, lookup_result: LookupResult | None) -> float:
        """Score from dictionary lookup, adjusted by match type.

        Exact and translit_variant matches are trusted fully. Phonetic and
        edit-distance matches are penalized since they produce many false
        positives (e.g., native words that happen to sound like English).
        """
        if lookup_result is None:
            return 0.5  # Neutral when no dictionary result

        # Apply match-type discount for non-exact matches
        match_type_factor = 1.0
        if lookup_result.match_detail is not None:
            mt = lookup_result.match_detail.match_type
            if mt == "phonetic":
                match_type_factor = 0.70
            elif mt == "edit_distance":
                match_type_factor = 0.50

        if lookup_result.confidence == Confidence.HIGH:
            return min(1.0, 1.0 * match_type_factor)
        elif lookup_result.confidence == Confidence.AMBIGUOUS:
            return lookup_result.score * match_type_factor
        elif lookup_result.confidence == Confidence.MEDIUM:
            return (0.4 + lookup_result.score * 0.3) * match_type_factor
        else:  # LOW
            return 0.1

    def _suffix_signal(self, word: str, script_name: str) -> float:
        """Check for English suffix patterns in the word."""
        patterns = _ENGLISH_SUFFIX_PATTERNS.get(script_name, [])
        for pattern in patterns:
            if word.endswith(pattern):
                return 0.85
        return 0.3  # Baseline — no suffix detected

    def _prefix_signal(self, word: str, script_name: str) -> float:
        """Check for English prefix patterns."""
        patterns = _ENGLISH_PREFIX_PATTERNS.get(script_name, [])
        for pattern in patterns:
            if word.startswith(pattern):
                return 0.75
        return 0.3

    def _length_signal(self, word: str, script_name: str) -> float:
        """Word length heuristic.

        English words transliterated into Indic scripts tend to be slightly
        longer (more aksharas) due to vowel expansion. Very short words (1-2
        aksharas) are more likely native function words.
        """
        # Count "logical" characters (base characters, not combining marks)
        base_chars = sum(
            1 for c in word
            if not unicodedata.category(c).startswith("M")
        )

        if base_chars <= 1:
            return 0.05  # Single-char words are almost never English
        elif base_chars <= 2:
            return 0.15  # 2-char words are very rarely English
        elif base_chars <= 4:
            return 0.5   # Could be either
        else:
            return 0.6   # Slightly favors English for longer transliterations

    def _char_composition_signal(self, word: str, script_name: str) -> float:
        """Analyze character composition for English transliteration patterns.

        English transliterations often have:
        - More halant/virama usage (consonant clusters)
        - Nukta characters (for foreign sounds like /f/, /z/)
        - Less use of aspirated consonants in Tamil
        """
        if not word:
            return 0.5

        has_nukta = any(unicodedata.name(c, "").endswith("NUKTA") for c in word)
        has_virama = any("VIRAMA" in unicodedata.name(c, "") or
                         "HALANT" in unicodedata.name(c, "") or
                         "SIGN VIRAMA" in unicodedata.name(c, "")
                         for c in word)

        # Nukta is a strong signal for English (used for /f/, /z/ etc.)
        if has_nukta:
            return 0.8

        # Virama/halant in middle of word suggests consonant cluster (English-like)
        virama_count = sum(
            1 for c in word
            if "VIRAMA" in unicodedata.name(c, "") or "HALANT" in unicodedata.name(c, "")
        )
        base_count = sum(
            1 for c in word if not unicodedata.category(c).startswith("M")
        )

        if base_count > 0:
            virama_ratio = virama_count / base_count
            if virama_ratio > 0.3:
                return 0.65  # High consonant cluster ratio → more likely English
            elif virama_ratio > 0.15:
                return 0.55

        return 0.4  # Neutral

    def _context_signal(
        self,
        prev_is_english: bool | None,
        next_is_english: bool | None,
    ) -> float:
        """Context from neighboring words.

        Code-switching tends to happen in spans — if surrounding words are
        English, the current word is more likely English too.
        """
        if prev_is_english is None and next_is_english is None:
            return 0.5  # No context available

        score = 0.5
        if prev_is_english is True:
            score += 0.2
        if next_is_english is True:
            score += 0.2
        if prev_is_english is False:
            score -= 0.1
        if next_is_english is False:
            score -= 0.1

        return max(0.0, min(1.0, score))

    def _native_word_list_signal(
        self,
        word: str,
        lang_code: str | None,
    ) -> float:
        """Check if word appears in native word frequency list.

        Words in the native list are definitively native.
        """
        if not lang_code or not self._native_word_lists:
            return 0.5  # Neutral when no list available

        native_words = self._native_word_lists.get(lang_code, set())
        if word in native_words:
            return 0.0  # Definitively native
        return 0.5  # Neutral — absence from list is not evidence of English
