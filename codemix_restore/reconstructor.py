"""Stage 5: Reconstruct the final mixed-script output."""

from __future__ import annotations

from dataclasses import dataclass

from codemix_restore.tokenizer import ScriptType, Token


@dataclass
class RestoredToken:
    """A token after script restoration."""
    original: str       # Original text from ASR
    restored: str       # Restored text (English in Latin or unchanged native)
    was_restored: bool  # Whether this token was changed
    script_type: ScriptType


# Indic sentence-ender punctuation to replace with Latin equivalents
_INDIC_TO_LATIN_PUNCT = {
    "।": ".",   # Devanagari purna viram
    "॥": ".",   # Devanagari double danda
    "۔": ".",   # Urdu/Arabic full stop
    "؟": "?",   # Arabic question mark
}


class Reconstructor:
    """Reassembles tokens into a properly formatted mixed-script string.

    Handles:
    - Capitalization of English words (sentence start, "I")
    - Punctuation normalization (Indic → Latin at script boundaries)
    - Whitespace normalization
    """

    def __init__(self, capitalize: bool = True, normalize_punctuation: bool = True):
        self._capitalize = capitalize
        self._normalize_punct = normalize_punctuation

    def reconstruct(
        self,
        tokens: list[Token],
        restorations: dict[int, str],
        lang_code: str | None = None,
    ) -> str:
        """Reconstruct the final output string.

        Args:
            tokens: Original token list from tokenizer.
            restorations: Dict mapping token position → English word.
            lang_code: Source language code (for punctuation handling).

        Returns:
            Reconstructed string with English words in Latin script.
        """
        restored_tokens: list[RestoredToken] = []

        for token in tokens:
            if token.position in restorations:
                restored_text = restorations[token.position]
                restored_tokens.append(RestoredToken(
                    original=token.text,
                    restored=restored_text,
                    was_restored=True,
                    script_type=ScriptType.LATIN,
                ))
            else:
                restored_tokens.append(RestoredToken(
                    original=token.text,
                    restored=token.text,
                    was_restored=False,
                    script_type=token.script_type,
                ))

        # Post-processing passes
        if self._capitalize:
            self._apply_capitalization(restored_tokens)

        if self._normalize_punct:
            self._apply_punctuation_normalization(restored_tokens)

        # Join tokens back into string
        return "".join(t.restored for t in restored_tokens)

    def _apply_capitalization(self, tokens: list[RestoredToken]) -> None:
        """Capitalize English words at sentence boundaries and pronoun 'I'."""
        at_sentence_start = True

        for token in tokens:
            if token.script_type == ScriptType.WHITESPACE:
                continue

            if token.script_type == ScriptType.PUNCTUATION:
                # Check if this punctuation ends a sentence
                if any(c in token.restored for c in ".!?।॥۔"):
                    at_sentence_start = True
                continue

            if token.was_restored and token.restored:
                # Capitalize at sentence start
                if at_sentence_start:
                    token.restored = token.restored[0].upper() + token.restored[1:]
                    at_sentence_start = False
                # Always capitalize "I" as a standalone word
                elif token.restored.lower() == "i":
                    token.restored = "I"
                else:
                    at_sentence_start = False
            else:
                # Native word — doesn't affect capitalization state, but
                # resets sentence_start flag since we're in a sentence
                at_sentence_start = False

    def _apply_punctuation_normalization(self, tokens: list[RestoredToken]) -> None:
        """Convert Indic punctuation to Latin equivalents when adjacent to English words.

        Only converts when the punctuation is near restored (English) words,
        preserving native punctuation in pure native-script context.
        """
        for i, token in enumerate(tokens):
            if token.script_type != ScriptType.PUNCTUATION:
                continue

            # Check if adjacent to a restored English word
            has_english_neighbor = False

            # Look at previous non-whitespace token
            for j in range(i - 1, max(i - 3, -1), -1):
                if tokens[j].script_type == ScriptType.WHITESPACE:
                    continue
                if tokens[j].was_restored:
                    has_english_neighbor = True
                break

            # Look at next non-whitespace token
            for j in range(i + 1, min(i + 3, len(tokens))):
                if tokens[j].script_type == ScriptType.WHITESPACE:
                    continue
                if tokens[j].was_restored:
                    has_english_neighbor = True
                break

            if has_english_neighbor:
                # Replace Indic punctuation with Latin equivalent
                new_punct = token.restored
                for indic, latin in _INDIC_TO_LATIN_PUNCT.items():
                    new_punct = new_punct.replace(indic, latin)
                token.restored = new_punct
