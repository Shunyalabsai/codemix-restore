#!/usr/bin/env python3
"""Extract native vocabulary from Shunyalabs ASR predictions to expand native word lists.

Reads prediction JSONL files, extracts words per language, filters by script,
excludes known English transliterations, and merges with existing word lists.
"""

import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

# Reuse infrastructure from build_native_wordlists.py
sys.path.insert(0, str(Path(__file__).parent))
from build_native_wordlists import (
    SCRIPT_RANGES, LANG_SCRIPTS,
    is_native_script, is_latin, has_digits, clean_word,
    filter_words, merge_with_existing, write_wordlist,
    DATA_DIR,
)

PROJECT_DIR = Path(__file__).parent.parent

INPUT_FILES = [
    PROJECT_DIR / "shunyalabs_predictions_p1.jsonl",
    PROJECT_DIR / "shunyalabs_predictions-p2.jsonl",
]

LANG_CODE_MAP = {
    "Hindi": "hi", "Bengali": "bn", "Tamil": "ta", "Telugu": "te",
    "Kannada": "kn", "Marathi": "mr", "Gujarati": "gu", "Punjabi": "pa",
    "Malayalam": "ml", "Odia": "or", "Assamese": "as", "Nepali": "ne",
    "Urdu": "ur", "Konkani": "kok", "Maithili": "mai", "Dogri": "doi",
    "Sindhi": "sd", "Kashmiri": "ks", "Sanskrit": "sa", "Bodo": "brx",
    "Manipuri": "mni", "Santali": "sat",
    # Unsupported but in data:
    "Bhojpuri": "bho", "Chhattisgarhi": "hne",
}


def load_known_transliteration_keys() -> dict[str, set[str]]:
    """Load all Indic-script keys from _KNOWN_TRANSLITERATIONS in dictionary_lookup.py.

    These words must NOT appear in native word lists, as they are legitimate
    English loanwords that need to be detected.
    """
    # Import the actual dict from the module
    sys.path.insert(0, str(PROJECT_DIR))
    from codemix_restore.dictionary_lookup import DictionaryLookup

    keys_by_lang: dict[str, set[str]] = defaultdict(set)
    for lang_code, overrides in DictionaryLookup._KNOWN_TRANSLITERATIONS.items():
        for indic_word in overrides.keys():
            keys_by_lang[lang_code].add(indic_word)
    return dict(keys_by_lang)


def extract_words_from_predictions() -> dict[str, Counter]:
    """Extract and count all words from ASR predictions, grouped by language."""
    word_counts: dict[str, Counter] = defaultdict(Counter)

    for input_file in INPUT_FILES:
        if not input_file.exists():
            print(f"  Warning: {input_file} not found, skipping")
            continue

        print(f"  Reading {input_file.name}...")
        with open(input_file, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    record = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue

                lang_name = record.get("language", "")
                lang_code = LANG_CODE_MAP.get(lang_name)
                if not lang_code:
                    continue

                prediction = record.get("prediction", "")
                if not prediction:
                    continue

                # Split on whitespace and clean each word
                for raw_word in prediction.split():
                    word = clean_word(raw_word)
                    if word and len(word) >= 2:
                        word_counts[lang_code][word] += 1

        print(f"    Done. Languages so far: {sorted(word_counts.keys())}")

    return dict(word_counts)


def filter_native_words(
    word_counts: Counter,
    lang_code: str,
    known_translit_keys: set[str],
    max_words: int = 50000,
) -> list[str]:
    """Filter word counts to only native-script words, excluding known transliterations."""
    script = LANG_SCRIPTS.get(lang_code)
    if not script:
        print(f"    Warning: No script mapping for {lang_code}, skipping")
        return []

    # Convert counter to (word, freq) list for filter_words()
    word_freq_list = [(word, count) for word, count in word_counts.items()]

    # Use the standard filter (script check, latin exclusion, digit exclusion, length)
    filtered = filter_words(word_freq_list, script, max_words=max_words * 2)  # over-select, trim after exclusion

    # Exclude known transliteration keys AND their agglutinated forms
    # (e.g., "ઓફિસમાં" should be excluded because "ઓફિસ" is a known loanword)
    excluded_count = 0
    final = []
    for word in filtered:
        if word in known_translit_keys:
            excluded_count += 1
            continue
        # Check if any known key is a prefix (catches agglutinated forms)
        is_agglutinated = False
        for key in known_translit_keys:
            if len(key) >= 2 and word.startswith(key) and len(word) > len(key):
                is_agglutinated = True
                break
        if is_agglutinated:
            excluded_count += 1
            continue
        final.append(word)
        if len(final) >= max_words:
            break

    if excluded_count:
        print(f"    Excluded {excluded_count} known transliteration keys")

    return final


def main():
    max_words = int(sys.argv[1]) if len(sys.argv) > 1 else 50000

    print("Step 1: Loading known transliteration keys...")
    known_keys = load_known_transliteration_keys()
    total_keys = sum(len(v) for v in known_keys.values())
    print(f"  Loaded {total_keys} keys across {len(known_keys)} languages\n")

    print("Step 2: Extracting words from ASR predictions...")
    word_counts = extract_words_from_predictions()
    print()

    print("Step 3: Filtering and expanding native word lists...")
    for lang_code in sorted(word_counts.keys()):
        if lang_code not in LANG_SCRIPTS:
            print(f"  {lang_code}: No script mapping (unsupported), skipping")
            continue

        counts = word_counts[lang_code]
        translit_keys = known_keys.get(lang_code, set())

        # Also get transliteration keys from related languages sharing the same script
        # e.g., Assamese shares Bengali script, Maithili shares Devanagari
        script = LANG_SCRIPTS[lang_code]
        for other_lang, other_script in LANG_SCRIPTS.items():
            if other_script == script and other_lang != lang_code:
                translit_keys = translit_keys | known_keys.get(other_lang, set())

        print(f"  {lang_code}: {len(counts):,} unique raw words, {sum(counts.values()):,} total occurrences")

        filtered = filter_native_words(counts, lang_code, translit_keys, max_words=max_words)
        print(f"    After filtering: {len(filtered):,} native words")

        # Rebuild word list (replace, don't merge, to ensure exclusions take effect)
        output_file = DATA_DIR / f"{lang_code}_common.txt"
        merged = sorted(filtered)
        print(f"    Final word list: {len(merged):,} words")

        write_wordlist(merged, lang_code, output_file,
                       source=f"Shunyalabs ASR predictions ({len(counts):,} unique words)")
        print(f"    Written to {output_file.name}")

    print("\nDone! Summary:")
    for lang_code in sorted(LANG_SCRIPTS.keys()):
        filepath = DATA_DIR / f"{lang_code}_common.txt"
        if filepath.exists():
            count = sum(1 for line in open(filepath) if line.strip() and not line.startswith("#"))
            print(f"  {lang_code}: {count:,} words")


if __name__ == "__main__":
    main()
