#!/usr/bin/env python3
"""Fresh end-to-end test with entirely new sentences, words, and domains.

Every sentence here is unique — no overlap with e2e_test.py, e2e_test_expanded.py,
e2e_test_comprehensive.py, e2e_test_unseen.py, test_new_examples.py, or
test_new_examples_2.py.

Focuses on under-tested domains: cooking/food, fashion, real estate, science,
sports commentary, music, automotive, legal proceedings, environmental topics,
and casual/slang code-mixing patterns.

Also tests under-represented languages more heavily.
"""

import sys
import time

from codemix_restore import ScriptRestorer

print("Initializing ScriptRestorer...")
t0 = time.time()
restorer = ScriptRestorer()
print(f"Initialized in {time.time() - t0:.2f}s\n")
print("Neural available:", restorer._neural.is_available if restorer._neural else False)
print("=" * 80)
# ==============================================================================
# Test cases: (lang, input_text, expected_words_list)
#
# expected_words_list is a list of groups. Each group is a list of words that
# must ALL appear (case-insensitive) in the output. If any ONE group matches
# fully, the test passes. An empty list [] means NO English words are expected
# (native-only sentence — tests false-positive protection).
# ==============================================================================

TEST_CASES = [
    # =========================================================================
    # HINDI (hi) — Cooking, Automotive, Fashion, Real Estate, Science
    # =========================================================================
    # Cooking / Food
    ("hi", "रेसिपी ऑनलाइन सर्च करो", [["recipe", "online", "search"], ["online", "search"]]),
    ("hi", "माइक्रोवेव में हीट करो", [["microwave", "heat"], ["microwave"]]),
    ("hi", "ब्लेंडर से जूस बनाओ", [["blender", "juice"], ["blender"]]),
    ("hi", "फ्रिज में स्टोर करके रखो", [["fridge", "store"], ["fridge"]]),
    # Automotive
    ("hi", "गाड़ी का इंश्योरेंस रिन्यू करवाओ", [["insurance", "renew"]]),
    ("hi", "ब्रेक पैड चेंज करवाना है", [["brake", "pad", "change"], ["break", "change"]]),
    ("hi", "माइलेज बहुत कम आ रहा है", [["mileage"]]),
    ("hi", "पार्किंग स्लॉट खाली नहीं है", [["parking", "slot"], ["parking"]]),
    # Fashion
    ("hi", "ये ड्रेस ट्रेंडिंग में है", [["dress", "trending"], ["dress"]]),
    ("hi", "ब्रांड का लेटेस्ट कलेक्शन देखो", [["brand", "latest", "collection"], ["brand", "latest"]]),
    # Real Estate
    ("hi", "फ्लैट का रजिस्ट्रेशन करवाना है", [["flat", "registration"], ["registration"]]),
    ("hi", "प्रॉपर्टी का वैल्यूएशन करवाओ", [["property", "valuation"], ["property"]]),
    # Science
    ("hi", "एक्सपेरिमेंट फेल हो गया", [["experiment", "fail"], ["experiment"]]),
    ("hi", "सैम्पल लैब में भेजो", [["sample", "lab"], ["sample"]]),
    # Native-only (FALSE POSITIVE tests)
    ("hi", "सुबह जल्दी उठकर दौड़ने जाओ", []),
    ("hi", "पहाड़ों पर बर्फ गिर रही है", []),

    # =========================================================================
    # BENGALI (bn) — Music, Environment, Casual slang
    # =========================================================================
    ("bn", "গিটার প্র্যাক্টিস করো", [["guitar", "practice"], ["practice"]]),
    ("bn", "অ্যালবাম রিলিজ হয়েছে", [["album", "release"], ["album"]]),
    ("bn", "পলিউশন লেভেল বেড়ে গেছে", [["pollution", "level"], ["pollution"]]),
    ("bn", "সোলার প্যানেল ইনস্টল করো", [["solar", "panel", "install"], ["install"]]),
    ("bn", "প্লাস্টিক ব্যান করা উচিত", [["plastic", "ban"], ["plastic"]]),
    ("bn", "ক্যামেরা ফোকাস ঠিক করো", [["camera", "focus"], ["camera"]]),
    ("bn", "ব্যাটারি চার্জ দাও", [["battery", "charge"], ["battery"]]),
    # Native-only
    ("bn", "আকাশে মেঘ জমেছে বৃষ্টি হবে", []),
    ("bn", "ছোটবেলায় আমরা মাঠে খেলতাম", []),

    # =========================================================================
    # TAMIL (ta) — Sports, Legal, Science
    # =========================================================================
    ("ta", "மேட்ச் டை ஆகிவிட்டது", [["match", "tie"], ["match"]]),
    ("ta", "கோச் பிளேயர்ஸ் செலக்ட் செய்தார்", [["coach", "players", "select"], ["players", "select"]]),
    ("ta", "பேட்டிங் ஆர்டர் மாற்ற வேண்டும்", [["batting", "order"], ["order"]]),
    ("ta", "லாயர் கேஸ் ஃபைல் செய்தார்", [["lawyer", "case", "file"], ["case", "file"]]),
    ("ta", "ஹியரிங் போஸ்ட்போன் ஆனது", [["hearing", "postpone"], ["hearing"]]),
    ("ta", "ரிசர்ச் பேப்பர் பப்ளிஷ் ஆனது", [["research", "paper", "publish"], ["research", "paper"]]),
    ("ta", "வேக்சின் டோஸ் எடுத்துக்கொள்ளுங்கள்", [["vaccine", "dose"], ["vaccine"]]),
    # Native-only (FALSE POSITIVE tests)
    ("ta", "மழை வந்தால் வீட்டிலேயே இருங்கள்", []),
    ("ta", "அம்மா சமைத்த சாப்பாடு மிகவும் சுவையாக இருந்தது", []),

    # =========================================================================
    # TELUGU (te) — Music, Fitness, Environment
    # =========================================================================
    ("te", "కాన్సర్ట్ టికెట్ బుక్ చేయండి", [["concert", "ticket", "book"], ["ticket", "book"]]),
    ("te", "వర్కౌట్ రూటీన్ ఫాలో చేయండి", [["workout", "routine", "follow"], ["workout", "follow"]]),
    ("te", "ప్రొటీన్ షేక్ తాగండి", [["protein", "shake"], ["protein"]]),
    ("te", "క్లైమేట్ చేంజ్ సీరియస్ ప్రాబ్లం", [["climate", "change", "serious", "problem"], ["climate", "change"]]),
    ("te", "రీసైకిల్ చేయడం మంచిది", [["recycle"]]),
    ("te", "స్మార్ట్ వాచ్ ట్రాక్ చేస్తుంది", [["smart", "watch", "track"], ["smart", "track"]]),
    # Native-only
    ("te", "ఈ రోజు ఎండ చాలా ఎక్కువగా ఉంది", []),
    ("te", "పిల్లలు బడికి వెళ్ళారు", []),

    # =========================================================================
    # KANNADA (kn) — Startup, Gaming, Automotive
    # =========================================================================
    ("kn", "ಸ್ಟಾರ್ಟಪ್ ಫಂಡಿಂಗ್ ಸಿಕ್ಕಿದೆ", [["startup", "funding"]]),
    ("kn", "ಪಿಚ್ ಡೆಕ್ ರೆಡಿ ಮಾಡಿ", [["pitch", "deck", "ready"], ["ready"]]),
    ("kn", "ಗೇಮ್ ಅಪ್ಡೇಟ್ ಡೌನ್ಲೋಡ್ ಮಾಡಿ", [["game", "update", "download"], ["update", "download"]]),
    ("kn", "ಲೆವೆಲ್ ಅನ್ಲಾಕ್ ಆಗಿದೆ", [["level", "unlock"]]),
    ("kn", "ಟಯರ್ ಪಂಕ್ಚರ್ ಆಗಿದೆ", [["tire", "puncture"], ["tyre", "puncture"], ["puncture"]]),
    ("kn", "ಸರ್ವಿಸ್ ಸೆಂಟರ್ ಗೆ ಕಾರ್ ತೆಗೆದುಕೊಂಡು ಹೋಗಿ", [["service", "center", "car"], ["service", "centre", "car"], ["service", "car"]]),
    # Native-only
    ("kn", "ಮನೆಯಲ್ಲಿ ಎಲ್ಲರೂ ಆರೋಗ್ಯವಾಗಿದ್ದಾರೆ", []),
    ("kn", "ಮಳೆ ಬಂದು ಹೊಳೆ ತುಂಬಿ ಹರಿಯುತ್ತಿದೆ", []),

    # =========================================================================
    # MARATHI (mr) — Fitness, Photography, Real Estate
    # =========================================================================
    ("mr", "जिम मेंबरशिप रिन्यू करा", [["gym", "membership", "renew"], ["membership", "renew"]]),
    ("mr", "ट्रेडमिल वर रनिंग करा", [["treadmill", "running"]]),
    ("mr", "फोटो एडिट करून पोस्ट करा", [["photo", "edit", "post"], ["edit", "post"]]),
    ("mr", "झूम इन करा डिटेल बघा", [["zoom", "detail"], ["zoom", "in"], ["detail"]]),
    ("mr", "ब्रोकर कडून प्रॉपर्टी शो करवून घ्या", [["broker", "property", "show"], ["broker", "property"]]),
    ("mr", "लोन अप्रूव्ह झाले", [["loan", "approve"], ["loan"]]),
    # Native-only
    ("mr", "आज पहाटे खूप धुके होते", []),
    ("mr", "बाजारातून भाजीपाला आणा", []),

    # =========================================================================
    # GUJARATI (gu) — Travel, Shopping, Science
    # =========================================================================
    ("gu", "ક્રૂઝ ટ્રિપ બુક કરો", [["cruise", "trip", "book"], ["trip", "book"]]),
    ("gu", "પાસપોર્ટ એક્સપાયર થઈ ગયો છે", [["passport", "expire"], ["passport"]]),
    ("gu", "ડિસ્કાઉન્ટ કૂપન અપ્લાય કરો", [["discount", "coupon", "apply"], ["discount", "apply"]]),
    ("gu", "વોરંટી પીરિયડ પૂરો થઈ ગયો", [["warranty", "period"], ["warranty"]]),
    ("gu", "લેબોરેટરી રિપોર્ટ રેડી છે", [["laboratory", "report", "ready"], ["report", "ready"]]),
    # Native-only (FALSE POSITIVE test)
    ("gu", "સવારે વહેલા ઊઠીને યોગ કરો", []),
    ("gu", "દાદીમાએ રસોઈ બનાવી અને બધાને જમાડ્યા", []),

    # =========================================================================
    # PUNJABI (pa) — Agriculture, Music, Fitness
    # =========================================================================
    ("pa", "ਫਰਟੀਲਾਈਜ਼ਰ ਸਪ੍ਰੇ ਕਰੋ", [["fertilizer", "spray"], ["fertilizer"]]),
    ("pa", "ਹਾਰਵੈਸਟ ਸੀਜ਼ਨ ਸ਼ੁਰੂ ਹੋ ਗਿਆ", [["harvest", "season"]]),
    ("pa", "ਡੀਜੇ ਨੇ ਟ੍ਰੈਕ ਪਲੇ ਕੀਤਾ", [["dj", "track", "play"], ["d.j.", "track", "play"], ["track"]]),
    ("pa", "ਸਪੀਕਰ ਦੀ ਵਾਲਿਊਮ ਵਧਾਓ", [["speaker", "volume"]]),
    ("pa", "ਡਾਇਟ ਪਲੈਨ ਫਾਲੋ ਕਰੋ", [["diet", "plan", "follow"], ["diet", "follow"]]),
    ("pa", "ਕੈਲੋਰੀ ਕਾਊਂਟ ਕਰੋ", [["calorie", "count"], ["count"]]),
    # Native-only
    ("pa", "ਖੇਤਾਂ ਵਿੱਚ ਕਣਕ ਪੱਕ ਗਈ ਹੈ", []),
    ("pa", "ਨਾਨੀ ਨੇ ਪਰਾਂਠੇ ਬਣਾ ਕੇ ਖਿਲਾਏ", []),

    # =========================================================================
    # MALAYALAM (ml) — Cinema, Cooking, Environment
    # =========================================================================
    ("ml", "ട്രെയിലർ റിലീസ് ആയി", [["trailer", "release"]]),
    ("ml", "ഡയറക്ടർ ഷൂട്ടിംഗ് തുടങ്ങി", [["director", "shooting"]]),
    ("ml", "ഓവൻ പ്രീഹീറ്റ് ചെയ്യൂ", [["oven", "preheat"], ["oven"]]),
    ("ml", "ഫ്രെഷ് ക്രീം ആഡ് ചെയ്യൂ", [["fresh", "cream", "add"], ["fresh"]]),
    ("ml", "ഡീസൽ വെഹിക്കിൾ ബാൻ ചെയ്യണം", [["diesel", "vehicle", "ban"]]),
    # Native-only (FALSE POSITIVE tests)
    ("ml", "മഴ പെയ്താൽ വീട്ടിൽ തന്നെ ഇരിക്കൂ", []),
    ("ml", "അമ്മ ഉണ്ടാക്കിയ പായസം വളരെ രുചിയായിരുന്നു", []),

    # =========================================================================
    # ODIA (or) — Education, Technology, Daily life
    # =========================================================================
    ("or", "ସ୍କଲାରଶିପ୍ ଫର୍ମ ଭରିବେ", [["scholarship", "form"], ["form"]]),
    ("or", "ସିଲେବସ୍ ଡାଉନଲୋଡ୍ କରନ୍ତୁ", [["syllabus", "download"], ["download"]]),
    ("or", "ଟଚ୍ ସ୍କ୍ରିନ୍ କାମ କରୁନାହିଁ", [["touch", "screen"], ["screen"]]),
    ("or", "ବ୍ଲୁଟୁଥ୍ ଅନ୍ କରନ୍ତୁ", [["bluetooth"]]),
    # Native-only
    ("or", "ଆଜି ସକାଳୁ ଖୁବ୍ ଥଣ୍ଡା ଲାଗୁଥିଲା", []),

    # =========================================================================
    # ASSAMESE (as) — Nature, Technology
    # =========================================================================
    ("as", "ৱেবছাইট ডিজাইন কৰক", [["website", "design"], ["website"]]),
    ("as", "ডমেইন ৰেজিষ্ট্ৰাৰ কৰক", [["domain", "register"], ["domain", "registrar"], ["domain"]]),
    ("as", "ফ্লাড ৱাৰ্নিং দিয়া হৈছে", [["flood", "warning"], ["flood"]]),
    ("as", "ক্লাইমেট ৰিপ'ৰ্ট পঢ়ক", [["climate", "report"], ["climate"]]),
    # Native-only
    ("as", "আজি বৰ গৰম পৰিছে বতাহ নাই", []),

    # =========================================================================
    # NEPALI (ne) — Tourism, Technology
    # =========================================================================
    ("ne", "ट्रेकिंग गाइड हायर गर", [["trekking", "guide", "hire"], ["tracking", "guide", "hire"], ["guide", "hire"]]),
    ("ne", "कैम्प साइट सेटअप गर", [["camp", "site", "setup"], ["camp", "site"]]),
    ("ne", "मोबाइल ब्राउजर स्लो छ", [["mobile", "browser", "slow"], ["mobile", "slow"]]),
    ("ne", "नोटिफिकेशन ऑफ गर", [["notification", "off"], ["notification"]]),
    # Native-only
    ("ne", "हिमालय धेरै सुन्दर छ हामी जानुपर्छ", []),

    # =========================================================================
    # URDU (ur) — Fashion, Food, Legal
    # =========================================================================
    ("ur", "ڈیزائنر کلیکشن لانچ ہوا", [["designer", "collection", "launch"], ["designer", "launch"]]),
    ("ur", "فیبرک کوالٹی چیک کرو", [["fabric", "quality", "check"], ["fabric", "check"]]),
    ("ur", "مینو میں نئی ڈش ایڈ کرو", [["menu", "dish", "add"], ["menu"]]),
    ("ur", "وکیل نے پٹیشن فائل کی", [["petition", "file"]]),
    ("ur", "بیل اپلیکیشن جمع کرو", [["bail", "application"]]),
    # Native-only
    ("ur", "آج بہت تیز دھوپ ہے باہر مت جاؤ", []),

    # =========================================================================
    # KASHMIRI (ks) — Daily life, Technology
    # =========================================================================
    ("ks", "موبایل چارج کرو", [["mobile", "charge"], ["mobile"]]),
    ("ks", "سگنل ویک چھُ", [["signal", "weak"], ["signal"]]),
    ("ks", "ٹیچر نے ریزلٹ دِتھ", [["teacher", "result"], ["result"]]),
    # Native-only (FALSE POSITIVE test)
    ("ks", "آج ہوا بوہ تیز چھے", []),

    # =========================================================================
    # SINDHI (sd) — Commerce, Technology
    # =========================================================================
    ("sd", "آرڊر ٽريڪ ڪريو", [["order", "track"], ["order"]]),
    ("sd", "ڊليوري ليٽ ٿي وئي", [["delivery", "late"], ["delivery"]]),
    ("sd", "ٽيبليٽ ھينگ ٿي پيو آھي", [["tablet", "hang"], ["tablet"]]),
    # Native-only
    ("sd", "اڄ مينھن جو موسم آھي", []),

    # =========================================================================
    # MAITHILI (mai) — Education, Daily life
    # =========================================================================
    ("mai", "ट्यूशन फीस जमा करू", [["tuition", "fees"], ["fees"]]),
    ("mai", "होस्टल रूम अलॉट भेल", [["hostel", "room", "allot"], ["hostel"]]),
    ("mai", "ऑनलाइन क्लास ज्वाइन करू", [["online", "class", "join"], ["online", "class"]]),
    # Native-only
    ("mai", "आइ बड़ी ठंढी अछि बाहर नहि जाउ", []),

    # =========================================================================
    # KONKANI (kok) — Food, Technology
    # =========================================================================
    ("kok", "ब्लॉग पोस्ट पब्लिश करा", [["blog", "post", "publish"], ["blog", "post"]]),
    ("kok", "वेबसाइट मेंटेनन्स चालू आसा", [["website", "maintenance"], ["website"]]),
    ("kok", "मेन्यू कार्ड प्रिंट करा", [["menu", "card", "print"], ["print"]]),
    # Native-only
    ("kok", "आयज सकाळीं खूब पावस पडलो", []),

    # =========================================================================
    # DOGRI (doi) — Agriculture, Daily life
    # =========================================================================
    ("doi", "पेस्टिसाइड स्प्रे करो", [["pesticide", "spray"], ["pesticide"]]),
    ("doi", "ट्रैक्टर सर्विस करवाओ", [["tractor", "service"], ["service"]]),
    ("doi", "मार्केट रेट चेक करो", [["market", "rate", "check"]]),
    # Native-only
    ("doi", "अज्ज बड़ी सर्दी ऐ घरे बैठो", []),

    # =========================================================================
    # SANSKRIT (sa) — Academic, Modern usage
    # =========================================================================
    ("sa", "डिजिटल लाइब्रेरी उपयोगी अस्ति", [["digital", "library"], ["digital"]]),
    ("sa", "रिसर्च ग्रांट प्राप्तम्", [["research", "grant"], ["research"]]),
    # Native-only
    ("sa", "विद्यालये छात्राः पठन्ति", []),

    # =========================================================================
    # BODO (brx) — Technology, Education
    # =========================================================================
    ("brx", "वाईफाई पासवर्ड चेंज करो", [["wifi", "password", "change"], ["password", "change"]]),
    ("brx", "प्रोजेक्ट रिपोर्ट सबमिट करो", [["project", "report", "submit"]]),
    # Native-only
    ("brx", "दिनै गोजोन बेरनि जोबोद सिगां", []),

    # =========================================================================
    # MANIPURI (mni) — Technology
    # =========================================================================
    ("mni", "ꯑꯦꯞ ꯏꯅꯁ꯭ꯇꯣꯜ ꯇꯧꯕꯤꯌꯨ", [["app", "install"], ["app"]]),
    # Native-only
    ("mni", "ꯅꯣꯡꯃꯥꯏꯖꯤꯡ ꯑꯁꯤꯗ ꯐꯖ ꯐꯖꯕ ꯂꯩ", []),

    # =========================================================================
    # SANTALI (sat) — Technology
    # =========================================================================
    ("sat", "ᱯᱷᱚᱱ ᱨᱤᱥᱴᱟᱨᱴ ᱢᱮ", [["phone", "restart"]]),
    # Native-only
    ("sat", "ᱱᱚᱣᱟ ᱫᱤᱱ ᱨᱮ ᱡᱚᱛᱚ ᱥᱟᱱᱟᱢ", []),
]


