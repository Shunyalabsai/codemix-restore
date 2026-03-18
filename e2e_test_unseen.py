#!/usr/bin/env python3
"""Unseen sentence test — entirely new sentences the system has never encountered.

Tests all 22 scheduled Indian languages with fresh code-mixed sentences
covering diverse domains: social media, food delivery, gaming, travel,
banking, weather, sports, entertainment, agriculture, and more.

Every sentence here is NEW — not used in any prior test file.
"""

from codemix_restore import ScriptRestorer

restorer = ScriptRestorer()

# ──────────────────────────────────────────────────────────────────────────────
# Test cases: (lang_code, input_sentence, expected_english_words, description)
#
# expected_english_words: list of English words that MUST appear in the output
#   Use None for "native-only" sentences where NO English should appear
# ──────────────────────────────────────────────────────────────────────────────

TESTS = [
    # ═══════════════════════════════════════════════════════════════════════════
    # HINDI (hi) — Devanagari
    # ═══════════════════════════════════════════════════════════════════════════
    ("hi", "पिज़्ज़ा ऑर्डर कर दो ऑनलाइन", ["order", "online"], "food delivery"),
    ("hi", "इंस्टाग्राम पर रील्स बनाओ", ["reels"], "social media"),
    ("hi", "बैंक से लोन का स्टेटस पूछो", ["loan", "status"], "banking"),
    ("hi", "क्रिकेट मैच का स्कोर क्या है", ["match", "score"], "sports"),
    ("hi", "ट्रैफिक बहुत है रूट चेंज करो", ["traffic", "route", "change"], "navigation"),
    # Native-only (no English expected)
    ("hi", "आज बारिश हो रही है बाहर मत जाओ", None, "native weather"),
    ("hi", "दादी ने खाना बनाया बहुत स्वादिष्ट है", None, "native daily life"),

    # ═══════════════════════════════════════════════════════════════════════════
    # BENGALI (bn) — Bengali script
    # ═══════════════════════════════════════════════════════════════════════════
    ("bn", "ফ্লাইট ক্যান্সেল হয়ে গেছে রিফান্ড চাই", ["flight", "cancel", "refund"], "travel"),
    ("bn", "গেম ল্যাগ করছে সার্ভার ডাউন", ["game", "server", "down"], "gaming"),
    ("bn", "ইউটিউব ভিডিও আপলোড করো", ["video", "upload"], "social media"),
    # Native-only
    ("bn", "আজ আকাশে মেঘ অনেক সুন্দর দেখাচ্ছে", None, "native weather"),
    ("bn", "মা ভাত রান্না করছেন রান্নাঘরে", None, "native daily life"),

    # ═══════════════════════════════════════════════════════════════════════════
    # TAMIL (ta) — Tamil script
    # ═══════════════════════════════════════════════════════════════════════════
    ("ta", "ஓடிடி சப்ஸ்கிரிப்ஷன் ரெனிவல் பண்ணுங்க", ["subscription", "renewal"], "entertainment"),
    ("ta", "ஜிம் மெம்பர்ஷிப் எக்ஸ்பையர் ஆகிடுச்சு", ["gym", "membership", "expire"], "fitness"),
    ("ta", "வெதர் ரிப்போர்ட் சொல்லுங்க", ["weather", "report"], "weather"),
    # Native-only
    ("ta", "அம்மா கோவிலுக்கு போயிருக்காங்க", None, "native daily life"),
    ("ta", "மழை பெய்யுது குடை எடுத்துக்கோ", None, "native weather"),

    # ═══════════════════════════════════════════════════════════════════════════
    # TELUGU (te) — Telugu script
    # ═══════════════════════════════════════════════════════════════════════════
    ("te", "వీడియో కాల్ లో లాగ్ వస్తోంది", ["video", "call"], "tech"),
    ("te", "క్రెడిట్ కార్డ్ బిల్ పే చేయండి", ["credit", "card", "bill"], "banking"),
    ("te", "స్పోర్ట్స్ ఛానెల్ ఆన్ చేయి", ["sports", "channel"], "entertainment"),
    # Native-only
    ("te", "నాన్న పొలంలో పని చేస్తున్నారు", None, "native agriculture"),
    ("te", "అమ్మ వంటగదిలో ఉంది భోజనం చేద్దాం", None, "native daily life"),

    # ═══════════════════════════════════════════════════════════════════════════
    # KANNADA (kn) — Kannada script
    # ═══════════════════════════════════════════════════════════════════════════
    ("kn", "ಪಾರ್ಕಿಂಗ್ ಸ್ಪೇಸ್ ಸಿಗ್ತಾ ಇಲ್ಲ", ["parking", "space"], "travel"),
    ("kn", "ವೈರಸ್ ಸ್ಕ್ಯಾನ್ ರನ್ ಮಾಡಿ", ["virus", "scan", "run"], "tech"),
    ("kn", "ಟಿಕೆಟ್ ಬುಕ್ ಆಯ್ತು ಕನ್ಫರ್ಮ್ ಆಗಿದೆ", ["ticket", "book", "confirm"], "travel"),
    # Native-only
    ("kn", "ಅಜ್ಜಿ ಮನೆಯಲ್ಲಿ ಹೂವಿನ ತೋಟ ಚೆನ್ನಾಗಿದೆ", None, "native daily life"),

    # ═══════════════════════════════════════════════════════════════════════════
    # MARATHI (mr) — Devanagari
    # ═══════════════════════════════════════════════════════════════════════════
    ("mr", "ब्लॉग पोस्ट ड्राफ्ट रेडी आहे", ["blog", "post", "draft", "ready"], "content creation"),
    ("mr", "पेट्रोल पंप लोकेशन शेअर कर", ["petrol", "pump", "location", "share"], "navigation"),
    ("mr", "लाइब्ररी कार्ड रिन्यू करा", ["library", "card", "renew"], "daily life"),
    # Native-only
    ("mr", "शेतात आज कापूस वेचला चांगला भाव मिळाला", None, "native agriculture"),

    # ═══════════════════════════════════════════════════════════════════════════
    # GUJARATI (gu) — Gujarati script
    # ═══════════════════════════════════════════════════════════════════════════
    ("gu", "ટ્રેન ટિકિટ કેન્સલ કરો રિફંડ જોઈએ", ["train", "ticket", "cancel", "refund"], "travel"),
    ("gu", "વેબસાઈટ ડિઝાઈન ચેન્જ કરવી છે", ["website", "design", "change"], "tech"),
    ("gu", "ક્રિકેટ મેચ લાઈવ સ્ટ્રીમ ચાલુ કરો", ["cricket", "match", "live", "stream"], "sports"),
    # Native-only
    ("gu", "દાદા ખેતરમાં કામ કરે છે ખૂબ મહેનતુ છે", None, "native agriculture"),

    # ═══════════════════════════════════════════════════════════════════════════
    # PUNJABI (pa) — Gurmukhi
    # ═══════════════════════════════════════════════════════════════════════════
    ("pa", "ਵੀਡੀਓ ਐਡਿਟ ਕਰਕੇ ਅਪਲੋਡ ਕਰੋ", ["video", "edit", "upload"], "content creation"),
    ("pa", "ਫਲਾਈਟ ਡਿਲੇ ਹੋ ਗਈ ਹੈ", ["flight", "delay"], "travel"),
    ("pa", "ਬੈਂਕ ਲੋਨ ਅਪਰੂਵ ਹੋ ਗਿਆ", ["bank", "loan", "approve"], "banking"),
    # Native-only
    ("pa", "ਬੇਬੇ ਨੇ ਸਰੋਂ ਦਾ ਸਾਗ ਬਣਾਇਆ ਬਹੁਤ ਸੋਹਣਾ", None, "native food"),

    # ═══════════════════════════════════════════════════════════════════════════
    # MALAYALAM (ml) — Malayalam script
    # ═══════════════════════════════════════════════════════════════════════════
    ("ml", "വൈഫൈ പാസ്വേർഡ് ഷെയർ ചെയ്യൂ", ["wifi", "password", "share"], "tech"),
    ("ml", "ഫുഡ് ഡെലിവറി ലേറ്റ് ആണ്", ["food", "delivery", "late"], "food delivery"),
    ("ml", "ഗൂഗിൾ മാപ്പ് ഓപ്പൺ ചെയ്യൂ", ["google", "map", "open"], "navigation"),
    # Native-only
    ("ml", "അച്ഛൻ വയലിൽ നെല്ല് കൊയ്യുകയാണ്", None, "native agriculture"),

    # ═══════════════════════════════════════════════════════════════════════════
    # ODIA (or) — Odia script
    # ═══════════════════════════════════════════════════════════════════════════
    ("or", "ଫ୍ଲାଇଟ୍ ଟିକେଟ୍ ବୁକ କରନ୍ତୁ", ["flight", "ticket", "book"], "travel"),
    ("or", "ମୋବାଇଲ୍ ରିଚାର୍ଜ କରିବା ଦରକାର", ["mobile", "recharge"], "telecom"),
    # Native-only
    ("or", "ବାପା ଖେତରେ ଧାନ ବୁଣୁଛନ୍ତି ଆଜି", None, "native agriculture"),

    # ═══════════════════════════════════════════════════════════════════════════
    # ASSAMESE (as) — Bengali script
    # ═══════════════════════════════════════════════════════════════════════════
    ("as", "মবাইল নেটৱৰ্ক সিগনেল দুৰ্বল", ["mobile", "network", "signal"], "telecom"),
    ("as", "ফটো এডিট কৰি পঠিয়াওঁক", ["photo", "edit"], "social media"),
    # Native-only
    ("as", "মাক ৰান্ধনী ঘৰত ভাত ৰান্ধিছে", None, "native daily life"),

    # ═══════════════════════════════════════════════════════════════════════════
    # NEPALI (ne) — Devanagari
    # ═══════════════════════════════════════════════════════════════════════════
    ("ne", "ट्राफिक जाम भयो रुट चेन्ज गर", ["traffic", "jam", "route", "change"], "navigation"),
    ("ne", "होटल बुकिंग कन्फर्म गर", ["hotel", "booking", "confirm"], "travel"),
    # Native-only
    ("ne", "आमाले भात पकाउनुभयो स्वादिष्ट छ", None, "native daily life"),

    # ═══════════════════════════════════════════════════════════════════════════
    # URDU (ur) — Perso-Arabic
    # ═══════════════════════════════════════════════════════════════════════════
    ("ur", "فلائٹ ٹکٹ کینسل کرو ریفنڈ چاہیے", ["flight", "ticket", "cancel", "refund"], "travel"),
    ("ur", "موبائل ریچارج کرنا ہے", ["mobile", "recharge"], "telecom"),
    # Native-only
    ("ur", "ابو کھانا پکا رہے ہیں باورچی خانے میں", None, "native daily life"),

    # ═══════════════════════════════════════════════════════════════════════════
    # MAITHILI (mai) — Devanagari
    # ═══════════════════════════════════════════════════════════════════════════
    ("mai", "ट्रेन टिकट बुक करू ऑनलाइन", ["train", "ticket", "book", "online"], "travel"),
    ("mai", "नेटवर्क सिग्नल नहिं अबैत छै", ["network", "signal"], "telecom"),
    # Native-only
    ("mai", "माय भात रान्हि रहल छथि आइ", None, "native daily life"),

    # ═══════════════════════════════════════════════════════════════════════════
    # KONKANI (kok) — Devanagari
    # ═══════════════════════════════════════════════════════════════════════════
    ("kok", "मीटिंग स्टार्ट जाल्या वेळार या", ["meeting", "start"], "workplace"),
    ("kok", "ट्रेन लेट जाल्या रूट बदला", ["train", "late", "route"], "travel"),
    # Native-only
    ("kok", "आवय जेवण करता रांदपाच्या कुडींत", None, "native daily life"),

    # ═══════════════════════════════════════════════════════════════════════════
    # DOGRI (doi) — Devanagari
    # ═══════════════════════════════════════════════════════════════════════════
    ("doi", "मीटिंग कैंसल होई गई ऑनलाइन करो", ["meeting", "cancel", "online"], "workplace"),
    ("doi", "बैंक लोन अप्रूव होई गया", ["bank", "loan"], "banking"),
    # Native-only
    ("doi", "अम्मा ने रोटी बनाई बहुत सोहणी है", None, "native daily life"),

    # ═══════════════════════════════════════════════════════════════════════════
    # SINDHI (sd) — Perso-Arabic
    # ═══════════════════════════════════════════════════════════════════════════
    ("sd", "ميٽنگ ڪينسل ٿي وئي آهي", ["meeting", "cancel"], "workplace"),
    ("sd", "موبائل ريچارج ڪيو", ["mobile", "recharge"], "telecom"),
    # Native-only
    ("sd", "اڄ مينهن پئجي رهيو آهي ٻاهر نه وڃو", None, "native weather"),

    # ═══════════════════════════════════════════════════════════════════════════
    # KASHMIRI (ks) — Perso-Arabic
    # ═══════════════════════════════════════════════════════════════════════════
    ("ks", "میٹنگ کینسل چھِ آن لائن کرِو", ["meeting", "cancel", "online"], "workplace"),
    ("ks", "ایپ اپ ڈیٹ کرِو", ["app", "update"], "tech"),
    # Native-only
    ("ks", "اَز بارش چھِ پیوان بوٗزِ مَت وچھِو", None, "native weather"),

    # ═══════════════════════════════════════════════════════════════════════════
    # SANSKRIT (sa) — Devanagari
    # ═══════════════════════════════════════════════════════════════════════════
    ("sa", "मीटिंग कैन्सल् अस्ति ऑनलाइन कुरुत", ["meeting", "online"], "workplace"),
    # Native-only
    ("sa", "अद्य वर्षा भवति गृहे तिष्ठतु", None, "native weather"),

    # ═══════════════════════════════════════════════════════════════════════════
    # BODO (brx) — Devanagari
    # ═══════════════════════════════════════════════════════════════════════════
    ("brx", "मीटिंग कैंसल जादों ऑनलाइन खालाम", ["meeting", "cancel", "online"], "workplace"),
    # Native-only
    ("brx", "दानि सान्नाय जानो नोंथांनि बिफां", None, "native daily life"),

    # ═══════════════════════════════════════════════════════════════════════════
    # MANIPURI (mni) — MeeteiMayek
    # ═══════════════════════════════════════════════════════════════════════════
    # (MeeteiMayek phoneme map is basic — test conservatively)
    ("mni", "ꯃꯤꯇꯤꯡ ꯀꯦꯟꯁꯜ ꯑꯣꯏ", ["meeting", "cancel"], "workplace"),
    # Native-only
    ("mni", "ꯏꯃꯥ ꯆꯥꯛ ꯊꯣꯡꯕ ꯂꯩꯔꯤ", None, "native daily life"),

    # ═══════════════════════════════════════════════════════════════════════════
    # SANTALI (sat) — OlChiki
    # ═══════════════════════════════════════════════════════════════════════════
    # (OlChiki script — very limited support, test basic)
    ("sat", "ᱢᱤᱴᱤᱝ ᱠᱮᱱᱥᱮᱞ ᱦᱩᱭ ᱮᱱᱟ", ["meeting", "cancel"], "workplace"),
    # Native-only
    ("sat", "ᱟᱡ ᱫᱟᱨᱮ ᱵᱟᱝ ᱵᱟᱝ ᱛᱟᱸᱜᱤ ᱦᱩᱭ ᱮᱱᱟ", None, "native weather"),
]


