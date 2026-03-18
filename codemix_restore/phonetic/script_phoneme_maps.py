"""Script-specific phoneme mapping tables for Indic → Latin transliteration.

These maps provide more accurate romanization than the generic Unicode name-based
fallback, specifically tuned for how Indians transliterate English words.
"""

import unicodedata

# Devanagari consonant and vowel mappings to Latin (colloquial/phonetic style)
DEVANAGARI_MAP: dict[str, str] = {
    # Vowels (independent)
    "अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo",
    "ऋ": "ri", "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au",
    "ऑ": "o",  # Candra O (independent) — English loanwords: ऑफिस, ऑनलाइन
    # Vowel signs (dependent)
    "ा": "aa", "ि": "i", "ी": "ee", "ु": "u", "ू": "oo",
    "ृ": "ri", "े": "e", "ै": "ai", "ो": "o", "ौ": "au",
    # Consonants
    "क": "ka", "ख": "kha", "ग": "ga", "घ": "gha", "ङ": "nga",
    "च": "cha", "छ": "chha", "ज": "ja", "झ": "jha", "ञ": "nya",
    "ट": "ta", "ठ": "tha", "ड": "da", "ढ": "dha", "ण": "na",
    "त": "ta", "थ": "tha", "द": "da", "ध": "dha", "न": "na",
    "प": "pa", "फ": "pha", "ब": "ba", "भ": "bha", "म": "ma",
    "य": "ya", "र": "ra", "ल": "la", "व": "va", "श": "sha",
    "ष": "sha", "स": "sa", "ह": "ha",
    # Special
    "ं": "n", "ः": "h", "ँ": "n",
    "्": "",  # Virama — suppresses inherent vowel
    "़": "",  # Nukta
    "ॉ": "o",  # Candra O (used in English loanwords like "doctor" → "डॉक्टर")
    "ॅ": "e",  # Candra E (used in English loanwords)
    # Nukta variants (for English sounds)
    "क़": "qa", "ख़": "kha", "ग़": "gha", "ज़": "za", "ड़": "da",
    "ढ़": "dha", "फ़": "fa", "य़": "ya",
}

# Bengali consonant and vowel mappings
BENGALI_MAP: dict[str, str] = {
    # Vowels
    "অ": "a", "আ": "aa", "ই": "i", "ঈ": "ee", "উ": "u", "ঊ": "oo",
    "ঋ": "ri", "এ": "e", "ঐ": "ai", "ও": "o", "ঔ": "au",
    # Vowel signs
    "া": "aa", "ি": "i", "ী": "ee", "ু": "u", "ূ": "oo",
    "ৃ": "ri", "ে": "e", "ৈ": "ai", "ো": "o", "ৌ": "au",
    # Consonants
    "ক": "ka", "খ": "kha", "গ": "ga", "ঘ": "gha", "ঙ": "nga",
    "চ": "cha", "ছ": "chha", "জ": "ja", "ঝ": "jha", "ঞ": "nya",
    "ট": "ta", "ঠ": "tha", "ড": "da", "ঢ": "dha", "ণ": "na",
    "ত": "ta", "থ": "tha", "দ": "da", "ধ": "dha", "ন": "na",
    "প": "pa", "ফ": "pha", "ব": "ba", "ভ": "bha", "ম": "ma",
    "য": "ja", "র": "ra", "ল": "la", "শ": "sha",
    "ষ": "sha", "স": "sa", "হ": "ha", "য়": "ya",
    "ং": "ng", "ঃ": "h", "ঁ": "n",
    "্": "",  # Virama
    "়": "",  # Nukta (standalone)
    # Special Bengali
    "ড়": "ra", "ঢ়": "rha",
}