def run_tests():
    passed = 0
    failed = 0
    errors = []

    for i, (lang, input_text, expected_groups) in enumerate(TEST_CASES, 1):
        try:
            output = restorer.restore(input_text, lang=lang)
        except Exception as e:
            failed += 1
            errors.append((i, lang, input_text, f"EXCEPTION: {e}", ""))
            continue

        output_lower = output.lower()

        if not expected_groups:
            # Native-only: output should be very close to input (no English injected)
            has_latin = any(c.isascii() and c.isalpha() for c in output)
            if has_latin:
                failed += 1
                errors.append((i, lang, input_text, "Expected native-only but got English", output))
            else:
                passed += 1
            continue

        # Check if ANY group fully matches
        matched = False
        for group in expected_groups:
            if all(word.lower() in output_lower for word in group):
                matched = True
                break

        if matched:
            passed += 1
        else:
            failed += 1
            errors.append((i, lang, input_text, f"Expected one of {expected_groups}", output))

    # Print results
    total = passed + failed
    print(f"\n{'='*70}")
    print(f"RESULTS: {passed}/{total} passed ({100*passed/total:.1f}%)")
    print(f"{'='*70}")

    if errors:
        print(f"\n--- {len(errors)} FAILED ---\n")
        for idx, lang, inp, expected, got in errors:
            print(f"  #{idx} [{lang}]")
            print(f"    Input:    {inp}")
            print(f"    Expected: {expected}")
            print(f"    Got:      {got}")
            print()

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
