# codemix_restore-shunyalabs

Restore English words from transliterated Indic script in code-mixed ASR output.

ASR models for Indian languages output everything in a single native script. When users code-switch (mix English with their native language), English words get transliterated into the native script. This library detects those English words and converts them back to Latin script, preserving native language words as-is.

```
Input  (ASR output):  "धन्यवाद फॉर योर हेल्प, थैंक यू सो मच।"
Output (restored):    "धन्यवाद for your help. Thank you so much."
```

## Installation

**Basic (rule-based only):**

```bash
pip install codemix_restore-shunyalabs
```

**With neural transliteration (recommended for best accuracy):**

```bash
# Step 1: Install codemix_restore with all resolvable neural deps (torch, omegaconf, hydra, etc.)
pip install "codemix_restore-shunyalabs[neural]"

# Step 2: Install fairseq and ai4bharat-transliteration (broken transitive deps, must skip resolution)
pip install fairseq==0.12.2 --no-deps
pip install ai4bharat-transliteration --no-deps
```

> **Why two steps?** `fairseq` requires `omegaconf<2.1`, but all omegaconf 2.0.x versions have invalid metadata that pip >= 24.1 rejects. Step 1 installs `omegaconf>=2.1` (valid metadata, works at runtime thanks to our compatibility patches). Step 2 installs fairseq/ai4bharat without pip trying to resolve their broken dependency tree.

The neural mode uses [IndicXlit](https://github.com/AI4Bharat/IndicXlit) (AI4Bharat's neural transliteration model) and PyTorch. This gives significantly better accuracy on novel/rare English words but requires more memory (~1.4 GB) and has higher latency (~115ms/word vs <5ms/word). The library includes built-in Python 3.12 compatibility patches for fairseq/hydra.

### Requirements

- Python 3.10+

**Core dependencies (installed automatically):**

| Package | Purpose |
|---------|---------|
| `aksharamukha` | Rule-based Indic-to-Roman script conversion (ISO 15919) |
| `metaphone` | Double Metaphone phonetic encoding |
| `symspellpy` | Fast edit-distance dictionary lookup |

**Optional neural dependencies (`[neural]` extra):**

| Package | Purpose |
|---------|---------|
| `ai4bharat-transliteration` | IndicXlit neural back-transliteration (21 languages) |
| `torch` | PyTorch runtime |

## Quick Start

```python
from codemix_restore import ScriptRestorer

restorer = ScriptRestorer()

# Hindi
result = restorer.restore("धन्यवाद फॉर योर हेल्प", lang="hi")
# -> "धन्यवाद for your help"

# Bengali
result = restorer.restore("মিটিং ক্যান্সেল হয়ে গেছে", lang="bn")
# -> "Meeting cancel হয়ে গেছে"

# Tamil
result = restorer.restore("ப்ளீஸ் டாக்குமென்ட் ஷேர் பண்ணுங்க", lang="ta")
# -> "Please document share பண்ணுங்க"

# Telugu
result = restorer.restore("ప్లీజ్ డాక్యుమెంట్ షేర్ చేయండి", lang="te")
# -> "Please document share చేయండి"
```

### Auto-detect language

If you don't pass a `lang` code, the library auto-detects the script:

```python
# No lang= needed — detected as Telugu from the script
result = restorer.restore("ప్లీజ్ డాక్యుమెంట్ షేర్ చేయండి")
# -> "Please document share చేయండి"
```

### Get detailed per-token output

Use `return_details=True` for debugging or downstream analysis:

```python
result = restorer.restore(
    "प्लीज डॉक्यूमेंट शेयर करो",
    lang="hi",
    return_details=True,
)

print(result.text)
# "Please document share करो"

print(f"Total: {result.tokens_total}, Restored: {result.tokens_restored}, Native: {result.tokens_native}")
# Total: 4, Restored: 3, Native: 1

for detail in result.details:
    print(f"  {detail.original:15s} -> {detail.restored:15s}  [{detail.stage}, {detail.confidence:.2f}]")
# प्लीज           -> please           [dictionary, 0.95]
# डॉक्यूमेंट       -> document          [dictionary, 0.95]
# शेयर            -> share             [dictionary, 0.95]
# करो             -> करो               [viterbi, 1.00]
```

### Batch processing

```python
sentences = [
    ("प्लीज मीटिंग शेड्यूल करो", "hi"),
    ("মিটিং ক্যান্সেল হয়ে গেছে", "bn"),
    ("ப்ளீஸ் டாக்குமென்ட் ஷேர் பண்ணுங்க", "ta"),
]

for text, lang in sentences:
    restored = restorer.restore(text, lang=lang)
    print(f"[{lang}] {restored}")
```

### Disable neural mode

If you don't want to use IndicXlit (e.g., for lower latency or if it's not installed), pass `use_neural=False`:

