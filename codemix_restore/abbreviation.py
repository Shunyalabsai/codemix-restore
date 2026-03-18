"""Abbreviation detection for code-mixed ASR output.

Detects sequences of short Indic tokens that represent English letter names
(e.g., "ડીએ બીએ" → "D.A. B.A.", "एम पी" → "M.P.").
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Mapping from romanized letter names to English letters.
# These are the common phonetic spellings ASR produces for spoken English letters.
_LETTER_MAP: dict[str, str] = {
    # Standard letter names
    "e": "A", "ee": "E", "ai": "I", "o": "O", "yu": "U",
    "a": "A",
    # Consonants
    "bi": "B", "bee": "B",
    "si": "C", "see": "C",
    "di": "D", "dee": "D",
    "ef": "F", "eph": "F",
    "ji": "G", "jee": "G",
    "ech": "H", "aich": "H",
    "je": "J", "jay": "J",
    "ke": "K", "kay": "K",
    "el": "L",
    "em": "M",
    "en": "N",
    "pi": "P", "pee": "P",
    "kyu": "Q", "kyoo": "Q",
    "ar": "R", "aar": "R",
    "es": "S",
    "ti": "T", "tee": "T",
    "vi": "V", "vee": "V",
    "dabalyu": "W", "dablyu": "W",
    "eks": "X",
    "vai": "Y", "way": "Y",
    "zed": "Z", "zee": "Z", "zet": "Z",
}

# Per-script Indic representations of letter names.
# Key: Indic form → uppercase English letter
INDIC_LETTER_MAP: dict[str, str] = {
    # Devanagari
    "ए": "A", "बी": "B", "सी": "C", "डी": "D", "ई": "E",
    "एफ": "F", "एफ़": "F", "जी": "G", "एच": "H", "आई": "I",
    "जे": "J", "के": "K", "एल": "L", "एम": "M", "एन": "N",
    "ओ": "O", "पी": "P", "क्यू": "Q", "आर": "R", "एस": "S",
    "टी": "T", "यू": "U", "वी": "V", "डब्ल्यू": "W",
    "एक्स": "X", "वाई": "Y", "ज़ेड": "Z", "ज़ी": "Z",
    # Bengali / Assamese
    "এ": "A", "বি": "B", "বী": "B", "সি": "C", "সী": "C",
    "ডি": "D", "ডী": "D", "ই": "E", "ঈ": "E",
    "এফ": "F", "জি": "G", "জী": "G", "এইচ": "H",
    "আই": "I", "জে": "J", "কে": "K", "এল": "L",
    "এম": "M", "এন": "N", "ও": "O", "পি": "P", "পী": "P",
    "আর": "R", "এস": "S", "টি": "T", "টী": "T",
    "ইউ": "U", "ভি": "V", "ভী": "V",
    # Gujarati
    "એ": "A", "બી": "B", "સી": "C", "ડી": "D", "ઈ": "E",
    "એફ": "F", "જી": "G", "એચ": "H", "આઈ": "I",
    "જે": "J", "કે": "K", "એલ": "L", "એમ": "M", "એન": "N",
    "ઓ": "O", "પી": "P", "આર": "R", "એસ": "S",
    "ટી": "T", "યુ": "U", "વી": "V",
    # Gurmukhi (Punjabi)
    "ਏ": "A", "ਬੀ": "B", "ਸੀ": "C", "ਡੀ": "D", "ਈ": "E",
    "ਐੱਫ": "F", "ਜੀ": "G", "ਐੱਚ": "H", "ਆਈ": "I",
    "ਜੇ": "J", "ਕੇ": "K", "ਐੱਲ": "L", "ਐੱਮ": "M", "ਐੱਨ": "N",
    "ਓ": "O", "ਪੀ": "P", "ਆਰ": "R", "ਐੱਸ": "S",
    "ਟੀ": "T", "ਯੂ": "U", "ਵੀ": "V",
    # Tamil
    "ஏ": "A", "பி": "B", "பீ": "B", "சி": "C", "சீ": "C",
    "டி": "D", "டீ": "D", "ஈ": "E",
    "எஃப்": "F", "ஜி": "G", "ஜீ": "G", "எச்": "H",
    "ஐ": "I", "ஜே": "J", "கே": "K", "எல்": "L",
    "எம்": "M", "என்": "N", "ஓ": "O", "பி": "P",
    "ஆர்": "R", "எஸ்": "S", "டி": "T", "டீ": "T",
    "யு": "U", "வி": "V", "வீ": "V",
    # Telugu
    "ఏ": "A", "బి": "B", "బీ": "B", "సి": "C", "సీ": "C",
    "డి": "D", "డీ": "D", "ఈ": "E",
    "ఎఫ్": "F", "జి": "G", "జీ": "G", "ఎచ్": "H",
    "ఐ": "I", "జె": "J", "కె": "K", "ఎల్": "L",
    "ఎమ్": "M", "ఎన్": "N", "ఓ": "O", "పి": "P",
    "ఆర్": "R", "ఎస్": "S", "టి": "T", "టీ": "T",
    "యు": "U", "వి": "V", "వీ": "V",
    # Kannada
    "ಎ": "A", "ಬಿ": "B", "ಬೀ": "B", "ಸಿ": "C", "ಸೀ": "C",
    "ಡಿ": "D", "ಡೀ": "D", "ಈ": "E",
    "ಎಫ್": "F", "ಜಿ": "G", "ಜೀ": "G", "ಎಚ್": "H",
    "ಐ": "I", "ಜೆ": "J", "ಕೆ": "K", "ಎಲ್": "L",
    "ಎಮ್": "M", "ಎನ್": "N", "ಓ": "O", "ಪಿ": "P",
    "ಆರ್": "R", "ಎಸ್": "S", "ಟಿ": "T", "ಟೀ": "T",
    "ಯು": "U", "ವಿ": "V", "ವೀ": "V",
}


def detect_abbreviation(word: str) -> str | None:
    """Check if a single Indic word represents an English letter.

    Args:
        word: Word in Indic script.

    Returns:
        The English letter (e.g., "D") if detected, or None.
    """
    return INDIC_LETTER_MAP.get(word)


def detect_abbreviation_sequence(
    words: list[str],
    start_idx: int,
) -> tuple[str, int] | None:
    """Detect a sequence of Indic words that form an English abbreviation.

    Looks for 2+ consecutive words that each map to a single English letter.

    Args:
        words: List of word strings (Indic script).
        start_idx: Index to start scanning from.

    Returns:
        Tuple of (abbreviation string like "D.A.", count of words consumed),
        or None if no abbreviation sequence found.
    """
    if start_idx >= len(words):
        return None

    letters: list[str] = []
    count = 0

    for i in range(start_idx, len(words)):
        letter = INDIC_LETTER_MAP.get(words[i])
        if letter is None:
            break
        letters.append(letter)
        count += 1

    if count >= 2:
        # Format as abbreviation: "D.A." or "B.A."
        abbreviation = ".".join(letters) + "."
        return abbreviation, count

    return None
