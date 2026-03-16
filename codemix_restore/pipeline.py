"""Main pipeline orchestrator: chains all 5 stages together.

Usage:
    from codemix_restore import ScriptRestorer

    restorer = ScriptRestorer()
    result = restorer.restore("धन्यवाद फॉर योर हेल्प, थैंक यू सो मच।", lang="hi")
    # -> "धन्यवाद for your help. Thank you so much."
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from codemix_restore.config import detect_lang_from_script, get_config
from codemix_restore.dictionary_lookup import Confidence, DictionaryLookup
from codemix_restore.language_id import WordLanguageIdentifier
from codemix_restore.neural_translit import NeuralTransliterator
from codemix_restore.phonetic.engine import PhoneticMatcher
from codemix_restore.reconstructor import Reconstructor
from codemix_restore.tokenizer import ScriptType, Token, tokenize

logger = logging.getLogger(__name__)


@dataclass
class RestoreResult:
    """Complete result of script restoration."""
    text: str                    # The restored text
    original: str                # Original ASR output
    lang_code: str               # Detected/specified language
    tokens_total: int            # Total tokens processed
    tokens_restored: int         # Tokens converted to English
    tokens_native: int           # Tokens kept in native script
    details: list[TokenDetail]   # Per-token details (for debugging)


@dataclass
class TokenDetail:
    """Debug information for a single token."""
    original: str
    restored: str
    script_type: str
    stage: str  # Which stage resolved this: "passthrough", "dictionary", "lid+neural", "neural"
    confidence: float


class ScriptRestorer:
    """Main API for code-mixed ASR script restoration.

    Orchestrates the 5-stage pipeline:
    1. Tokenization (Unicode-aware, script detection)
    2. Dictionary fast-path (romanization + phonetic matching)
    3. Language identification (for ambiguous tokens)
    4. Neural back-transliteration (IndicXlit for remaining tokens)
    5. Reconstruction (capitalization, punctuation normalization)
    """

    def __init__(
        self,
        dict_path: str | Path | None = None,
        warm_cache_dir: str | Path | None = None,
        use_neural: bool = True,
        high_threshold: float = 0.75,
        low_threshold: float = 0.4,
        lid_threshold: float = 0.65,
    ):
        """Initialize the script restoration pipeline.

        Args:
            dict_path: Path to English dictionary file (JSON or text).
                If None, uses built-in minimal dictionary.
            warm_cache_dir: Directory containing pre-computed warm caches.
            use_neural: Whether to use IndicXlit for neural transliteration.
            high_threshold: Score above which dictionary match is considered HIGH confidence.
            low_threshold: Score below which dictionary match is considered LOW confidence.
            lid_threshold: Probability threshold for language identification.
        """
        # Shared phonetic matcher
        self._matcher = PhoneticMatcher(dict_path=dict_path)
        logger.info("PhoneticMatcher initialized with %d words", self._matcher.vocab_size)

        # Stage 4: Neural transliteration (initialize before Stage 2 so we can inject it)
        self._neural = None
        if use_neural:
            self._neural = NeuralTransliterator(
                phonetic_matcher=self._matcher,
                cache_dir=warm_cache_dir,
            )
            if not self._neural.is_available:
                logger.warning("Neural transliteration unavailable; "
                               "pipeline will use dictionary-only mode")

        # Stage 2: Dictionary lookup (with optional neural transliterator for direct lookups)
        self._dict_lookup = DictionaryLookup(
            phonetic_matcher=self._matcher,
            warm_cache_dir=warm_cache_dir,
            high_threshold=high_threshold,
            low_threshold=low_threshold,
            neural_transliterator=self._neural,
        )

        # Stage 3: Language identification
        self._lid = WordLanguageIdentifier(
            english_threshold=lid_threshold,
        )

        # Stage 5: Reconstruction
        self._reconstructor = Reconstructor()

    def restore(
        self,
        text: str,
        lang: str | None = None,
        return_details: bool = False,
    ) -> str | RestoreResult:
        """Restore English words in code-mixed ASR output.

        Args:
            text: ASR output text in a single Indic script.
            lang: Language code (e.g., "hi", "ta", "bn").
                Auto-detected from script if None.
            return_details: If True, return full RestoreResult with debug info.

        Returns:
            Restored text string, or RestoreResult if return_details=True.
        """
        if not text or not text.strip():
            if return_details:
                return RestoreResult(
                    text=text, original=text, lang_code=lang or "",
                    tokens_total=0, tokens_restored=0, tokens_native=0, details=[],
                )
            return text

        # Auto-detect language from script
        if lang is None:
            lang = detect_lang_from_script(text)
            if lang is None:
                logger.warning("Could not detect language from script; returning text as-is")
                if return_details:
                    return RestoreResult(
                        text=text, original=text, lang_code="",
                        tokens_total=0, tokens_restored=0, tokens_native=0, details=[],
                    )
                return text

        config = get_config(lang)

        # === STAGE 1: Tokenize ===
        tokens = tokenize(text, config)

        # === STAGE 2-4: Process each Indic token ===
        restorations: dict[int, str] = {}  # position -> english word
        details: list[TokenDetail] = []

        # First pass: dictionary lookup for all Indic tokens
        lookup_results: dict[int, LookupResult] = {}
        for token in tokens:
            if token.script_type == ScriptType.INDIC:
                result = self._dict_lookup.lookup(
                    token.text, lang, token.script_name
                )
                lookup_results[token.position] = result

        # Second pass: classify tokens using all stages
        for i, token in enumerate(tokens):
            if token.script_type != ScriptType.INDIC:
                # Non-Indic tokens pass through unchanged
                details.append(TokenDetail(
                    original=token.text,
                    restored=token.text,
                    script_type=token.script_type.name,
                    stage="passthrough",
                    confidence=1.0,
                ))
                continue

            lookup = lookup_results.get(token.position)

            # Stage 2: Fast-path — HIGH confidence dictionary match
            if lookup and lookup.confidence == Confidence.HIGH and lookup.english_match:
                restorations[token.position] = lookup.english_match
                details.append(TokenDetail(
                    original=token.text,
                    restored=lookup.english_match,
                    script_type="INDIC→ENGLISH",
                    stage="dictionary",
                    confidence=lookup.score,
                ))
                continue

            # Stage 2: Fast-path — LOW confidence → keep as native
            if lookup and lookup.confidence == Confidence.LOW:
                details.append(TokenDetail(
                    original=token.text,
                    restored=token.text,
                    script_type="INDIC_NATIVE",
                    stage="dictionary",
                    confidence=1.0 - (lookup.score if lookup else 0),
                ))
                continue

            # Stage 3: Language identification for AMBIGUOUS tokens
            prev_english = None
            next_english = None

            # Check previous token's resolution
            for j in range(i - 1, -1, -1):
                if tokens[j].script_type == ScriptType.WHITESPACE:
                    continue
                if tokens[j].script_type == ScriptType.PUNCTUATION:
                    break
                prev_english = tokens[j].position in restorations
                break

            # Check next token's dictionary result (lookahead)
            for j in range(i + 1, len(tokens)):
                if tokens[j].script_type == ScriptType.WHITESPACE:
                    continue
                if tokens[j].script_type == ScriptType.PUNCTUATION:
                    break
                next_lookup = lookup_results.get(tokens[j].position)
                if next_lookup:
                    next_english = next_lookup.confidence == Confidence.HIGH
                break

            lid_result = self._lid.classify(
                word=token.text,
                script_name=token.script_name or config.script_name,
                lookup_result=lookup,
                prev_is_english=prev_english,
                next_is_english=next_english,
            )

            if lid_result.is_english:
                # Stage 4: Neural back-transliteration
                english_word = None

                # Try dictionary match first (it may have a medium-confidence match)
                if lookup and lookup.english_match:
                    english_word = lookup.english_match

                # Try neural transliteration
                if english_word is None and self._neural and self._neural.is_available:
                    english_word = self._neural.transliterate(token.text, lang)

                if english_word:
                    restorations[token.position] = english_word
                    details.append(TokenDetail(
                        original=token.text,
                        restored=english_word,
                        script_type="INDIC→ENGLISH",
                        stage="lid+neural" if not (lookup and lookup.english_match) else "lid+dictionary",
                        confidence=lid_result.probability,
                    ))
                else:
                    # LID says English but we couldn't transliterate — keep native
                    details.append(TokenDetail(
                        original=token.text,
                        restored=token.text,
                        script_type="INDIC_NATIVE",
                        stage="lid_unresolved",
                        confidence=lid_result.probability,
                    ))
            else:
                # LID says native — keep as-is
                details.append(TokenDetail(
                    original=token.text,
                    restored=token.text,
                    script_type="INDIC_NATIVE",
                    stage="lid",
                    confidence=1.0 - lid_result.probability,
                ))

        # === STAGE 5: Reconstruction ===
        restored_text = self._reconstructor.reconstruct(
            tokens, restorations, lang_code=lang
        )

        if return_details:
            content_tokens = [t for t in tokens if t.script_type not in
                              (ScriptType.WHITESPACE, ScriptType.PUNCTUATION)]
            return RestoreResult(
                text=restored_text,
                original=text,
                lang_code=lang,
                tokens_total=len(content_tokens),
                tokens_restored=len(restorations),
                tokens_native=len(content_tokens) - len(restorations),
                details=details,
            )

        return restored_text
