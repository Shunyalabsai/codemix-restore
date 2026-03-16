"""Stage 4: Neural back-transliteration using IndicXlit."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from codemix_restore.phonetic.engine import PhoneticMatcher

logger = logging.getLogger(__name__)


class NeuralTransliterator:
    """Back-transliterates Indic script words to English using IndicXlit.

    Uses beam search to generate top-k candidates, then reranks them
    against an English dictionary for best results.

    Falls back gracefully if IndicXlit is not installed.
    """

    def __init__(
        self,
        phonetic_matcher: PhoneticMatcher | None = None,
        beam_width: int = 10,
        top_k: int = 5,
        cache_dir: str | Path | None = None,
    ):
        self._matcher = phonetic_matcher
        self._beam_width = beam_width
        self._top_k = top_k
        self._engine = None
        self._available = False
        self._runtime_cache: dict[tuple[str, str], str | None] = {}

        # Pre-computed warm cache
        self._warm_cache: dict[str, dict[str, str]] = {}
        if cache_dir:
            self._load_warm_cache(Path(cache_dir))

        self._init_engine()

    def _init_engine(self) -> None:
        """Initialize IndicXlit transliteration engine."""
        try:
            # Apply Python 3.12 compatibility patches before importing fairseq/hydra.
            # This patches dataclasses._get_field and torch.load at minimum.
            from codemix_restore.compat.fairseq_patch import apply_patch
            apply_patch()

            # Import XlitEngine — this triggers the fairseq/hydra import chain.
            # hydra_init() may fail due to MISSING fields, but that's non-fatal
            # for the actual transliteration functionality (it only affects
            # hydra config store registration, which we don't use).
            import warnings
            import logging as _logging
            _fseq_init_logger = _logging.getLogger("fairseq.dataclass.initialize")
            _prev_level = _fseq_init_logger.level
            _fseq_init_logger.setLevel(_logging.CRITICAL)  # suppress expected errors
            try:
                from ai4bharat.transliteration import XlitEngine
            finally:
                _fseq_init_logger.setLevel(_prev_level)

            # Initialize for Indic-to-English direction
            self._engine = XlitEngine(
                src_script_type="indic",
                beam_width=self._beam_width,
                rescore=True,
            )
            self._available = True
            logger.info("IndicXlit engine initialized (beam_width=%d)", self._beam_width)
        except ImportError as e:
            missing = str(e)
            if "fairseq" in missing:
                logger.warning(
                    "fairseq not installed; neural transliteration disabled. "
                    "Install with: pip install fairseq==0.12.2 --no-deps && "
                    "pip install ai4bharat-transliteration --no-deps"
                )
            elif "ai4bharat" in missing:
                logger.warning(
                    "ai4bharat-transliteration not installed; neural transliteration disabled. "
                    "Install with: pip install fairseq==0.12.2 --no-deps && "
                    "pip install ai4bharat-transliteration --no-deps"
                )
            else:
                logger.warning(
                    "Neural transliteration dependency missing (%s). "
                    "Install with: pip install fairseq==0.12.2 --no-deps && "
                    "pip install ai4bharat-transliteration --no-deps", e
                )
        except Exception as e:
            logger.warning("Failed to initialize IndicXlit: %s", e)

    def _load_warm_cache(self, cache_dir: Path) -> None:
        """Load pre-computed warm caches."""
        if not cache_dir.exists():
            return
        for cache_file in cache_dir.glob("*_cache.json"):
            lang_code = cache_file.stem.replace("_cache", "")
            try:
                with open(cache_file) as f:
                    self._warm_cache[lang_code] = json.load(f)
                logger.info("Loaded neural warm cache for %s: %d entries",
                            lang_code, len(self._warm_cache[lang_code]))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load cache %s: %s", cache_file, e)

    @property
    def is_available(self) -> bool:
        return self._available

    def transliterate(self, word: str, lang_code: str) -> str | None:
        """Transliterate a single Indic word to English.

        Generates top-k candidates and picks the best one, preferring
        candidates that match known English words.

        Args:
            word: Word in Indic script.
            lang_code: Language code (e.g., "hi", "ta", "bn").

        Returns:
            Best English transliteration, or None if transliteration fails.
        """
        # Check warm cache first
        if lang_code in self._warm_cache:
            cached = self._warm_cache[lang_code].get(word)
            if cached:
                return cached

        # Check runtime cache
        cache_key = (word, lang_code)
        if cache_key in self._runtime_cache:
            return self._runtime_cache[cache_key]

        if not self._available or self._engine is None:
            result = None
        else:
            result = self._neural_transliterate(word, lang_code)

        self._runtime_cache[cache_key] = result
        return result

    def transliterate_to_candidates(self, word: str, lang_code: str) -> list[str]:
        """Return all top-k IndicXlit candidates for dictionary lookup.

        Unlike transliterate() which picks the best single result, this returns
        all raw candidates so the caller can try each against the dictionary.

        Args:
            word: Word in Indic script.
            lang_code: Language code (e.g., "hi", "ta", "bn").

        Returns:
            List of English candidate strings (may be empty).
        """
        if not self._available or self._engine is None:
            return []

        try:
            result = self._engine.translit_word(word, lang_code, topk=self._top_k)
            if not result:
                return []
            if isinstance(result, list):
                return [c.lower().strip() for c in result if c]
            if isinstance(result, dict) and lang_code in result:
                return [c.lower().strip() for c in result[lang_code] if c]
            return []
        except Exception as e:
            logger.debug("IndicXlit candidates failed for %r (%s): %s", word, lang_code, e)
            return []

    def _neural_transliterate(self, word: str, lang_code: str) -> str | None:
        """Core neural transliteration with candidate reranking."""
        try:
            # Get top-k candidates from IndicXlit
            result = self._engine.translit_word(word, lang_code, topk=self._top_k)

            if not result:
                return None

            # IndicXlit API returns a flat list[str], not a dict
            if isinstance(result, list):
                candidates = result
            elif isinstance(result, dict) and lang_code in result:
                candidates = result[lang_code]
            else:
                return None

            if not candidates:
                return None

            # Rerank candidates using English dictionary
            if self._matcher:
                return self._rerank_candidates(candidates)

            # Without dictionary, just return top candidate
            return candidates[0]

        except Exception as e:
            logger.debug("IndicXlit transliteration failed for %r (%s): %s",
                         word, lang_code, e)
            return None

    def _rerank_candidates(self, candidates: list[str]) -> str:
        """Rerank IndicXlit candidates, preferring English dictionary matches.

        Scoring:
        1. Exact English dictionary hit → highest priority
        2. Phonetic English match → medium priority
        3. Original beam order → fallback
        """
        best_score = -1.0
        best_word = candidates[0]  # Default to top beam candidate

        for i, candidate in enumerate(candidates):
            candidate_lower = candidate.lower().strip()

            # Check against English dictionary
            is_eng, match = self._matcher.is_english(candidate_lower, threshold=0.5)

            if is_eng and match is not None:
                # Weight: dictionary score + beam position bonus
                beam_bonus = 0.1 * (1.0 - i / len(candidates))
                score = match.score + beam_bonus

                if score > best_score:
                    best_score = score
                    best_word = match.english_word
            else:
                # No dictionary match — use beam score as tiebreaker
                score = 0.1 * (1.0 - i / len(candidates))
                if score > best_score:
                    best_score = score
                    best_word = candidate_lower

        return best_word

    def batch_transliterate(
        self,
        words: list[tuple[str, str]],
    ) -> list[str | None]:
        """Batch transliterate multiple words.

        Args:
            words: List of (word, lang_code) tuples.

        Returns:
            List of transliterated words (or None for failures).
        """
        return [self.transliterate(w, lc) for w, lc in words]

    def generate_warm_cache(
        self,
        english_words: list[str],
        lang_code: str,
        output_path: str | Path,
    ) -> dict[str, str]:
        """Generate a warm cache by transliterating English words to Indic and storing reverse mapping.

        This creates a {indic_word: english_word} lookup table for fast-path resolution.
        Requires IndicXlit to be available.

        Args:
            english_words: List of English words to transliterate.
            lang_code: Target language code.
            output_path: Path to save the JSON cache file.

        Returns:
            Dictionary mapping Indic words to English words.
        """
        if not self._available or self._engine is None:
            logger.error("IndicXlit not available; cannot generate warm cache")
            return {}

        cache: dict[str, str] = {}
        for word in english_words:
            try:
                # Transliterate English → Indic (Roman-to-Native direction)
                # Note: This requires a separate engine instance for en->indic
                result = self._engine.translit_word(word, lang_code, topk=1)
                if not result:
                    continue
                candidates = result if isinstance(result, list) else result.get(lang_code, [])
                if candidates:
                    indic_form = candidates[0]
                    cache[indic_form] = word.lower()
            except Exception as e:
                logger.debug("Warm cache generation failed for %r: %s", word, e)

        # Save to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

        logger.info("Generated warm cache for %s: %d entries -> %s",
                     lang_code, len(cache), output_path)
        return cache