```python
restorer = ScriptRestorer(use_neural=False)

# Still works — falls back to rule-based romanization + phonetic matching
result = restorer.restore("प्लीज मीटिंग शेड्यूल करो", lang="hi")
# -> "Please meeting schedule करो"
```

### Disable Viterbi sequence tagging

The pipeline uses an HMM/Viterbi algorithm by default for globally optimal language tagging. To fall back to greedy per-token classification:

```python
restorer = ScriptRestorer(use_viterbi=False)
```

## Supported Languages

24 languages across 12 scripts. All 22 scheduled languages of India plus Bhojpuri and Chhattisgarhi.

| Language | Script | Code | Status |
|----------|--------|------|--------|
| Hindi | Devanagari | `hi` | 100% tested |
| Bengali | Bengali | `bn` | 100% tested |
| Tamil | Tamil | `ta` | 100% tested |
| Telugu | Telugu | `te` | 100% tested |
| Marathi | Devanagari | `mr` | 100% tested |
| Kannada | Kannada | `kn` | 100% tested |
| Gujarati | Gujarati | `gu` | 100% tested |
| Punjabi | Gurmukhi | `pa` | 100% tested |
| Malayalam | Malayalam | `ml` | 100% tested |
| Odia | Odia | `or` | 100% tested |
| Assamese | Bengali | `as` | 100% tested |
| Nepali | Devanagari | `ne` | 100% tested |
| Urdu | Perso-Arabic | `ur` | 100% tested |
| Maithili | Devanagari | `mai` | 100% tested |
| Konkani | Devanagari | `kok` | 100% tested |
| Dogri | Devanagari | `doi` | 100% tested |
| Sindhi | Perso-Arabic | `sd` | 100% tested |
| Kashmiri | Perso-Arabic | `ks` | 100% tested |
| Sanskrit | Devanagari | `sa` | 100% tested |
| Bodo | Devanagari | `brx` | 100% tested |
| Manipuri | Meetei Mayek | `mni` | 100% tested |
| Santali | Ol Chiki | `sat` | 100% tested |
| Bhojpuri | Devanagari | `bho` | Supported |
| Chhattisgarhi | Devanagari | `hne` | Supported |

## How It Works

The library uses a 5-stage hybrid pipeline with two pre-passes and HMM-based sequence tagging:

