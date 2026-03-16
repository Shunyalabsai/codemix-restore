# codemix_restore-shunyalabs

Restore English words from transliterated Indic script in code-mixed ASR output.

ASR models for Indian languages output everything in a single native script. When users code-switch (mix English with their native language), English words get transliterated into the native script. This library detects those English words and converts them back to Latin script, preserving native language words as-is.

```
Input  (ASR output):  "धन्यवाद फॉर योर हेल्प, थैंक यू सो मच।"
Output (restored):    "धन्यवाद for your help, thank you so much।"
```

## Installation

**Basic (rule-based only):**

```bash
pip install codemix_restore-shunyalabs
```

**With neural transliteration (recommended for best accuracy):**

```bash
pip install "codemix_restore-shunyalabs[neural]"
```

The `[neural]` extra installs [IndicXlit](https://github.com/AI4Bharat/IndicXlit) (AI4Bharat's neural transliteration model) and PyTorch. This gives significantly better accuracy on novel/rare English words but requires more memory (~1.4 GB) and has higher latency (~115ms/word vs <5ms/word).

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
# करो             -> करो               [dictionary, 1.00]
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

## Supported Languages

All 8 primary languages are tested at **100% accuracy** on 111 test sentences. 14 additional scheduled languages of India are supported.

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
| Odia | Odia | `or` | Supported |
| Malayalam | Malayalam | `ml` | Supported |
| Assamese | Bengali | `as` | Supported |
| Urdu | Arabic | `ur` | Supported |
| Sindhi | Arabic/Devanagari | `sd` | Supported |
| Nepali | Devanagari | `ne` | Supported |
| Konkani | Devanagari | `kok` | Supported |
| Maithili | Devanagari | `mai` | Supported |
| Dogri | Devanagari | `doi` | Supported |
| Kashmiri | Arabic/Devanagari | `ks` | Supported |
| Sanskrit | Devanagari | `sa` | Supported |
| Santali | Ol Chiki | `sat` | Supported |
| Manipuri | Meitei | `mni` | Supported |
| Bodo | Devanagari | `brx` | Supported |

## How It Works

The library uses a 5-stage hybrid pipeline with 3-tier romanization for maximum accuracy:

```
ASR Output (single Indic script)
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
    |      e.g. "कंप्यूटर" -> ["computer", "komputer", ...] -> "computer" (exact hit)
    |
    |-- Tier 2: Aksharamukha ISO romanization (if installed)
    |      Indic word -> ISO 15919 Latin -> normalize -> phonetic dictionary match
    |      e.g. "कंप्यूटर" -> "kampyūṭar" -> "kampyutar" -> phonetic match "computer"
    |
    '-- Tier 3: Phoneme maps + transliteration variants (built-in fallback)
           Indic word -> character-by-character Latin -> phonetic match
           e.g. "कंप्यूटर" -> "kampyootar" -> phonetic match "computer"
    |
    |-- HIGH confidence  -> English word (done)
    |-- LOW confidence   -> native word (done)
    '-- AMBIGUOUS        -> Stage 3
    |
    v
[Stage 3] LANGUAGE IDENTIFICATION
    Weighted signals: dictionary score, suffix patterns (-ment, -ing, -tion),
    character composition, word length, context from neighboring tokens
    |-- P(english) >= threshold -> Stage 4
    '-- P(english) <  threshold -> native word (done)
    |
    v
[Stage 4] NEURAL BACK-TRANSLITERATION (optional)
    IndicXlit beam search -> top-k candidates -> rerank against 30K English dictionary
    |
    v
[Stage 5] RECONSTRUCTION
    Reassemble: English words in Latin script, native words unchanged
    Capitalize sentence starts, normalize punctuation
    |
    v
Output (mixed-script text)
```

### 3-Tier Romanization — Graceful Degradation

The key design decision is the 3-tier romanization in Stage 2:

| Tier | Engine | Accuracy | Latency | Memory | Requires |
|------|--------|----------|---------|--------|----------|
| 1 | IndicXlit (neural) | Best — produces actual English words directly | ~115ms/word | ~1.4 GB | `[neural]` extra |
| 2 | Aksharamukha (rule-based) | Good — ISO romanization + phonetic matching | <5ms/word | ~50 MB | `aksharamukha` (core dep) |
| 3 | Phoneme maps (built-in) | Baseline — character-level maps + translit variants | <1ms/word | ~50 MB | Nothing extra |

The pipeline tries each tier in order and falls back gracefully. If IndicXlit is not installed, Tier 2+3 still provide strong coverage. If Aksharamukha is also missing, Tier 3 handles the basics.

**Why IndicXlit matters:** Traditional romanization converts "कंप्यूटर" to something like "kampyutar" and then phonetically matches it to "computer" (score ~0.74, AMBIGUOUS). IndicXlit directly outputs "computer" as its top candidate, giving an exact dictionary match (score 1.0, HIGH confidence). This eliminates the need for phonetic fuzzy matching on the most common words.

### Why Not NLLB / Machine Translation?

NLLB and similar MT models are sentence-level semantic translators, not word-level script converters:

- Language tags declare the entire input as one language, but code-mixed input has both languages at the word level
- MT models translate/hallucinate native words that should be kept as-is
- 54.5B parameters is overkill for what is fundamentally a phonetic mapping + classification task
- No control over which words get translated

Our pipeline handles ~90% of words via fast dictionary lookup (<5ms), reserving neural inference only for the long tail of ambiguous tokens.

## Configuration

```python
restorer = ScriptRestorer(
    dict_path="path/to/english_dict.json",  # Custom English dictionary (default: built-in 30K words)
    warm_cache_dir="path/to/warm_cache/",   # Pre-computed Indic->English lookup tables
    use_neural=True,                         # Enable IndicXlit neural transliteration
    high_threshold=0.75,                     # Score >= this -> HIGH confidence (auto-restore)
    low_threshold=0.4,                       # Score <= this -> LOW confidence (keep native)
    lid_threshold=0.65,                      # LID P(english) >= this -> classify as English
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

Tested on 111 sentences across 8 languages with the IndicXlit neural backend:

| Language | Sentences | Accuracy |
|----------|-----------|----------|
| Hindi | 31 | 100% |
| Bengali | 14 | 100% |
| Tamil | 13 | 100% |
| Telugu | 13 | 100% |
| Kannada | 10 | 100% |
| Gujarati | 10 | 100% |
| Punjabi | 10 | 100% |
| Marathi | 10 | 100% |
| **Overall** | **111** | **100%** |

The test suite covers common English loanwords used in Indian code-mixed speech: meeting, cancel, document, schedule, please, share, budget, approve, deadline, update, download, password, software, server, network, project, database, backup, file, system, restart, mobile, number, plan, search, and more.

### Agglutination Handling

Indian languages fuse postpositions/case markers with nouns. The library handles this via suffix stripping:

```
ऑफिसमध्ये = office + मध्ये (Marathi locative) -> "office"
টিমকে     = team + কে (Bengali dative)        -> "team"
ஆபிஸ்ல    = office + ல (Tamil locative)        -> "office"
```

Supported suffix patterns: Hindi (-में, -को, -से), Bengali (-কে, -তে, -র), Tamil (-ல, -கிட்ட, -க்கு), Telugu (-లో, -కి), Marathi (-मध्ये, -ला, -साठी), Kannada (-ಲ್ಲಿ, -ಗೆ), Gujarati (-માં, -ને), Punjabi (-ਵਿੱਚ, -ਨੂੰ).

## Development

```bash
# Clone and install
git clone https://github.com/shunyalabs/codemix-restore.git
cd codemix-restore
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,neural]"

