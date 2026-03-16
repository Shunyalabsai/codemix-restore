"""Stage 2: Fast-path dictionary lookup using romanization + phonetic matching."""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from dataclasses import dataclass
from enum import Enum, auto
from functools import lru_cache
from pathlib import Path

from codemix_restore.config import get_config
from codemix_restore.phonetic.engine import MatchResult, PhoneticMatcher
from codemix_restore.phonetic.script_phoneme_maps import romanize_with_map
from codemix_restore.suffix_map import AGGLUTINATIVE_SUFFIXES

logger = logging.getLogger(__name__)


class Confidence(Enum):
    """Confidence level of the dictionary lookup."""
    HIGH = auto()       # Strong English match — use this word
    MEDIUM = auto()     # Possible match — defer to LID
    LOW = auto()        # No match — likely a native word
    AMBIGUOUS = auto()  # Uncertain — needs LID classifier


@dataclass
class LookupResult:
    """Result of dictionary lookup for a single word."""
    original: str               # Original Indic word
    romanized: str              # Romanized form
    english_match: str | None   # Best English match, if any
    confidence: Confidence
    score: float                # Match score 0.0-1.0
    match_detail: MatchResult | None = None


class DictionaryLookup:
    """Fast-path English word detection via romanization + dictionary matching.

    Pipeline:
    1. Check if word is a known native word (exclusion list)
    2. Romanize Indic word using Aksharamukha (or fallback)
    3. Look up romanized form in English dictionary (exact + phonetic + edit distance)
    4. Return confidence-scored result
    """

    # Common native words that get false-positive matched to English.
    # These are high-frequency function words / particles across Indian languages.
    # Key: romanized-ish form → should NOT be matched to English.
    _NATIVE_EXCLUSIONS: dict[str, set[str]] = {
        # Hindi / Marathi / Devanagari-script languages
        "hi": {"हा", "हां", "ना", "मी", "या", "हो", "का", "की", "के", "को", "से",
               "में", "पर", "ने", "है", "था", "हूं", "हैं", "अब", "तो", "भी",
               "वो", "जो", "सो", "कर", "यह", "वह", "उद्या", "आज", "कल", "दो"},
        "mr": {"हा", "हां", "ना", "मी", "या", "हो", "का", "की", "के", "आहे",
               "करा", "करतो", "मला", "त्या", "ही", "उद्या", "तुम्हाला"},
        # Bengali
        "bn": {"কাল", "আছে", "করো", "আমি", "তোমাকে", "এই", "করবো", "দ্য",
               "হ্যাঁ", "না", "এটা", "ওই", "কি", "সে", "তুমি", "আর", "ভালো", "এ"},
        # Tamil
        "ta": {"இந்த", "நான்", "நாளைக்கு", "இருக்கு", "பண்ணுங்க", "உங்களுக்கு",
               "என்", "அது", "இது", "ஒரு", "போ", "வா"},
        # Telugu
        "te": {"ఈ", "నేను", "మీకు", "ఉంది", "చేయండి", "చేస్తాను", "రేపు",
               "ఆ", "ఏం", "ఎందుకు", "అది", "ఇది"},
        # Kannada
        "kn": {"ಈ", "ನಾನು", "ನಿಮಗೆ", "ಇದೆ", "ಮಾಡಿ", "ಮಾಡುತ್ತೇನೆ", "ನಾಳೆ",
               "ಅದು", "ಇದು", "ಒಂದು"},
        # Gujarati
        "gu": {"આ", "હું", "તમને", "છે", "કરો", "કરીશ", "કાલે",
               "એ", "તે", "ને", "પણ"},
        # Punjabi
        "pa": {"ਇਹ", "ਮੈਂ", "ਤੁਹਾਨੂੰ", "ਹੈ", "ਕਰੋ", "ਕਰਾਂਗਾ", "ਕੱਲ",
               "ਉਹ", "ਤੇ", "ਨੂੰ", "ਵੀ"},
        # Odia
        "or": {"ଏ", "ମୁଁ", "ଆପଣ", "ଅଛି", "କରନ୍ତୁ"},
        # Assamese
        "as": {"মই", "আপুনি", "আছে", "কৰক"},
    }

    def __init__(
        self,
        phonetic_matcher: PhoneticMatcher | None = None,
        warm_cache_dir: str | Path | None = None,
        high_threshold: float = 0.75,
        low_threshold: float = 0.4,
        neural_transliterator=None,
    ):
        self._matcher = phonetic_matcher or PhoneticMatcher()
        self._high_threshold = high_threshold
        self._low_threshold = low_threshold
        self._neural = neural_transliterator

        # Warm cache: pre-computed Indic -> English mappings per language
        self._warm_cache: dict[str, dict[str, str]] = {}
        if warm_cache_dir:
            self._load_warm_cache(Path(warm_cache_dir))

        # Aksharamukha availability flag
        self._aksharamukha_available = False
        self._init_romanizer()

    def _init_romanizer(self) -> None:
        """Initialize Aksharamukha for rule-based romanization."""
        try:
            from aksharamukha import transliterate as aksha_trans
            self._aksha_trans = aksha_trans
            self._aksharamukha_available = True
            logger.info("Aksharamukha romanization engine initialized")
        except ImportError:
            logger.warning(
                "aksharamukha not installed; using fallback romanization. "
                "Install with: pip install aksharamukha"
            )
            self._aksha_trans = None

    def _load_warm_cache(self, cache_dir: Path) -> None:
        """Load pre-computed Indic->English warm caches."""
        if not cache_dir.exists():
            logger.warning("Warm cache dir %s does not exist", cache_dir)
            return

        for cache_file in cache_dir.glob("*_cache.json"):
            lang_code = cache_file.stem.replace("_cache", "")
            try:
                with open(cache_file) as f:
                    self._warm_cache[lang_code] = json.load(f)
                logger.info("Loaded warm cache for %s: %d entries",
                            lang_code, len(self._warm_cache[lang_code]))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load warm cache %s: %s", cache_file, e)

    @lru_cache(maxsize=50000)
    def romanize(self, word: str, script_name: str) -> str:
        """Convert an Indic-script word to romanized form.

        Uses Aksharamukha (if installed) with post-processing to produce
        romanizations that match how English words are typically spelled.

        Args:
            word: Word in Indic script.
            script_name: Aksharamukha script name (e.g., "Devanagari", "Tamil").

        Returns:
            Romanized (Latin) form of the word.
        """
        raw = None

        # 1. Try Aksharamukha first (most complete script coverage)
        if self._aksharamukha_available and self._aksha_trans:
            try:
                raw = self._aksha_trans.process(script_name, "ISO", word)
                raw = raw.lower().strip()
            except Exception as e:
                logger.debug("Aksharamukha failed for %r (%s): %s", word, script_name, e)

        # 2. Fallback to script-specific phoneme maps
        if raw is None:
            raw = romanize_with_map(word, script_name)

        # 3. Last resort: Unicode name-based fallback
        if raw is None:
            raw = self._fallback_romanize(word)

        # Post-process: normalize for English dictionary matching
        return self._normalize_romanization(raw)

    @staticmethod
    def _normalize_romanization(rom: str) -> str:
        """Normalize romanized form for better English dictionary matching.

        - Strip trailing inherent 'a' vowel (common in Indic romanization)
        - Simplify diacritics and digraphs
        - Map Indic phonemes to their English equivalents
        """
        # Remove ISO diacritics and normalize to ASCII-friendly forms
        diacritic_map = {
            "ā": "a", "ī": "i", "ū": "u", "ṛ": "ri", "ṝ": "ri",
            "ē": "e", "ō": "o", "ṭ": "t", "ḍ": "d", "ṇ": "n",
            "ś": "sh", "ṣ": "sh", "ṃ": "n", "ṁ": "n",  # anusvara → n
            "ḥ": "h", "ñ": "n", "ṅ": "ng", "ṉ": "n",
            "ŏ": "o", "ĕ": "e", "ô": "o", "ê": "e",  # Candra vowels
            "æ": "a",  # Candra A (used in Marathi for English 'a' sound)
            "ẏ": "y",  # Bengali ya
        }
        result = rom
        for old, new in diacritic_map.items():
            result = result.replace(old, new)

        # Strip trailing 'a' (inherent vowel in Indic scripts that doesn't
        # exist in English loanword pronunciation)
        # e.g., "senda" → "send", "phora" → "phor", "helpa" → "help"
        if len(result) > 2 and result.endswith("a") and not result.endswith("aa"):
            result = result[:-1]

        # ISO uses "c" for Indic "ch" sound (च/চ/ச etc.)
        # In English context, "c" before e/i = "s" sound, but Indic "c" = "ch"
        # Map: "c" → "ch" when it appears to be Indic "ch" phoneme
        result = re.sub(r"c(?=[eiaou])", "ch", result)
        result = re.sub(r"c$", "ck", result)  # Word-final "c" → "ck" (check)

        # j → z for some English words (plij → pliz → please)
        # Only when preceded by vowel (common in Indian English transliteration)
        result = re.sub(r"j$", "z", result)  # Word-final j → z

        # Common phoneme mappings for English matching
        result = re.sub(r"^ph", "f", result)  # Word-initial ph → f
        result = result.replace("chh", "ch")   # Aspirated ch → ch

        return result

    def _fallback_romanize(self, word: str) -> str:
        """Basic fallback romanization using Unicode character names.

        Extracts the phonetic name from Unicode (e.g., DEVANAGARI LETTER KA -> ka).
        Not perfect but provides a reasonable approximation.
        """
        result = []
        for char in word:
            try:
                name = unicodedata.name(char, "").lower()
                # Extract the letter/vowel name from Unicode names like
                # "devanagari letter ka" -> "ka"
                # "devanagari vowel sign aa" -> "aa"
                if " letter " in name:
                    phoneme = name.split(" letter ")[-1]
                    # Handle compound names like "ka" vs "kha"
                    result.append(phoneme.replace(" ", ""))
                elif " vowel sign " in name:
                    vowel = name.split(" vowel sign ")[-1]
                    result.append(vowel.replace(" ", ""))
                elif " sign " in name:
                    sign_name = name.split(" sign ")[-1]
                    if sign_name == "virama":
                        pass  # Skip virama (halant) — it suppresses inherent vowel
                    elif sign_name == "nukta":
                        pass  # Nukta modifies previous consonant
                    elif sign_name in ("anusvara", "anunasika"):
                        result.append("n")
                    elif sign_name == "visarga":
                        result.append("h")
                    else:
                        result.append(sign_name.replace(" ", ""))
                elif " digit " in name:
                    digit = name.split(" digit ")[-1]
                    digit_map = {
                        "zero": "0", "one": "1", "two": "2", "three": "3",
                        "four": "4", "five": "5", "six": "6", "seven": "7",
                        "eight": "8", "nine": "9",
                    }
                    result.append(digit_map.get(digit, digit))
                else:
                    result.append(char)
            except ValueError:
                result.append(char)

        return "".join(result)

    def lookup(self, word: str, lang_code: str, script_name: str | None = None) -> LookupResult:
        """Look up a single Indic word against the English dictionary.

        Args:
            word: Word in Indic script.
            lang_code: Language code (e.g., "hi", "ta", "bn").
            script_name: Aksharamukha script name. Auto-detected if None.

        Returns:
            LookupResult with confidence-scored English match.
        """
        # 0. Check native exclusion list (fastest rejection)
        exclusions = self._NATIVE_EXCLUSIONS.get(lang_code, set())
        if word in exclusions:
            return LookupResult(
                original=word,
                romanized="",
                english_match=None,
                confidence=Confidence.LOW,
                score=0.0,
            )

        # 1. Check warm cache first (fastest path)
        if lang_code in self._warm_cache:
            cached = self._warm_cache[lang_code].get(word)
            if cached:
                return LookupResult(
                    original=word,
                    romanized=cached,
                    english_match=cached,
                    confidence=Confidence.HIGH,
                    score=1.0,
                )

        # 2. Try IndicXlit direct lookup (highest quality, if available)
        neural_result = self._try_neural_lookup(word, lang_code)
        if neural_result is not None:
            return neural_result

        # 3. Romanize the word
        if script_name is None:
            config = get_config(lang_code)
            script_name = config.script_name

        romanized = self.romanize(word, script_name)

        # 4. Phonetic dictionary lookup
        is_english, match = self._matcher.is_english(romanized, threshold=self._low_threshold)

        if not is_english or match is None:
            # Try suffix stripping as fallback (handles agglutinated loanwords)
            stripped = self._try_suffix_strip(word, lang_code, script_name)
            if stripped is not None:
                return stripped

            return LookupResult(
                original=word,
                romanized=romanized,
                english_match=None,
                confidence=Confidence.LOW,
                score=0.0,
            )

        # 5. For non-exact matches, also try suffix stripping — the stem match
        #    may be more accurate than a phonetic match on the full agglutinated form.
        #    e.g., "aapisla" phonetically matches "apply" but the stem "aapis" = "office"
        if match.match_type != "exact" and match.match_type != "translit_variant":
            stripped = self._try_suffix_strip(word, lang_code, script_name)
            if stripped is not None and stripped.score >= match.score:
                return stripped

        # 6. Determine confidence based on score
        if match.score >= self._high_threshold:
            confidence = Confidence.HIGH
        elif match.score >= self._low_threshold:
            confidence = Confidence.AMBIGUOUS
        else:
            confidence = Confidence.LOW

        return LookupResult(
            original=word,
            romanized=romanized,
            english_match=match.english_word,
            confidence=confidence,
            score=match.score,
            match_detail=match,
        )

    def _try_neural_lookup(self, word: str, lang_code: str) -> LookupResult | None:
        """Try IndicXlit → direct dictionary match.

        Iterates IndicXlit beam candidates and picks the best dictionary match,
        preferring earlier beam positions (IndicXlit confidence) and higher dict scores.
        Accepts exact matches and translit_variant matches (score >= 0.9).
        """
        if self._neural is None or not self._neural.is_available:
            return None

        candidates = self._neural.transliterate_to_candidates(word, lang_code)
        if not candidates:
            return None

        best_result: LookupResult | None = None
        best_priority = (-1, -1.0)  # (beam_bonus, score)

        for i, candidate in enumerate(candidates):
            candidate_lower = candidate.lower().strip()
            is_eng, match = self._matcher.is_english(candidate_lower, threshold=0.9)
            if not is_eng or match is None:
                continue
            if match.match_type not in ("exact", "translit_variant"):
                continue

            # Prefer earlier beam positions (higher IndicXlit confidence)
            # and higher dictionary scores
            beam_bonus = len(candidates) - i
            priority = (beam_bonus, match.score)

            if priority > best_priority:
                best_priority = priority
                best_result = LookupResult(
                    original=word,
                    romanized=candidate_lower,
                    english_match=match.english_word,
                    confidence=Confidence.HIGH,
                    score=match.score,
                    match_detail=match,
                )

        return best_result

    def _try_suffix_strip(
        self, word: str, lang_code: str, script_name: str,
    ) -> LookupResult | None:
        """Try stripping native grammatical suffixes to find an English stem.

        Indian languages fuse postpositions/case markers with nouns:
            ऑफिसमध्ये = office + मध्ये (locative)
            টিমকে = team + কে (dative)

        This method tries each known suffix for the language, strips it,
        and looks up the remaining stem against the English dictionary.

        Returns a LookupResult if a HIGH confidence match is found, else None.
        """
        suffixes = AGGLUTINATIVE_SUFFIXES.get(lang_code, [])
        if not suffixes:
            return None

        for suffix in suffixes:
            if not word.endswith(suffix):
                continue

            stem = word[: -len(suffix)]

            # Require stem to have at least 2 base characters (avoid spurious matches)
            base_chars = sum(
                1 for c in stem
                if not unicodedata.category(c).startswith("M")
            )
            if base_chars < 2:
                continue

            # Romanize and look up the stem
            romanized_stem = self.romanize(stem, script_name)
            is_eng, match = self._matcher.is_english(
                romanized_stem, threshold=self._low_threshold
            )

            if is_eng and match is not None and match.score >= self._high_threshold:
                return LookupResult(
                    original=word,
                    romanized=romanized_stem,
                    english_match=match.english_word,
                    confidence=Confidence.HIGH,
                    score=match.score,
                    match_detail=match,
                )

        return None

    def batch_lookup(
        self,
        words: list[tuple[str, str, str | None]],
    ) -> list[LookupResult]:
        """Batch lookup for multiple words.

        Args:
            words: List of (word, lang_code, script_name) tuples.

        Returns:
            List of LookupResult in the same order.
        """
        return [self.lookup(w, lc, sn) for w, lc, sn in words]
