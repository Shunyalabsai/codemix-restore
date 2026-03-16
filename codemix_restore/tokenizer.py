"""Stage 1: Unicode-aware tokenization with script detection."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum, auto

from codemix_restore.config import LanguageConfig, detect_script


class ScriptType(Enum):
    """Script category for a token."""
    INDIC = auto()      # Any Indic script (Devanagari, Tamil, Bengali, etc.)
    LATIN = auto()      # Already in Latin script
    NUMERIC = auto()    # Digits (any script)
    PUNCTUATION = auto()
    WHITESPACE = auto()
    UNKNOWN = auto()


@dataclass
class Token:
    """A single token from the ASR output."""
    text: str
    position: int           # Index in the original token list
    script_type: ScriptType
    script_name: str | None  # e.g., "Devanagari", "Tamil", None for non-Indic
    is_mixed_script: bool = False  # Token contains chars from multiple scripts

    def __repr__(self) -> str:
        return f"Token({self.text!r}, {self.script_type.name}, {self.script_name})"


# Latin character ranges (Basic Latin + Latin Extended)
_LATIN_RANGES = set(range(0x0041, 0x005B)) | set(range(0x0061, 0x007B))  # A-Z, a-z

# Common punctuation that appears in Indic text
_INDIC_PUNCTUATION = {"।", "॥", "؟", "۔", ",", ".", "!", "?", ";", ":", "–", "—", "'", '"'}


def _is_latin(char: str) -> bool:
    """Check if character is Latin letter."""
    return ord(char) in _LATIN_RANGES or unicodedata.category(char).startswith("L") and char.isascii()


def _is_digit(char: str) -> bool:
    """Check if character is a digit (any script)."""
    return unicodedata.category(char).startswith("N")


def _is_punctuation(char: str) -> bool:
    """Check if character is punctuation."""
    if char in _INDIC_PUNCTUATION:
        return True
    cat = unicodedata.category(char)
    return cat.startswith("P") or cat.startswith("S")


def _classify_char(char: str) -> tuple[ScriptType, str | None]:
    """Classify a single character into script type and script name."""
    if char.isspace():
        return ScriptType.WHITESPACE, None

    if _is_punctuation(char):
        return ScriptType.PUNCTUATION, None

    if _is_digit(char):
        return ScriptType.NUMERIC, None

    if _is_latin(char):
        return ScriptType.LATIN, None

    # Check Indic scripts
    script_name = detect_script(char)
    if script_name:
        return ScriptType.INDIC, script_name

    # Indic combining marks (nukta, virama, etc.) that may not be in main ranges
    cat = unicodedata.category(char)
    if cat.startswith("M"):  # Mark characters (combining)
        return ScriptType.INDIC, None  # Will inherit script from base char

    return ScriptType.UNKNOWN, None


def tokenize(text: str, lang_config: LanguageConfig | None = None) -> list[Token]:
    """Tokenize text into script-aware tokens.

    Splits on whitespace and punctuation boundaries while keeping Indic words
    (including combining marks, virama, ZWJ/ZWNJ) as single tokens.

    Args:
        text: Input text from ASR output.
        lang_config: Optional language config for script-specific handling.

    Returns:
        List of Token objects with script classification.
    """
    if not text:
        return []

    tokens: list[Token] = []
    # Split on whitespace first, preserving whitespace tokens
    # Use regex pattern that splits on whitespace but keeps punctuation attached
    # then separate punctuation in a second pass
    raw_parts = re.split(r'(\s+)', text)

    position = 0
    for part in raw_parts:
        if not part:
            continue

        if part.isspace():
            tokens.append(Token(
                text=part,
                position=position,
                script_type=ScriptType.WHITESPACE,
                script_name=None,
            ))
            position += 1
            continue

        # Split punctuation from word boundaries
        sub_tokens = _split_punctuation(part)
        for sub in sub_tokens:
            if not sub:
                continue
            token = _classify_token(sub, position)
            tokens.append(token)
            position += 1

    return tokens


def _split_punctuation(text: str) -> list[str]:
    """Split leading/trailing punctuation from a word.

    Keeps internal punctuation (like hyphens in compound words) attached.
    Handles Indic punctuation (purna viram, etc.).
    """
    if not text:
        return []

    # Check if the entire text is punctuation
    if all(_is_punctuation(c) for c in text):
        return [text]

    parts: list[str] = []

    # Strip leading punctuation
    i = 0
    while i < len(text) and _is_punctuation(text[i]):
        parts.append(text[i])
        i += 1

    # Strip trailing punctuation
    j = len(text)
    trailing: list[str] = []
    while j > i and _is_punctuation(text[j - 1]):
        trailing.append(text[j - 1])
        j -= 1

    # The core word
    if i < j:
        parts.append(text[i:j])

    # Add trailing punctuation
    parts.extend(reversed(trailing))

    return parts


def _classify_token(text: str, position: int) -> Token:
    """Classify a token based on its character composition."""
    if not text:
        return Token(text="", position=position, script_type=ScriptType.UNKNOWN, script_name=None)

    # Check for pure punctuation
    if all(_is_punctuation(c) for c in text):
        return Token(text=text, position=position, script_type=ScriptType.PUNCTUATION, script_name=None)

    # Check for pure digits
    if all(_is_digit(c) or _is_punctuation(c) for c in text) and any(_is_digit(c) for c in text):
        return Token(text=text, position=position, script_type=ScriptType.NUMERIC, script_name=None)

    # Analyze script composition
    scripts_found: dict[str, int] = {}
    latin_count = 0
    indic_count = 0

    for char in text:
        stype, sname = _classify_char(char)
        if stype == ScriptType.LATIN:
            latin_count += 1
        elif stype == ScriptType.INDIC and sname:
            scripts_found[sname] = scripts_found.get(sname, 0) + 1
            indic_count += 1
        elif stype == ScriptType.INDIC:
            # Combining marks without clear script — count as Indic
            indic_count += 1

    is_mixed = bool(scripts_found) and latin_count > 0

    if indic_count > latin_count and scripts_found:
        dominant_script = max(scripts_found, key=scripts_found.get)  # type: ignore[arg-type]
        return Token(
            text=text,
            position=position,
            script_type=ScriptType.INDIC,
            script_name=dominant_script,
            is_mixed_script=is_mixed,
        )
    elif latin_count > 0:
        return Token(
            text=text,
            position=position,
            script_type=ScriptType.LATIN,
            script_name=None,
            is_mixed_script=is_mixed,
        )
    elif indic_count > 0:
        # All combining marks, no base chars with identifiable script
        return Token(
            text=text,
            position=position,
            script_type=ScriptType.INDIC,
            script_name=None,
        )
    else:
        return Token(
            text=text,
            position=position,
            script_type=ScriptType.UNKNOWN,
            script_name=None,
        )


def detokenize(tokens: list[Token]) -> str:
    """Reconstruct text from tokens."""
    return "".join(t.text for t in tokens)