def run_tests():
    results_by_lang = {}
    failures = []
    total = 0
    passed = 0

    for lang_code, sentence, expected_words, desc in TESTS:
        total += 1
        restored = restorer.restore(sentence, lang_code)

        if expected_words is None:
            # Native-only test: restored should equal original
            ok = (restored == sentence)
            if not ok:
                failures.append({
                    "num": total,
                    "lang": lang_code,
                    "desc": desc,
                    "input": sentence,
                    "output": restored,
                    "issue": "NATIVE sentence was modified (false positive)",
                })
        else:
            # Code-mixed test: expected English words must appear
            restored_lower = restored.lower()
            missing = [w for w in expected_words if w.lower() not in restored_lower]
            ok = len(missing) == 0
            if not ok:
                failures.append({
                    "num": total,
                    "lang": lang_code,
                    "desc": desc,
                    "input": sentence,
                    "output": restored,
                    "expected": expected_words,
                    "missing": missing,
                    "issue": f"Missing: {', '.join(missing)}",
                })

        if ok:
            passed += 1

        # Track per-language
        if lang_code not in results_by_lang:
            results_by_lang[lang_code] = {"total": 0, "passed": 0, "failed": 0}
        results_by_lang[lang_code]["total"] += 1
        results_by_lang[lang_code]["passed" if ok else "failed"] += 1

    # ── Print Results ─────────────────────────────────────────────────────
    lang_names = {
        "hi": "Hindi", "bn": "Bengali", "ta": "Tamil", "te": "Telugu",
        "kn": "Kannada", "mr": "Marathi", "gu": "Gujarati", "pa": "Punjabi",
        "ml": "Malayalam", "or": "Odia", "as": "Assamese", "ne": "Nepali",
        "ur": "Urdu", "mai": "Maithili", "kok": "Konkani", "doi": "Dogri",
        "sd": "Sindhi", "ks": "Kashmiri", "sa": "Sanskrit", "brx": "Bodo",
        "mni": "Manipuri", "sat": "Santali",
    }

    print("=" * 90)
    print("UNSEEN SENTENCE TEST — ALL 22 SCHEDULED LANGUAGES")
    print("=" * 90)
    print()
    print(f"{'Language':<14}{'Code':<6}{'Total':>6}{'Pass':>6}{'Fail':>6}{'Acc':>8}")
    print("-" * 46)

    for lang_code in ["hi", "bn", "ta", "te", "kn", "mr", "gu", "pa",
                       "ml", "or", "as", "ne", "ur", "mai", "kok", "doi",
                       "sd", "ks", "sa", "brx", "mni", "sat"]:
        r = results_by_lang.get(lang_code, {"total": 0, "passed": 0, "failed": 0})
        if r["total"] == 0:
            continue
        acc = f"{r['passed']/r['total']*100:.0f}%"
        status = "✓" if r["failed"] == 0 else ""
        name = lang_names.get(lang_code, lang_code)
        print(f"{name:<14}{lang_code:<6}{r['total']:>6}{r['passed']:>6}{r['failed']:>6}{acc:>8}  {status}")

    print("-" * 46)
    print(f"{'OVERALL':<20}{total:>6}{passed:>6}{total-passed:>6}{passed/total*100:.1f}%")
    print()

    if failures:
        print(f"FAILURES ({len(failures)})")
        print("=" * 90)
        for f in failures:
            print(f"\n  #{f['num']} [{f['lang']}] {f['desc']}")
            print(f"    Input:   {f['input']}")
            print(f"    Output:  {f['output']}")
            print(f"    Issue:   {f['issue']}")
    else:
        print("ALL TESTS PASSED!")

    print(f"\n{passed}/{total} tests passed ({passed/total*100:.1f}%)")
    return passed, total


if __name__ == "__main__":
    passed, total = run_tests()
    exit(0 if passed == total else 1)
