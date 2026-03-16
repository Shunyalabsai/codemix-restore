"""Per-language agglutinative suffix tables for deagglutination.

Indian languages commonly attach grammatical suffixes (case markers,
postpositions) directly to nouns. When an English loanword is used in
Indic script, native suffixes fuse with it:

    ऑफिस + मध्ये → ऑफिसमध्ये  (office + locative "in")
    টিম + কে → টিমকে          (team + dative "to")

These tables list common suffixes per language, sorted longest-first
so that stripping tries the most specific suffix before shorter ones.
"""

from __future__ import annotations

# Suffixes are sorted longest-first within each language to avoid
# partial matches (e.g., "मध्ये" must be tried before "ये").
AGGLUTINATIVE_SUFFIXES: dict[str, list[str]] = {
    # Hindi — postpositions that sometimes fuse in ASR output
    "hi": sorted([
        "में", "को", "से", "के", "की", "का", "पे", "ने",
        "वाला", "वाली", "वाले",
    ], key=len, reverse=True),

    # Marathi — case markers and postpositions
    "mr": sorted([
        "मध्ये", "मधून", "साठी",
        "ला", "ने", "चा", "ची", "चे", "त", "ना",
    ], key=len, reverse=True),

    # Bengali — case markers
    "bn": sorted([
        "গুলো", "গুলি",
        "কে", "তে", "দের", "এ", "র", "য়",
    ], key=len, reverse=True),

    # Tamil — case markers and postpositions
    "ta": sorted([
        "கிட்ட", "கிட்டே",
        "யில்", "ல்ல",
        "க்கு", "ல்",
        "ல", "இல்",
    ], key=len, reverse=True),

    # Telugu — case markers
    "te": sorted([
        "లోకి", "లోనే",
        "లో", "కి", "కు", "ని", "తో",
    ], key=len, reverse=True),

    # Kannada — case markers
    "kn": sorted([
        "ನಲ್ಲಿ", "ಅಲ್ಲಿ", "ಇಂದ",
        "ಗೆ", "ಕ್ಕೆ", "ನ",
    ], key=len, reverse=True),

    # Gujarati — case markers and postpositions
    "gu": sorted([
        "માંથી", "માટે",
        "માં", "ને", "નો", "ના", "ની", "થી",
    ], key=len, reverse=True),

    # Punjabi (Gurmukhi) — postpositions
    "pa": sorted([
        "ਵਿੱਚ", "ਤੋਂ",
        "ਨੂੰ", "ਦਾ", "ਦੀ", "ਦੇ",
    ], key=len, reverse=True),

    # Odia — case markers
    "or": sorted([
        "ରେ", "କୁ", "ର",
    ], key=len, reverse=True),

    # Assamese — uses Bengali script, similar suffixes
    "as": sorted([
        "কে", "ত", "ৰ", "লৈ",
    ], key=len, reverse=True),
}
