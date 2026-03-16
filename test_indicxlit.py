#!/usr/bin/env python3
"""Test IndicXlit transliteration with Python 3.12 compatibility patch.

fairseq and hydra use mutable dataclass defaults which Python 3.12 rejects.
This script patches dataclasses._get_field before any imports to work around it.
"""

import dataclasses

# ── Python 3.12 compatibility patch ──────────────────────────────────────────
# fairseq, hydra-core, and older torch all use mutable objects as dataclass
# field defaults (e.g. `field_name: SomeConfig = SomeConfig()`).  Python >= 3.11
# raises ValueError for these.  We intercept the check and auto-wrap them in
# `default_factory`.

_original_get_field = dataclasses._get_field

def _patched_get_field(cls, a_name, a_type, kw_only):
    """Allow mutable defaults in dataclass fields for fairseq/hydra compat."""
    try:
        return _original_get_field(cls, a_name, a_type, kw_only)
    except (ValueError, TypeError) as e:
        if "mutable default" not in str(e) and "default factory" not in str(e):
            raise
        # Get the current class attribute
        default = cls.__dict__.get(a_name, dataclasses.MISSING)
        if isinstance(default, dataclasses.Field):
            # field(default=MutableObj()) — convert to default_factory
            if default.default is not dataclasses.MISSING:
                mutable_val = default.default
                new_field = dataclasses.field(
                    default_factory=lambda d=mutable_val: d,
                    init=default.init,
                    repr=default.repr,
                    hash=default.hash,
                    compare=default.compare,
                    metadata=default.metadata,
                    kw_only=default.kw_only,
                )
                setattr(cls, a_name, new_field)
            else:
                raise
        elif default is not dataclasses.MISSING:
            # Raw mutable default on the class
            mutable_val = default
            setattr(cls, a_name, dataclasses.field(default_factory=lambda d=mutable_val: d))
        else:
            raise
        return _original_get_field(cls, a_name, a_type, kw_only)

dataclasses._get_field = _patched_get_field
# ─────────────────────────────────────────────────────────────────────────────

print("Patch applied. Importing IndicXlit...")

from ai4bharat.transliteration import XlitEngine

print("Initializing Indic->English engine (this downloads ~120MB model on first run)...")
engine = XlitEngine(src_script_type="indic", beam_width=4, rescore=True)
print("Engine initialized!\n")

# Test words across languages
tests = [
    # (word, lang_code, expected_english)
    # Hindi (Devanagari)
    ("कंप्यूटर", "hi", "computer"),
    ("इंजीनियर", "hi", "engineer"),
    ("मैनेजर", "hi", "manager"),
    ("ऑफिस", "hi", "office"),
    ("ऑनलाइन", "hi", "online"),
    ("पेमेंट", "hi", "payment"),
    ("सॉफ्टवेयर", "hi", "software"),
    ("ट्रैफिक", "hi", "traffic"),
    ("हॉस्पिटल", "hi", "hospital"),
    ("यूनिवर्सिटी", "hi", "university"),
    ("रेस्टोरेंट", "hi", "restaurant"),
    ("टेक्नोलॉजी", "hi", "technology"),
    ("प्रॉब्लम", "hi", "problem"),
    ("कस्टमर", "hi", "customer"),
    # Bengali
    ("ইঞ্জিনিয়ার", "bn", "engineer"),
    ("কম্পিউটার", "bn", "computer"),
    ("সফটওয়্যার", "bn", "software"),
    ("সার্ভার", "bn", "server"),
    ("ইন্টারনেট", "bn", "internet"),
    # Tamil
    ("கம்ப்யூட்டர்", "ta", "computer"),
    ("ப்ராஜெக்ட்", "ta", "project"),
    ("மீட்டிங்", "ta", "meeting"),
    # Telugu
    ("ప్రాజెక్ట్", "te", "project"),
    ("ఆఫీస్", "te", "office"),
    # Kannada
    ("ಮ್ಯಾನೇಜರ್", "kn", "manager"),
    ("ಕ್ಯಾನ್ಸಲ್", "kn", "cancel"),
    # Gujarati
    ("ઓફિસ", "gu", "office"),
    # Punjabi
    ("ਕੰਪਿਊਟਰ", "pa", "computer"),
    # Marathi
    ("ऑफिसमध्ये", "mr", "office (agglutinated)"),
]

print(f"{'Word':20s} {'Lang':5s} {'Top-3 IndicXlit':50s} {'Expected':15s} {'Match?'}")
print("=" * 100)
correct = 0
for word, lang, expected in tests:
    try:
        results = engine.translit_word(word, lang_code=lang, topk=4)
        top3_str = ", ".join(results[:3]) if results else "(no result)"
        expected_clean = expected.split(" (")[0]  # strip comments
        match = any(expected_clean in r for r in results[:4])
        if match:
            correct += 1
        print(f"{word:20s} {lang:5s} {top3_str:50s} {expected:15s} {'OK' if match else 'MISS'}")
    except Exception as e:
        print(f"{word:20s} {lang:5s} ERROR: {e}")

print(f"\n{correct}/{len(tests)} words had expected English in top-4 ({correct/len(tests)*100:.0f}%)")