# Tamil consonant and vowel mappings
TAMIL_MAP: dict[str, str] = {
    # Vowels
    "அ": "a", "ஆ": "aa", "இ": "i", "ஈ": "ee", "உ": "u", "ஊ": "oo",
    "எ": "e", "ஏ": "ee", "ஐ": "ai", "ஒ": "o", "ஓ": "oo", "ஔ": "au",
    # Vowel signs
    "ா": "aa", "ி": "i", "ீ": "ee", "ு": "u", "ூ": "oo",
    "ெ": "e", "ே": "ee", "ை": "ai", "ொ": "o", "ோ": "oo", "ௌ": "au",
    # Consonants (Tamil has no aspirated consonants)
    "க": "ka", "ங": "nga", "ச": "cha", "ஞ": "nya",
    "ட": "ta", "ண": "na", "த": "tha", "ந": "na",
    "ப": "pa", "ம": "ma", "ய": "ya", "ர": "ra",
    "ல": "la", "வ": "va", "ழ": "zha", "ள": "la",
    "ற": "ra", "ன": "na", "ஜ": "ja", "ஷ": "sha",
    "ஸ": "sa", "ஹ": "ha",
    "்": "",  # Virama
    "ஃ": "h",  # Aytham
}

# Telugu consonant and vowel mappings
TELUGU_MAP: dict[str, str] = {
    # Vowels
    "అ": "a", "ఆ": "aa", "ఇ": "i", "ఈ": "ee", "ఉ": "u", "ఊ": "oo",
    "ఋ": "ri", "ఎ": "e", "ఏ": "ee", "ఐ": "ai", "ఒ": "o", "ఓ": "oo", "ఔ": "au",
    # Vowel signs
    "ా": "aa", "ి": "i", "ీ": "ee", "ు": "u", "ూ": "oo",
    "ృ": "ri", "ె": "e", "ే": "ee", "ై": "ai", "ొ": "o", "ో": "oo", "ౌ": "au",
    # Consonants
    "క": "ka", "ఖ": "kha", "గ": "ga", "ఘ": "gha", "ఙ": "nga",
    "చ": "cha", "ఛ": "chha", "జ": "ja", "ఝ": "jha", "ఞ": "nya",
    "ట": "ta", "ఠ": "tha", "డ": "da", "ఢ": "dha", "ణ": "na",
    "త": "ta", "థ": "tha", "ద": "da", "ధ": "dha", "న": "na",
    "ప": "pa", "ఫ": "pha", "బ": "ba", "భ": "bha", "మ": "ma",
    "య": "ya", "ర": "ra", "ల": "la", "వ": "va", "శ": "sha",
    "ష": "sha", "స": "sa", "హ": "ha",
    "ం": "n", "ః": "h",
    "్": "",  # Virama
}

# Kannada consonant and vowel mappings
KANNADA_MAP: dict[str, str] = {
    # Vowels
    "ಅ": "a", "ಆ": "aa", "ಇ": "i", "ಈ": "ee", "ಉ": "u", "ಊ": "oo",
    "ಋ": "ri", "ಎ": "e", "ಏ": "ee", "ಐ": "ai", "ಒ": "o", "ಓ": "oo", "ಔ": "au",
    # Vowel signs
    "ಾ": "aa", "ಿ": "i", "ೀ": "ee", "ು": "u", "ೂ": "oo",
    "ೃ": "ri", "ೆ": "e", "ೇ": "ee", "ೈ": "ai", "ೊ": "o", "ೋ": "oo", "ೌ": "au",
    # Consonants
    "ಕ": "ka", "ಖ": "kha", "ಗ": "ga", "ಘ": "gha", "ಙ": "nga",
    "ಚ": "cha", "ಛ": "chha", "ಜ": "ja", "ಝ": "jha", "ಞ": "nya",
    "ಟ": "ta", "ಠ": "tha", "ಡ": "da", "ಢ": "dha", "ಣ": "na",
    "ತ": "ta", "ಥ": "tha", "ದ": "da", "ಧ": "dha", "ನ": "na",
    "ಪ": "pa", "ಫ": "pha", "ಬ": "ba", "ಭ": "bha", "ಮ": "ma",
    "ಯ": "ya", "ರ": "ra", "ಲ": "la", "ವ": "va", "ಶ": "sha",
    "ಷ": "sha", "ಸ": "sa", "ಹ": "ha",
    "ಂ": "n", "ಃ": "h",
    "್": "",  # Virama
}

