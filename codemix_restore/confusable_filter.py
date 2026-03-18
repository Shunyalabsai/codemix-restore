"""Confusable pair blocklist: prevents known false-positive restorations.

Certain native words consistently get false-matched to English words due to
phonetic similarity. This filter blocks those known confusable pairs and also
applies a romanization distance check to catch new ones.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class ConfusableFilter:
    """Blocks known false-positive native-to-English matches.

    Two layers of protection:
    1. Explicit blocklist of (lang, indic_word) pairs known to false-positive
    2. Romanization distance heuristic for catch-all protection
    """

    # Known false positives discovered through error analysis.
    # Key: (lang_code, indic_word) → set of English words to block.
    # Use "*" as lang_code for cross-language blocks.
    _BLOCKLIST: dict[tuple[str, str], set[str]] = {
        # Assamese false positives
        ("as", "অঁ"): {"am", "um", "on"},
        ("as", "তেনেকুৱাকে"): {"think"},
        ("as", "এইবাৰ"): {"up"},
        ("as", "চাগে"): {"sage"},
        ("as", "হেতু"): {"had"},
        ("as", "কেনে"): {"can"},
        ("as", "এয়া"): {"you"},
        ("as", "পৰা"): {"para", "per"},
        # Bengali false positives
        ("bn", "সঠিকে"): {"said"},
        ("bn", "পিউনের"): {"been"},
        ("bn", "আধ্যে"): {"it"},
        ("bn", "জেটা"): {"zeta"},
        # Gujarati false positives
        ("gu", "અ"): {"you", "a"},
        ("gu", "જ"): {"ja"},
        ("gu", "મેં"): {"men", "man"},
        ("gu", "ભલે"): {"play"},
        ("gu", "ઈ"): {"you", "e"},
        ("gu", "લોકોને"): {"like"},
        ("gu", "લોકો"): {"loco"},
        ("gu", "લોકોના"): {"like"},
        ("gu", "ખાતો"): {"ja"},
        ("gu", "યાં"): {"yan"},
        ("gu", "ભારતમાં"): {"pretty"},
        ("gu", "જ્યારે"): {"your"},
        ("gu", "ડીએ"): {"die"},
        ("gu", "બીએ"): {"be"},
        ("gu", "જાય"): {"joy", "ja"},
        ("gu", "ઉઠા"): {"it"},
        ("gu", "એવી"): {"of"},
        # Hindi false positives
        ("hi", "छठमे"): {"shit"},
        ("hi", "ताजे"): {"take"},
        # Kannada false positives
        ("kn", "ಹೈ"): {"he"},
        ("kn", "ಸೆಟ್"): {"set"},
        # Marathi false positives
        ("mr", "ताजे"): {"take"},
        ("mr", "दुरून"): {"turn"},
        # Malayalam false positives
        ("ml", "ഹോർ"): {"here", "her"},
        # Maithili false positives
        ("mai", "छठमे"): {"shit"},
        ("mai", "परतौ"): {"pretty"},
        # Odia false positives
        ("or", "ତେଣୁ"): {"don"},
        ("or", "ଜାପାନୀ"): {"open"},
        # Tamil false positives
        ("ta", "யூதி"): {"it"},
        ("ta", "அன்றட்"): {"ant"},
        ("ta", "ஆண்டிக்"): {"ant"},
        # Urdu false positives
        ("ur", "سنٹون"): {"the"},
        ("ur", "ہمارے"): {"we"},
        # Kannada false positives
        ("kn", "ಹೂವಿನ"): {"have"},
        # Odia false positives
        ("or", "ଖେତରେ"): {"good"},
        # Konkani false positives
        ("kok", "कुडींत"): {"good"},
        # Kashmiri false positives
        ("ks", "مَت"): {"mat", "met", "mut"},
        ("ks", "بارش"): {"barish", "bar", "bars"},
        ("ks", "اپ"): {"up", "app"},
        ("ks", "ڈیٹ"): {"diet", "date", "dit"},
        # Urdu false positives — common native words
        ("ur", "بارش"): {"barish", "bar", "bars"},
    }

    # Build a fast lookup: (lang, word) -> blocked English words
    # Also includes cross-language ("*") blocks applied to all languages.
    _CROSS_LANG_BLOCKS: dict[str, set[str]] = {}

    def __init__(self) -> None:
        # Pre-build the lookup structures
        self._lang_blocks: dict[str, dict[str, set[str]]] = {}
        for (lang, word), blocked in self._BLOCKLIST.items():
            if lang == "*":
                self._CROSS_LANG_BLOCKS[word] = blocked
            else:
                self._lang_blocks.setdefault(lang, {}).setdefault(word, set()).update(
                    {w.lower() for w in blocked}
                )

    def should_block(
        self,
        word: str,
        lang_code: str,
        english_candidate: str,
        romanized: str = "",
        match_type: str = "",
    ) -> bool:
        """Check if a proposed English restoration should be blocked.

        Args:
            word: Original Indic word.
            lang_code: Language code.
            english_candidate: Proposed English word.
            romanized: Romanized form of the Indic word.
            match_type: How the match was found ("exact", "phonetic", "edit_distance").

        Returns:
            True if the match should be blocked (it's a known false positive).
        """
        candidate_lower = english_candidate.lower()

        # 1. Check explicit blocklist
        lang_dict = self._lang_blocks.get(lang_code, {})
        blocked = lang_dict.get(word)
        if blocked and candidate_lower in blocked:
            logger.debug("Blocked confusable: %s (%s) -> %s", word, lang_code, english_candidate)
            return True

        # Cross-language blocks
        cross_blocked = self._CROSS_LANG_BLOCKS.get(word)
        if cross_blocked and candidate_lower in cross_blocked:
            return True

        # 2. Romanization distance heuristic: if the romanized form and the
        # English candidate are very different, it's likely a false positive.
        # Only apply to phonetic/edit_distance matches (not exact/translit_variant).
        if (
            romanized
            and match_type in ("phonetic", "edit_distance")
            and len(romanized) >= 3
            and len(candidate_lower) >= 3
        ):
            distance = _normalized_levenshtein(romanized.lower(), candidate_lower)
            if distance > 0.50:
                logger.debug(
                    "Blocked by distance (%.2f): %s -> %s (romanized: %s)",
                    distance, word, english_candidate, romanized,
                )
                return True

        return False


def _normalized_levenshtein(s1: str, s2: str) -> float:
    """Compute normalized Levenshtein distance (0.0 = identical, 1.0 = completely different)."""
    if s1 == s2:
        return 0.0
    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 1.0

    # Standard DP Levenshtein
    matrix = list(range(len2 + 1))
    for i in range(1, len1 + 1):
        prev = matrix[0]
        matrix[0] = i
        for j in range(1, len2 + 1):
            temp = matrix[j]
            if s1[i - 1] == s2[j - 1]:
                matrix[j] = prev
            else:
                matrix[j] = 1 + min(prev, matrix[j], matrix[j - 1])
            prev = temp

    return matrix[len2] / max(len1, len2)
