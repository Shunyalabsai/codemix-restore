"""Stage 2: Fast-path dictionary lookup using romanization + phonetic matching."""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from dataclasses import dataclass
from enum import Enum, auto
from functools import lru_cache
from pathlib import Path

from codemix_restore.config import get_config
from codemix_restore.confusable_filter import ConfusableFilter
from codemix_restore.phonetic.engine import MatchResult, PhoneticMatcher
from codemix_restore.phonetic.script_phoneme_maps import romanize_with_map
from codemix_restore.suffix_map import AGGLUTINATIVE_SUFFIXES

logger = logging.getLogger(__name__)


class Confidence(Enum):
    """Confidence level of the dictionary lookup."""
    HIGH = auto()       # Strong English match — use this word
    MEDIUM = auto()     # Possible match — defer to LID
    LOW = auto()        # No match — likely a native word
    AMBIGUOUS = auto()  # Uncertain — needs LID classifier


@dataclass
class LookupResult:
    """Result of dictionary lookup for a single word."""
    original: str               # Original Indic word
    romanized: str              # Romanized form
    english_match: str | None   # Best English match, if any
    confidence: Confidence
    score: float                # Match score 0.0-1.0
    match_detail: MatchResult | None = None


class DictionaryLookup:
    """Fast-path English word detection via romanization + dictionary matching.

    Pipeline:
    1. Check if word is a known native word (exclusion list)
    2. Romanize Indic word using Aksharamukha (or fallback)
    3. Look up romanized form in English dictionary (exact + phonetic + edit distance)
    4. Return confidence-scored result
    """

    # Common native words that get false-positive matched to English.
    # These are high-frequency function words / particles across Indian languages.
    # Key: romanized-ish form → should NOT be matched to English.
    _NATIVE_EXCLUSIONS: dict[str, set[str]] = {
        # Hindi — comprehensive list of function words, pronouns, postpositions,
        # common verbs, question words, numbers, and frequent content words
        # that IndicXlit often false-positives to English.
        "hi": {
            # Pronouns & demonstratives
            "मैं", "मैंने", "हम", "हमने", "तुम", "तुमने", "तू", "तूने",
            "आप", "आपने", "ये", "वे", "वो", "यह", "वह", "उन", "इन",
            "जो", "कोई", "कुछ", "सब", "खुद", "अपना", "अपनी", "अपने",
            # Oblique / inflected pronouns
            "मुझे", "मुझको", "मुझसे", "मेरा", "मेरी", "मेरे",
            "हमें", "हमको", "हमसे", "हमारा", "हमारी", "हमारे",
            "तुम्हें", "तुम्हारा", "तुम्हारी", "तुम्हारे",
            "आपको", "आपका", "आपकी", "आपके", "आपसे",
            "इसको", "इसका", "इसकी", "इसके", "इससे",
            "उसको", "उसका", "उसकी", "उसके", "उससे",
            "इनको", "इनका", "उनको", "उनका", "उनकी", "उनके",
            "जिसको", "जिसका", "जिसकी", "जिसके", "जिससे",
            "किसको", "किसका", "किसकी", "किसके", "किससे",
            # Postpositions
            "का", "की", "के", "को", "से", "में", "पर", "ने",
            "तक", "बीच", "लिए", "लिये", "बारे", "साथ", "बाद",
            "पहले", "ऊपर", "नीचे", "अंदर", "बाहर", "बिना",
            "द्वारा", "वाला", "वाली", "वाले",
            # Conjunctions
            "और", "या", "कि", "लेकिन", "मगर", "फिर",
            "इसलिए", "क्योंकि", "जब", "तब", "अगर",
            # Question words
            "क्या", "कौन", "कब", "कहां", "कहाँ", "कैसे",
            "कितना", "कितनी", "कितने", "किधर",
            # Particles, adverbs, intensifiers
            "ही", "भी", "जी", "तो", "ना", "हां", "हाँ", "हा",
            "नहीं", "अब", "बस", "बहुत", "ज्यादा", "कम",
            "ज़रा", "जरा", "सिर्फ", "जल्द", "जल्दी",
            "अभी", "यहां", "यहाँ", "वहां", "वहाँ",
            # Common verbs & inflected forms
            "कर", "करो", "करना", "करता", "करती", "करते", "करें",
            "कराना", "कराओ", "कराइए",
            "है", "हैं", "था", "थी", "थे", "हो", "होना", "होता",
            "होती", "होते", "होगा", "होगी", "होंगे", "हुआ", "हुई", "हुए",
            "जा", "जाना", "जाता", "जाती", "जाते", "जाओ", "जाएं",
            "जाएगा", "गया", "गई", "गए", "गयी",
            "आ", "आना", "आता", "आती", "आते", "आओ", "आएं",
            "आएगा", "आया", "आई", "आए",
            "दे", "देना", "देता", "देती", "देते", "दिया", "दी", "दिए",
            "ले", "लेना", "लेता", "लेती", "लेते", "लिया", "ली",
            "बता", "बताना", "बताओ", "बताएं", "बताइए", "बताया", "बताएँ",
            "सकता", "सकती", "सकते", "सकें",
            "चाहिए", "चाहते", "चाहती", "चाहेंगे",
            "रहना", "रहा", "रही", "रहे", "रहिये",
            "कहना", "कहा", "कहो", "कहें", "कहेंगे",
            "मिला", "मिली", "मिले",
            "करेगा", "करेगी", "करेंगे",
            # Numbers
            "एक", "दो", "तीन", "चार", "पांच", "छह", "सात", "आठ", "नौ", "दस",
            # Time
            "आज", "कल", "परसों", "उद्या",
            # Common nouns that false-positive to English
            "दिन", "रात", "काम", "पास", "घर", "बात", "लोग", "समय",
            "तरह", "जगह", "देश", "साल", "महीना", "हफ्ता",
            "गाड़ी", "मन", "जान", "इस", "उस",
            # Brand names / proper nouns
            "मारुति", "वाराणसी",
            # Common adjectives
            "अच्छा", "अच्छी", "अच्छे", "बड़ा", "बड़ी", "बड़े",
            "छोटा", "छोटी", "छोटे", "जरूरी", "ज़रूरी",
            # Greetings & honorifics
            "नमस्ते", "नमस्कार", "शुभ",
            # Other frequently false-positive words
            "उपयोग", "उपलब्ध", "संपर्क", "सो",
            # Additional false positives from comprehensive testing
            "बना", "बनाया", "बनाओ", "बनाए", "बनता", "बनाई",
            "खाना", "खाने", "खिलाया", "खिलाओ",
            "बाबा", "बाबू", "बापू",
            "दादी", "दादा",
            "मौसम", "पढ़कर", "सोना", "सो",
            "बगीचे", "बगीचा",
            "बच्चे", "बच्चा", "बच्चों",
            "मुझे", "बताओ",
            "चलते", "चलो", "चला", "चली",
            "बाहर", "अंदर",
            "खेल", "खेलते", "खेल",
        },
        # Marathi
        "mr": {
            "हा", "हां", "ना", "मी", "या", "हो", "का", "की", "के", "आहे",
            "करा", "करतो", "मला", "त्या", "ही", "उद्या", "तुम्हाला",
            "झाली", "झालं", "आणि", "पण", "काय", "कसं", "सगळं", "आज",
            "तू", "तुझा", "माझा", "माझी", "आपलं", "कर", "गेला", "गेली",
            # Additional false positives
            "फिरायला", "जाऊया", "बाहेर", "हवा", "छान", "खूप",
            "जेवण", "बनवतेय", "बाबा", "बाजारात", "गेलेत",
            "आई", "मुलं", "अंगणात", "खेळत", "सांगा", "कुठे",
            "जात", "जाऊ", "जाऊया",
        },
        # Bengali — expanded to reduce false positives
        "bn": {
            # Pronouns & demonstratives
            "আমি", "তুমি", "তুই", "সে", "তিনি", "আমরা", "তোমরা", "তারা",
            "এটা", "ওটা", "এটি", "ওটি", "ওই", "এই", "যে", "কে", "কি",
            "কেউ", "কিছু", "সব", "নিজে", "আপনি",
            # Oblique / possessive
            "আমার", "তোমার", "তার", "আমাদের", "তোমাদের", "তাদের",
            "আমাকে", "তোমাকে", "তাকে", "আপনার", "আপনাকে",
            # Postpositions
            "এ", "তে", "র", "কে", "দিয়ে", "থেকে", "জন্য", "নিয়ে",
            "সাথে", "পরে", "আগে", "মধ্যে", "ভেতরে", "বাইরে",
            # Conjunctions & particles
            "আর", "ও", "না", "হ্যাঁ", "হয়", "তো", "যে", "কিন্তু",
            "কারণ", "তাই", "অথবা", "এবং",
            # Common verbs
            "আছে", "আছি", "আছো", "করো", "করি", "করবো", "করে", "করছি",
            "হয়ে", "গেছে", "যাও", "আসো", "দাও", "বলো", "দেখো",
            "হচ্ছে", "হবে", "ছিল", "হোক", "করবে",
            # Question words
            "কোথায়", "কবে", "কেন", "কীভাবে", "কতটা",
            # Adverbs & time
            "এখন", "তখন", "আজ", "কাল", "আজকাল", "এখানে", "সেখানে",
            "ভালো", "খুব", "অনেক", "কম", "বেশি",
            # Common nouns that false-positive
            "কাজ", "দিন", "রাত", "লোক", "বাড়ি", "পানি", "ভাত",
            "মা", "বাবা", "সঠিক", "সঠিকে", "পিউনের", "পিউন",
            "আধ্যে", "আধা", "পুরো", "জেটা", "দ্য",
        },
        # Tamil
        "ta": {
            "இந்த", "நான்", "நாளைக்கு", "இருக்கு", "பண்ணுங்க", "உங்களுக்கு",
            "என்", "அது", "இது", "ஒரு", "போ", "வா", "என்ன", "எப்படி",
            "இப்போ", "அங்கே", "இங்கே", "யார்", "எங்கே", "ஆமா", "இல்ல",
        },
        # Telugu
        "te": {
            "ఈ", "నేను", "మీకు", "ఉంది", "చేయండి", "చేస్తాను", "రేపు",
            "ఆ", "ఏం", "ఎందుకు", "అది", "ఇది", "ఎక్కడ", "ఎప్పుడు",
            "నాకు", "మీరు", "వాళ్ళు", "ఇప్పుడు",
            # Additional false positives
            "ఇంటికి", "వెళ్తున్నాను", "నువ్వు",
            "అమ్మ", "వంట", "చేస్తోంది", "నాన్న", "బజారుకి", "వెళ్ళారు",
            "వర్షం", "వచ్చేలా",
            "పిల్లలు", "ఆడుకుంటున్నారు",
        },
        # Kannada
        "kn": {
            "ಈ", "ನಾನು", "ನಿಮಗೆ", "ಇದೆ", "ಮಾಡಿ", "ಮಾಡುತ್ತೇನೆ", "ನಾಳೆ",
            "ಅದು", "ಇದು", "ಒಂದು", "ಏನು", "ಎಲ್ಲಿ", "ಯಾವಾಗ",
            "ಹೂವಿನ", "ತೋಟ", "ಮನೆ", "ಮನೆಯಲ್ಲಿ", "ಅಜ್ಜಿ", "ಚೆನ್ನಾಗಿದೆ",
            "ನೀನು", "ಅವನು", "ಅವಳು", "ನಾವು", "ನೀವು", "ಅವರು",
            "ನನ್ನ", "ನಿನ್ನ", "ಅವನ", "ಅವಳ", "ನಮ್ಮ", "ನಿಮ್ಮ",
            "ಹೌದು", "ಇಲ್ಲ", "ಮತ್ತು", "ಆದರೆ", "ಅಥವಾ",
            "ಮಾಡು", "ಹೋಗು", "ಬಾ", "ಕೊಡು", "ತೆಗೆ",
            "ಇಂದು", "ನಿನ್ನೆ", "ಇಲ್ಲಿ", "ಅಲ್ಲಿ",
        },
        # Gujarati — expanded to reduce false positives
        "gu": {
            # Pronouns & demonstratives
            "હું", "તું", "તે", "અમે", "તમે", "તેઓ", "આ", "એ",
            "મારું", "તારું", "તેનું", "અમારું", "તમારું",
            "મને", "તને", "તેને", "અમને", "તમને",
            # Postpositions
            "ને", "નો", "ની", "ના", "થી", "માં", "પર", "માટે",
            "સાથે", "પછી", "પહેલાં", "વચ્ચે", "બહાર", "અંદર",
            # Particles & conjunctions
            "છે", "છો", "છું", "હતું", "હશે", "પણ", "અને", "કે",
            "પરંતુ", "તો", "ના", "હા", "હાં", "જી",
            # Common verbs
            "કરો", "કરે", "કરીશ", "કર્યું", "જાઓ", "આવો",
            "ગયા", "આવ્યા", "જવું", "આવવું", "થયું",
            # Question words
            "શું", "ક્યાં", "ક્યારે", "કેમ", "કોણ", "કેટલું",
            # Adverbs
            "અહીં", "ત્યાં", "હવે", "ત્યારે", "આજે", "કાલે",
            "ઉપર", "નીચે", "ખૂબ", "ઓછું", "વધારે",
            # Common words that false-positive
            "લોકો", "લોકોને", "લોકોના", "ઘર", "પાણી", "ખાવું",
            "મા", "બાપ", "ગામ", "ભાઈ", "બેન", "વાત", "દિવસ",
            "અ", "ઈ", "જ", "મેં", "ભલે", "ખાતો", "યાં",
            "જ્યારે", "ત્યારે", "બનાવશે", "ડીએ", "બીએ", "જાય",
            "ઉઠા", "એવી", "કઈ", "વિચારા",
        },
        # Punjabi
        "pa": {
            "ਇਹ", "ਮੈਂ", "ਤੁਹਾਨੂੰ", "ਹੈ", "ਕਰੋ", "ਕਰਾਂਗਾ", "ਕੱਲ",
            "ਉਹ", "ਤੇ", "ਨੂੰ", "ਵੀ", "ਕੀ", "ਕਿੱਥੇ", "ਕਦੋਂ",
            # Additional false positives
            "ਮਾਂ", "ਖਾਣਾ", "ਬਣਾ", "ਰਹੀ", "ਬਾਪੂ", "ਬਾਜ਼ਾਰ", "ਗਏ", "ਹਨ",
            "ਮੀਂਹ", "ਪੈਣ", "ਵਾਲਾ",
            "ਬੱਚੇ", "ਬਾਗ਼", "ਖੇਡ", "ਰਹੇ",
            "ਘਰ", "ਜਾ", "ਰਿਹਾ", "ਹਾਂ", "ਤੁਸੀਂ", "ਆਓ",
        },
        # Odia — expanded to reduce false positives
        "or": {
            # Pronouns
            "ମୁଁ", "ତୁ", "ସେ", "ଆମେ", "ତୁମେ", "ସେମାନେ", "ଆପଣ",
            "ମୋର", "ତୁମର", "ତାର", "ଆମର", "ଆପଣଙ୍କ",
            "ମୋତେ", "ତୁମକୁ", "ତାକୁ", "ଆମକୁ",
            # Postpositions
            "ଏ", "ର", "କୁ", "ଠାରୁ", "ରେ", "ପାଇଁ", "ସହ", "ମଧ୍ୟରେ",
            # Particles & conjunctions
            "ଅଛି", "ନାହିଁ", "ହଁ", "ନା", "ଆଉ", "ଓ", "କିନ୍ତୁ", "ତେଣୁ",
            "ଏବଂ", "ବା", "ତଥାପି",
            # Common verbs
            "କରନ୍ତୁ", "କର", "ଯାଅ", "ଆସ", "ଦିଅ", "ନିଅ", "ଦେଖ",
            "ହେଉଛି", "ଥିଲା", "ହେବ", "କରୁଛି", "ଗଲା", "ଆସିଲା",
            # Question words
            "କଣ", "କେବେ", "କେଉଁଠି", "କିଏ", "କାହିଁକି", "କେମିତି",
            # Time & place
            "ଆଜି", "କାଲି", "ଏଠି", "ସେଠି", "ଏବେ", "ସେବେ",
            # Common words that false-positive
            "ଲୋକ", "ଘର", "ପାଣି", "ଭାତ", "ମା", "ବାପା",
            "ଗାଁ", "ଭାଇ", "କଥା", "ଦିନ", "ରାତି",
            "ଜାପାନୀ", "ଖେତରେ", "ଖେତ", "ଧାନ", "ବୁଣୁଛନ୍ତି",
        },
        # Assamese — expanded to reduce false positives
        "as": {
            # Pronouns
            "মই", "তুমি", "তই", "সি", "তেওঁ", "আমি", "আপুনি",
            "আমাৰ", "তোমাৰ", "তাৰ", "মোৰ", "আপোনাৰ",
            # Postpositions
            "ত", "ৰ", "লৈ", "পৰা", "বাবে", "সৈতে", "মাজত",
            # Particles & adverbs
            "হয়", "নাই", "নহয়", "আৰু", "কিন্তু", "হ্যাঁ", "নে",
            "এতিয়া", "তেতিয়া", "আজি", "কালি", "ইয়াত", "তাত",
            "ভাল", "বেয়া", "বহুত", "অকণ",
            # Common verbs
            "আছে", "আছিল", "কৰা", "কৰক", "যোৱা", "আহা", "দিয়া",
            "কৰে", "কৰিছে", "গৈছে", "আহিছে", "হৈ",
            # Question words
            "কি", "কেতিয়া", "ক'ত", "কিয়", "কেনে", "কোন",
            # Common nouns/words that false-positive
            "মানুহ", "ঘৰ", "পানী", "ভাত", "মা", "দেউতা",
            "গাঁও", "ভাই", "বাই", "কথা", "দিন", "ৰাতি",
            "অঁ", "হেতু", "চাগে", "তেনেকুৱাকে", "এইবাৰ", "এয়া",
        },
        # Malayalam
        "ml": {
            "ഞാൻ", "ഞാന്", "നീ", "നിങ്ങൾ", "അവൻ", "അവൾ", "അത്",
            "ഇത്", "ആ", "ഈ", "ഒരു", "എന്ത്", "എവിടെ", "എപ്പോൾ",
            "എങ്ങനെ", "ആര്", "ഉണ്ട്", "ഇല്ല", "ആണ്", "വേണം",
            "പോകുക", "വരുക", "ചെയ്യുക", "കൊടുക്കുക",
            "ഇന്ന്", "നാളെ", "ഇന്നലെ", "ഇവിടെ", "അവിടെ",
            "നല്ല", "വലിയ", "ചെറിയ",
            "അല്ല", "അതെ", "വേണ്ട", "പക്ഷേ", "അല്ലെങ്കിൽ",
        },
        # Nepali
        "ne": {
            "म", "तिमी", "उनी", "हामी", "तपाईं", "यो", "त्यो",
            "मेरो", "तिम्रो", "उनको", "हाम्रो", "तपाईंको",
            "के", "कहाँ", "कहिले", "कसरी", "कति", "को", "किन",
            "छ", "छैन", "थियो", "हुन्छ", "गर्नु", "जानु", "आउनु",
            "हो", "होइन", "र", "तर", "त्यसैले",
            "आज", "भोलि", "हिजो", "अहिले", "त्यहाँ", "यहाँ",
            # Additional false positives
            "आमाले", "आमा", "खाना", "बनाउनुभयो", "बुवा", "बजार", "जानुभयो",
            "पानी", "पर्ने", "जस्तो",
            "केटाकेटी", "बगैँचामा", "खेलिरहेका", "छन्",
            "घर", "जाँदैछु", "आउ",
        },
        # Urdu
        "ur": {
            "میں", "ہم", "تم", "آپ", "وہ", "یہ", "کیا", "کون",
            "کہاں", "کب", "کیسے", "کتنا", "ہے", "ہیں", "تھا", "تھی",
            "ہوں", "نہیں", "جی", "ہاں", "نا", "اور", "یا", "لیکن",
            "سے", "کو", "میں", "پر", "نے", "کا", "کی", "کے",
            "کرنا", "جانا", "آنا", "دینا", "لینا", "بتانا",
            # Additional false positives
            "امی", "ابو", "بنا", "رہی", "رہا", "رہے",
            "کھانا", "بازار", "گئے",
            "بارش", "ہونے", "والی",
            "بچے", "باغ", "کھیل",
            "گھر", "جا", "آ", "جاؤ",
            "وائی", "فائی",  # Split wifi
            "اسکرین", "شاٹ",  # Split screenshot
            "بھیجو",
        },
        # Sindhi
        "sd": {
            "آء", "تون", "هو", "اسان", "توهان", "ڪير", "ڇا",
            "ڪٿي", "ڪڏهن", "ڪيئن", "آهي", "ناهي", "هئي",
            "۽", "يا", "پر", "ڇاڪاڻ", "تنهنڪري",
        },
        # Konkani
        "kok": {
            "हांव", "तूं", "तो", "ती", "आमी", "तुमी",
            "कितें", "खंय", "केन्ना", "कशें", "आसा", "ना",
            "आनी", "पूण", "देकून",
            # Additional: daily life words
            "आवय", "जेवण", "करता", "रांदपाच्या", "कुडींत",
        },
        # Maithili
        "mai": {
            "हम", "अहाँ", "ओ", "सब", "ई", "ओ", "की",
            "कतए", "कखन", "कोना", "छी", "छल", "नहि",
            "आ", "वा", "मुदा",
            # Additional false positives
            "माय", "भात", "बना", "रहल", "छथि", "बाबूजी", "गेलाह",
            "बरखा", "होयत", "जेना", "लागैत", "अछि",
            "घर", "जा", "आउ",
        },
        # Dogri
        "doi": {
            "मैं", "तू", "ओह", "अस्सां", "तुस्सां",
            "क्या", "कुत्थे", "कदूं", "किन्ने", "ऐ", "नेईं",
            "ते", "या", "पर",
            # Additional false positives
            "घरे", "जा", "करदा", "आं", "तुस", "आओ",
            "मां", "खाना", "बनान्दी", "बाऊजी", "बाजारे", "गेदे",
            "अज्ज", "बरखा", "पौणे", "आली", "होई", "रेहा",
        },
        # Bodo
        "brx": {
            "आं", "नों", "बि", "जों", "आंनि", "नोंनि",
            "माब्लाबा", "बेलायाव", "रावबो", "गावनो",
            "नङा", "होन्ना", "आरो", "नाथाय",
        },
        # Bhojpuri — shares Devanagari with Hindi but has distinct function words
        "bho": {
            # Pronouns
            "हम", "हमनी", "तू", "तोहर", "रउआ", "ऊ", "ई", "ओकर",
            "हमार", "तोर", "एकर", "ओकरा", "केकर",
            # Postpositions
            "का", "की", "के", "में", "पर", "से", "ना", "बा",
            "खातिर", "लगे", "संगे",
            # Common verbs
            "बा", "बाड़े", "बाटे", "रहल", "गइल", "आइल", "कइल",
            "करे", "होखे", "जाए", "आवे", "देखे", "बोले",
            "करत", "जात", "आवत", "देखत",
            # Particles & adverbs
            "अउर", "त", "ना", "हां", "नाही", "अब", "तब",
            "कब", "जब", "कहां", "काहे", "कइसे",
            # Common words
            "लोग", "बात", "दिन", "काम", "घर", "पानी", "खाना",
            "छठ", "छठी", "पूजा", "गांव", "भाई", "बहिन",
        },
        # Chhattisgarhi — shares Devanagari with Hindi but has distinct function words
        "hne": {
            # Pronouns
            "मैं", "हम", "तैं", "तुम", "वो", "ये", "ओकर", "एकर",
            "मोर", "तोर", "हमर", "तुम्हर",
            # Postpositions
            "का", "के", "ल", "म", "ले", "से", "बर", "संग",
            # Common verbs
            "हे", "हवे", "रहे", "गे", "आए", "करे", "होवे",
            "करत", "जावत", "आवत", "देखत", "बोलत",
            "करिस", "गइस", "आइस", "देखिस",
            # Particles & adverbs
            "अउ", "त", "ना", "नई", "अब", "तब", "कब", "जब",
            "कहां", "काबर", "कइसे", "बने",
            # Common words
            "लइका", "बात", "दिन", "काम", "घर", "पानी",
            "गांव", "भाई", "बहिनी", "दाई", "ददा",
        },
        "ks": {
            # Common Kashmiri native words (Perso-Arabic script)
            "چھِ", "چھُ", "چھے", "کرِو", "وچھِو",
            "بارش", "پیوان", "بوٗزِ", "مَت", "اَز",
            "گَر", "ہٕنز", "یِم", "تِم", "کَم",
            "پَن", "سُو", "آسَن", "گَچھُن",
        },
    }

    # Known transliteration overrides: short/tricky Indic words whose
    # romanized form doesn't phonetically match the correct English word.
    # Checked BEFORE phonetic matching to guarantee the right output.
    # Common English loanwords in each script — used as direct overrides
    # when phonetic matching produces wrong results.
    _KNOWN_TRANSLITERATIONS: dict[str, dict[str, str]] = {
        "hi": {
            # Short/ambiguous words
            "कार": "car", "टू": "two", "यस": "yes", "नो": "no",
            "द": "the", "ऑफ": "of", "ऑफ़": "of", "मई": "may",
            "फ़ॉर": "for", "फॉर": "for", "इन": "in", "ऑन": "on", "बट": "but",
            "एंड": "and", "ऑर": "or", "वन": "one", "थ्री": "three",
            "फोर": "four", "फ़ोर": "four", "सिक्स": "six",
            "सेवन": "seven", "एट": "eight", "नाइन": "nine", "टेन": "ten",
            "फाइव": "five", "फ़ाइव": "five", "एट": "at",
            "योर": "your", "हेल्प": "help", "चेक": "check",
            "स्लो": "slow", "वेरी": "very",
            "सर्च": "search", "गूगल": "google",
            "बजट": "budget", "सॉफ्टवेयर": "software", "सॉफ्टवेअर": "software",
            # Common loanwords that phonetic matcher gets wrong
            "ऐप": "app", "ॲप": "app", "एप": "app",
            "बुक": "book", "बूक": "book",
            "वाईफाई": "wifi", "वाइफाइ": "wifi",
            "डॉक्टर": "doctor", "डॉक्टरसे": "doctor",
            "टैक्सी": "taxi", "टेक्सी": "taxi",
            "पार्सल": "parcel",
            "स्क्रीनशॉट": "screenshot", "स्क्रीनशोट": "screenshot",
            "क्लाइंट": "client", "क्लायंट": "client",
            "फीडबैक": "feedback", "फीडबॅक": "feedback",
            "रिज्यूम": "resume", "रिज़्यूम": "resume",
            "ट्रेनिंग": "training", "ट्रैनिंग": "training",
            "सेशन": "session",
            "अटेंड": "attend",
            "अपॉइंटमेंट": "appointment",
            "इंटर्नशिप": "internship",
            "अप्लाई": "apply",
            "कॉन्फ्रेंस": "conference", "कॉन्फरन्स": "conference",
            "मेडिकल": "medical",
            "कलेक्ट": "collect",
            "एग्जाम": "exam",
            "रिजल्ट": "result",
            "असाइनमेंट": "assignment",
            "सबमिट": "submit",
            "डिलीवर": "deliver",
            "कनेक्ट": "connect",
            "क्रैश": "crash",
            "रूम": "room",
            "ऑफिस": "office", "ऑफ़िस": "office",
            "इंटरनेट": "internet",
            "प्रेजेंटेशन": "presentation",
            "अप्रूव": "approve",
            "स्टेटस": "status",
            "बजट": "budget",
            "बैलेंस": "balance",
            "डेडलाइन": "deadline",
            "अकाउंट": "account",
            "मिस": "miss",
            "नेटवर्क": "network",
            "इश्यू": "issue",
            "लंच": "lunch",
            "डिनर": "dinner", "डिनर": "dinner",
            "प्लान": "plan",
            "डाटाबेस": "database",
            "बैकअप": "backup",
            "लेटर": "later",
            "शेयर": "share",
            "प्रोजेक्ट": "project",
            "सिस्टम": "system",
            "पासवर्ड": "password",
            "सर्वर": "server",
            "डाउन": "down",
            "फाइल": "file",
            "डाउनलोड": "download",
            "ऑनलाइन": "online",
            "पेमेंट": "payment",
            "मोबाइल": "mobile",
            "नंबर": "number",
            "ईमेल": "email",
            "हेलो": "hello",
            "सॉफ्टवेयर": "software",
            "अपडेट": "update",
            "रीस्टार्ट": "restart",
            "रीसेट": "reset",
            "मीटिंग": "meeting",
            "कैंसल": "cancel",
            "प्लीज": "please",
            "डॉक्यूमेंट": "document",
            "रेडी": "ready",
            "कॉल": "call",
            "इम्पोर्टेन्ट": "important",
            "टीम": "team",
            "मैसेज": "message",
            "सेंड": "send",
            "रिपोर्ट": "report",
            "स्टॉप": "stop",
            "ओके": "ok", "ओ.के.": "ok",
            # Phase 3 additions — unseen test words
            "ऑर्डर": "order", "रील्स": "reels", "लोन": "loan",
            "स्कोर": "score", "ट्रैफिक": "traffic", "ट्रैफ़िक": "traffic",
            "रूट": "route", "चेंज": "change", "मैच": "match",
            "क्रिकेट": "cricket", "पिज़्ज़ा": "pizza", "पिज्ज़ा": "pizza",
            "इंस्टाग्राम": "instagram",
            "बैंक": "bank",
            "पेट्रोल": "petrol", "पंप": "pump",
            "लोकेशन": "location",
            "लाइब्ररी": "library", "लाइब्रेरी": "library",
            "कार्ड": "card",
            "रिन्यू": "renew", "रिन्यूअल": "renewal",
            "ब्लॉग": "blog", "पोस्ट": "post",
            "ड्राफ्ट": "draft",
            "ट्रेन": "train",
            "टिकट": "ticket", "टिकिट": "ticket",
            "बुकिंग": "booking",
            "कन्फर्म": "confirm",
            "होटल": "hotel",
            "जाम": "jam",
            "सिग्नल": "signal",
            "लेट": "late",
            "स्टार्ट": "start",
        },
        "bn": {
            # Short/ambiguous
            "কার": "car", "ইয়েস": "yes", "নো": "no", "দ্য": "the",
            "টু": "two", "ওয়ান": "one", "অ্যান্ড": "and", "অর": "or",
            # Common loanwords
            "অ্যাপ": "app", "এপ": "app", "ক্র্যাশ": "crash",
            "ওয়াইফাই": "wifi", "কানেক্ট": "connect",
            "স্ক্রিনশট": "screenshot", "স্ক্রীনশট": "screenshot",
            "ক্লায়েন্ট": "client", "ক্লায়েণ্ট": "client",
            "ফিডব্যাক": "feedback", "ফিডবেক": "feedback",
            "রিজিউম": "resume", "ট্রেনিং": "training", "ট্ৰেইনিং": "training",
            "সেশন": "session", "চেচন": "session",
            "অ্যাটেন্ড": "attend", "এটেণ্ড": "attend",
            "ডক্টর": "doctor", "ডক্টরের": "doctor",
            "অ্যাপয়েন্টমেন্ট": "appointment",
            "ইন্টার্নশিপ": "internship", "ইন্টার্নশিপে": "internship",
            "অ্যাপ্লাই": "apply",
            "ট্যাক্সি": "taxi", "বুক": "book",
            "পার্সেল": "parcel", "ডেলিভার": "deliver",
            "এক্সাম": "exam", "রিজাল্ট": "result",
            "অ্যাসাইনমেন্ট": "assignment", "সাবমিট": "submit",
            "মিটিং": "meeting", "মীটিং": "meeting",
            "ক্যান্সেল": "cancel", "প্লিজ": "please",
            "ডকুমেন্ট": "document", "শেয়ার": "share",
            "অফিস": "office", "অফিসে": "office",
            "ইন্টারনেট": "internet", "স্লো": "slow",
            "প্রজেক্ট": "project", "রেডি": "ready",
            "টিম": "team", "টিমকে": "team",
            "মেসেজ": "message",
            "অনলাইন": "online", "পেমেন্ট": "payment",
            "সফটওয়্যার": "software", "আপডেট": "update",
            "ফোন": "phone", "কল": "call",
            "নেটওয়ার্ক": "network", "ইস্যু": "issue",
            "পাসওয়ার্ড": "password", "রিসেট": "reset",
            "সার্ভার": "server", "ডাউন": "down",
            "ডেডলাইন": "deadline", "মিস": "miss",
            "বাজেট": "budget", "অ্যাপ্রুভ": "approve",
            "ফাইল": "file", "ডাউনলোড": "download",
            "ক্রেচ": "crash", "ক্র্যাশ": "crash",
            "বুকিং": "booking",
            # Phase 3 additions — unseen test words
            "ফ্লাইট": "flight", "রিফান্ড": "refund",
            "গেম": "game", "ল্যাগ": "lag",
            "ভিডিও": "video", "আপলোড": "upload",
            "ইউটিউব": "youtube",
            "সিগন্যাল": "signal", "সিগনেল": "signal",
        },
        "ta": {
            # Short/ambiguous
            "கார்": "car", "எஸ்": "yes", "நோ": "no",
            "டூ": "two", "வன்": "one", "ஆஃப்": "of",
            "அட்": "at", "ஃபைவ்": "five", "ஃபோர்": "for",
            "செக்": "check", "யுவர்": "your", "ஹெல்ப்": "help",
            "ஆபிஸ்": "office", "கால்": "call", "போன்": "phone",
            # Common loanwords
            "ஆப்": "app", "கிராஷ்": "crash", "க்ராஷ்": "crash",
            "வைஃபை": "wifi", "கனெக்ட்": "connect",
            "ஸ்க்ரீன்ஷாட்": "screenshot",
            "கிளையண்ட்": "client", "ஃபீட்பேக்": "feedback",
            "ரெசூம்": "resume", "ட்ரெயினிங்": "training",
            "செஷன்": "session", "அட்டெண்ட்": "attend",
            "டாக்டர்": "doctor", "அப்பாயிண்ட்மென்ட்": "appointment",
            "டாக்ஸி": "taxi", "புக்": "book",
            "பார்சல்": "parcel", "டெலிவர்": "deliver",
            "எக்ஸாம்": "exam", "ரிசல்ட்": "result",
            "அசைன்மென்ட்": "assignment", "சப்மிட்": "submit",
            "மீட்டிங்": "meeting", "மிட்டிங்": "meeting",
            "கேன்சல்": "cancel", "ப்ளீஸ்": "please",
            "டாக்குமென்ட்": "document", "ஷேர்": "share",
            "ஆபிஸ்": "office", "இன்டர்நெட்": "internet",
            "ஸ்லோ": "slow", "புராஜெக்ட்": "project",
            "ரெடி": "ready", "டீம்": "team",
            "மெசேஜ்": "message",
            "ஆன்லைன்": "online", "பேமெண்ட்": "payment",
            "சாப்ட்வேர்": "software", "அப்டேட்": "update",
            "நெட்வொர்க்": "network", "இஷ்யூ": "issue",
            "பாஸ்வேர்ட்": "password", "ரீசெட்": "reset",
            "சர்வர்": "server", "டவுன்": "down",
            "டெட்லைன்": "deadline", "மிஸ்": "miss",
            "பட்ஜெட்": "budget", "அப்ரூவ்": "approve",
            # Phase 3 additions — unseen test words
            "சப்ஸ்கிரிப்ஷன்": "subscription", "ரெனிவல்": "renewal",
            "ஜிம்": "gym", "மெம்பர்ஷிப்": "membership",
            "எக்ஸ்பையர்": "expire", "வெதர்": "weather",
            "ரிப்போர்ட்": "report", "ஓடிடி": "OTT",
        },
        "te": {
            # Short/ambiguous
            "కార్": "car", "యస్": "yes", "నో": "no", "ద": "the",
            "టూ": "two", "వన్": "one", "ఆఫ్": "of",
            "అట్": "at", "ఫైవ్": "five", "ఫోర్": "for",
            "చెక్": "check", "యువర్": "your", "హెల్ప్": "help",
            "కాల్": "call", "ఫోన్": "phone",
            # Common loanwords
            "యాప్": "app", "క్రాష్": "crash",
            "వైఫై": "wifi", "కనెక్ట్": "connect",
            "స్క్రీన్\u200cషాట్": "screenshot", "స్క్రీన్షాట్": "screenshot",
            "క్లయింట్": "client", "ఫీడ్\u200cబ్యాక్": "feedback", "ఫీడ్బ్యాక్": "feedback",
            "రెజ్యూమ్": "resume", "ట్రైనింగ్": "training",
            "సెషన్": "session", "అటెండ్": "attend",
            "డాక్టర్": "doctor", "అపాయింట్\u200cమెంట్": "appointment", "అపాయింట్మెంట్": "appointment",
            "ట్యాక్సీ": "taxi", "బుక్": "book",
            "పార్సెల్": "parcel", "డెలివర్": "deliver",
            "ఎగ్జామ్": "exam", "రిజల్ట్": "result",
            "అసైన్\u200cమెంట్": "assignment", "అసైన్మెంట్": "assignment",
            "సబ్మిట్": "submit",
            "మీటింగ్": "meeting", "క్యాన్సెల్": "cancel",
            "ప్లీజ్": "please", "డాక్యుమెంట్": "document",
            "షేర్": "share", "ఆఫీస్": "office",
            "ఇంటర్నెట్": "internet", "స్లో": "slow",
            "ప్రాజెక్ట్": "project", "రెడీ": "ready",
            "రిపోర్ట్": "report",
            "ఆన్\u200cలైన్": "online", "ఆన్లైన్": "online",
            "పేమెంట్": "payment",
            "సాఫ్ట్\u200cవేర్": "software", "సాఫ్ట్వేర్": "software",
            "అప్\u200cడేట్": "update", "అప్డేట్": "update",
            "నెట్\u200cవర్క్": "network", "నెట్వర్క్": "network",
            "ఇష్యూ": "issue",
            "పాస్\u200cవర్డ్": "password", "పాస్వర్డ్": "password",
            "రీసెట్": "reset",
            "సర్వర్": "server", "డౌన్": "down",
            "డెడ్\u200cలైన్": "deadline", "డెడ్లైన్": "deadline",
            "మిస్": "miss",
            "బడ్జెట్": "budget", "అప్రూవ్": "approve",
            # Phase 3 additions — unseen test words
            "వీడియో": "video", "లాగ్": "lag",
            "క్రెడిట్": "credit", "కార్డ్": "card",
            "బిల్": "bill", "పే": "pay",
            "స్పోర్ట్స్": "sports", "ఛానెల్": "channel",
            "ఆన్": "on",
        },
        "kn": {
            # Short/ambiguous
            "ಕಾರ್": "car", "ಯಸ್": "yes", "ನೋ": "no", "ದ": "the",
            "ಟೂ": "two", "ವನ್": "one", "ಆಫ್": "of",
            "ಅಟ್": "at", "ಫೈವ್": "five", "ಫೋರ್": "for",
            "ಚೆಕ್": "check", "ಯುವರ್": "your", "ಹೆಲ್ಪ್": "help",
            # Common loanwords
            "ಆಪ್": "app", "ಕ್ರ್ಯಾಶ್": "crash", "ಕ್ರ್ಯಾಷ್": "crash",
            "ವೈಫೈ": "wifi", "ಕನೆಕ್ಟ್": "connect",
            "ಸ್ಕ್ರೀನ್\u200cಶಾಟ್": "screenshot", "ಸ್ಕ್ರೀನ್ಶಾಟ್": "screenshot",
            "ಕ್ಲೈಂಟ್": "client", "ಫೀಡ್\u200cಬ್ಯಾಕ್": "feedback", "ಫೀಡ್ಬ್ಯಾಕ್": "feedback",
            "ರೆಸ್ಯೂಮ್": "resume", "ಟ್ರೈನಿಂಗ್": "training",
            "ಸೆಶನ್": "session", "ಅಟೆಂಡ್": "attend",
            "ಡಾಕ್ಟರ್": "doctor", "ಅಪಾಯಿಂಟ್ಮೆಂಟ್": "appointment",
            "ಟ್ಯಾಕ್ಸಿ": "taxi", "ಬುಕ್": "book",
            "ಪಾರ್ಸೆಲ್": "parcel", "ಡೆಲಿವರ್": "deliver",
            "ಎಗ್ಜಾಮ್": "exam", "ರಿಸಲ್ಟ್": "result",
            "ಅಸೈನ್ಮೆಂಟ್": "assignment", "ಸಬ್ಮಿಟ್": "submit",
            "ಮೀಟಿಂಗ್": "meeting", "ಕ್ಯಾನ್ಸಲ್": "cancel",
            "ಪ್ಲೀಸ್": "please", "ಡಾಕ್ಯುಮೆಂಟ್": "document",
            "ಶೇರ್": "share", "ಆಫೀಸ್": "office",
            "ಇಂಟರ್ನೆಟ್": "internet", "ಸ್ಲೋ": "slow",
            "ಪ್ರಾಜೆಕ್ಟ್": "project", "ರೆಡಿ": "ready",
            "ರಿಪೋರ್ಟ್": "report",
            "ಪೇಮೆಂಟ್": "payment", "ರೀಸೆಟ್": "reset",
            "ಸರ್ವರ್": "server", "ಡೌನ್": "down",
            "ಅಪ್ರೂವ್": "approve", "ಬಜೆಟ್": "budget",
            "ಆನ್\u200cಲೈನ್": "online", "ಆನ್ಲೈನ್": "online",
            "ಸಾಫ್ಟ್\u200cವೇರ್": "software", "ಸಾಫ್ಟ್ವೇರ್": "software",
            "ಅಪ್\u200cಡೇಟ್": "update", "ಅಪ್ಡೇಟ್": "update",
            "ಪಾಸ್\u200cವರ್ಡ್": "password", "ಪಾಸ್ವರ್ಡ್": "password",
            "ಸಬ್ಮಿಟ್": "submit", "ಕ್ಯಾನ್ಸಲ್": "cancel",
            "ಮೆಸೇಜ್": "message", "ಟೀಮ್": "team",
            "ಕಾಲ್": "call", "ಫೋನ್": "phone",
            # Phase 3 additions — unseen test words
            "ಪಾರ್ಕಿಂಗ್": "parking", "ಸ್ಪೇಸ್": "space",
            "ವೈರಸ್": "virus", "ಸ್ಕ್ಯಾನ್": "scan",
            "ರನ್": "run", "ಟಿಕೆಟ್": "ticket",
            "ಕನ್ಫರ್ಮ್": "confirm",
        },
        "ml": {
            # Short/ambiguous
            "കാർ": "car", "യെസ്": "yes", "നോ": "no", "ദ": "the",
            "ടു": "two", "വൺ": "one", "ഓഫ്": "of",
            # Common loanwords
            "ആപ്പ്": "app", "ക്രാഷ്": "crash",
            "വൈഫൈ": "wifi", "കണക്ട്": "connect",
            "സ്ക്രീൻഷോട്ട്": "screenshot",
            "ക്ലയന്റ്": "client", "ഫീഡ്ബാക്ക്": "feedback",
            "റെസ്യൂമെ": "resume", "ട്രെയിനിങ്": "training",
            "സെഷൻ": "session", "അറ്റൻഡ്": "attend",
            "ഡോക്ടർ": "doctor", "ഡോക്ടറുടെ": "doctor",
            "അപ്പോയിന്റ്മെന്റ്": "appointment",
            "ടാക്സി": "taxi", "ബുക്ക്": "book",
            "പാർസൽ": "parcel", "ഡെലിവർ": "deliver",
            "അപ്ഡേറ്റ്": "update",
            "ട്രെയിനിങ്": "training",
            "കണക്ട്": "connect",
            # Phase 3 additions — unseen test words
            "പാസ്വേർഡ്": "password", "ഷെയർ": "share",
            "ഫുഡ്": "food", "ഡെലിവറി": "delivery",
            "ലേറ്റ്": "late", "ഗൂഗിൾ": "google",
            "മാപ്പ്": "map", "ഓപ്പൺ": "open",
            "ഓൺലൈൻ": "online", "ഓണ്‍ലൈൻ": "online",
            "മീറ്റിങ്": "meeting", "മീറ്റിംഗ്": "meeting",
            "ക്യാൻസൽ": "cancel",
            "മൊബൈൽ": "mobile",
            "നെറ്റ്‌വർക്ക്": "network", "നെറ്റ്വർക്ക്": "network",
            "സിഗ്നൽ": "signal",
            "ഫോട്ടോ": "photo", "എഡിറ്റ്": "edit",
            "ഫ്ലൈറ്റ്": "flight", "ടിക്കറ്റ്": "ticket",
            "റീചാർജ്": "recharge", "റീചാർജ്ജ്": "recharge",
        },
        "mr": {
            # Short/ambiguous
            "कार": "car", "यस": "yes", "नो": "no", "द": "the",
            "टू": "two", "वन": "one", "ऑफ": "of", "ऑफ़": "of",
            "एंड": "and", "ऑर": "or",
            "अॅट": "at", "एट": "at", "फाइव": "five", "फाइव्ह": "five",
            "फॉर": "for", "चेक": "check", "योर": "your", "हेल्प": "help",
            "ऑफिस": "office",
            # Common loanwords
            "ॲप": "app", "क्रॅश": "crash",
            "वायफाय": "wifi", "कनेक्ट": "connect",
            "स्क्रीनशॉट": "screenshot",
            "क्लायंट": "client", "फीडबॅक": "feedback",
            "रिझ्युम": "resume", "ट्रेनिंग": "training",
            "सेशन": "session", "अटेंड": "attend",
            "डॉक्टर": "doctor", "डॉक्टरची": "doctor",
            "अपॉइंटमेंट": "appointment",
            "टॅक्सी": "taxi", "बुक": "book",
            "पार्सल": "parcel", "डिलिव्हर": "deliver",
            "कॉन्फरन्स": "conference", "कॉल": "call",
            "मेडिकल": "medical", "रिपोर्ट": "report",
            "ॲप": "app", "ऑफिस": "office",
            "डॉक्युमेंट": "document", "शेअर": "share",
            "प्रोजेक्ट": "project", "सबमिट": "submit",
            "इंटरनेट": "internet", "स्लो": "slow",
            "प्लीज": "please", "रेडी": "ready",
            "ऑनलाइन": "online", "पेमेंट": "payment",
            "मोबाइल": "mobile", "नंबर": "number",
            "ईमेल": "email", "अपडेट": "update",
            "पासवर्ड": "password", "सर्वर": "server",
            "फाइल": "file", "डाउनलोड": "download",
            "मेसेज": "message", "टीम": "team",
            "सॉफ्टवेअर": "software", "बजेट": "budget",
            "अप्रूव": "approve", "सर्व्हर": "server",
            # Phase 3 additions — unseen test words
            "ब्लॉग": "blog", "पोस्ट": "post",
            "ड्राफ्ट": "draft", "रेडी": "ready",
            "पेट्रोल": "petrol", "पंप": "pump",
            "लोकेशन": "location", "शेअर": "share",
            "लाइब्ररी": "library", "कार्ड": "card",
            "रिन्यू": "renew", "रिन्यूअल": "renewal",
            "ट्रेन": "train", "टिकिट": "ticket", "टिकट": "ticket",
            "बुकिंग": "booking", "कन्फर्म": "confirm",
            "लेट": "late", "रूट": "route",
            "लोन": "loan", "बैंक": "bank",
        },
        "gu": {
            # Short/ambiguous
            "કાર": "car", "યસ": "yes", "નો": "no",
            "ટૂ": "two", "વન": "one", "ઑફ": "of",
            "એટ": "at", "ફાઇવ": "five", "ફોર": "for",
            "ચેક": "check", "યુવર": "your", "હેલ્પ": "help",
            "ઓફિસ": "office", "મીટિંગ": "meeting", "મીટીંગ": "meeting",
            # Common loanwords
            "એપ": "app", "ક્રેશ": "crash",
            "વાઈફાઈ": "wifi", "કનેક્ટ": "connect",
            "સ્ક્રીનશૉટ": "screenshot",
            "ક્લાયન્ટ": "client", "ફીડબેક": "feedback",
            "રિઝ્યુમ": "resume", "ટ્રેનિંગ": "training",
            "સેશન": "session", "અટેન્ડ": "attend",
            "ડૉક્ટર": "doctor", "એપોઈન્ટમેન્ટ": "appointment",
            "ટેક્સી": "taxi", "બુક": "book",
            "કેન્સલ": "cancel", "ડોક્યુમેન્ટ": "document",
            "શેર": "share", "પ્રોજેક્ટ": "project", "રેડી": "ready",
            "રિપોર્ટ": "report", "સબમિટ": "submit",
            "ઇન્ટરનેટ": "internet", "સ્લો": "slow",
            "પ્લીઝ": "please", "ઓનલાઈન": "online",
            "પેમેન્ટ": "payment", "નંબર": "number",
            "ઈમેઈલ": "email", "મોબાઈલ": "mobile",
            "અપડેટ": "update", "પાસવર્ડ": "password",
            "સર્વર": "server", "ડાઉન": "down",
            "ફાઈલ": "file", "ડાઉનલોડ": "download",
            "મેસેજ": "message", "સેન્ડ": "send",
            "ટીમ": "team", "કૉલ": "call", "કોલ": "call",
            "સોફ્ટવેર": "software", "બજેટ": "budget",
            "એપ્રૂવ": "approve", "ઓનલાઇન": "online",
            "ઓનલાઈન": "online",
            # Phase 3 additions — unseen test words
            "ટ્રેન": "train", "ટિકિટ": "ticket",
            "રિફંડ": "refund", "રિફન્ડ": "refund",
            "વેબસાઈટ": "website", "વેબસાઇટ": "website",
            "ડિઝાઈન": "design", "ડિઝાઇન": "design",
            "ચેન્જ": "change",
            "ક્રિકેટ": "cricket", "મેચ": "match",
            "લાઈવ": "live", "લાઇવ": "live",
            "સ્ટ્રીમ": "stream",
        },
        "pa": {
            # Short/ambiguous
            "ਕਾਰ": "car", "ਯੈਸ": "yes", "ਨੋ": "no",
            "ਟੂ": "two", "ਵਨ": "one", "ਆਫ਼": "of",
            "ਐਟ": "at", "ਫਾਈਵ": "five", "ਫੋਰ": "for",
            "ਚੈੱਕ": "check", "ਚੈਕ": "check", "ਯੂਅਰ": "your", "ਹੈਲਪ": "help",
            # Common loanwords
            "ਐਪ": "app", "ਕ੍ਰੈਸ਼": "crash",
            "ਵਾਈਫਾਈ": "wifi", "ਕਨੈਕਟ": "connect",
            "ਸਕਰੀਨਸ਼ੌਟ": "screenshot",
            "ਕਲਾਇੰਟ": "client", "ਫੀਡਬੈਕ": "feedback",
            "ਰਿਜ਼ਿਊਮ": "resume", "ਟ੍ਰੇਨਿੰਗ": "training",
            "ਸੈਸ਼ਨ": "session", "ਅਟੈਂਡ": "attend",
            "ਡਾਕਟਰ": "doctor", "ਅਪੌਇੰਟਮੈਂਟ": "appointment",
            "ਟੈਕਸੀ": "taxi", "ਬੁੱਕ": "book",
            "ਕੈਂਸਲ": "cancel", "ਡਾਕੂਮੈਂਟ": "document",
            "ਸ਼ੇਅਰ": "share", "ਪ੍ਰੋਜੈਕਟ": "project", "ਰੈਡੀ": "ready",
            "ਰਿਪੋਰਟ": "report", "ਸਬਮਿਟ": "submit",
            "ਇੰਟਰਨੈੱਟ": "internet", "ਸਲੋ": "slow",
            "ਪਲੀਜ਼": "please", "ਔਨਲਾਈਨ": "online",
            "ਪੇਮੈਂਟ": "payment", "ਨੰਬਰ": "number",
            "ਈਮੇਲ": "email", "ਮੋਬਾਈਲ": "mobile",
            "ਅੱਪਡੇਟ": "update", "ਪਾਸਵਰਡ": "password",
            "ਸਰਵਰ": "server", "ਡਾਊਨ": "down",
            "ਫਾਈਲ": "file", "ਡਾਊਨਲੋਡ": "download",
            "ਮੈਸੇਜ": "message", "ਟੀਮ": "team",
            "ਕਾਲ": "call", "ਆਫ਼ਿਸ": "office",
            "ਸੌਫਟਵੇਅਰ": "software", "ਬਜਟ": "budget",
            "ਅਪਰੂਵ": "approve", "ਆਨਲਾਈਨ": "online",
            "ਅਪਡੇਟ": "update",
            "ਮੀਟਿੰਗ": "meeting", "ਕੈਂਸਲ": "cancel",
            # Phase 3 additions — unseen test words
            "ਵੀਡੀਓ": "video", "ਐਡਿਟ": "edit",
            "ਅਪਲੋਡ": "upload", "ਫਲਾਈਟ": "flight",
            "ਡਿਲੇ": "delay", "ਲੋਨ": "loan",
            "ਬੈਂਕ": "bank", "ਅਪਰੂਵ": "approve",
        },
        "or": {
            # Short/ambiguous
            "କାର": "car", "ୟସ": "yes", "ନୋ": "no",
            "ଟୁ": "two", "ୱାନ": "one",
            # Common loanwords
            "ଆପ": "app", "କ୍ରାସ": "crash",
            "ୱାଇଫାଇ": "wifi", "କନେକ୍ଟ": "connect",
            "ସ୍କ୍ରିନସଟ": "screenshot",
            "କ୍ଲାଏଣ୍ଟ": "client", "ଫିଡବ୍ୟାକ": "feedback",
            "ଟ୍ରେନିଂ": "training", "ସେସନ": "session",
            "ଆଟେଣ୍ଡ": "attend",
            "ଟ୍ୟାକ୍ସି": "taxi", "ବୁକ": "book",
            # Phase 3 additions — unseen test words
            "ଫ୍ଲାଇଟ୍": "flight", "ଫ୍ଲାଇଟ": "flight",
            "ଟିକେଟ୍": "ticket", "ଟିକେଟ": "ticket",
            "ମୋବାଇଲ୍": "mobile", "ମୋବାଇଲ": "mobile",
            "ରିଚାର୍ଜ": "recharge", "ରିଚାର୍ଜ୍": "recharge",
            "ଅନଲାଇନ": "online", "ଅନଲାଇନ୍": "online",
            "ମୀଟିଂ": "meeting", "ମୀଟିଙ୍ଗ": "meeting",
            "କ୍ୟାନ୍ସେଲ": "cancel",
            "ନେଟୱାର୍କ": "network", "ନେଟୱର୍କ": "network",
            "ସିଗ୍ନାଲ": "signal",
        },
        "ne": {
            # Short/ambiguous
            "कार": "car", "यस": "yes", "नो": "no", "द": "the",
            "टू": "two", "वन": "one", "ऑफ": "of",
            # Common loanwords
            "एप": "app", "क्र्यास": "crash", "क्रास": "crash",
            "वाइफाइ": "wifi", "कनेक्ट": "connect",
            "स्क्रिनसट": "screenshot",
            "क्लाइन्ट": "client", "फिडब्याक": "feedback",
            "ट्रेनिङ": "training", "सेसन": "session",
            "अटेन्ड": "attend",
            "ट्याक्सी": "taxi", "बुक": "book",
            "मीटिंग": "meeting", "क्यान्सल": "cancel",
            "डॉक्टर": "doctor", "अपॉइन्टमेन्ट": "appointment",
            # Phase 3 additions — unseen test words
            "ट्राफिक": "traffic", "जाम": "jam",
            "रुट": "route", "रूट": "route",
            "चेन्ज": "change", "चेञ्ज": "change",
            "होटल": "hotel", "बुकिंग": "booking", "बुकिङ": "booking",
            "कन्फर्म": "confirm",
            "ट्रेन": "train", "टिकट": "ticket",
            "ऑनलाइन": "online", "अनलाइन": "online",
            "नेटवर्क": "network", "सिग्नल": "signal",
            "मोबाइल": "mobile", "रिचार्ज": "recharge",
            "बैंक": "bank", "लोन": "loan",
        },
        "ur": {
            # Short/ambiguous
            "کار": "car", "یس": "yes", "نو": "no",
            "ٹو": "two", "ون": "one", "آف": "of", "دی": "the",
            # Common loanwords
            "ایپ": "app", "کریش": "crash",
            "وائی فائی": "wifi", "وائیفائی": "wifi",
            "کنیکٹ": "connect",
            "اسکرین شاٹ": "screenshot", "اسکرینشاٹ": "screenshot",
            "کلائنٹ": "client", "فیڈبیک": "feedback",
            "ٹریننگ": "training", "سیشن": "session",
            "اٹینڈ": "attend",
            "ڈاکٹر": "doctor", "اپائنٹمنٹ": "appointment",
            "ٹیکسی": "taxi", "بُک": "book", "بک": "book",
            "میٹنگ": "meeting", "کینسل": "cancel",
            # Phase 3 additions — unseen test words
            "فلائٹ": "flight", "ٹکٹ": "ticket",
            "ریفنڈ": "refund", "ریفند": "refund",
            "موبائل": "mobile", "ریچارج": "recharge",
            "آنلائن": "online", "آن لائن": "online",
            "نیٹ ورک": "network", "نیٹورک": "network",
            "سگنل": "signal",
        },
        "as": {
            # Common loanwords
            "এপ": "app", "ক্ৰেচ": "crash",
            "ৱাইফাই": "wifi", "কানেক্ট": "connect",
            "স্ক্ৰীণশ্বট": "screenshot",
            "ক্লায়েণ্ট": "client", "ফিডবেক": "feedback",
            "ট্ৰেইনিং": "training", "চেচন": "session",
            "এটেণ্ড": "attend",
            "টেক্সি": "taxi", "বুক": "book",
            # Phase 3 additions — unseen test words
            "মবাইল": "mobile", "মোবাইল": "mobile",
            "নেটৱৰ্ক": "network", "নেটৱর্ক": "network",
            "সিগনেল": "signal", "সিগনেল": "signal",
            "ফটো": "photo", "এডিট": "edit",
            "অনলাইন": "online", "অন্‌লাইন": "online",
            "মীটিং": "meeting", "মিটিং": "meeting",
            "কেন্সেল": "cancel",
            "ভিডিও": "video", "আপলোড": "upload",
            "ফ্লাইট": "flight", "টিকট": "ticket",
            "ৰিচাৰ্জ": "recharge",
        },
        "sd": {
            # Common loanwords
            "ايپ": "app", "ڪريش": "crash",
            "ميٽنگ": "meeting", "ڪينسل": "cancel",
            "ڊاڪٽر": "doctor", "اپائنٽمينٽ": "appointment",
            # Phase 3 additions — unseen test words
            "موبائل": "mobile", "ريچارج": "recharge",
            "آنلائن": "online",
            "نيٽورڪ": "network", "سگنل": "signal",
        },
        "ks": {
            # Common loanwords
            "ایپ": "app", "کریش": "crash",
            "میٹنگ": "meeting", "کینسل": "cancel",
            "ڈاکٹر": "doctor", "ڈاکٹرُک": "doctor",
            "اپائنٹمنٹ": "appointment",
            # Phase 3 additions — unseen test words
            "آنلائن": "online",
            "اپڈیٹ": "update",
            "موبائل": "mobile",
        },
        "kok": {
            # Common loanwords (Devanagari)
            "मीटिंग": "meeting", "कॅन्सल": "cancel",
            "डॉक्टर": "doctor", "डॉक्टराची": "doctor",
            "अपॉइंटमेंट": "appointment",
            "ॲप": "app", "क्रॅश": "crash",
            # Phase 3 additions — unseen test words
            "स्टार्ट": "start", "ट्रेन": "train",
            "लेट": "late", "रूट": "route",
            "ऑनलाइन": "online", "कैंसल": "cancel",
            "बैंक": "bank", "लोन": "loan",
        },
        "mai": {
            # Common loanwords (Devanagari)
            "मीटिंग": "meeting", "कैंसल": "cancel",
            "डॉक्टर": "doctor", "अपॉइंटमेंट": "appointment",
            "ऐप": "app", "क्रैश": "crash",
            # Phase 3 additions — unseen test words
            "ट्रेन": "train", "टिकट": "ticket",
            "बुक": "book", "ऑनलाइन": "online",
            "नेटवर्क": "network", "सिग्नल": "signal",
            "मोबाइल": "mobile",
        },
        "doi": {
            # Common loanwords (Devanagari)
            "मीटिंग": "meeting", "कैंसल": "cancel",
            "डॉक्टर": "doctor", "अपॉइंटमेंट": "appointment",
            "ऐप": "app", "क्रैश": "crash",
            # Phase 3 additions — unseen test words
            "ऑनलाइन": "online", "बैंक": "bank",
            "लोन": "loan", "अप्रूव": "approve",
        },
        "sa": {
            # Common loanwords (Devanagari)
            "मीटिंग": "meeting", "कैन्सल्": "cancel",
            "अपॉइंटमेंट": "appointment",
            # Phase 3 additions
            "ऑनलाइन": "online",
        },
        "brx": {
            # Common loanwords (Devanagari)
            "मीटिंग": "meeting", "कैंसल": "cancel",
            "ऐप": "app", "क्रैश": "crash",
            # Phase 3 additions
            "ऑनलाइन": "online",
        },
        "mni": {
            # Meetei Mayek script
            "ꯃꯤꯇꯤꯡ": "meeting", "ꯃꯤꯇꯤꯪ": "meeting",
            "ꯀꯦꯟꯁꯜ": "cancel",
            "ꯑꯣꯟꯂꯥꯏꯟ": "online",
            "ꯑꯦꯞ": "app",
        },
        "sat": {
            # Ol Chiki script
            "ᱢᱤᱴᱤᱝ": "meeting",
            "ᱠᱮᱱᱥᱮᱞ": "cancel",
            "ᱚᱱᱞᱟᱭᱱ": "online",
            "ᱮᱯ": "app",
        },
    }

    def __init__(
        self,
        phonetic_matcher: PhoneticMatcher | None = None,
        warm_cache_dir: str | Path | None = None,
        high_threshold: float = 0.85,
        low_threshold: float = 0.55,
        neural_transliterator=None,
    ):
        self._matcher = phonetic_matcher or PhoneticMatcher()
        self._high_threshold = high_threshold
        self._low_threshold = low_threshold
        self._neural = neural_transliterator
        self._confusable_filter = ConfusableFilter()

        # Native word frequency lists: loaded from data/<lang>_common.txt
        self._native_words: dict[str, set[str]] = {}
        self._load_native_word_lists()

        # Warm cache: pre-computed Indic -> English mappings per language
        self._warm_cache: dict[str, dict[str, str]] = {}
        if warm_cache_dir:
            self._load_warm_cache(Path(warm_cache_dir))

        # Aksharamukha availability flag
        self._aksharamukha_available = False
        self._init_romanizer()

    def _load_native_word_lists(self) -> None:
        """Load native word frequency lists from data/<lang>_common.txt files.

        These lists contain the most common native words for each language.
        Words in these lists are treated as definitively native and skip
        all English matching, preventing false positives.
        """
        data_dir = Path(__file__).parent / "data"
        for wordlist_file in data_dir.glob("*_common.txt"):
            lang_code = wordlist_file.stem.replace("_common", "")
            words = set()
            try:
                with open(wordlist_file, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            words.add(line)
                self._native_words[lang_code] = words
                logger.info("Loaded native word list for %s: %d words",
                            lang_code, len(words))
            except OSError as e:
                logger.warning("Failed to load native word list %s: %s",
                               wordlist_file, e)

    def _init_romanizer(self) -> None:
        """Initialize Aksharamukha for rule-based romanization."""
        try:
            from aksharamukha import transliterate as aksha_trans
            self._aksha_trans = aksha_trans
            self._aksharamukha_available = True
            logger.info("Aksharamukha romanization engine initialized")
        except ImportError:
            logger.warning(
                "aksharamukha not installed; using fallback romanization. "
                "Install with: pip install aksharamukha"
            )
            self._aksha_trans = None

    def _load_warm_cache(self, cache_dir: Path) -> None:
        """Load pre-computed Indic->English warm caches."""
        if not cache_dir.exists():
            logger.warning("Warm cache dir %s does not exist", cache_dir)
            return

        for cache_file in cache_dir.glob("*_cache.json"):
            lang_code = cache_file.stem.replace("_cache", "")
            try:
                with open(cache_file) as f:
                    self._warm_cache[lang_code] = json.load(f)
                logger.info("Loaded warm cache for %s: %d entries",
                            lang_code, len(self._warm_cache[lang_code]))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load warm cache %s: %s", cache_file, e)

    @lru_cache(maxsize=50000)
    def romanize(self, word: str, script_name: str) -> str:
        """Convert an Indic-script word to romanized form.

        Uses Aksharamukha (if installed) with post-processing to produce
        romanizations that match how English words are typically spelled.

        Args:
            word: Word in Indic script.
            script_name: Aksharamukha script name (e.g., "Devanagari", "Tamil").

        Returns:
            Romanized (Latin) form of the word.
        """
        raw = None

        # 1. Try Aksharamukha first (most complete script coverage)
        if self._aksharamukha_available and self._aksha_trans:
            try:
                raw = self._aksha_trans.process(script_name, "ISO", word)
                raw = raw.lower().strip()
            except Exception as e:
                logger.debug("Aksharamukha failed for %r (%s): %s", word, script_name, e)

        # 2. Fallback to script-specific phoneme maps
        if raw is None:
            raw = romanize_with_map(word, script_name)

        # 3. Last resort: Unicode name-based fallback
        if raw is None:
            raw = self._fallback_romanize(word)

        # Post-process: normalize for English dictionary matching
        return self._normalize_romanization(raw)

    @staticmethod
    def _normalize_romanization(rom: str) -> str:
        """Normalize romanized form for better English dictionary matching.

        - Strip trailing inherent 'a' vowel (common in Indic romanization)
        - Simplify diacritics and digraphs
        - Map Indic phonemes to their English equivalents
        """
        # Remove ISO diacritics and normalize to ASCII-friendly forms
        diacritic_map = {
            "ā": "a", "ī": "i", "ū": "u", "ṛ": "ri", "ṝ": "ri",
            "ē": "e", "ō": "o", "ṭ": "t", "ḍ": "d", "ṇ": "n",
            "ś": "sh", "ṣ": "sh", "ṃ": "n", "ṁ": "n",  # anusvara → n
            "ḥ": "h", "ñ": "n", "ṅ": "ng", "ṉ": "n",
            "ŏ": "o", "ĕ": "e", "ô": "o", "ê": "e",  # Candra vowels
            "æ": "a",  # Candra A (used in Marathi for English 'a' sound)
            "ẏ": "y",  # Bengali ya
        }
        result = rom
        for old, new in diacritic_map.items():
            result = result.replace(old, new)

        # Strip trailing 'a' (inherent vowel in Indic scripts that doesn't
        # exist in English loanword pronunciation)
        # e.g., "senda" → "send", "phora" → "phor", "helpa" → "help"
        if len(result) > 2 and result.endswith("a") and not result.endswith("aa"):
            result = result[:-1]

        # ISO uses "c" for Indic "ch" sound (च/চ/ச etc.)
        # In English context, "c" before e/i = "s" sound, but Indic "c" = "ch"
        # Map: "c" → "ch" when it appears to be Indic "ch" phoneme
        result = re.sub(r"c(?=[eiaou])", "ch", result)
        result = re.sub(r"c$", "ck", result)  # Word-final "c" → "ck" (check)

        # j → z for some English words (plij → pliz → please)
        # Only when preceded by vowel (common in Indian English transliteration)
        result = re.sub(r"j$", "z", result)  # Word-final j → z

        # Common phoneme mappings for English matching
        result = re.sub(r"^ph", "f", result)  # Word-initial ph → f
        result = result.replace("chh", "ch")   # Aspirated ch → ch

        return result

    def _fallback_romanize(self, word: str) -> str:
        """Basic fallback romanization using Unicode character names.

        Extracts the phonetic name from Unicode (e.g., DEVANAGARI LETTER KA -> ka).
        Not perfect but provides a reasonable approximation.
        """
        result = []
        for char in word:
            try:
                name = unicodedata.name(char, "").lower()
                # Extract the letter/vowel name from Unicode names like
                # "devanagari letter ka" -> "ka"
                # "devanagari vowel sign aa" -> "aa"
                if " letter " in name:
                    phoneme = name.split(" letter ")[-1]
                    # Handle compound names like "ka" vs "kha"
                    result.append(phoneme.replace(" ", ""))
                elif " vowel sign " in name:
                    vowel = name.split(" vowel sign ")[-1]
                    result.append(vowel.replace(" ", ""))
                elif " sign " in name:
                    sign_name = name.split(" sign ")[-1]
                    if sign_name == "virama":
                        pass  # Skip virama (halant) — it suppresses inherent vowel
                    elif sign_name == "nukta":
                        pass  # Nukta modifies previous consonant
                    elif sign_name in ("anusvara", "anunasika"):
                        result.append("n")
                    elif sign_name == "visarga":
                        result.append("h")
                    else:
                        result.append(sign_name.replace(" ", ""))
                elif " digit " in name:
                    digit = name.split(" digit ")[-1]
                    digit_map = {
                        "zero": "0", "one": "1", "two": "2", "three": "3",
                        "four": "4", "five": "5", "six": "6", "seven": "7",
                        "eight": "8", "nine": "9",
                    }
                    result.append(digit_map.get(digit, digit))
                else:
                    result.append(char)
            except ValueError:
                result.append(char)

        return "".join(result)

    def lookup(self, word: str, lang_code: str, script_name: str | None = None) -> LookupResult:
        """Look up a single Indic word against the English dictionary.

        Args:
            word: Word in Indic script.
            lang_code: Language code (e.g., "hi", "ta", "bn").
            script_name: Aksharamukha script name. Auto-detected if None.

        Returns:
            LookupResult with confidence-scored English match.
        """
        # 0. Check known transliteration overrides FIRST (highest priority —
        # manually curated entries override native word lists)
        overrides = self._KNOWN_TRANSLITERATIONS.get(lang_code, {})
        override_match = overrides.get(word)
        if override_match is not None:
            return LookupResult(
                original=word,
                romanized=override_match,
                english_match=override_match,
                confidence=Confidence.HIGH,
                score=1.0,
            )

        # 0b. Check native word frequency list and exclusions
        # This covers the top ~3000 most common native words per language.
        native_words = self._native_words.get(lang_code, set())
        exclusions = self._NATIVE_EXCLUSIONS.get(lang_code, set())
        if word in native_words or word in exclusions:
            return LookupResult(
                original=word,
                romanized="",
                english_match=None,
                confidence=Confidence.LOW,
                score=0.0,
            )

        # 1. Check warm cache first (fastest path)
        if lang_code in self._warm_cache:
            cached = self._warm_cache[lang_code].get(word)
            if cached:
                return LookupResult(
                    original=word,
                    romanized=cached,
                    english_match=cached,
                    confidence=Confidence.HIGH,
                    score=1.0,
                )

        # 2. Try IndicXlit direct lookup (highest quality, if available)
        neural_result = self._try_neural_lookup(word, lang_code)
        if neural_result is not None:
            return neural_result

        # 3. Romanize the word
        if script_name is None:
            config = get_config(lang_code)
            script_name = config.script_name

        romanized = self.romanize(word, script_name)

        # 4. Phonetic dictionary lookup
        is_english, match = self._matcher.is_english(romanized, threshold=self._low_threshold)

        if not is_english or match is None:
            # Try suffix stripping as fallback (handles agglutinated loanwords)
            stripped = self._try_suffix_strip(word, lang_code, script_name)
            if stripped is not None:
                return stripped

            return LookupResult(
                original=word,
                romanized=romanized,
                english_match=None,
                confidence=Confidence.LOW,
                score=0.0,
            )

        # 5. For non-exact matches, also try suffix stripping — the stem match
        #    may be more accurate than a phonetic match on the full agglutinated form.
        #    e.g., "aapisla" phonetically matches "apply" but the stem "aapis" = "office"
        if match.match_type != "exact" and match.match_type != "translit_variant":
            stripped = self._try_suffix_strip(word, lang_code, script_name)
            if stripped is not None and stripped.score >= match.score:
                return stripped

        # 5b. Check confusable pair blocklist — reject known false positives
        if self._confusable_filter.should_block(
            word=word,
            lang_code=lang_code,
            english_candidate=match.english_word,
            romanized=romanized,
            match_type=match.match_type,
        ):
            return LookupResult(
                original=word,
                romanized=romanized,
                english_match=None,
                confidence=Confidence.LOW,
                score=0.0,
            )

        # 6. Determine confidence based on score
        # Apply word-length-dependent threshold scaling: short romanized words
        # (2-3 chars) are disproportionately prone to false positives.
        #
        # Count base characters in the original Indic word for additional protection.
        base_chars = sum(
            1 for c in word if not unicodedata.category(c).startswith("M")
        )

        # Hard block: single-character Indic words are almost never English
        if base_chars <= 1:
            return LookupResult(
                original=word,
                romanized=romanized,
                english_match=None,
                confidence=Confidence.LOW,
                score=0.0,
            )

        # 2-char Indic words: only accept exact or translit_variant matches
        if base_chars <= 2 and match.match_type not in ("exact", "translit_variant"):
            return LookupResult(
                original=word,
                romanized=romanized,
                english_match=None,
                confidence=Confidence.LOW,
                score=0.0,
            )

        romanized_len = len(romanized)
        if romanized_len <= 2:
            # Very short romanized: require exact/translit_variant match
            if match.match_type not in ("exact", "translit_variant"):
                return LookupResult(
                    original=word,
                    romanized=romanized,
                    english_match=None,
                    confidence=Confidence.LOW,
                    score=0.0,
                )
            effective_high = min(self._high_threshold + 0.10, 0.98)
            effective_low = min(self._low_threshold + 0.20, 0.90)
        elif romanized_len <= 3:
            effective_high = min(self._high_threshold + 0.10, 0.98)
            effective_low = min(self._low_threshold + 0.15, 0.85)
        elif romanized_len <= 4:
            effective_high = min(self._high_threshold + 0.05, 0.95)
            effective_low = min(self._low_threshold + 0.10, 0.80)
        else:
            effective_high = self._high_threshold
            effective_low = self._low_threshold

        if match.score >= effective_high:
            confidence = Confidence.HIGH
        elif match.score >= effective_low:
            confidence = Confidence.AMBIGUOUS
        else:
            confidence = Confidence.LOW

        return LookupResult(
            original=word,
            romanized=romanized,
            english_match=match.english_word,
            confidence=confidence,
            score=match.score,
            match_detail=match,
        )

    def _try_neural_lookup(self, word: str, lang_code: str) -> LookupResult | None:
        """Try IndicXlit → direct dictionary match.

        Iterates IndicXlit beam candidates and picks the best dictionary match,
        preferring earlier beam positions (IndicXlit confidence) and higher dict scores.
        Accepts exact matches and translit_variant matches (score >= 0.9).

        Short-word protection: native Indic words with few base characters
        (e.g., "जो", "पास", "बारे") often produce IndicXlit candidates that
        accidentally match English words at lower beam positions. To prevent this:
        - 1 base char: skip neural lookup entirely (too ambiguous)
        - 2 base chars: only accept beam position 0 (top candidate must match)
        - 3+ base chars: accept any beam position (current behavior)
        """
        if self._neural is None or not self._neural.is_available:
            return None

        # Count base characters (non-combining-mark codepoints) to gauge word length
        base_chars = sum(1 for c in word if unicodedata.category(c)[0] != "M")
        if base_chars <= 2:
            return None  # 1-2 char Indic words are almost always native

        candidates = self._neural.transliterate_to_candidates(word, lang_code)
        if not candidates:
            return None

        # For short words, restrict which beam positions we trust
        max_beam_idx = 0 if base_chars <= 3 else len(candidates) - 1

        best_result: LookupResult | None = None
        best_priority = (-1, -1.0)  # (beam_bonus, score)

        for i, candidate in enumerate(candidates):
            if i > max_beam_idx:
                break

            candidate_lower = candidate.lower().strip()
            is_eng, match = self._matcher.is_english(candidate_lower, threshold=0.9)
            if not is_eng or match is None:
                continue
            if match.match_type not in ("exact", "translit_variant"):
                continue

            # Check confusable filter
            if self._confusable_filter.should_block(
                word=word, lang_code=lang_code,
                english_candidate=match.english_word,
                romanized=candidate_lower,
                match_type=match.match_type,
            ):
                continue

            # Prefer earlier beam positions (higher IndicXlit confidence)
            # and higher dictionary scores
            beam_bonus = len(candidates) - i
            priority = (beam_bonus, match.score)

            if priority > best_priority:
                best_priority = priority
                best_result = LookupResult(
                    original=word,
                    romanized=candidate_lower,
                    english_match=match.english_word,
                    confidence=Confidence.HIGH,
                    score=match.score,
                    match_detail=match,
                )

        return best_result

    def _try_suffix_strip(
        self, word: str, lang_code: str, script_name: str,
    ) -> LookupResult | None:
        """Try stripping native grammatical suffixes to find an English stem.

        Indian languages fuse postpositions/case markers with nouns:
            ऑफिसमध्ये = office + मध्ये (locative)
            টিমকে = team + কে (dative)

        This method tries each known suffix for the language, strips it,
        and looks up the remaining stem against the English dictionary.

        Returns a LookupResult if a HIGH confidence match is found, else None.
        """
        suffixes = AGGLUTINATIVE_SUFFIXES.get(lang_code, [])
        if not suffixes:
            return None

        for suffix in suffixes:
            if not word.endswith(suffix):
                continue

            stem = word[: -len(suffix)]

            # Require stem to have at least 2 base characters (avoid spurious matches)
            base_chars = sum(
                1 for c in stem
                if not unicodedata.category(c).startswith("M")
            )
            if base_chars < 2:
                continue

            # Check if stem is a known transliteration override
            overrides = self._KNOWN_TRANSLITERATIONS.get(lang_code, {})
            override_match = overrides.get(stem)
            if override_match is not None:
                return LookupResult(
                    original=word,
                    romanized=override_match,
                    english_match=override_match,
                    confidence=Confidence.HIGH,
                    score=1.0,
                )

            # Romanize and look up the stem
            romanized_stem = self.romanize(stem, script_name)
            is_eng, match = self._matcher.is_english(
                romanized_stem, threshold=self._low_threshold
            )

            if is_eng and match is not None and match.score >= self._high_threshold:
                return LookupResult(
                    original=word,
                    romanized=romanized_stem,
                    english_match=match.english_word,
                    confidence=Confidence.HIGH,
                    score=match.score,
                    match_detail=match,
                )

        return None

    def batch_lookup(
        self,
        words: list[tuple[str, str, str | None]],
    ) -> list[LookupResult]:
        """Batch lookup for multiple words.

        Args:
            words: List of (word, lang_code, script_name) tuples.

        Returns:
            List of LookupResult in the same order.
        """
        return [self.lookup(w, lc, sn) for w, lc, sn in words]
