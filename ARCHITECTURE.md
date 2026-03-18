# codemix_restore — System Architecture

## Overview

`codemix_restore` is a Python library that restores English words in code-mixed Indian language ASR (Automatic Speech Recognition) output back to Latin script. When Indian ASR systems process bilingual speech, English words get transliterated into the native script (e.g., Hindi "फॉर" for "for", Bengali "ফ্লাইট" for "flight"). This system detects and converts those words back to English while preserving genuinely native words.

**Supported languages**: 24 (all 22 Scheduled Indian languages + Bhojpuri + Chhattisgarhi)
**Supported scripts**: 12 (Devanagari, Bengali, Gujarati, Gurmukhi, Oriya, Tamil, Telugu, Kannada, Malayalam, Perso-Arabic, Meetei Mayek, Ol Chiki)

```
Input:  "धन्यवाद फॉर योर हेल्प, थैंक यू सो मच।"
Output: "धन्यवाद for your help. Thank you so much."
```

---

## Pipeline Architecture

The system uses a **5-stage sequential pipeline** with two pre-passes. Each stage narrows the set of unresolved tokens until all are classified as either English (restore) or native (keep).

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ScriptRestorer.restore()                     │
│                          (pipeline.py)                              │
│                                                                     │
│  ┌──────────────┐                                                   │
│  │ Pre-Pass A   │  Abbreviation Detection (abbreviation.py)        │
│  │              │  "ડીએ બીએ" → "D.A. B.A."                         │
│  └──────┬───────┘                                                   │
│         ▼                                                           │
│  ┌──────────────┐                                                   │
│  │ Pre-Pass B   │  Compound Word Detection (pipeline.py)           │
│  │              │  "آن لائن" → "online" (Urdu/Kashmiri/Sindhi)     │
│  └──────┬───────┘                                                   │
│         ▼                                                           │
│  ┌──────────────┐                                                   │
│  │  Stage 1     │  Tokenization (tokenizer.py)                     │
│  │              │  Unicode-aware script detection & splitting       │
│  └──────┬───────┘                                                   │
│         ▼                                                           │
│  ┌──────────────┐                                                   │
│  │  Stage 2     │  Dictionary Lookup (dictionary_lookup.py)        │
│  │              │  Known transliterations → Romanization →          │
│  │              │  PhoneticMatcher (engine.py)                      │
│  │              │  Result: HIGH → restore, LOW → keep native        │
│  └──────┬───────┘                                                   │
│         │ MEDIUM / AMBIGUOUS tokens                                 │
│         ▼                                                           │
│  ┌──────────────┐                                                   │
│  │  Stage 3     │  Language Identification (language_id.py)        │
│  │              │  7-signal weighted classifier                     │
│  │              │  → is_english=True / False                        │
│  └──────┬───────┘                                                   │
│         │ is_english=True                                           │
│         ▼                                                           │
│  ┌──────────────┐                                                   │
│  │  Stage 4     │  Neural Transliteration (neural_translit.py)     │
│  │              │  IndicXlit beam search + dictionary reranking     │
│  │              │  Fallback: dictionary match from Stage 2          │
│  └──────┬───────┘                                                   │
│         ▼                                                           │
│  ┌──────────────┐                                                   │
│  │  Stage 5     │  Reconstruction (reconstructor.py)               │
│  │              │  Reassemble tokens, capitalize, normalize punct   │
│  └──────────────┘                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Module Reference

### 1. Entry Point — `__init__.py`

**Path**: `codemix_restore/__init__.py`

Exports the public API:
- `ScriptRestorer` — main class
- `__version__` — current version string (`"0.2.5"`)

```python
from codemix_restore import ScriptRestorer
restorer = ScriptRestorer()
result = restorer.restore("धन्यवाद फॉर योर हेल्प", lang="hi")
```

---

### 2. Pipeline Orchestrator — `pipeline.py`

**Path**: `codemix_restore/pipeline.py` (~396 lines)

The central coordinator that chains all stages together.

#### Classes