# Gujarati consonant and vowel mappings
GUJARATI_MAP: dict[str, str] = {
    # Vowels
    "અ": "a", "આ": "aa", "ઇ": "i", "ઈ": "ee", "ઉ": "u", "ઊ": "oo",
    "ઋ": "ri", "એ": "e", "ઐ": "ai", "ઓ": "o", "ઔ": "au",
    # Vowel signs
    "ા": "aa", "િ": "i", "ી": "ee", "ુ": "u", "ૂ": "oo",
    "ૃ": "ri", "ે": "e", "ૈ": "ai", "ો": "o", "ૌ": "au",
    # Consonants
    "ક": "ka", "ખ": "kha", "ગ": "ga", "ઘ": "gha", "ઙ": "nga",
    "ચ": "cha", "છ": "chha", "જ": "ja", "ઝ": "jha", "ઞ": "nya",
    "ટ": "ta", "ઠ": "tha", "ડ": "da", "ઢ": "dha", "ણ": "na",
    "ત": "ta", "થ": "tha", "દ": "da", "ધ": "dha", "ન": "na",
    "પ": "pa", "ફ": "pha", "બ": "ba", "ભ": "bha", "મ": "ma",
    "ય": "ya", "ર": "ra", "લ": "la", "વ": "va", "શ": "sha",
    "ષ": "sha", "સ": "sa", "હ": "ha",
    "ં": "n", "ઃ": "h",
    "્": "",  # Virama
}

# Gurmukhi (Punjabi) consonant and vowel mappings
GURMUKHI_MAP: dict[str, str] = {
    # Vowels
    "ਅ": "a", "ਆ": "aa", "ਇ": "i", "ਈ": "ee", "ਉ": "u", "ਊ": "oo",
    "ਏ": "e", "ਐ": "ai", "ਓ": "o", "ਔ": "au",
    # Vowel signs
    "ਾ": "aa", "ਿ": "i", "ੀ": "ee", "ੁ": "u", "ੂ": "oo",
    "ੇ": "e", "ੈ": "ai", "ੋ": "o", "ੌ": "au",
    # Consonants
    "ਕ": "ka", "ਖ": "kha", "ਗ": "ga", "ਘ": "gha", "ਙ": "nga",
    "ਚ": "cha", "ਛ": "chha", "ਜ": "ja", "ਝ": "jha", "ਞ": "nya",
    "ਟ": "ta", "ਠ": "tha", "ਡ": "da", "ਢ": "dha", "ਣ": "na",
    "ਤ": "ta", "ਥ": "tha", "ਦ": "da", "ਧ": "dha", "ਨ": "na",
    "ਪ": "pa", "ਫ": "pha", "ਬ": "ba", "ਭ": "bha", "ਮ": "ma",
    "ਯ": "ya", "ਰ": "ra", "ਲ": "la", "ਵ": "va", "ਸ਼": "sha",
    "ਸ": "sa", "ਹ": "ha",
    "ੰ": "n", "ੱ": "",  # Gemination sign (addak)
    "ਂ": "n",  # Bindi (nasal) — distinct from tippi (ੰ)
    "਼": "",  # Nukta
    "੍": "",  # Virama
}

# Odia (Oriya) consonant and vowel mappings
ODIA_MAP: dict[str, str] = {
    # Vowels
    "ଅ": "a", "ଆ": "aa", "ଇ": "i", "ଈ": "ee", "ଉ": "u", "ଊ": "oo",
    "ଋ": "ri", "ଏ": "e", "ଐ": "ai", "ଓ": "o", "ଔ": "au",
    # Vowel signs
    "ା": "aa", "ି": "i", "ୀ": "ee", "ୁ": "u", "ୂ": "oo",
    "ୃ": "ri", "େ": "e", "ୈ": "ai", "ୋ": "o", "ୌ": "au",
    # Consonants
    "କ": "ka", "ଖ": "kha", "ଗ": "ga", "ଘ": "gha", "ଙ": "nga",
    "ଚ": "cha", "ଛ": "chha", "ଜ": "ja", "ଝ": "jha", "ଞ": "nya",
    "ଟ": "ta", "ଠ": "tha", "ଡ": "da", "ଢ": "dha", "ଣ": "na",
    "ତ": "ta", "ଥ": "tha", "ଦ": "da", "ଧ": "dha", "ନ": "na",
    "ପ": "pa", "ଫ": "pha", "ବ": "ba", "ଭ": "bha", "ମ": "ma",
    "ଯ": "ya", "ର": "ra", "ଲ": "la", "ଳ": "la", "ଵ": "va",
    "ଶ": "sha", "ଷ": "sha", "ସ": "sa", "ହ": "ha",
    "ଂ": "n", "ଃ": "h", "ଁ": "n",
    "୍": "",  # Virama
    "଼": "",  # Nukta
    # Nukta variants
    "ଡ଼": "da", "ଢ଼": "dha",
}

