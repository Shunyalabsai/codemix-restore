#!/usr/bin/env python3
"""Run codemix_restore on a stratified sample from ShunyaLabs ASR predictions.

Takes N records per language for balanced evaluation across all languages.
"""

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

from codemix_restore import ScriptRestorer

LANG_CODE_MAP = {
    "Hindi": "hi", "Bengali": "bn", "Tamil": "ta", "Telugu": "te",
    "Kannada": "kn", "Marathi": "mr", "Gujarati": "gu", "Punjabi": "pa",
    "Malayalam": "ml", "Odia": "or", "Assamese": "as", "Nepali": "ne",
    "Urdu": "ur", "Konkani": "kok", "Maithili": "mai", "Dogri": "doi",
    "Sindhi": "sd", "Kashmiri": "ks", "Sanskrit": "sa", "Bodo": "brx",
    "Manipuri": "mni", "Santali": "sat",
    "Bhojpuri": "bho", "Chhattisgarhi": "hne",
}

INPUT_FILES = [
    "shunyalabs_predictions_p1.jsonl",
    "shunyalabs_predictions-p2.jsonl",
]

# How many records per language
PER_LANG = int(sys.argv[1]) if len(sys.argv) > 1 else 500

OUTPUT_FILE = f"shunyalabs_restored_xlit_sample_{PER_LANG}.jsonl"
STATS_FILE = f"shunyalabs_restore_stats_xlit_sample_{PER_LANG}.json"


def count_english_words(text: str) -> int:
    count = 0
    for word in text.split():
        cleaned = word.strip(".,!?;:'\"()[]{}—–-")
        if cleaned.isascii() and cleaned.isalpha() and len(cleaned) >= 2:
            count += 1
    return count


def main():
    # First pass: collect stratified sample
    print(f"Collecting {PER_LANG} records per language...")
    lang_records = defaultdict(list)
    for input_file in INPUT_FILES:
        filepath = Path(input_file)
        if not filepath.exists():
            continue
        with open(filepath, encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue
                lang = record.get("language", "")
                if len(lang_records[lang]) < PER_LANG:
                    lang_records[lang].append(record)

    total_sampled = sum(len(v) for v in lang_records.values())
    print(f"Sampled {total_sampled} records across {len(lang_records)} languages:")
    for lang in sorted(lang_records.keys()):
        print(f"  {lang}: {len(lang_records[lang])}")

    # Process
    print("\nInitializing ScriptRestorer...")
    t0 = time.time()
    restorer = ScriptRestorer()
    print(f"Initialized in {time.time() - t0:.2f}s\n")

    stats = defaultdict(lambda: {
        "total": 0, "modified": 0, "unchanged": 0, "skipped": 0,
        "english_words_found": 0, "total_words_processed": 0, "errors": 0,
        "sample_modifications": [],
    })

    total_processed = 0
    total_modified = 0

    out_f = open(OUTPUT_FILE, "w", encoding="utf-8")

    for lang_name in sorted(lang_records.keys()):
        records = lang_records[lang_name]
        lang_code = LANG_CODE_MAP.get(lang_name)
        lang_start = time.time()

        for record in records:
            prediction = record.get("prediction", "")
            lang_stats = stats[lang_name]
            lang_stats["total"] += 1
            total_processed += 1

            if not lang_code or not prediction.strip():
                lang_stats["skipped"] += 1
                record["restored"] = prediction
                record["restore_changed"] = False
                out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                continue

            try:
                restored = restorer.restore(prediction, lang_code)
            except Exception as e:
                lang_stats["errors"] += 1
                record["restored"] = prediction
                record["restore_changed"] = False
                record["restore_error"] = str(e)
                out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                continue

            changed = restored != prediction
            eng_words = count_english_words(restored)
            lang_stats["total_words_processed"] += len(prediction.split())
            lang_stats["english_words_found"] += eng_words

            if changed:
                lang_stats["modified"] += 1
                total_modified += 1
                if len(lang_stats["sample_modifications"]) < 10:
                    lang_stats["sample_modifications"].append({
                        "original": prediction,
                        "restored": restored,
                    })
            else:
                lang_stats["unchanged"] += 1

            record["restored"] = restored
            record["restore_changed"] = changed
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")

        elapsed_lang = time.time() - lang_start
        rate = len(records) / elapsed_lang if elapsed_lang > 0 else 0
        mod_pct = lang_stats["modified"] / lang_stats["total"] * 100 if lang_stats["total"] > 0 else 0
        print(f"  {lang_name:<16} {len(records):>5} records in {elapsed_lang:.1f}s "
              f"({rate:.1f}/s) | Modified: {lang_stats['modified']} ({mod_pct:.1f}%)")

    out_f.close()

    elapsed = time.time() - t0
    print(f"\nDone! Processed {total_processed:,} predictions in {elapsed:.1f}s "
          f"({total_processed/elapsed:.0f}/s)")
    print(f"Modified: {total_modified:,} ({total_modified/total_processed*100:.1f}%)")

    # Summary table
    print(f"\n{'='*90}")
    print(f"{'Language':<16}{'Total':>10}{'Modified':>10}{'Unchanged':>10}"
          f"{'Skipped':>10}{'Mod%':>8}{'EngWords':>10}")
    print(f"{'-'*90}")

    for lang_name in sorted(stats.keys(), key=lambda x: -stats[x]["total"]):
        s = stats[lang_name]
        mod_pct = f"{s['modified']/s['total']*100:.1f}%" if s["total"] > 0 else "N/A"
        print(f"{lang_name:<16}{s['total']:>10,}{s['modified']:>10,}{s['unchanged']:>10,}"
              f"{s['skipped']:>10,}{mod_pct:>8}{s['english_words_found']:>10,}")

    print(f"{'-'*90}")
    total_eng = sum(s["english_words_found"] for s in stats.values())
    total_skip = sum(s["skipped"] for s in stats.values())
    mod_pct = f"{total_modified/total_processed*100:.1f}%"
    print(f"{'TOTAL':<16}{total_processed:>10,}{total_modified:>10,}"
          f"{total_processed-total_modified-total_skip:>10,}{total_skip:>10,}"
          f"{mod_pct:>8}{total_eng:>10,}")

    # Sample modifications
    print(f"\n{'='*90}")
    print("SAMPLE MODIFICATIONS (first 5 per language)")
    print(f"{'='*90}")
    for lang_name in sorted(stats.keys(), key=lambda x: -stats[x]["modified"]):
        samples = stats[lang_name]["sample_modifications"][:5]
        if not samples:
            continue
        print(f"\n--- {lang_name} ({stats[lang_name]['modified']:,} modified) ---")
        for i, s in enumerate(samples, 1):
            print(f"  {i}. Original: {s['original']}")
            print(f"     Restored: {s['restored']}")

    # Save stats
    stats_out = {lang: {k: v for k, v in s.items()} for lang, s in stats.items()}
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats_out, f, ensure_ascii=False, indent=2)
    print(f"\nStats saved to {STATS_FILE}")
    print(f"Results saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