| Class | Purpose |
|---|---|
| `ScriptRestorer` | Main API. Initializes all stage components and orchestrates the pipeline. |
| `RestoreResult` | Dataclass returned when `return_details=True`. Contains restored text, original, lang_code, token counts, and per-token details. |
| `TokenDetail` | Per-token debug info: original text, restored text, script_type, which stage resolved it, confidence score. |

#### `ScriptRestorer.__init__()`

Initializes components in dependency order:

```
PhoneticMatcher(dict_path)
    ↓
NeuralTransliterator(phonetic_matcher, cache_dir)   [optional]
    ↓
DictionaryLookup(phonetic_matcher, warm_cache_dir, neural_transliterator)
    ↓
WordLanguageIdentifier(english_threshold, native_word_lists)
    ↓
Reconstructor()
```

**Constructor Parameters**:
| Parameter | Default | Purpose |
|---|---|---|
| `dict_path` | `None` (built-in) | Path to English dictionary file |
| `warm_cache_dir` | `None` | Pre-computed warm caches for neural transliteration |
| `use_neural` | `True` | Enable/disable IndicXlit neural transliteration |
| `high_threshold` | `0.85` | Score above which dictionary match = HIGH confidence |
| `low_threshold` | `0.55` | Score below which dictionary match = LOW confidence |
| `lid_threshold` | `0.70` | Probability threshold for language identification |

#### `ScriptRestorer.restore(text, lang, return_details)`

Main processing flow:

1. **Input validation** — empty/whitespace text returns as-is
2. **Language detection** — auto-detect from Unicode script if `lang=None`
3. **Get config** — retrieve `LanguageConfig` for the detected language
4. **Stage 1: Tokenize** — split into `Token` objects with script classification
5. **Pre-Pass A: Abbreviations** — detect letter-name sequences (e.g., "एम पी" → "M.P.")
6. **Pre-Pass B: Compounds** — detect split English words in Perso-Arabic scripts
7. **First pass: Dictionary lookup** — bulk lookup all INDIC tokens (skipping abbreviation/compound positions)
8. **Second pass: Classify** — for each INDIC token:
   - HIGH confidence → restore immediately
   - LOW confidence → keep native
   - MEDIUM/AMBIGUOUS → run LID
     - LID says English → try dictionary match (with confidence gating) or neural transliteration
     - LID says native → keep as-is
9. **Stage 5: Reconstruct** — reassemble tokens with capitalization and punctuation normalization

#### Compound Word Detection

Handles ASR-split English words in Perso-Arabic scripts:

```python
_COMPOUND_WORDS = {
    "ks": {("آن", "لائن"): "online", ("اپ", "ڈیٹ"): "update", ...},
    "ur": {("آن", "لائن"): "online", ("نیٹ", "ورک"): "network", ("ڈیڈ", "لائن"): "deadline", ...},
    "sd": {("آن", "لائن"): "online", ...},
}
```

---

### 3. Configuration — `config.py`

**Path**: `codemix_restore/config.py` (~328 lines)

Defines per-language configuration and script detection utilities.

#### `LanguageConfig` Dataclass

| Field | Type | Purpose |
|---|---|---|
| `lang_code` | `str` | ISO 639 code (e.g., "hi", "bn", "ta") |
| `lang_name` | `str` | Human-readable name |
| `script_name` | `str` | Unicode script name (e.g., "Devanagari", "Bengali") |
| `unicode_ranges` | `list[tuple[int,int]]` | Character code point ranges for this script |
| `indicxlit_code` | `str \| None` | Language code for IndicXlit neural model (`None` = not supported) |
| `has_aspirates` | `bool` | Whether the script has aspirated consonants |
| `has_retroflex` | `bool` | Whether the script has retroflex consonants |
| `sentence_enders` | `str` | Script-specific sentence-ending punctuation |
| `family` | `str` | Language family ("indo-aryan", "dravidian", "sino-tibetan", "austroasiatic", "perso-arabic") |

#### Language Coverage