```
ASR Output (single Indic script)
    |
    v
[Pre-Pass A] ABBREVIATION DETECTION
    Detects letter-name sequences: "ડીએ બીએ" -> "D.A. B.A."
    |
    v
[Pre-Pass B] COMPOUND WORD DETECTION
    Joins ASR-split English words (Urdu/Kashmiri/Sindhi):
    "آن لائن" -> "online",  "ڈیڈ لائن" -> "deadline"
    |
    v
[Stage 1] TOKENIZER
    Unicode-aware word splitting + per-token script detection
    |
    v
[Stage 2] DICTIONARY FAST-PATH (3-tier romanization)
    |
    |-- Tier 1: IndicXlit neural lookup (if installed)
    |      Indic word -> top-k English candidates -> exact dictionary match
    |      e.g. "कंप्यूटर" -> ["computer", "komputer", ...] -> "computer"
    |
    |-- Tier 2: Aksharamukha ISO romanization (if installed)
    |      Indic word -> ISO 15919 Latin -> normalize -> phonetic match
    |      e.g. "कंप्यूटर" -> "kampyūṭar" -> "kampyutar" -> "computer"
    |
    '-- Tier 3: Phoneme maps + transliteration variants (built-in fallback)
           Indic word -> character-by-character Latin -> phonetic match
    |
    |-- Known transliterations: direct Indic->English lookup (highest priority)
    |-- Native exclusions: words guaranteed native (never restore)
    |-- Confusable filter: blocks known false-positive matches
    |-- Agglutinative suffix stripping: "ऑफिसमें" -> "ऑफिस" + "में"
    |
    |-- HIGH confidence  -> English (done)
    |-- LOW confidence   -> Native (done)
    '-- MEDIUM/AMBIGUOUS -> Stage 3
    |
    v
[Stage 3] HMM/VITERBI SEQUENCE TAGGER
    Hidden Markov Model with 2 states (English, Native).
    - Emission probabilities: from 6 LID signals (dictionary score, suffix
      patterns, character composition, word length, native word lists, prefix)
    - Transition probabilities: encode language inertia (consecutive words
      tend to share a language) and code-switching patterns
    - HIGH/LOW tokens act as clamped anchors that propagate influence to
      neighboring ambiguous tokens via the Viterbi path
    |
    |   Finds the GLOBALLY optimal label sequence for the entire sentence,
    |   instead of making greedy per-token decisions.
    |
    |   Example: "रैंडम" (weak match alone) gets tagged English because
    |   its neighbor "स्क्रिप्ट" (strong match) makes N-E-E more likely
    |   than N-N-E.
    |
    |-- Label = English -> Stage 4
    '-- Label = Native  -> keep as-is (done)
    |
    v
[Stage 4] NEURAL BACK-TRANSLITERATION (optional)
    IndicXlit beam search -> top-k candidates -> rerank against 30K dictionary
    |
    v
[Stage 5] RECONSTRUCTION
    Reassemble: English words in Latin, native words unchanged
    Capitalize at sentence boundaries, normalize punctuation (। -> . near English)
    |
    v
Output (mixed-script text)
```

### HMM/Viterbi Sequence Tagging (Stage 3)

Previous versions used a greedy per-token classifier that decided each word's language independently. This caused three problems:

1. **Isolated false positives** -- a native word with a marginal phonetic match got tagged English even though it was surrounded by native words
2. **Missed English spans** -- two consecutive English words where each individually scored just below the threshold both got tagged Native
3. **Cascade errors** -- one wrong decision propagated to the next token via the context signal

The HMM/Viterbi approach solves all three by finding the **globally optimal** label sequence. It uses a 2-state Hidden Markov Model (English/Native) with:

- **Emission probabilities** derived from the existing 6 weighted signals (dictionary 0.40, suffix 0.12, char_composition 0.13, length 0.10, native_list 0.10, prefix 0.05)
- **Transition matrix** encoding that consecutive tokens usually share a language:

```
              English  Native
  English     [0.70    0.30]
  Native      [0.15    0.85]
```

HIGH and LOW confidence tokens from Stage 2 participate as **clamped anchors** (emission near 0.99 or 0.01), propagating their influence bidirectionally to neighboring ambiguous tokens. Sentences are split at punctuation boundaries to prevent context from bleeding across sentences.

**Complexity**: O(T x 4) for T tokens with 2 states. A 20-word sentence = 80 operations -- essentially free.

### 3-Tier Romanization -- Graceful Degradation

The key design decision is the 3-tier romanization in Stage 2:

| Tier | Engine | Accuracy | Latency | Memory | Requires |
|------|--------|----------|---------|--------|----------|
| 1 | IndicXlit (neural) | Best -- produces actual English words directly | ~115ms/word | ~1.4 GB | `[neural]` extra |
| 2 | Aksharamukha (rule-based) | Good -- ISO romanization + phonetic matching | <5ms/word | ~50 MB | `aksharamukha` (core dep) |
| 3 | Phoneme maps (built-in) | Baseline -- character-level maps + translit variants | <1ms/word | ~50 MB | Nothing extra |

The pipeline tries each tier in order and falls back gracefully. If IndicXlit is not installed, Tier 2+3 still provide strong coverage. If Aksharamukha is also missing, Tier 3 handles the basics.

