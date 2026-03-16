#!/usr/bin/env python3
"""Build a comprehensive English dictionary from CMU Dict + SUBTLEX-US.

Downloads:
  1. CMU Pronouncing Dictionary (~134K words with phonetic transcriptions)
  2. SUBTLEX-US word frequencies (~74K words from movie subtitles)

Joins them to produce a frequency-ranked dictionary of real English words.
Outputs JSON: {"word": frequency_count, ...}

Usage:
    python scripts/build_dictionary.py [--top-k 30000] [--output path/to/dict.json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

# CMU Dict: one of the most comprehensive open English pronunciation dictionaries
CMU_DICT_URL = "https://raw.githubusercontent.com/cmusphinx/cmudict/master/cmudict.dict"

# SUBTLEX-US: word frequency from 51M words of American English movie subtitles
# JSON format from the words/subtlex-word-frequencies repo: {"word": count, ...}
SUBTLEX_URL = "https://raw.githubusercontent.com/words/subtlex-word-frequencies/master/index.json"


def download(url: str, description: str) -> str:
    """Download a URL and return the text content."""
    print(f"Downloading {description}...")
    print(f"  URL: {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "codemix-restore/0.1"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read().decode("utf-8", errors="replace")
        print(f"  Downloaded {len(data):,} bytes")
        return data
    except Exception as e:
        print(f"  FAILED: {e}")
        return ""


def parse_cmu_dict(text: str) -> set[str]:
    """Parse CMU Pronouncing Dictionary, return set of lowercase words."""
    words = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(";;;"):
            continue
        # Format: "WORD  P1 P2 P3" or "WORD(2)  P1 P2 P3"
        parts = line.split(None, 1)
        if parts:
            word = parts[0].lower()
            # Remove variant markers like "(2)", "(3)"
            word = re.sub(r"\(\d+\)$", "", word)
            # Only keep alphabetic words (no abbreviations with periods, etc.)
            if word.isalpha() and len(word) >= 2:
                words.add(word)
    return words


def parse_subtlex(text: str) -> dict[str, int]:
    """Parse SUBTLEX-US frequency data, return {word: frequency_count}.

    Supports two formats:
    - JSON: {"word": count, ...} (from words/subtlex-word-frequencies repo)
    - TSV: Word<tab>FREQcount<tab>... (from original SUBTLEX-US download)
    """
    freqs: dict[str, int] = {}

    # Try JSON first (array of {word, count} or dict {word: count})
    text_stripped = text.strip()
    if text_stripped.startswith(("[", "{")):
        try:
            raw = json.loads(text_stripped)
            if isinstance(raw, list):
                # Array format: [{"word": "you", "count": 2134713}, ...]
                for entry in raw:
                    w = entry.get("word", "").lower().strip()
                    count = entry.get("count", 0)
                    if w.isalpha() and len(w) >= 2:
                        freqs[w] = int(count)
            elif isinstance(raw, dict):
                # Dict format: {"word": count, ...}
                for word, count in raw.items():
                    w = word.lower().strip()
                    if w.isalpha() and len(w) >= 2:
                        freqs[w] = int(count)
            return freqs
        except (json.JSONDecodeError, ValueError):
            pass

    # Fall back to TSV parsing
    lines = text.splitlines()
    if not lines:
        return freqs

    header = lines[0].lower().split("\t")
    try:
        word_idx = header.index("word")
    except ValueError:
        word_idx = 0
    try:
        freq_idx = header.index("freqcount")
    except ValueError:
        try:
            freq_idx = header.index("subtlwf")
        except ValueError:
            freq_idx = 1

    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) <= max(word_idx, freq_idx):
            continue
        word = parts[word_idx].lower().strip()
        try:
            freq = int(float(parts[freq_idx]))
        except (ValueError, IndexError):
            continue

        if word.isalpha() and len(word) >= 2:
            freqs[word] = freq

    return freqs


def build_dictionary(top_k: int = 30000) -> dict[str, int]:
    """Build the merged dictionary."""
    # Download sources
    cmu_text = download(CMU_DICT_URL, "CMU Pronouncing Dictionary")
    subtlex_text = download(SUBTLEX_URL, "SUBTLEX-US frequency list")

    if not cmu_text and not subtlex_text:
        print("ERROR: Could not download either source. Cannot build dictionary.")
        sys.exit(1)

    # Parse
    cmu_words = parse_cmu_dict(cmu_text) if cmu_text else set()
    print(f"CMU Dict: {len(cmu_words):,} unique words")

    subtlex_freqs = parse_subtlex(subtlex_text) if subtlex_text else {}
    print(f"SUBTLEX-US: {len(subtlex_freqs):,} unique words")

    if cmu_words and subtlex_freqs:
        # Intersection: words that are both valid English (CMU) and attested in usage (SUBTLEX)
        common = cmu_words & set(subtlex_freqs.keys())
        print(f"Intersection (CMU ∩ SUBTLEX): {len(common):,} words")
        merged = {w: subtlex_freqs[w] for w in common}
    elif subtlex_freqs:
        # Only SUBTLEX available
        print("Using SUBTLEX-US only (CMU download failed)")
        merged = subtlex_freqs
    else:
        # Only CMU available
        print("Using CMU Dict only (SUBTLEX download failed)")
        merged = {w: 1 for w in cmu_words}

    # Sort by frequency (highest first) and take top-k
    sorted_words = sorted(merged.items(), key=lambda x: -x[1])
    top_words = dict(sorted_words[:top_k])

    print(f"\nFinal dictionary: {len(top_words):,} words")
    if sorted_words:
        print(f"  Most frequent: {sorted_words[0][0]} ({sorted_words[0][1]:,})")
        print(f"  Least frequent (in top-k): {sorted_words[min(top_k, len(sorted_words)) - 1][0]} ({sorted_words[min(top_k, len(sorted_words)) - 1][1]:,})")

    return top_words


def main():
    parser = argparse.ArgumentParser(description="Build English dictionary for codemix_restore")
    parser.add_argument("--top-k", type=int, default=30000,
                        help="Number of top-frequency words to keep (default: 30000)")
    parser.add_argument("--output", type=str,
                        default=str(Path(__file__).parent.parent / "codemix_restore" / "data" / "en_dict_30k.json"),
                        help="Output JSON file path")
    args = parser.parse_args()

    dictionary = build_dictionary(top_k=args.top_k)

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(dictionary, f, ensure_ascii=True, indent=None, separators=(",", ":"))

    file_size = output_path.stat().st_size
    print(f"\nSaved to: {output_path}")
    print(f"File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