| Script | Languages |
|---|---|
| Devanagari | Hindi (hi), Marathi (mr), Nepali (ne), Sanskrit (sa), Konkani (kok), Dogri (doi), Maithili (mai), Bodo (brx), Bhojpuri (bho), Chhattisgarhi (hne) |
| Bengali | Bengali (bn), Assamese (as) |
| Gujarati | Gujarati (gu) |
| Gurmukhi | Punjabi (pa) |
| Oriya | Odia (or) |
| Tamil | Tamil (ta) |
| Telugu | Telugu (te) |
| Kannada | Kannada (kn) |
| Malayalam | Malayalam (ml) |
| Perso-Arabic | Urdu (ur), Kashmiri (ks), Sindhi (sd) |
| Meetei Mayek | Manipuri (mni) |
| Ol Chiki | Santali (sat) |

#### Key Functions

- **`get_config(lang_code)`** → `LanguageConfig` — looks up config by language code
- **`detect_script(text)`** → `str | None` — determines dominant script in text by Unicode character analysis
- **`detect_lang_from_script(text)`** → `str | None` — detects language from script (unambiguous for single-language scripts; defaults to "hi" for Devanagari, "bn" for Bengali)

#### Derived Mappings

- `SCRIPT_TO_LANGS`: Maps script name → list of language codes sharing that script
- `FAMILY_GROUPS`: Maps language family → list of language codes

---

### 4. Tokenizer — `tokenizer.py`

**Path**: `codemix_restore/tokenizer.py` (~243 lines)

Stage 1: Unicode-aware tokenization with per-character script classification.

#### `ScriptType` Enum

| Value | Meaning |
|---|---|
| `INDIC` | Characters from any supported Indic script |
| `LATIN` | ASCII/Latin characters (already English) |
| `NUMERIC` | Digits (ASCII or Indic numerals) |
| `PUNCTUATION` | Punctuation marks (including Indic-specific like "।") |
| `WHITESPACE` | Spaces, tabs, newlines |
| `UNKNOWN` | Unrecognized characters |

#### `Token` Dataclass

| Field | Type | Purpose |
|---|---|---|
| `text` | `str` | The token's text content |
| `position` | `int` | Sequential position index in the token list |
| `script_type` | `ScriptType` | Classified script type |
| `script_name` | `str \| None` | Specific script name (e.g., "Devanagari") for INDIC tokens |
| `is_mixed_script` | `bool` | Whether the token mixes multiple scripts |

#### Processing Flow

```
Input text
    ↓
Split on whitespace
    ↓
For each word:
    ├─ _split_punctuation() — separate leading/trailing punctuation
    ├─ _classify_char() per character — determine script
    ├─ Majority script vote → assign ScriptType
    └─ Generate Token objects with positions
    ↓
List[Token]  (including WHITESPACE and PUNCTUATION tokens)
```

#### Key Behaviors

- **Punctuation separation**: Leading/trailing punctuation split into separate tokens, preserving attachment info
- **Script classification**: Each character classified against all configured Unicode ranges. Majority vote determines token script.
- **Mixed-script detection**: Tokens with characters from multiple Indic scripts flagged via `is_mixed_script`
- **Position tracking**: Every token (including whitespace/punctuation) gets a unique position for reconstruction

---

### 5. Dictionary Lookup — `dictionary_lookup.py`

**Path**: `codemix_restore/dictionary_lookup.py` (~1700+ lines)

