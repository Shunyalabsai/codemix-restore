#!/usr/bin/env python3
"""Download and process native word frequency lists for all supported languages.

Sources:
- FrequencyWords (hermitdave/FrequencyWords on GitHub) — bn, ta, te, ml
- Motaitalic Hindi frequency list — hi
- Manually curated lists — all other languages

Output: codemix_restore/data/{lang_code}_common.txt files
"""

import re
import sys
import unicodedata
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "codemix_restore" / "data"
RAW_DIR = Path("/tmp/freq_data")

# Unicode ranges for each script — used to filter out non-native words
SCRIPT_RANGES = {
    "Devanagari": [(0x0900, 0x097F), (0xA8E0, 0xA8FF)],
    "Bengali": [(0x0980, 0x09FF)],
    "Tamil": [(0x0B80, 0x0BFF)],
    "Telugu": [(0x0C00, 0x0C7F)],
    "Kannada": [(0x0C80, 0x0CFF)],
    "Gujarati": [(0x0A80, 0x0AFF)],
    "Gurmukhi": [(0x0A00, 0x0A7F)],
    "Oriya": [(0x0B00, 0x0B7F)],
    "Malayalam": [(0x0D00, 0x0D7F)],
    "Urdu": [(0x0600, 0x06FF), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)],
    "Sindhi": [(0x0600, 0x06FF), (0xFB50, 0xFDFF)],
    "MeeteiMayek": [(0xABC0, 0xABFF), (0xAAE0, 0xAAFF)],
    "OlChiki": [(0x1C50, 0x1C7F)],
}

# Map language codes to their scripts
LANG_SCRIPTS = {
    "hi": "Devanagari", "mr": "Devanagari", "ne": "Devanagari",
    "sa": "Devanagari", "kok": "Devanagari", "doi": "Devanagari",
    "mai": "Devanagari", "brx": "Devanagari",
    "bn": "Bengali", "as": "Bengali",
    "ta": "Tamil", "te": "Telugu", "kn": "Kannada",
    "gu": "Gujarati", "pa": "Gurmukhi", "or": "Oriya",
    "ml": "Malayalam", "ur": "Urdu", "sd": "Sindhi",
    "mni": "MeeteiMayek", "sat": "OlChiki",
    "ks": "Urdu",  # Kashmiri uses Perso-Arabic
}


def is_native_script(word: str, script: str) -> bool:
    """Check if word is primarily in the expected native script."""
    ranges = SCRIPT_RANGES.get(script, [])
    if not ranges:
        return True  # No filter for unknown scripts

    native_chars = 0
    total_chars = 0
    for ch in word:
        cat = unicodedata.category(ch)
        if cat.startswith("M"):  # Combining marks — skip
            continue
        total_chars += 1
        cp = ord(ch)
        for start, end in ranges:
            if start <= cp <= end:
                native_chars += 1
                break

    if total_chars == 0:
        return False
    return native_chars / total_chars >= 0.8  # Allow some punctuation/numbers


def is_latin(word: str) -> bool:
    """Check if word contains Latin/ASCII letters (likely English loanword)."""
    return bool(re.search(r"[a-zA-Z]", word))


def has_digits(word: str) -> bool:
    """Check if word contains digits."""
    return bool(re.search(r"\d", word))


def clean_word(word: str) -> str:
    """Clean a word: strip whitespace, punctuation, etc."""
    word = word.strip()
    # Remove leading/trailing punctuation
    word = re.sub(r"^[।॥,.!?;:\"'()\[\]{}<>]+", "", word)
    word = re.sub(r"[।॥,.!?;:\"'()\[\]{}<>]+$", "", word)
    return word.strip()


def parse_frequency_file(filepath: Path, has_frequency: bool = True) -> list[tuple[str, int]]:
    """Parse a frequency file into (word, frequency) pairs."""
    results = []
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if has_frequency:
                # Format: "word frequency" (space or tab separated)
                parts = line.rsplit(None, 1)
                if len(parts) == 2:
                    word = parts[0]
                    try:
                        freq = int(parts[1])
                    except ValueError:
                        continue
                else:
                    word = parts[0]
                    freq = 1
            else:
                word = line
                freq = 1

            word = clean_word(word)
            if word:
                results.append((word, freq))

    return results


