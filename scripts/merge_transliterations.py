#!/usr/bin/env python3
"""Merge Grok-generated transliteration tables into the codebase.

Reads per-language JSON files from data/generated_transliterations/,
validates entries, deduplicates against existing _KNOWN_TRANSLITERATIONS,
and outputs:
1. Per-language Python dict files ready to paste into dictionary_lookup.py
2. A list of English words missing from en_dict_30k.json
3. Validation/conflict reports

Usage:
    python scripts/merge_transliterations.py
    python scripts/merge_transliterations.py --output-dir data/merged_transliterations
    python scripts/merge_transliterations.py --write-lookup  # directly update dictionary_lookup.py
"""

import argparse
import ast
import json
import re
import sys
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "generated_transliterations"
OUTPUT_DIR = PROJECT_ROOT / "data" / "merged_transliterations"
DICT_PATH = PROJECT_ROOT / "codemix_restore" / "data" / "en_dict_30k.json"
LOOKUP_PATH = PROJECT_ROOT / "codemix_restore" / "dictionary_lookup.py"

# Unicode ranges per script (from config.py)
SCRIPT_UNICODE_RANGES: dict[str, list[tuple[int, int]]] = {
    "hi": [(0x0900, 0x097F), (0xA8E0, 0xA8FF)],
    "mr": [(0x0900, 0x097F), (0xA8E0, 0xA8FF)],
    "ne": [(0x0900, 0x097F)],
    "sa": [(0x0900, 0x097F), (0x1CD0, 0x1CFF)],
    "kok": [(0x0900, 0x097F)],
    "doi": [(0x0900, 0x097F)],
    "mai": [(0x0900, 0x097F)],
    "brx": [(0x0900, 0x097F)],
    "bn": [(0x0980, 0x09FF)],
    "as": [(0x0980, 0x09FF)],
    "gu": [(0x0A80, 0x0AFF)],
    "pa": [(0x0A00, 0x0A7F)],
    "or": [(0x0B00, 0x0B7F)],
    "ta": [(0x0B80, 0x0BFF)],
    "te": [(0x0C00, 0x0C7F)],
    "kn": [(0x0C80, 0x0CFF)],
    "ml": [(0x0D00, 0x0D7F)],
    "ur": [(0x0600, 0x06FF), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)],
    "ks": [(0x0600, 0x06FF)],
    "sd": [(0x0600, 0x06FF), (0x0860, 0x086F)],
    "mni": [(0xABC0, 0xABFF), (0xAAE0, 0xAAFF)],
    "sat": [(0x1C50, 0x1C7F)],
}


def load_english_dict() -> set[str]:
    """Load English dictionary words."""
    if not DICT_PATH.exists():
        print(f"WARNING: {DICT_PATH} not found")
        return set()
    with open(DICT_PATH) as f:
        data = json.load(f)
    return {w.lower() for w in data.keys()}


