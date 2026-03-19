#!/usr/bin/env python3
"""Ultimate robustness test with entirely unseen sentences and words.

Every sentence and every English target word in this file is NEW — no overlap with
e2e_test.py, e2e_test_expanded.py, e2e_test_comprehensive.py, e2e_test_unseen.py,
or e2e_test_fresh.py.

Tests domains: healthcare procedures, legal filings, construction, logistics,
agriculture tech, fintech, edtech, gaming, astronomy, marine, textile, mining,
renewable energy, aerospace, cybersecurity, culinary arts, veterinary, archaeology.

Also stress-tests: very short words, multi-loanword sentences, rare/technical terms,
and native-only sentences with no English at all.
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
# (lang, input_text, expected_words_list)
# [] = native-only (no English expected)
# ==============================================================================

TEST_CASES = [
    # =========================================================================
    # HINDI (hi) — Construction, Cybersecurity, Culinary, Veterinary
    # =========================================================================
    ("hi", "कॉन्ट्रैक्टर ने ब्लूप्रिंट दिखाया", [["contractor", "blueprint"], ["contractor"]]),
    ("hi", "सीमेंट और कंक्रीट का मिक्सचर तैयार करो", [["cement", "concrete", "mixture"], ["cement", "concrete"]]),
    ("hi", "फायरवॉल कॉन्फिगर करना ज़रूरी है", [["firewall", "configure"], ["firewall"]]),
    ("hi", "एन्क्रिप्शन कमजोर है पैच लगाओ", [["encryption", "patch"], ["encryption"]]),
    ("hi", "गार्निश करके सर्व करो", [["garnish", "serve"], ["garnish"]]),
    ("hi", "पशु चिकित्सक ने सर्जरी की", [["surgery"]]),
    # Native-only
    ("hi", "गंगा नदी बहुत पवित्र मानी जाती है", []),
    ("hi", "दादाजी ने कहानी सुनाई और सब सो गए", []),

    # =========================================================================
    # BENGALI (bn) — Marine, Textile, Aerospace
    # =========================================================================
    ("bn", "অ্যাংকর পয়েন্ট চেক করো", [["anchor", "point"], ["anchor"]]),
    ("bn", "সাবমেরিন সোনার টেস্ট করো", [["submarine", "sonar", "test"], ["submarine", "sonar"]]),
    ("bn", "ফেব্রিক কোয়ালিটি ইন্সপেকশন করো", [["inspection"], ["quality"]]),
    ("bn", "স্যাটেলাইট অরবিট অ্যাডজাস্ট করো", [["satellite", "orbit", "adjust"], ["satellite", "orbit"]]),
    # Native-only
    ("bn", "নদীর ধারে বসে পাখি দেখছিলাম", []),

    # =========================================================================
    # TAMIL (ta) — Mining, Renewable Energy, Archaeology
    # =========================================================================
    ("ta", "டர்பைன் எஃபிசியன்சி சோதனை செய்யுங்கள்", [["turbine", "efficiency"], ["turbine"]]),
    ("ta", "எக்ஸ்கவேட்டர் சைட்டில் நிறுத்துங்கள்", [["excavator", "site"], ["excavator"]]),
    ("ta", "ஆர்க்கியாலஜி டீம் வந்துவிட்டது", [["archaeology", "team"], ["archaeology"]]),
    ("ta", "கார்பன் ஃபுட்பிரிண்ட் குறைக்க வேண்டும்", [["carbon", "footprint"], ["carbon"]]),
    # Native-only
    ("ta", "காலையில் கோவிலுக்கு சென்று வழிபட்டோம்", []),

    # =========================================================================
    # TELUGU (te) — Fintech, Gaming, Astronomy
    # =========================================================================
    ("te", "క్రిప్టోకరెన్సీ వాలెట్ సెటప్ చేయండి", [["cryptocurrency", "wallet", "setup"], ["cryptocurrency", "wallet"]]),
    ("te", "కన్సోల్ గేమింగ్ హెడ్సెట్ కనెక్ట్ చేయండి", [["console", "gaming", "headset"], ["console", "gaming"]]),
    ("te", "టెలిస్కోప్ లెన్స్ క్లీన్ చేయండి", [["telescope", "lens", "clean"], ["telescope", "lens"]]),
    ("te", "బ్లాక్చెయిన్ ట్రాన్సాక్షన్ వెరిఫై చేయండి", [["blockchain", "transaction", "verify"], ["blockchain", "transaction"]]),
    # Native-only
    ("te", "అమ్మమ్మ చేతి పులిహోర చాలా బాగుంటుంది", []),

    # =========================================================================
    # KANNADA (kn) — EdTech, Logistics, Aerospace
    # =========================================================================
    ("kn", "ಕರಿಕ್ಯುಲಂ ಅಪ್ಲೋಡ್ ಮಾಡಿ", [["curriculum", "upload"], ["curriculum"]]),
    ("kn", "ವೇರ್ಹೌಸ್ ಇನ್ವೆಂಟರಿ ಚೆಕ್ ಮಾಡಿ", [["warehouse", "inventory"], ["warehouse"]]),
    ("kn", "ರಾಕೆಟ್ ಪ್ರೊಪಲ್ಶನ್ ಸಿಸ್ಟಮ್ ಟೆಸ್ಟ್ ಮಾಡಿ", [["rocket", "propulsion", "system", "test"], ["rocket", "propulsion"]]),
    ("kn", "ಟ್ಯೂಟೋರಿಯಲ್ ವೀಡಿಯೋ ರೆಕಾರ್ಡ್ ಮಾಡಿ", [["tutorial", "record"], ["tutorial"]]),
    # Native-only
    ("kn", "ಅಜ್ಜಿ ಮನೆಯಲ್ಲಿ ಹೋಳಿಗೆ ಮಾಡಿದ್ದರು", []),

    # =========================================================================
    # MARATHI (mr) — Construction, Veterinary, Renewable
    # =========================================================================
    ("mr", "प्लंबर ने पाइपलाइन फिक्स केली", [["plumber", "pipeline", "fix"], ["plumber", "pipeline"]]),
    ("mr", "सोलर इन्व्हर्टर वॉरंटी संपली", [["solar", "inverter", "warranty"], ["solar", "inverter"]]),
    ("mr", "व्हेटर्नरी क्लिनिक मध्ये पेट स्कॅन केला", [["veterinary", "clinic", "pet", "scan"], ["veterinary", "clinic"]]),
    # Native-only
    ("mr", "पावसाळ्यात शेतकरी नांगरणी करतात", []),

    # =========================================================================
    # GUJARATI (gu) — Mining, Textile, Fintech
    # =========================================================================
    ("gu", "માઇનિંગ ઇક્વિપમેન્ટ ઇન્સ્ટોલ કરો", [["mining", "equipment", "install"], ["mining", "equipment"]]),
    ("gu", "ગાર્મેન્ટ ફેક્ટરી ઓર્ડર ડિસ્પેચ કરો", [["garment", "factory", "dispatch"], ["garment", "factory"]]),
    ("gu", "ડિજિટલ પેમેન્ટ ગેટવે ઇન્ટિગ્રેટ કરો", [["gateway", "integrate"], ["gateway"]]),
    # Native-only
    ("gu", "નવરાત્રીમાં ગરબા રમવાની ખૂબ મજા આવે છે", []),

    # =========================================================================
    # PUNJABI (pa) — Dairy, Logistics, Construction
    # =========================================================================
    ("pa", "ਪਾਸਚਰਾਈਜ਼ਡ ਮਿਲਕ ਪੈਕ ਕਰੋ", [["pasteurized", "milk", "pack"], ["milk", "pack"]]),
    ("pa", "ਕੰਟੇਨਰ ਸ਼ਿਪਮੈਂਟ ਟ੍ਰੈਕ ਕਰੋ", [["container", "shipment"], ["container"]]),
    ("pa", "ਫਾਊਂਡੇਸ਼ਨ ਲੇਅਰ ਪੱਕੀ ਕਰੋ", [["foundation", "layer"], ["foundation"]]),
    # Native-only
    ("pa", "ਵਿਸਾਖੀ ਦਾ ਤਿਉਹਾਰ ਬੜੀ ਧੂਮਧਾਮ ਨਾਲ ਮਨਾਇਆ ਜਾਂਦਾ ਹੈ", []),

    # =========================================================================
    # MALAYALAM (ml) — Marine, Culinary, Healthcare
    # =========================================================================
    ("ml", "ലൈഫ്ജാക്കറ്റ് ഇൻസ്പെക്ഷൻ പൂർത്തിയാക്കൂ", [["lifejacket", "inspection"], ["inspection"]]),
    ("ml", "മറൈൻ ഡ്രൈവർ ലൈസൻസ് റിന്യൂ ചെയ്യൂ", [["marine", "driver", "license"], ["marine", "license"]]),
    ("ml", "ആന്റിബയോട്ടിക് കോഴ്സ് കംപ്ലീറ്റ് ചെയ്യൂ", [["antibiotic", "course", "complete"], ["antibiotic", "course"]]),
    # Native-only
    ("ml", "ഓണത്തിന് സദ്യ ഉണ്ടാക്കി എല്ലാവരും ഒരുമിച്ചു കഴിച്ചു", []),

    # =========================================================================
    # ODIA (or) — Agriculture Tech, Construction
    # =========================================================================
    ("or", "ଡ୍ରିପ୍ ଇରିଗେସନ୍ ସିଷ୍ଟମ ଇନଷ୍ଟଲ କରନ୍ତୁ", [["drip", "irrigation", "system"], ["drip", "irrigation"]]),
    ("or", "ଇଲେକ୍ଟ୍ରିକ୍ ସର୍କିଟ୍ ବ୍ରେକର ଲଗାନ୍ତୁ", [["electric", "circuit", "breaker"], ["electric", "circuit"]]),
    # Native-only
    ("or", "ଓଡ଼ିଶାର ଜଗନ୍ନାଥ ମନ୍ଦିର ବହୁତ ପ୍ରସିଦ୍ଧ", []),

    # =========================================================================
    # ASSAMESE (as) — Tea Industry, Wildlife
    # =========================================================================
    ("as", "গ্ৰেডিং মেচিন চালু কৰক", [["grading", "machine"], ["grading"]]),
    ("as", "ৱাইল্ডলাইফ ফটোগ্ৰাফী ৱৰ্কশ্বপ আছে", [["wildlife", "photography", "workshop"], ["wildlife", "photography"]]),
    # Native-only
    ("as", "বিহুৰ সময়ত সকলোৱে একেলগে নাচে আৰু গায়", []),

    # =========================================================================
    # NEPALI (ne) — Mountaineering, Hydropower
    # =========================================================================
    ("ne", "हार्नेस र कार्बিनर इन्स्पेक्ट गर", [["harness", "carabiner", "inspect"], ["harness", "inspect"]]),
    ("ne", "हाइड्रोपावर टर्बाइन मेन्टेनेन्स गर", [["hydropower", "turbine", "maintenance"], ["hydropower", "turbine"]]),
    # Native-only
    ("ne", "दशैंमा टीकाको लागि सबै घर जम्मा हुन्छन्", []),

    # =========================================================================
    # URDU (ur) — Calligraphy, Architecture, Legal
    # =========================================================================
    ("ur", "آرکیٹیکچر فرم میں ماڈل تیار کرو", [["architecture", "firm", "model"], ["architecture", "model"]]),
    ("ur", "کلائنٹ کا نوٹری ورک پورا کرو", [["notary", "work"], ["notary"]]),
    # Native-only
    ("ur", "رمضان میں سحری اور افطاری کا خاص خیال رکھو", []),

    # =========================================================================
    # KASHMIRI (ks) — Tourism, Handicraft
    # =========================================================================
    ("ks", "ہینڈیکرافٹ ایکسپورٹ آرڈر پیک کرو", [["handicraft", "export"], ["handicraft"]]),
    # Native-only
    ("ks", "شکرگاہ مَنز پھول کھِلان چھِ", []),

    # =========================================================================
    # SINDHI (sd) — Commerce, Agriculture
    # =========================================================================
    ("sd", "ڪاٽن جي ڪوالٽي ٽيسٽ ڪريو", [["cotton", "quality", "test"], ["cotton", "test"]]),
    ("sd", "فرٽيلائيزر ڊوز ايڊجسٽ ڪريو", [["dose", "adjust"], ["adjust"]]),
    # Native-only
    ("sd", "سنڌ جي ماڻهو مهمان نواز آهن", []),

    # =========================================================================
    # MAITHILI (mai) — Education, Rural Tech
    # =========================================================================
    ("mai", "स्मार्टफोन से वीडियो कॉन्फ्रेंस करू", [["smartphone", "video", "conference"], ["smartphone", "conference"]]),
    ("mai", "बायोमेट्रिक अटेंडेंस मशीन लगाऊ", [["biometric", "attendance", "machine"], ["biometric", "attendance"]]),
    # Native-only
    ("mai", "छठ पूजा में सूर्य देव कऽ पूजा होइत अछि", []),

    # =========================================================================
    # KONKANI (kok) — Tourism, Fishery
    # =========================================================================
    ("kok", "रिसॉर्ट बुकिंग कन्फर्म करा", [["resort", "booking", "confirm"], ["resort"]]),
    ("kok", "फिश प्रोसेसिंग प्लांट इन्स्पेक्शन करा", [["fish", "processing", "plant", "inspection"], ["fish", "processing"]]),
    # Native-only
    ("kok", "गोंयच्या बीचार चलून वारो लागता", []),

    # =========================================================================
    # DOGRI (doi) — Handicraft, Agriculture
    # =========================================================================
    ("doi", "हैंडलूम प्रोडक्ट पैक करो", [["handloom", "product", "pack"], ["handloom", "product"]]),
    ("doi", "ड्रोन से क्रॉप मॉनिटरिंग करो", [["drone", "crop", "monitoring"], ["drone", "crop"]]),
    # Native-only
    ("doi", "डोगरी बोली बड़ी मिठी ऐ सुणदियां मन खुश होई जंदा", []),

    # =========================================================================
    # SANSKRIT (sa) — Academic, Digital
    # =========================================================================
    ("sa", "वेबिनार रजिस्ट्रेशन पूर्णम् अस्ति", [["webinar", "registration"], ["webinar"]]),
    ("sa", "ऑनलाइन आर्काइव अपडेट करोतु", [["archive"], ["archive"]]),
    # Native-only
    ("sa", "गुरोः आशीर्वादेन शिष्यः सफलः भवति", []),

    # =========================================================================
    # BODO (brx) — Education, Infrastructure
    # =========================================================================
    ("brx", "डिजिटल स्कोरबोर्ड इंस्टॉल करो", [["scoreboard", "install"], ["scoreboard"]]),
    ("brx", "ब्रिज कंस्ट्रक्शन इंस्पेक्शन करो", [["bridge", "construction", "inspection"], ["bridge", "construction"]]),
    # Native-only
    ("brx", "बिसुवा सानजा जोबोद गोजोन होयो", []),

    # =========================================================================
    # MANIPURI (mni) — Traditional, Digital
    # =========================================================================
    ("mni", "ꯏ-ꯀꯃꯔ꯭ꯁ ꯄ꯭ꯂꯦꯇꯐꯣꯔꯃ ꯁꯦꯇꯑꯞ ꯇꯧꯕꯤꯌꯨ", [["platform", "setup"], ["platform"]]),
    # Native-only
    ("mni", "ꯃꯅꯤꯄꯨꯔꯗ ꯁꯥꯟꯅ ꯂꯩꯕ ꯑꯁꯤ ꯌꯥꯝꯅ ꯐꯕ ꯂꯩ", []),

    # =========================================================================
    # SANTALI (sat) — Education, Agriculture
    # =========================================================================
    ("sat", "ᱮᱜᱡᱟᱢ ᱨᱤᱡᱟᱞᱴ ᱫᱮᱠᱷᱟ ᱢᱮ", [["result"], ["exam"]]),
    # Native-only
    ("sat", "ᱥᱟᱶᱦᱮᱫ ᱫᱚ ᱡᱚᱛᱚ ᱥᱮᱨᱢᱟ ᱠᱟᱱᱟ", []),
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
            has_latin = any(c.isascii() and c.isalpha() for c in output)
            if has_latin:
                failed += 1
                errors.append((i, lang, input_text, "Expected native-only but got English", output))
            else:
                passed += 1
            continue

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

    total = passed + failed
    print(f"\n{'='*70}")
    print(f"ROBUSTNESS TEST: {passed}/{total} passed ({100*passed/total:.1f}%)")
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