# Malayalam consonant and vowel mappings
MALAYALAM_MAP: dict[str, str] = {
    # Vowels
    "അ": "a", "ആ": "aa", "ഇ": "i", "ഈ": "ee", "ഉ": "u", "ഊ": "oo",
    "ഋ": "ri", "എ": "e", "ഏ": "ee", "ഐ": "ai", "ഒ": "o", "ഓ": "oo", "ഔ": "au",
    # Vowel signs
    "ാ": "aa", "ി": "i", "ീ": "ee", "ു": "u", "ൂ": "oo",
    "ൃ": "ri", "െ": "e", "േ": "ee", "ൈ": "ai", "ൊ": "o", "ോ": "oo", "ൌ": "au",
    "ൗ": "au",
    # Consonants
    "ക": "ka", "ഖ": "kha", "ഗ": "ga", "ഘ": "gha", "ങ": "nga",
    "ച": "cha", "ഛ": "chha", "ജ": "ja", "ഝ": "jha", "ഞ": "nya",
    "ട": "ta", "ഠ": "tha", "ഡ": "da", "ഢ": "dha", "ണ": "na",
    "ത": "tha", "ഥ": "thha", "ദ": "da", "ധ": "dha", "ന": "na",
    "പ": "pa", "ഫ": "pha", "ബ": "ba", "ഭ": "bha", "മ": "ma",
    "യ": "ya", "ര": "ra", "ല": "la", "വ": "va", "ശ": "sha",
    "ഷ": "sha", "സ": "sa", "ഹ": "ha",
    "ള": "la", "ഴ": "zha", "റ": "ra",
    "ം": "n", "ഃ": "h",
    "്": "",  # Virama (chandrakkala)
    # Chillu consonants (pure consonants without inherent vowel)
    "ൻ": "n", "ൺ": "n", "ൾ": "l", "ൽ": "l", "ർ": "r", "ൿ": "k",
}

# Urdu (Perso-Arabic) consonant and vowel mappings
URDU_MAP: dict[str, str] = {
    # Consonants
    "ا": "a", "آ": "aa", "ب": "ba", "پ": "pa", "ت": "ta", "ٹ": "ta",
    "ث": "sa", "ج": "ja", "چ": "cha", "ح": "ha", "خ": "kha",
    "د": "da", "ڈ": "da", "ذ": "za", "ر": "ra", "ڑ": "ra",
    "ز": "za", "ژ": "zha", "س": "sa", "ش": "sha", "ص": "sa",
    "ض": "za", "ط": "ta", "ظ": "za", "ع": "a", "غ": "gha",
    "ف": "fa", "ق": "qa", "ک": "ka", "گ": "ga", "ل": "la",
    "م": "ma", "ن": "na", "ں": "n", "و": "va", "ہ": "ha",
    "ھ": "ha", "ء": "", "ی": "ya", "ے": "e",
    # Diacritics
    "َ": "a", "ِ": "i", "ُ": "u", "ّ": "",  # Shadda (gemination)
    "ً": "an", "ٍ": "in", "ٌ": "un",
    "ٰ": "aa",  # Superscript alef
    "ؤ": "va", "ئ": "ya",
}

# MeeteiMayek (Manipuri) consonant and vowel mappings
MEETEI_MAYEK_MAP: dict[str, str] = {
    # Vowels (independent)
    "ꯑ": "a", "ꯒ": "ga",
    # Consonants
    "ꯀ": "ka", "ꯈ": "kha", "ꯉ": "nga",
    "ꯆ": "cha", "ꯖ": "ja", "ꯇ": "ta", "ꯊ": "tha",
    "ꯗ": "da", "ꯙ": "dha", "ꯅ": "na",
    "ꯄ": "pa", "ꯐ": "pha", "ꯕ": "ba", "ꯚ": "bha", "ꯃ": "ma",
    "ꯌ": "ya", "ꯔ": "ra", "ꯂ": "la", "ꯋ": "va",
    "ꯁ": "sa", "ꯍ": "ha",
    # Vowel signs
    "ꯥ": "aa", "ꯤ": "i", "ꯨ": "u", "ꯦ": "e", "ꯩ": "ai",
    "ꯣ": "o", "ꯧ": "au",
    # Special
    "ꯪ": "ng",
    "꯭": "",  # Virama
}

