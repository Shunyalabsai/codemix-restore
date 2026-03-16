"""Language configuration registry for all 22 scheduled Indian languages."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LanguageConfig:
    """Configuration for a single language."""

    lang_code: str  # ISO 639-1/3 code
    lang_name: str
    script_name: str  # Aksharamukha script name
    unicode_ranges: list[tuple[int, int]]  # (start, end) inclusive
    indicxlit_code: str | None  # IndicXlit language code, None if unsupported
    has_aspirates: bool = True
    has_retroflex: bool = True
    # Punctuation characters that act as sentence-enders in this script
    sentence_enders: list[str] = field(default_factory=lambda: ["।", "॥"])
    family: str = "indo-aryan"  # indo-aryan, dravidian, tibeto-burman, austroasiatic


# All 22 scheduled languages of India
LANGUAGE_CONFIGS: dict[str, LanguageConfig] = {
    # --- Indo-Aryan (Devanagari script) ---
    "hi": LanguageConfig(
        lang_code="hi",
        lang_name="Hindi",
        script_name="Devanagari",
        unicode_ranges=[(0x0900, 0x097F), (0xA8E0, 0xA8FF)],  # + Devanagari Extended
        indicxlit_code="hi",
        has_aspirates=True,
        has_retroflex=True,
        family="indo-aryan",
    ),
    "mr": LanguageConfig(
        lang_code="mr",
        lang_name="Marathi",
        script_name="Devanagari",
        unicode_ranges=[(0x0900, 0x097F), (0xA8E0, 0xA8FF)],
        indicxlit_code="mr",
        has_aspirates=True,
        has_retroflex=True,
        family="indo-aryan",
    ),
    "ne": LanguageConfig(
        lang_code="ne",
        lang_name="Nepali",
        script_name="Devanagari",
        unicode_ranges=[(0x0900, 0x097F)],
        indicxlit_code="ne",
        has_aspirates=True,
        has_retroflex=True,
        family="indo-aryan",
    ),
    "sa": LanguageConfig(
        lang_code="sa",
        lang_name="Sanskrit",
        script_name="Devanagari",
        unicode_ranges=[(0x0900, 0x097F), (0x1CD0, 0x1CFF)],  # + Vedic Extensions
        indicxlit_code=None,  # Not supported by IndicXlit
        has_aspirates=True,
        has_retroflex=True,
        family="indo-aryan",
    ),
    "kok": LanguageConfig(
        lang_code="kok",
        lang_name="Konkani",
        script_name="Devanagari",
        unicode_ranges=[(0x0900, 0x097F)],
        indicxlit_code="kok",
        has_aspirates=True,
        has_retroflex=True,
        family="indo-aryan",
    ),
    "doi": LanguageConfig(
        lang_code="doi",
        lang_name="Dogri",
        script_name="Devanagari",
        unicode_ranges=[(0x0900, 0x097F)],
        indicxlit_code=None,
        has_aspirates=True,
        has_retroflex=True,
        family="indo-aryan",
    ),
    "mai": LanguageConfig(
        lang_code="mai",
        lang_name="Maithili",
        script_name="Devanagari",
        unicode_ranges=[(0x0900, 0x097F)],
        indicxlit_code="mai",
        has_aspirates=True,
        has_retroflex=True,
        family="indo-aryan",
    ),
    "brx": LanguageConfig(
        lang_code="brx",
        lang_name="Bodo",
        script_name="Devanagari",
        unicode_ranges=[(0x0900, 0x097F)],
        indicxlit_code="brx",
        has_aspirates=True,
        has_retroflex=False,
        family="tibeto-burman",
    ),
    # --- Indo-Aryan (Bengali script) ---
    "bn": LanguageConfig(
        lang_code="bn",
        lang_name="Bengali",
        script_name="Bengali",
        unicode_ranges=[(0x0980, 0x09FF)],
        indicxlit_code="bn",
        has_aspirates=True,
        has_retroflex=True,
        family="indo-aryan",
    ),
    "as": LanguageConfig(
        lang_code="as",
        lang_name="Assamese",
        script_name="Assamese",  # Uses Bengali script with minor differences
        unicode_ranges=[(0x0980, 0x09FF)],
        indicxlit_code="as",
        has_aspirates=True,
        has_retroflex=True,
        family="indo-aryan",
    ),
    # --- Indo-Aryan (Gujarati script) ---
    "gu": LanguageConfig(
        lang_code="gu",
        lang_name="Gujarati",
        script_name="Gujarati",
        unicode_ranges=[(0x0A80, 0x0AFF)],
        indicxlit_code="gu",
        has_aspirates=True,
        has_retroflex=True,
        family="indo-aryan",
    ),
    # --- Indo-Aryan (Gurmukhi/Punjabi script) ---
    "pa": LanguageConfig(
        lang_code="pa",
        lang_name="Punjabi",
        script_name="Gurmukhi",
        unicode_ranges=[(0x0A00, 0x0A7F)],
        indicxlit_code="pa",
        has_aspirates=True,
        has_retroflex=True,
        family="indo-aryan",
    ),
    # --- Indo-Aryan (Odia script) ---
    "or": LanguageConfig(
        lang_code="or",
        lang_name="Odia",
        script_name="Oriya",
        unicode_ranges=[(0x0B00, 0x0B7F)],
        indicxlit_code="or",
        has_aspirates=True,
        has_retroflex=True,
        family="indo-aryan",
    ),
    # --- Indo-Aryan (Perso-Arabic scripts) ---
    "ur": LanguageConfig(
        lang_code="ur",
        lang_name="Urdu",
        script_name="Urdu",
        unicode_ranges=[(0x0600, 0x06FF), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)],
        indicxlit_code="ur",
        has_aspirates=True,
        has_retroflex=True,
        sentence_enders=["۔"],
        family="indo-aryan",
    ),
    "sd": LanguageConfig(
        lang_code="sd",
        lang_name="Sindhi",
        script_name="Sindhi",  # Perso-Arabic variant
        unicode_ranges=[(0x0600, 0x06FF), (0x0860, 0x086F)],
        indicxlit_code="sd",
        has_aspirates=True,
        has_retroflex=True,
        sentence_enders=["۔"],
        family="indo-aryan",
    ),
    "ks": LanguageConfig(
        lang_code="ks",
        lang_name="Kashmiri",
        script_name="Kashmiri",  # Perso-Arabic variant
        unicode_ranges=[(0x0600, 0x06FF)],
        indicxlit_code=None,
        has_aspirates=True,
        has_retroflex=True,
        sentence_enders=["۔"],
        family="indo-aryan",
    ),
    # --- Dravidian ---
    "ta": LanguageConfig(
        lang_code="ta",
        lang_name="Tamil",
        script_name="Tamil",
        unicode_ranges=[(0x0B80, 0x0BFF)],
        indicxlit_code="ta",
        has_aspirates=False,  # Tamil lacks aspirated consonants
        has_retroflex=True,
        sentence_enders=["।", "॥"],
        family="dravidian",
    ),
    "te": LanguageConfig(
        lang_code="te",
        lang_name="Telugu",
        script_name="Telugu",
        unicode_ranges=[(0x0C00, 0x0C7F)],
        indicxlit_code="te",
        has_aspirates=True,
        has_retroflex=True,
        family="dravidian",
    ),
    "kn": LanguageConfig(
        lang_code="kn",
        lang_name="Kannada",
        script_name="Kannada",
        unicode_ranges=[(0x0C80, 0x0CFF)],
        indicxlit_code="kn",
        has_aspirates=True,
        has_retroflex=True,
        family="dravidian",
    ),
    "ml": LanguageConfig(
        lang_code="ml",
        lang_name="Malayalam",
        script_name="Malayalam",
        unicode_ranges=[(0x0D00, 0x0D7F)],
        indicxlit_code="ml",
        has_aspirates=True,
        has_retroflex=True,
        family="dravidian",
    ),
    # --- Other ---
    "mni": LanguageConfig(
        lang_code="mni",
        lang_name="Manipuri",
        script_name="MeeteiMayek",
        unicode_ranges=[(0xABC0, 0xABFF), (0xAAE0, 0xAAFF)],
        indicxlit_code="mni",
        has_aspirates=True,
        has_retroflex=False,
        family="tibeto-burman",
    ),
    "sat": LanguageConfig(
        lang_code="sat",
        lang_name="Santali",
        script_name="OlChiki",
        unicode_ranges=[(0x1C50, 0x1C7F)],
        indicxlit_code=None,  # Not supported by IndicXlit
        has_aspirates=False,
        has_retroflex=False,
        family="austroasiatic",
    ),
}

# Mapping from script name to list of language codes that use it
SCRIPT_TO_LANGS: dict[str, list[str]] = {}
for _code, _cfg in LANGUAGE_CONFIGS.items():
    SCRIPT_TO_LANGS.setdefault(_cfg.script_name, []).append(_code)

# Language family groupings for shared LID classifiers
FAMILY_GROUPS: dict[str, list[str]] = {}
for _code, _cfg in LANGUAGE_CONFIGS.items():
    FAMILY_GROUPS.setdefault(_cfg.family, []).append(_code)


def get_config(lang_code: str) -> LanguageConfig:
    """Get language config by code. Raises KeyError if not found."""
    if lang_code not in LANGUAGE_CONFIGS:
        raise KeyError(
            f"Unsupported language: {lang_code}. "
            f"Supported: {sorted(LANGUAGE_CONFIGS.keys())}"
        )
    return LANGUAGE_CONFIGS[lang_code]


def detect_script(char: str) -> str | None:
    """Detect which Indic script a character belongs to. Returns None for Latin/unknown."""
    cp = ord(char)
    for lang_code, cfg in LANGUAGE_CONFIGS.items():
        for start, end in cfg.unicode_ranges:
            if start <= cp <= end:
                return cfg.script_name
    return None


def detect_lang_from_script(text: str) -> str | None:
    """Detect the most likely language code from script analysis of text.

    For scripts used by multiple languages (e.g., Devanagari), returns the
    most common language for that script (e.g., 'hi' for Devanagari).
    """
    script_counts: dict[str, int] = {}
    for ch in text:
        script = detect_script(ch)
        if script:
            script_counts[script] = script_counts.get(script, 0) + 1

    if not script_counts:
        return None

    dominant_script = max(script_counts, key=script_counts.get)  # type: ignore[arg-type]
    langs = SCRIPT_TO_LANGS.get(dominant_script, [])
    return langs[0] if langs else None
