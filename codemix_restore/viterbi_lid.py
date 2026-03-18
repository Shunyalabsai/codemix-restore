"""HMM-based sequence tagger using the Viterbi algorithm.

Replaces the greedy per-token language identification in Stage 3 with
a globally optimal sequence decoder.  The two hidden states are
E (English / transliterated) and N (Native).  Emission probabilities
come from the existing WordLanguageIdentifier signals; transition
probabilities encode the observation that consecutive tokens usually
share a language (language inertia).

Usage inside pipeline.py:

    tagger = ViterbiSequenceTagger(lid=self._lid)
    labels = tagger.tag_sequence(tokens, lookup_results, config, skip_positions, lang)
    # labels: dict[int, str]  mapping token position -> "E" or "N"
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass

from codemix_restore.config import LanguageConfig
from codemix_restore.dictionary_lookup import Confidence, LookupResult
from codemix_restore.language_id import WordLanguageIdentifier
from codemix_restore.tokenizer import ScriptType, Token

logger = logging.getLogger(__name__)

# Sentence-ending punctuation (universal + Indic)
_SENTENCE_ENDERS: set[str] = {".", "?", "!", "।", "॥", "۔", "؟"}

# The two HMM states
_STATES = ("E", "N")

# Default transition matrix --------------------------------------------------
# Rows = previous state, columns = current state.
#
# N→N (0.85): native is the dominant language in code-mixed ASR.
# E→E (0.70): English spans are typically short (1-4 words).
# N→E (0.15): switching into English is relatively uncommon per boundary.
# E→N (0.30): switching back to native after short English insertions.
DEFAULT_TRANSITION: dict[tuple[str, str], float] = {
    ("E", "E"): 0.70,
    ("E", "N"): 0.30,
    ("N", "E"): 0.15,
    ("N", "N"): 0.85,
}

# Initial state distribution (most sentences start native)
DEFAULT_INITIAL: dict[str, float] = {"E": 0.20, "N": 0.80}


# ---------------------------------------------------------------------------
# Pure Viterbi DP
# ---------------------------------------------------------------------------

def _viterbi(
    emissions: list[tuple[float, float]],
    trans: dict[tuple[str, str], float],
    initial: dict[str, float],
) -> list[str]:
    """Viterbi decoding for a 2-state (E/N) HMM in log-space.

    Args:
        emissions: Per-position (P_english, P_native).  Values should be
            in (0, 1) — will be clamped to avoid log(0).
        trans: Transition probabilities keyed by (prev_state, curr_state).
        initial: Start-state probabilities.

    Returns:
        Optimal state sequence as a list of "E" / "N" strings.
    """
    n = len(emissions)
    if n == 0:
        return []

    # Pre-compute log values
    log_trans = {k: math.log(max(v, 1e-10)) for k, v in trans.items()}
    log_init = {s: math.log(max(initial[s], 1e-10)) for s in _STATES}

    # dp[t] = {state: (log_prob, backpointer_state)}
    dp: list[dict[str, tuple[float, str | None]]] = [{} for _ in range(n)]

    # --- Initialisation (t = 0) ---
    for si, s in enumerate(_STATES):
        emit_p = max(emissions[0][si], 1e-10)
        dp[0][s] = (log_init[s] + math.log(emit_p), None)

    # --- Forward pass ---
    for t in range(1, n):
        for si, s in enumerate(_STATES):
            best_score = -math.inf
            best_prev: str | None = None
            for prev_s in _STATES:
                score = dp[t - 1][prev_s][0] + log_trans[(prev_s, s)]
                if score > best_score:
                    best_score = score
                    best_prev = prev_s
            emit_p = max(emissions[t][si], 1e-10)
            dp[t][s] = (best_score + math.log(emit_p), best_prev)

    # --- Backtrace ---
    best_final = max(_STATES, key=lambda s: dp[n - 1][s][0])
    path: list[str] = [best_final]
    for t in range(n - 1, 0, -1):
        path.append(dp[t][path[-1]][1])  # type: ignore[arg-type]
    path.reverse()
    return path


# ---------------------------------------------------------------------------
# Sequence tagger (wraps Viterbi with pipeline integration logic)
# ---------------------------------------------------------------------------

class ViterbiSequenceTagger:
    """Tags a sequence of Indic tokens as English or Native using HMM/Viterbi.

    Emission probabilities are computed from the existing
    ``WordLanguageIdentifier.classify()`` method (called *without* context
    arguments so that Viterbi transitions handle context instead).

    HIGH/LOW confidence tokens participate as **clamped anchors** — their
    emissions are forced to near-certainty so they constrain the Viterbi
    path and propagate influence to neighbouring ambiguous tokens.
    """

    def __init__(
        self,
        lid: WordLanguageIdentifier,
        transition: dict[tuple[str, str], float] | None = None,
        initial: dict[str, float] | None = None,
    ):
        self._lid = lid
        self._trans = transition or DEFAULT_TRANSITION
        self._initial = initial or DEFAULT_INITIAL

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def tag_sequence(
        self,
        tokens: list[Token],
        lookup_results: dict[int, LookupResult],
        config: LanguageConfig,
        skip_positions: set[int],
        lang_code: str,
    ) -> dict[int, str]:
        """Label every INDIC token in *tokens* as ``"E"`` or ``"N"``.

        Returns:
            Mapping of ``token.position`` → ``"E"`` / ``"N"`` for all
            INDIC tokens that are not in *skip_positions*.
        """
        # Collect INDIC tokens (preserving order) that need classification
        indic_tokens: list[Token] = [
            t for t in tokens
            if t.script_type == ScriptType.INDIC and t.position not in skip_positions
        ]

        if not indic_tokens:
            return {}

        # Split into segments at sentence-ending punctuation
        segments = self._segment_by_punctuation(indic_tokens, tokens)

        result: dict[int, str] = {}
        for segment in segments:
            seg_result = self._tag_segment(segment, lookup_results, config, lang_code)
            result.update(seg_result)
        return result

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _segment_by_punctuation(
        self,
        indic_tokens: list[Token],
        all_tokens: list[Token],
    ) -> list[list[Token]]:
        """Split *indic_tokens* into sub-lists wherever a sentence-ending
        punctuation token appears between two consecutive INDIC tokens.

        We look at the *all_tokens* list to find punctuation between the
        positions of consecutive INDIC tokens.
        """
        if len(indic_tokens) <= 1:
            return [indic_tokens]

        # Build a quick position → token lookup for the full token list
        pos_to_token: dict[int, Token] = {t.position: t for t in all_tokens}

        segments: list[list[Token]] = []
        current_segment: list[Token] = [indic_tokens[0]]

        for idx in range(1, len(indic_tokens)):
            prev_pos = indic_tokens[idx - 1].position
            curr_pos = indic_tokens[idx].position

            # Check if any token between prev_pos and curr_pos is a
            # sentence-ending punctuation mark.
            has_boundary = False
            for p in range(prev_pos + 1, curr_pos):
                t = pos_to_token.get(p)
                if t and t.script_type == ScriptType.PUNCTUATION and t.text in _SENTENCE_ENDERS:
                    has_boundary = True
                    break

            if has_boundary:
                segments.append(current_segment)
                current_segment = [indic_tokens[idx]]
            else:
                current_segment.append(indic_tokens[idx])

        segments.append(current_segment)
        return segments

    def _tag_segment(
        self,
        segment: list[Token],
        lookup_results: dict[int, LookupResult],
        config: LanguageConfig,
        lang_code: str,
    ) -> dict[int, str]:
        """Run Viterbi on a single sentence segment and return labels."""
        emissions: list[tuple[float, float]] = []
        for token in segment:
            lookup = lookup_results.get(token.position)
            em = self._compute_emission(token, lookup, config, lang_code)
            emissions.append(em)

        if len(segment) == 1:
            # Single token: threshold-based decision (Viterbi adds no value)
            label = "E" if emissions[0][0] >= 0.65 else "N"
            return {segment[0].position: label}

        # Short segments (2 tokens) without a HIGH-confidence anchor can be
        # overpowered by the N→N transition inertia (0.85), swallowing weak
        # English matches that the greedy classifier would accept at 0.65.
        # Fall back to per-token threshold for these cases.
        if len(segment) == 2:
            has_anchor = any(em[0] >= 0.95 or em[1] >= 0.95 for em in emissions)
            if not has_anchor:
                return {
                    token.position: ("E" if em[0] >= 0.65 else "N")
                    for token, em in zip(segment, emissions)
                }

        labels = _viterbi(emissions, self._trans, self._initial)
        return {token.position: label for token, label in zip(segment, labels)}

    def _compute_emission(
        self,
        token: Token,
        lookup: LookupResult | None,
        config: LanguageConfig,
        lang_code: str,
    ) -> tuple[float, float]:
        """Compute (P_english, P_native) for a single token.

        HIGH / LOW confidence tokens are clamped to near-certainty so they
        act as anchors in the Viterbi path.
        """
        # Clamped anchors for HIGH / LOW confidence
        if lookup and lookup.confidence == Confidence.HIGH and lookup.english_match:
            return (0.99, 0.01)
        if lookup and lookup.confidence == Confidence.LOW:
            return (0.01, 0.99)

        # For MEDIUM / AMBIGUOUS: use the LID classifier *without* context
        # (context is handled by Viterbi transitions, not the signal).
        lid_result = self._lid.classify(
            word=token.text,
            script_name=token.script_name or config.script_name,
            lookup_result=lookup,
            prev_is_english=None,
            next_is_english=None,
            lang_code=lang_code,
        )

        p_eng = max(0.01, min(0.99, lid_result.probability))
        return (p_eng, 1.0 - p_eng)