**Why IndicXlit matters:** Traditional romanization converts "कंप्यूटर" to something like "kampyutar" and then phonetically matches it to "computer" (score ~0.74, AMBIGUOUS). IndicXlit directly outputs "computer" as its top candidate, giving an exact dictionary match (score 1.0, HIGH confidence). This eliminates the need for phonetic fuzzy matching on the most common words.

## Configuration

```python
restorer = ScriptRestorer(
    dict_path="path/to/english_dict.json",  # Custom English dictionary (default: built-in 30K words)
    warm_cache_dir="path/to/warm_cache/",   # Pre-computed Indic->English lookup tables
    use_neural=True,                         # Enable IndicXlit neural transliteration
    use_viterbi=True,                        # Enable HMM/Viterbi sequence tagging (default: True)
    high_threshold=0.85,                     # Score >= this -> HIGH confidence (auto-restore)
    low_threshold=0.55,                      # Score <= this -> LOW confidence (keep native)
    lid_threshold=0.70,                      # LID P(english) >= this -> classify as English
)
```

### Custom Dictionary

The built-in dictionary ships 30,000 English words with frequency rankings. To use a custom dictionary:

```python
# JSON format: {"word": frequency_rank, ...}
# Lower rank = more common (1 = most common)
restorer = ScriptRestorer(dict_path="my_dictionary.json")
```

```json
{
    "meeting": 1500,
    "cancel": 3200,
    "document": 2800,
    "kubernetes": 50000
}
```

You can also use a plain text file (one word per line, optionally with frequency):

```
meeting 1500
cancel 3200
document 2800
```

### Warm Cache

Pre-compute common Indic-to-English mappings per language for O(1) lookup:

```python
from codemix_restore.neural_translit import NeuralTransliterator

translit = NeuralTransliterator()
cache = translit.generate_warm_cache(
    english_words=["meeting", "cancel", "document", "schedule", "please"],
    lang_code="hi",
    output_path="warm_cache/hi_cache.json",
)
```

Warm caches bypass all pipeline stages and provide instant lookup for your most common words. Generate one per language.

## Accuracy

Tested across 755 sentences covering all 22 scheduled languages:

| Test Suite | Sentences | Languages | Accuracy |
|------------|-----------|-----------|----------|
| Core (e2e_test.py) | 50 | 8 | 100% |
| Expanded (e2e_test_expanded.py) | 111 | 8 | 100% |
| Comprehensive (e2e_test_comprehensive.py) | 213 | 21 | 100% |
| Unseen (e2e_test_unseen.py) | 77 | 22 | 100% |
| Batch 1 (test_new_examples.py) | 148 | 10 | Tested |
| Batch 2 (test_new_examples_2.py) | 156 | 10 | Tested |

The test suite covers common English loanwords used in Indian code-mixed speech across domains: business (meeting, cancel, deadline, approve, budget), tech (server, database, backup, deploy, API), finance (invoice, payment, credit, tax, loan), healthcare (doctor, patient, emergency), travel (flight, ticket, booking), and more.

### False Positive Prevention

The pipeline is tuned for **precision over recall** -- keeping a native word native is more important than catching every English word. Multiple layers prevent false positives:

- **Native exclusion lists**: Per-language sets of words that must never be restored (pronouns, postpositions, common verbs)
- **Confusable filter**: Blocks known false-positive pairs (e.g., Hindi "अभी" (now) != "abbey")
- **Short-word blocking**: Single-character Indic tokens are never restored; 2-character tokens require exact match only
- **Viterbi isolation penalty**: An isolated weak match surrounded by native words stays native due to the high N->N transition cost
- **Match-type awareness**: Phonetic and edit-distance matches are penalized vs exact matches in the LID signals

### Agglutination Handling

Indian languages fuse postpositions/case markers with nouns. The library handles this via suffix stripping:

```
ऑफिसमध्ये = office + मध्ये (Marathi locative) -> "office"
টিমকে     = team + কে (Bengali dative)        -> "team"
ஆபிஸ்ல    = office + ல (Tamil locative)        -> "office"
```