Stage 2: The largest and most complex module. Provides fast-path English word detection through multiple matching strategies.

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DictionaryLookup.lookup()                     │
│                                                                  │
│  1. Check _KNOWN_TRANSLITERATIONS[lang][word]                   │
│     → Direct hit? Return HIGH confidence                         │
│                                                                  │
│  2. Check _NATIVE_EXCLUSIONS[lang]                              │
│     → Word in set? Return LOW confidence (definitely native)     │
│                                                                  │
│  3. Check ConfusableFilter._BLOCKLIST                           │
│     → Blocked pair? Skip that English candidate                  │
│                                                                  │
│  4. Agglutinative suffix stripping (suffix_map.py)              │
│     → "ऑफिसमें" → base="ऑफिस", suffix="में"                     │
│     → Re-check known transliterations with base form             │
│                                                                  │
│  5. Romanize (aksharamukha or fallback script_phoneme_maps)     │
│     → "हेल्प" → "help"                                           │
│                                                                  │
│  6. PhoneticMatcher.lookup(romanized)                           │
│     → Exact match / Metaphone / Edit-distance / Translit variant│
│                                                                  │
│  7. Try neural direct lookup (_try_neural_lookup)               │
│     → IndicXlit beam search on original Indic text               │
│                                                                  │
│  8. Score calibration → Confidence assignment                    │
│     → HIGH (≥0.85) / MEDIUM / LOW (≤0.55) / AMBIGUOUS           │
└─────────────────────────────────────────────────────────────────┘
```

#### Key Data Structures

**`_KNOWN_TRANSLITERATIONS`** — `dict[str, dict[str, str]]`

Per-language dictionaries mapping Indic-script words directly to their English equivalents. Highest priority — checked before any romanization or phonetic matching. Contains ~300+ entries across 15 languages covering domain words that romanization can't reliably handle.

```python
_KNOWN_TRANSLITERATIONS = {
    "hi": {"अर्जेंट": "urgent", "कॉलबैक": "callback", "हेल्पडेस्क": "helpdesk", ...},
    "bn": {"আপগ্রেড": "upgrade", "প্রসেস": "process", "ডেমো": "demo", ...},
    "ta": {"ப்ராடக்ட்": "product", "கிரேட்": "great", "லைசென்ஸ்": "license", ...},
    # ... 12 more languages
}
```

**`_NATIVE_EXCLUSIONS`** — `dict[str, set[str]]`

Per-language sets of native words that must never be restored to English, even if they phonetically resemble an English word.

```python
_NATIVE_EXCLUSIONS = {
    "hi": {"अभी", "करें", "शाम", "बहन", ...},
    "bn": {"আমি", "তুমি", "কথা", "বলতে", "চাই", ...},
    # ... 13 more languages
}
```

**`_native_words`** — `dict[str, set[str]]`

Loaded from `data/{lang}_common.txt` files at init time. Larger word frequency lists (hundreds to thousands per language) used as a signal in LID, not as a hard block.

#### `LookupResult` Dataclass

| Field | Type | Purpose |
|---|---|---|
| `original` | `str` | Original Indic-script word |
| `romanized` | `str` | Romanized form |
| `english_match` | `str \| None` | Best English match found |
| `confidence` | `Confidence` | HIGH / MEDIUM / LOW / AMBIGUOUS |
| `score` | `float` | Numeric match score (0.0–1.0) |
| `match_detail` | `MatchResult \| None` | Detailed match info from PhoneticMatcher |

#### Romanization

Two romanization backends, tried in order:

1. **Aksharamukha** (`aksharamukha` package) — high-quality scholarly romanization (ISO 15919). Preferred but requires pip install.
2. **Fallback `romanize_with_map()`** (`script_phoneme_maps.py`) — built-in character-level mapping tables for all 12 scripts. Less accurate but always available.

#### Agglutinative Suffix Stripping

Indian languages agglutinate postpositions and case markers onto words. When an English loanword has a native suffix fused to it, the system strips it:

```
"ऑफिसमें" → base: "ऑफिस" (office), suffix: "में" (in)
"serverకి" → base: "server", suffix: "కి" (to)
```

Suffixes defined per-language in `suffix_map.py` (14 languages, 5–20 suffixes each).

---

### 6. Phonetic Matching Engine — `phonetic/engine.py`

**Path**: `codemix_restore/phonetic/engine.py` (~730+ lines)

Core matching engine used by `DictionaryLookup`. Maintains a 30K English word dictionary and provides multiple matching strategies.

#### `PhoneticMatcher` Architecture

```
┌──────────────────────────────────────────────────────┐
│                PhoneticMatcher.lookup()                │
│                                                       │
│  Input: romanized string (e.g., "help", "praatakt")  │
│                                                       │
│  1. Normalize input (lowercase, strip diacritics)     │
│                                                       │
│  2. Check _TRANSLIT_VARIANTS[normalized]              │
│     → Direct map? Return with score bonus             │
│                                                       │
│  3. Exact dictionary match                            │
│     → Found? Return score=1.0, match_type="exact"     │
│                                                       │
│  4. Double Metaphone match (requires `metaphone`)     │
│     → Same phonetic code? Return match_type="metaphone"│
│                                                       │
│  5. SymSpell edit-distance (requires `symspellpy`)    │
│     → Within edit distance 2? Return match_type=       │
│       "edit_distance"                                  │
│                                                       │
│  6. Score adjustments:                                │
│     - Short word penalty (≤2 chars: -0.35)            │
│     - Frequency rank bonus (common words score higher)│
│     - Confusable filter check                         │
│                                                       │
│  → Return MatchResult(english_word, score, match_type) │
└──────────────────────────────────────────────────────┘
```

#### `MatchResult` Dataclass

| Field | Type | Purpose |
|---|---|---|
| `english_word` | `str` | Matched English word |
| `score` | `float` | Match quality (0.0–1.0) |
| `match_type` | `str` | "exact", "translit_variant", "metaphone", or "edit_distance" |
| `frequency_rank` | `int` | Word frequency rank in English (lower = more common) |

#### `_TRANSLIT_VARIANTS` — ~300+ entries

Maps common Indian English romanization patterns to correct English words. Handles systematic pronunciation differences:

```python
_TRANSLIT_VARIANTS = {
    "bild": "build",      # Hindi/Kannada: no distinction between i/ɪ
    "phayl": "file",      # ph → f mapping in Indic scripts
    "texa": "tax",        # trailing vowel from Devanagari
    "prosesa": "process", # vowel insertion in consonant clusters
    "apagreda": "upgrade",# Indic phonological adaptations
    # ... 300+ more
}
```

#### English Dictionary

- **Primary**: Loaded from `data/en_dict_30k.json` — 30,000 most common English words with frequency ranks
- **Fallback**: `_BUILTIN_WORDS` — ~500 hardcoded common English words for when the JSON file isn't available

#### `is_english(word, threshold)` Method

Quick boolean check — returns `True` if the word is in the English dictionary. Used by other modules (LID, neural translit) for validation.

---

### 7. Script-Phoneme Maps — `phonetic/script_phoneme_maps.py`

**Path**: `codemix_restore/phonetic/script_phoneme_maps.py`

Fallback romanization when aksharamukha is not installed. Provides character-level mapping tables for all 12 supported scripts.

#### `romanize_with_map(word, script_name)` → `str`

Maps each Indic character to its closest Latin equivalent using curated per-script lookup tables.

**Coverage**: Devanagari, Bengali, Gujarati, Gurmukhi, Tamil, Telugu, Kannada, Malayalam, Oriya, Perso-Arabic, Meetei Mayek, Ol Chiki.

**Limitations vs. aksharamukha**:
- No context-dependent rules (e.g., inherent vowel deletion)
- No schwa dropping heuristics
- Less accurate for complex conjuncts
- Can produce longer romanized forms with trailing vowels

---

### 8. Language Identification — `language_id.py`

**Path**: `codemix_restore/language_id.py` (~347 lines)

Stage 3: Determines whether an Indic-script token is a transliterated English word or a genuine native word.

#### 7-Signal Weighted Classifier

| Signal | Weight | Description |
|---|---|---|
| **Dictionary** | 0.40 | Match confidence from Stage 2. Match-type aware: exact/translit_variant (1.0×), phonetic (0.7×), edit_distance (0.5×) |
| **Suffix** | 0.12 | Presence of English morphological suffixes written in Indic script (e.g., -मेंट/-ment, -शन/-tion, -इंग/-ing) |
| **Character composition** | 0.13 | Unicode character features: nukta presence (foreign sounds), virama (consonant clusters typical of loanwords), specific conjuncts |
| **Context** | 0.10 | Language of neighboring tokens. English neighbors increase probability. |
| **Length** | 0.10 | Heuristic: very short words (1-2 base chars) penalized; medium length (4-8 chars) favored |
| **Native word list** | 0.10 | Membership in `data/{lang}_common.txt` frequency lists → strong native signal |
| **Prefix** | 0.05 | English prefixes in Indic script (e.g., प्री-/pre-, रि-/re-, अन-/un-) |

#### `LIDResult` Dataclass

| Field | Type |
|---|---|
| `is_english` | `bool` |
| `probability` | `float` (0.0–1.0) |
| `signals` | `dict[str, float]` |

**Decision threshold**: `probability >= 0.65` → classified as English.

#### Context Signal

Uses a sliding window approach:
- Checks previous non-whitespace, non-punctuation token's classification
- Checks next token's dictionary lookup result (lookahead)
- Adjacent English tokens boost probability; adjacent native tokens reduce it

---

### 9. Neural Transliteration — `neural_translit.py`

**Path**: `codemix_restore/neural_translit.py` (~328 lines)

Stage 4: Neural back-transliteration using the ai4bharat IndicXlit model.

#### Architecture

```
┌───────────────────────────────────────────────────┐
│           NeuralTransliterator.transliterate()     │
│                                                    │
│  1. Check runtime cache (dedup within session)     │
│  2. Check warm cache (pre-computed JSON files)     │
│  3. Run IndicXlit beam search                      │
│     - beam_width=10, top_k=5 candidates            │
│  4. Rerank candidates against English dictionary   │
│     - PhoneticMatcher.is_english() check            │
│     - Prefer dictionary words over unknown strings  │
│  5. Cache result for future lookups                 │
│  → Return best English word or None                 │
└───────────────────────────────────────────────────┘
```

#### Key Features

- **Beam search with reranking**: IndicXlit produces multiple transliteration candidates. The system picks the one that matches a real English word.
- **Warm cache**: Pre-computed JSON files (`data/warm_cache/{lang}.json`) store known transliterations to avoid repeated model inference.
- **Runtime cache**: In-memory `dict` prevents duplicate model calls within a session.
- **Graceful degradation**: If fairseq/IndicXlit not installed, `is_available` returns `False` and the pipeline skips neural transliteration entirely.
- **Python 3.12 compatibility**: Patches fairseq/hydra import issues via `compat/fairseq_patch.py`.
- **Short word skip**: Tokens with ≤2 base characters skip neural transliteration (too ambiguous).

#### Dependencies (Optional)

```
torch>=2.0
fairseq==0.12.2
ai4bharat-transliteration
```

These are listed under `[project.optional-dependencies] neural` in `pyproject.toml`.

---

### 10. Reconstructor — `reconstructor.py`

**Path**: `codemix_restore/reconstructor.py` (~163 lines)

Stage 5: Reassembles classified tokens into the final output string.

#### Responsibilities

1. **Token reassembly**: Walks through all tokens (including whitespace/punctuation) in position order. Substitutes restored English words at their positions.
2. **Capitalization**: Capitalizes the first letter of English words at sentence boundaries (after `.`, `!`, `?`, `।`, or at text start).
3. **Punctuation normalization**: Converts Indic punctuation to Latin equivalents when adjacent to restored English words:
   - `।` (Devanagari danda) → `.` when next to English
   - `॥` (double danda) → `.`
4. **Abbreviation handling**: Tokens with empty-string restorations (parts 2+ of multi-token abbreviations) are collapsed — no extra whitespace.
5. **Whitespace normalization**: Collapses multiple spaces, trims edges.

---

### 11. Abbreviation Detection — `abbreviation.py`

**Path**: `codemix_restore/abbreviation.py` (~147 lines)

Pre-Pass A: Detects sequences of Indic-script tokens that represent English letter names.

#### How It Works

Indian ASR systems often produce spelled-out English abbreviations in Indic script:
- "ડી એ" (Gujarati: "D A") should become "D.A."
- "एम पी" (Hindi: "M P") should become "M.P."

#### `INDIC_LETTER_MAP`

Per-script mappings from Indic letter-name tokens to English letters:

```python
INDIC_LETTER_MAP = {
    "Devanagari": {"एम": "M", "एन": "N", "पी": "P", "सी": "C", "डी": "D", "बी": "B", ...},
    "Bengali": {"ডি": "D", "বি": "B", "এম": "M", ...},
    "Gujarati": {"ડી": "D", "બી": "B", "એમ": "M", ...},
    # ... 7 scripts total
}
```

#### `detect_abbreviation_sequence(words, start_index)` → `(str, count) | None`

Scans from `start_index` looking for 2+ consecutive words that are all in the letter map. Returns the joined abbreviation with dots (e.g., "D.A.") and the number of tokens consumed.

---

### 12. Confusable Filter — `confusable_filter.py`

**Path**: `codemix_restore/confusable_filter.py` (~204 lines)

Prevents known false-positive matches where an Indic native word phonetically resembles an English word but should not be restored.

#### Two-Layer Filtering

**Layer 1: `_BLOCKLIST`** — `dict[tuple[str, str], set[str]]`

Explicit (language, indic_word) → blocked English words:

```python
_BLOCKLIST = {
    ("hi", "अभी"): {"abbey", "abby"},    # "now" ≠ abbey
    ("bn", "আমি"): {"army", "ami"},       # "I" ≠ army
    ("ta", "ஊர்"): {"ur", "our"},          # "town" ≠ our
    # ... ~40 entries across 12 languages
}
```

**Layer 2: Romanization Distance Heuristic**

For phonetic and edit-distance matches (not exact), computes normalized Levenshtein distance between the romanized Indic form and the English candidate. If distance > 0.50, the match is blocked.

This catches cases where the phonetic algorithm finds a superficially similar word that's actually quite different when spelled out.

---

### 13. Suffix Map — `suffix_map.py`

**Path**: `codemix_restore/suffix_map.py` (~108 lines)

Provides per-language lists of agglutinative suffixes used for deagglutination in dictionary lookup.

#### `AGGLUTINATIVE_SUFFIXES`

```python
AGGLUTINATIVE_SUFFIXES = {
    "hi": ["में", "को", "से", "पर", "ने", "का", "की", "के", ...],
    "bn": ["তে", "কে", "র", "এ", "য়", ...],
    "ta": ["ல", "ல்", "க்கு", "யில்", ...],
    # ... 14 languages total
}
```

Each suffix list is ordered longest-first to prevent partial matches. The lookup module tries stripping each suffix and re-looking up the base form.

---

## Data Files

### `data/en_dict_30k.json`

30,000 most common English words with frequency ranks. Primary dictionary for PhoneticMatcher.

```json
{"the": 1, "be": 2, "to": 3, "of": 4, "and": 5, ...}
```

### `data/{lang}_common.txt`

Per-language native word frequency lists. One word per line, ordered by frequency. Used as a signal (not hard block) in LID.

**Coverage**: 21 languages. Size varies from ~300 words (Manipuri, Santali) to ~5000+ words (Hindi, Bengali).

### `data/warm_cache/{lang}.json`

Pre-computed neural transliteration results. Maps Indic words to their best English transliteration. Avoids repeated model inference.

```json
{"हेल्प": "help", "प्रोग्राम": "program", ...}
```

---

## Confidence & Decision Flow

The system uses a graduated confidence model to minimize false positives (native words wrongly converted to English), which are more damaging than false negatives (missed English words).

```
Token arrives (INDIC script)
    │
    ├─ In _KNOWN_TRANSLITERATIONS? ──→ HIGH → Restore ✓
    │
    ├─ In _NATIVE_EXCLUSIONS? ──→ LOW → Keep native ✓
    │
    ├─ In ConfusableFilter._BLOCKLIST? ──→ Block that candidate
    │
    ├─ Phonetic match score ≥ 0.85? ──→ HIGH → Restore ✓
    │
    ├─ Phonetic match score ≤ 0.55? ──→ LOW → Keep native ✓
    │
    ├─ Score in between? ──→ MEDIUM/AMBIGUOUS → Defer to LID
    │       │
    │       ├─ LID probability ≥ 0.75 + any match → Restore
    │       ├─ LID probability ≥ 0.65 + strong match → Restore
    │       ├─ LID probability ≥ 0.65 + weak match → Keep native
    │       └─ LID probability < 0.65 → Keep native ✓
    │
    └─ No match at all? ──→ LID + Neural transliteration
            │
            ├─ Neural finds dictionary word → Restore
            └─ Neural fails → Keep native ✓