# Run unit tests (60 tests)
pytest tests/ -v

# Run end-to-end tests (50 original sentences)
python e2e_test.py

# Run expanded test suite (111 sentences across 8 languages)
python e2e_test_expanded.py
```

## Project Structure

```
codemix_restore/
    __init__.py                  # Public API: ScriptRestorer
    pipeline.py                  # Main orchestrator (5-stage pipeline)
    config.py                    # Language config registry (22 languages)
    tokenizer.py                 # Stage 1: Unicode-aware tokenization + script detection
    dictionary_lookup.py         # Stage 2: 3-tier romanization + dictionary matching
    language_id.py               # Stage 3: Word-level language classifier
    neural_translit.py           # Stage 4: IndicXlit wrapper + caching
    reconstructor.py             # Stage 5: Reassembly, capitalization, punctuation
    suffix_map.py                # Agglutinative suffix patterns per language
    compat/
        __init__.py
        fairseq_patch.py         # Python 3.12 compatibility patches for fairseq/hydra
    phonetic/
        __init__.py
        engine.py                # Phonetic matching (Metaphone + SymSpell + translit variants)
        script_phoneme_maps.py   # Per-script character-to-Latin phoneme maps
    data/
        en_dict_30k.json         # Built-in 30K English dictionary with frequency ranks
        warm_cache/              # Pre-generated per-language Indic->English caches
tests/
    test_config.py               # Language config tests
    test_tokenizer.py            # Tokenizer tests
    test_phonetic.py             # Phonetic matching tests
    test_dictionary_lookup.py    # Dictionary lookup tests
    test_pipeline.py             # End-to-end pipeline tests
    test_suffix_stripping.py     # Agglutination suffix stripping tests
```

## License

MIT License. See [LICENSE](LICENSE) for details.