Supported suffix patterns for 14 languages: Hindi (-में, -को, -से), Bengali (-কে, -তে, -র), Tamil (-ல, -கிட்ட, -க்கு), Telugu (-లో, -కి), Marathi (-मध्ये, -ला, -साठी), Kannada (-ಲ್ಲಿ, -ಗೆ), Gujarati (-માં, -ને), Punjabi (-ਵਿੱਚ, -ਨੂੰ), Malayalam (-ല്, -ക്ക്), Odia (-ରେ, -କୁ), Nepali (-मा, -लाई), Urdu (-میں, -کو), Assamese (-ত, -ক), Kashmiri (-مٕنٛز).

### Abbreviation Detection

English abbreviations spelled out in Indic script are detected and joined:

```
"ડીએ બીએ" (Gujarati)  -> "D.A. B.A."
"एम पी"   (Hindi)      -> "M.P."
"ডি বি"    (Bengali)    -> "D.B."
```

Supported for 7 scripts: Devanagari, Bengali, Gujarati, Gurmukhi, Tamil, Telugu, Kannada.

### Compound Word Detection

ASR systems for Perso-Arabic scripts sometimes split single English words across two tokens. The pipeline detects and merges these:

```
"آن لائن"  (Urdu)     -> "online"
"ڈیڈ لائن" (Urdu)     -> "deadline"
"نیٹ ورک"  (Urdu)     -> "network"
"سافٹ ویئر" (Urdu)    -> "software"
```

Supported for Urdu, Kashmiri, and Sindhi.

## Development

```bash
# Clone and install
git clone https://github.com/shunyalabs/codemix-restore.git
cd codemix-restore
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,neural]"

# Run unit tests (77 tests)
pytest tests/ -v

# Run end-to-end tests
python e2e_test.py                # 50 sentences, 8 languages
python e2e_test_expanded.py       # 111 sentences, 8 languages
python e2e_test_comprehensive.py  # 213 sentences, 21 languages
python e2e_test_unseen.py         # 77 sentences, 22 languages
python test_new_examples.py       # 148 sentences, 10 languages
python test_new_examples_2.py     # 156 sentences, 10 languages
```

## Project Structure

```
codemix_restore/
    __init__.py                  # Public API: ScriptRestorer
    pipeline.py                  # Main orchestrator (5-stage pipeline + pre-passes)
    config.py                    # Language config registry (24 languages, 12 scripts)
    tokenizer.py                 # Stage 1: Unicode-aware tokenization + script detection
    dictionary_lookup.py         # Stage 2: 3-tier romanization + dictionary matching
    language_id.py               # Emission probability source (6 weighted signals)
    viterbi_lid.py               # Stage 3: HMM/Viterbi sequence tagger
    neural_translit.py           # Stage 4: IndicXlit wrapper + caching
    reconstructor.py             # Stage 5: Reassembly, capitalization, punctuation
    abbreviation.py              # Pre-pass: English abbreviation detection
    confusable_filter.py         # False positive prevention (blocklist + distance)
    suffix_map.py                # Agglutinative suffix patterns (14 languages)
    compat/
        __init__.py
        fairseq_patch.py         # Python 3.12 compatibility patches for fairseq/hydra
    phonetic/
        __init__.py
        engine.py                # Phonetic matching (Metaphone + SymSpell + translit variants)
        script_phoneme_maps.py   # Per-script character-to-Latin phoneme maps (12 scripts)
    data/
        en_dict_30k.json         # Built-in 30K English dictionary with frequency ranks
        {lang}_common.txt        # Native word frequency lists (23 languages)
        warm_cache/              # Pre-generated per-language Indic->English caches
tests/
    test_tokenizer.py            # Tokenizer tests
    test_phonetic.py             # Phonetic matching tests
    test_dictionary_lookup.py    # Dictionary lookup tests
    test_pipeline.py             # End-to-end pipeline tests
    test_suffix_stripping.py     # Agglutination suffix stripping tests
    test_viterbi_lid.py          # HMM/Viterbi sequence tagger tests
```

## License

MIT License. See [LICENSE](LICENSE) for details.