```

---

## Dependency Graph

```
pipeline.py (ScriptRestorer)
    ├── config.py (LanguageConfig, detect_lang_from_script)
    ├── tokenizer.py (tokenize, Token, ScriptType)
    ├── abbreviation.py (detect_abbreviation_sequence)
    ├── dictionary_lookup.py (DictionaryLookup, Confidence)
    │   ├── phonetic/engine.py (PhoneticMatcher)
    │   │   └── data/en_dict_30k.json
    │   ├── phonetic/script_phoneme_maps.py (romanize_with_map)
    │   ├── confusable_filter.py (ConfusableFilter)
    │   ├── suffix_map.py (AGGLUTINATIVE_SUFFIXES)
    │   ├── data/{lang}_common.txt (native word lists)
    │   └── [aksharamukha] (optional — romanization)
    ├── language_id.py (WordLanguageIdentifier)
    ├── neural_translit.py (NeuralTransliterator)
    │   ├── phonetic/engine.py (for candidate reranking)
    │   ├── data/warm_cache/{lang}.json
    │   └── [fairseq, ai4bharat-transliteration] (optional)
    └── reconstructor.py (Reconstructor)
```

---

## External Dependencies

| Package | Required | Purpose |
|---|---|---|
| `aksharamukha` | Core | High-quality Indic-to-Latin romanization |
| `metaphone` | Core | Double Metaphone phonetic encoding |
| `symspellpy` | Core | Fast edit-distance dictionary lookup |
| `torch` | Optional (neural) | PyTorch for IndicXlit model |
| `fairseq` | Optional (neural) | Sequence-to-sequence framework for IndicXlit |
| `ai4bharat-transliteration` | Optional (neural) | IndicXlit pre-trained transliteration models |

The system degrades gracefully when optional (or even core) dependencies are missing — fallback code paths exist for all three core dependencies.

---

## Test Infrastructure

| File | Tests | Purpose |
|---|---|---|
| `tests/` | 60 | Unit tests for individual modules (pytest) |
| `test_new_examples.py` | 148 | End-to-end integration tests — batch 1 |
| `test_new_examples_2.py` | 156 | End-to-end integration tests — batch 2 |
| `e2e_test_unseen.py` | 77 | Unseen sentence evaluation |
| `e2e_test_expanded.py` | — | Expanded end-to-end evaluation |
| `run_predictions_sample.py` | — | Bulk prediction sampling (200 sentences) |

---

## Design Principles

1. **Precision over recall**: False positives (native → English) are worse than false negatives (missed English). The system is tuned to keep native words native unless there's strong evidence.

2. **Graceful degradation**: Every optional dependency has a fallback. The system works (at reduced accuracy) even with zero optional packages installed.

3. **Language-agnostic pipeline, language-specific data**: The 5-stage pipeline logic is identical for all 24 languages. Language-specific behavior comes from `LanguageConfig`, transliteration tables, native word lists, and suffix maps.

4. **Multiple matching strategies**: No single matching approach works for all cases. The layered approach (known transliterations → romanization + exact match → phonetic → edit-distance → neural) catches different types of words.

5. **Explainability**: `return_details=True` provides per-token audit trail showing which stage made each decision and with what confidence.