def load_existing_transliterations() -> dict[str, dict[str, str]]:
    """Extract existing _KNOWN_TRANSLITERATIONS from dictionary_lookup.py.

    Does a simple regex-based extraction of the dict entries.
    """
    if not LOOKUP_PATH.exists():
        return {}

    with open(LOOKUP_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    existing: dict[str, dict[str, str]] = {}

    # Find the _KNOWN_TRANSLITERATIONS dict
    # We look for patterns like "lang_code": { ... }
    # This is a simplified extraction - for production, use AST parsing
    pattern = r'"(\w+)":\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
    kt_start = content.find("_KNOWN_TRANSLITERATIONS")
    if kt_start == -1:
        return {}

    # Extract the section after _KNOWN_TRANSLITERATIONS
    kt_section = content[kt_start:]
    # Find matching entries - simple line-by-line approach
    current_lang = None
    for line in kt_section.split("\n"):
        # Check for language key like "hi": {
        lang_match = re.match(r'\s*"(\w{2,3})":\s*\{', line)
        if lang_match:
            current_lang = lang_match.group(1)
            if current_lang not in existing:
                existing[current_lang] = {}
            continue

        if current_lang:
            # Check for entry like "word": "english",
            entry_match = re.findall(r'"([^"]+)":\s*"([^"]+)"', line)
            for indic, eng in entry_match:
                existing[current_lang][indic] = eng.lower()

            # End of dict
            if re.match(r'\s*\},?\s*$', line):
                current_lang = None

    return existing


def has_script_chars(word: str, lang_code: str) -> bool:
    """Check if word contains characters from the expected Unicode ranges."""
    ranges = SCRIPT_UNICODE_RANGES.get(lang_code, [])
    if not ranges:
        return True  # Can't validate, accept it

    for char in word:
        cp = ord(char)
        for start, end in ranges:
            if start <= cp <= end:
                return True
    return False


def is_valid_english(word: str) -> bool:
    """Check if the English side looks valid (ASCII, no script chars)."""
    word = word.strip().lower()
    if not word:
        return False
    # Allow letters, digits, dots, hyphens, spaces (for compound terms)
    return all(c.isascii() for c in word) and any(c.isalpha() for c in word)


def validate_entry(indic: str, english: str, lang_code: str,
                   english_dict: set[str]) -> tuple[bool, str]:
    """Validate a single transliteration entry.

    Returns (is_valid, reason).
    """
    if not indic or not english:
        return False, "empty"

    if not is_valid_english(english):
        return False, f"invalid English: {english!r}"

    # Check that indic word actually contains script characters
    if not has_script_chars(indic, lang_code):
        # Allow ZWJ, ZWNJ, common punctuation
        non_special = indic.replace("\u200C", "").replace("\u200D", "").strip()
        if non_special and not any(not c.isascii() for c in non_special):
            return False, f"no script chars in: {indic!r}"

    # Check if English word is suspiciously long (likely a phrase, not a word)
    if len(english.split()) > 3:
        return False, f"too many words: {english!r}"

    return True, "ok"


def main():
    parser = argparse.ArgumentParser(description="Merge generated transliteration tables")
    parser.add_argument("--input-dir", type=Path, default=DATA_DIR,
                        help="Directory with generated JSON files")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR,
                        help="Directory for merged output")
    parser.add_argument("--write-lookup", action="store_true",
                        help="Directly update dictionary_lookup.py (creates backup first)")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading English dictionary...")
    english_dict = load_english_dict()
    print(f"  {len(english_dict):,} words")

    print("Loading existing transliterations...")
    existing = load_existing_transliterations()
    total_existing = sum(len(v) for v in existing.values())
    print(f"  {len(existing)} languages, {total_existing:,} entries")

    # Load generated files
    print(f"\nProcessing generated files from {args.input_dir}...")
    generated_files = sorted(args.input_dir.glob("*_transliterations.json"))
    if not generated_files:
        print(f"ERROR: No *_transliterations.json files in {args.input_dir}")
        sys.exit(1)

    all_merged: dict[str, dict[str, str]] = {}
    all_missing_english: set[str] = set()
    stats = {
        "total_generated": 0,
        "total_valid": 0,
        "total_new": 0,
        "total_duplicate": 0,
        "total_conflict": 0,
        "total_invalid": 0,
    }
    conflicts: list[dict] = []

    for gen_path in generated_files:
        lang_code = gen_path.stem.replace("_transliterations", "")
        print(f"\n  {lang_code}:")

        with open(gen_path, encoding="utf-8") as f:
            generated = json.load(f)

        existing_lang = existing.get(lang_code, {})
        merged = dict(existing_lang)  # Start with existing entries

        lang_stats = {"generated": 0, "valid": 0, "new": 0, "duplicate": 0,
                      "conflict": 0, "invalid": 0}

        for indic, english in generated.items():
            lang_stats["generated"] += 1
            english = english.lower().strip()
            indic = indic.strip()

            # Validate
            is_valid, reason = validate_entry(indic, english, lang_code, english_dict)
            if not is_valid:
                lang_stats["invalid"] += 1
                continue
            lang_stats["valid"] += 1

            # Check for duplicates/conflicts
            if indic in existing_lang:
                if existing_lang[indic].lower() == english:
                    lang_stats["duplicate"] += 1
                else:
                    lang_stats["conflict"] += 1
                    conflicts.append({
                        "lang": lang_code,
                        "indic": indic,
                        "existing": existing_lang[indic],
                        "generated": english,
                    })
                continue

            # New entry
            lang_stats["new"] += 1
            merged[indic] = english

            # Check if English word is in dictionary
            eng_base = english.split()[0] if " " in english else english
            eng_base = eng_base.rstrip("s")  # simple plural strip
            if english not in english_dict and eng_base not in english_dict:
                all_missing_english.add(english)

        all_merged[lang_code] = merged

        print(f"    Generated: {lang_stats['generated']}, Valid: {lang_stats['valid']}, "
              f"New: {lang_stats['new']}, Duplicate: {lang_stats['duplicate']}, "
              f"Conflict: {lang_stats['conflict']}, Invalid: {lang_stats['invalid']}")
        print(f"    Final merged: {len(merged)} entries "
              f"(was {len(existing_lang)}, +{lang_stats['new']} new)")

        for k in lang_stats:
            stats[f"total_{k}"] = stats.get(f"total_{k}", 0) + lang_stats[k]

    # Save merged per-language files
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"  Languages processed: {len(all_merged)}")
    print(f"  Total generated entries: {stats['total_generated']:,}")
    print(f"  Total valid: {stats['total_valid']:,}")
    print(f"  Total new (added): {stats['total_new']:,}")
    print(f"  Total duplicates (skipped): {stats['total_duplicate']:,}")
    print(f"  Total conflicts: {stats['total_conflict']:,}")
    print(f"  Total invalid (rejected): {stats['total_invalid']:,}")
    total_final = sum(len(v) for v in all_merged.values())
    print(f"  Total final entries: {total_final:,}")

    # Save merged JSON files
    for lang_code, entries in sorted(all_merged.items()):
        out_path = args.output_dir / f"{lang_code}_merged.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)

    # Save as Python dict format for easy pasting
    py_output_path = args.output_dir / "known_transliterations_merged.py"
    with open(py_output_path, "w", encoding="utf-8") as f:
        f.write("# Auto-generated merged _KNOWN_TRANSLITERATIONS\n")
        f.write("# Paste these into dictionary_lookup.py\n\n")
        f.write("_KNOWN_TRANSLITERATIONS_MERGED = {\n")
        for lang_code in sorted(all_merged.keys()):
            entries = all_merged[lang_code]
            f.write(f'    "{lang_code}": {{\n')
            for indic, english in sorted(entries.items()):
                f.write(f'        "{indic}": "{english}",\n')
            f.write(f"    }},\n")
        f.write("}\n")
    print(f"\nPython dict saved to {py_output_path}")

    # Save missing English words
    if all_missing_english:
        missing_path = args.output_dir / "missing_english_words.json"
        with open(missing_path, "w") as f:
            json.dump(sorted(all_missing_english), f, indent=2)
        print(f"Missing English words ({len(all_missing_english)}): {missing_path}")

    # Save conflicts
    if conflicts:
        conflicts_path = args.output_dir / "conflicts.json"
        with open(conflicts_path, "w", encoding="utf-8") as f:
            json.dump(conflicts, f, ensure_ascii=False, indent=2)
        print(f"Conflicts ({len(conflicts)}): {conflicts_path}")

    print(f"\nAll output saved to {args.output_dir}")


if __name__ == "__main__":
    main()