def filter_words(words: list[tuple[str, int]], script: str, max_words: int = 50000) -> list[str]:
    """Filter and rank words for a native word list."""
    # Sort by frequency (descending)
    words.sort(key=lambda x: x[1], reverse=True)

    seen = set()
    filtered = []
    for word, freq in words:
        if word in seen:
            continue
        seen.add(word)

        # Skip if too short or too long
        if len(word) < 2 or len(word) > 25:
            continue
        # Skip Latin words (English loanwords)
        if is_latin(word):
            continue
        # Skip words with digits
        if has_digits(word):
            continue
        # Skip if not in expected script
        if not is_native_script(word, script):
            continue

        filtered.append(word)
        if len(filtered) >= max_words:
            break

    return filtered


def merge_with_existing(new_words: list[str], existing_file: Path) -> list[str]:
    """Merge new words with an existing word list, preserving the existing words."""
    existing = set()
    if existing_file.exists():
        with open(existing_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    existing.add(line)

    # Add new words that aren't already in the existing list
    merged = list(existing)
    for word in new_words:
        if word not in existing:
            merged.append(word)

    return sorted(merged)


def write_wordlist(words: list[str], lang_code: str, filepath: Path, source: str):
    """Write a native word list file."""
    header = f"""# Native word frequency list for {lang_code}
# Source: {source}
# Used to prevent false-positive transliteration of native words.
# Words: {len(words)}
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(header)
        for word in words:
            f.write(word + "\n")

    print(f"  Wrote {len(words)} words to {filepath.name}")


def process_downloaded_data():
    """Process all downloaded frequency data files."""

    # === Hindi ===
    print("\n=== Hindi (hi) ===")
    hi_file = RAW_DIR / "mota_hi.txt"
    if hi_file.exists():
        words = parse_frequency_file(hi_file, has_frequency=False)
        filtered = filter_words(words, "Devanagari")
        output = DATA_DIR / "hi_common.txt"
        merged = merge_with_existing(filtered, output)
        write_wordlist(merged, "hi", output, "motaitalic + manually curated")
    else:
        print("  No data found, keeping existing file")

    # === Bengali ===
    print("\n=== Bengali (bn) ===")
    bn_file = RAW_DIR / "fw_bn.txt"
    if bn_file.exists():
        words = parse_frequency_file(bn_file, has_frequency=True)
        filtered = filter_words(words, "Bengali")
        output = DATA_DIR / "bn_common.txt"
        write_wordlist(filtered, "bn", output, "FrequencyWords (hermitdave/FrequencyWords)")

    # === Tamil ===
    print("\n=== Tamil (ta) ===")
    ta_file = RAW_DIR / "fw_ta.txt"
    if ta_file.exists():
        words = parse_frequency_file(ta_file, has_frequency=True)
        filtered = filter_words(words, "Tamil")
        output = DATA_DIR / "ta_common.txt"
        write_wordlist(filtered, "ta", output, "FrequencyWords (hermitdave/FrequencyWords)")

    # === Telugu ===
    print("\n=== Telugu (te) ===")
    te_file = RAW_DIR / "fw_te.txt"
    if te_file.exists():
        words = parse_frequency_file(te_file, has_frequency=True)
        filtered = filter_words(words, "Telugu")
        output = DATA_DIR / "te_common.txt"
        write_wordlist(filtered, "te", output, "FrequencyWords (hermitdave/FrequencyWords)")

    # === Malayalam ===
    print("\n=== Malayalam (ml) ===")
    ml_file = RAW_DIR / "fw_ml.txt"
    if ml_file.exists():
        words = parse_frequency_file(ml_file, has_frequency=True)
        filtered = filter_words(words, "Malayalam")
        output = DATA_DIR / "ml_common.txt"
        write_wordlist(filtered, "ml", output, "FrequencyWords (hermitdave/FrequencyWords)")


if __name__ == "__main__":
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    process_downloaded_data()
    print("\nDone! Check codemix_restore/data/ for output files.")