# Ol Chiki (Santali) consonant and vowel mappings
OL_CHIKI_MAP: dict[str, str] = {
    # Consonants
    "ᱚ": "a", "ᱛ": "ta", "ᱜ": "ga", "ᱝ": "nga", "ᱞ": "la",
    "ᱟ": "aa", "ᱠ": "ka", "ᱡ": "ja", "ᱢ": "ma", "ᱣ": "va",
    "ᱤ": "i", "ᱥ": "sa", "ᱦ": "ha", "ᱧ": "nya", "ᱨ": "ra",
    "ᱩ": "u", "ᱪ": "cha", "ᱫ": "da", "ᱬ": "na", "ᱭ": "ya",
    "ᱮ": "e", "ᱯ": "pa", "ᱰ": "da", "ᱱ": "na", "ᱲ": "ra",
    "ᱳ": "o", "ᱴ": "ta", "ᱵ": "ba",
    # Vowel signs / modifiers
    "ᱶ": "n",  # Mu-gaahlaa
    "ᱷ": "h",  # Ahad
}

# Map from script name to character map
SCRIPT_MAPS: dict[str, dict[str, str]] = {
    "Devanagari": DEVANAGARI_MAP,
    "Bengali": BENGALI_MAP,
    "Assamese": BENGALI_MAP,  # Assamese uses Bengali script
    "Tamil": TAMIL_MAP,
    "Telugu": TELUGU_MAP,
    "Kannada": KANNADA_MAP,
    "Gujarati": GUJARATI_MAP,
    "Gurmukhi": GURMUKHI_MAP,
    "Oriya": ODIA_MAP,
    "Malayalam": MALAYALAM_MAP,
    "Urdu": URDU_MAP,
    "Sindhi": URDU_MAP,  # Sindhi uses extended Perso-Arabic
    "Kashmiri": URDU_MAP,  # Kashmiri uses Perso-Arabic
    "MeeteiMayek": MEETEI_MAYEK_MAP,
    "OlChiki": OL_CHIKI_MAP,
}


def romanize_with_map(word: str, script_name: str) -> str | None:
    """Romanize a word using the script-specific phoneme map.

    This produces a phonetic romanization closer to how Indians spell
    English words in Latin script, making dictionary matching more accurate.

    Returns None if the script is not supported.
    """
    char_map = SCRIPT_MAPS.get(script_name)
    if char_map is None:
        return None

    # Strip zero-width characters (ZWNJ, ZWJ) that break romanization
    word = word.replace("\u200c", "").replace("\u200d", "")

    result: list[str] = []
    i = 0
    chars = list(word)

    while i < len(chars):
        # Try 2-char sequences first (for multi-char mappings like nukta variants)
        if i + 1 < len(chars):
            bigram = chars[i] + chars[i + 1]
            if bigram in char_map:
                result.append(char_map[bigram])
                i += 2
                continue

        char = chars[i]
        if char in char_map:
            mapped = char_map[char]
            # Handle virama: if current char is a consonant followed by virama,
            # strip the inherent 'a' from the consonant
            if (i + 1 < len(chars) and chars[i + 1] in char_map
                    and char_map[chars[i + 1]] == ""):
                # Next char is virama/nukta — strip trailing 'a' from consonant
                if mapped.endswith("a") and len(mapped) > 1:
                    mapped = mapped[:-1]
            # Handle vowel sign: if current char is a consonant followed by a vowel sign,
            # replace the inherent 'a' with the vowel
            elif (i + 1 < len(chars) and chars[i + 1] in char_map
                  and chars[i + 1] not in ("्", "্", "்", "్", "್", "્", "੍")
                  and len(mapped) > 1 and mapped.endswith("a")):
                next_mapped = char_map.get(chars[i + 1], "")
                # Check if next char is a vowel sign (dependent vowel)
                next_cat = unicodedata.category(chars[i + 1])
                if next_cat.startswith("M"):  # Combining mark = vowel sign
                    mapped = mapped[:-1]  # Strip inherent 'a'

            result.append(mapped)
        else:
            result.append(char)
        i += 1

    return "".join(result).lower()
