#!/usr/bin/env python3
"""Comprehensive end-to-end test for codemix_restore across 8 languages."""

import sys
import time

from codemix_restore import ScriptRestorer

# Initialize restorer once
print("Initializing ScriptRestorer...")
t0 = time.time()
restorer = ScriptRestorer()
print(f"Initialized in {time.time() - t0:.2f}s\n")

# Test cases: list of (lang, input_text, expected_words_list)
# Each expected_words entry is a list of words that must ALL appear (case-insensitive) in the output
TEST_CASES = [
    # === Hindi (hi) ===
    ("hi", "धन्यवाद फॉर योर हेल्प", [["for", "your", "help"]]),
    ("hi", "मीटिंग कैंसल हो गयी है", [["meeting", "cancel"]]),
    ("hi", "प्लीज डॉक्यूमेंट शेयर करो", [["please", "document", "share"]]),
    ("hi", "ऑफिस में इंटरनेट स्लो है", [["office"], ["internet"], ["slow"]]),
    ("hi", "कल का प्रेजेंटेशन रेडी है", [["presentation", "ready"]]),
    ("hi", "मैं बस में हूँ, लेटर कॉल करता हूँ", [["later", "call"]]),
    ("hi", "सर प्लीज अप्रूव कर दीजिए", [["please", "approve"]]),
    ("hi", "ये प्रोजेक्ट वेरी इम्पोर्टेन्ट है", [["project", "very", "important"]]),
    ("hi", "टीम को मैसेज सेंड कर दो", [["team"], ["message"], ["send"]]),
    ("hi", "क्या स्टेटस है रिपोर्ट का", [["status"], ["report"]]),
    ("hi", "पासवर्ड रीसेट करना है", [["password", "reset"]]),
    ("hi", "डेडलाइन मिस मत करना", [["deadline", "miss"]]),
    ("hi", "बजट अप्रूव हो गया", [["budget", "approve"]]),
    ("hi", "सर्वर डाउन है", [["server", "down"]]),
    ("hi", "अकाउंट में बैलेंस चेक करो", [["account"], ["balance"], ["check"]]),

    # === Bengali (bn) ===
    ("bn", "মিটিং ক্যান্সেল হয়ে গেছে", [["meeting", "cancel"]]),
    ("bn", "প্লিজ ডকুমেন্ট শেয়ার করো", [["please", "document", "share"]]),
    ("bn", "অফিসে ইন্টারনেট স্লো", [["office", "internet", "slow"]]),
    ("bn", "প্রজেক্ট রেডি আছে", [["project", "ready"]]),
    ("bn", "টিমকে মেসেজ পাঠাও", [["team"], ["message"]]),

    # === Tamil (ta) ===
    ("ta", "மீட்டிங் கேன்சல் ஆயிடுச்சு", [["meeting", "cancel"]]),
    ("ta", "ப்ளீஸ் டாக்குமென்ட் ஷேர் பண்ணுங்க", [["please", "document", "share"]]),
    ("ta", "ஆபிஸ்ல இன்டர்நெட் ஸ்லோ", [["office", "internet", "slow"]]),
    ("ta", "புராஜெக்ட் ரெடி", [["project", "ready"]]),
    ("ta", "டீம்கிட்ட மெசேஜ் அனுப்புங்க", [["team"], ["message"]]),

    # === Telugu (te) ===
    ("te", "మీటింగ్ క్యాన్సెల్ అయింది", [["meeting", "cancel"]]),
    ("te", "ప్లీజ్ డాక్యుమెంట్ షేర్ చేయండి", [["please", "document", "share"]]),
    ("te", "ఆఫీస్లో ఇంటర్నెట్ స్లో", [["office", "internet", "slow"]]),
    ("te", "ప్రాజెక్ట్ రెడీ ఉంది", [["project", "ready"]]),
    ("te", "రిపోర్ట్ సబ్మిట్ చేయండి", [["report", "submit"]]),

    # === Kannada (kn) ===
    ("kn", "ಮೀಟಿಂಗ್ ಕ್ಯಾನ್ಸಲ್ ಆಗಿದೆ", [["meeting", "cancel"]]),
    ("kn", "ಪ್ಲೀಸ್ ಡಾಕ್ಯುಮೆಂಟ್ ಶೇರ್ ಮಾಡಿ", [["please", "document", "share"]]),
    ("kn", "ಆಫೀಸ್\u200cನಲ್ಲಿ ಇಂಟರ್ನೆಟ್ ಸ್ಲೋ", [["internet", "slow"]]),
    ("kn", "ಪ್ರಾಜೆಕ್ಟ್ ರೆಡಿ ಇದೆ", [["project", "ready"]]),
    ("kn", "ರಿಪೋರ್ಟ್ ಸಬ್ಮಿಟ್ ಮಾಡಿ", [["report", "submit"]]),

    # === Gujarati (gu) ===
    ("gu", "મીટિંગ કેન્સલ થઈ ગઈ છે", [["meeting", "cancel"]]),
    ("gu", "પ્લીઝ ડોક્યુમેન્ટ શેર કરો", [["please", "document", "share"]]),
    ("gu", "ઓફિસમાં ઇન્ટરનેટ સ્લો છે", [["office", "internet", "slow"]]),
    ("gu", "પ્રોજેક્ટ રેડી છે", [["project", "ready"]]),
    ("gu", "રિપોર્ટ સબમિટ કરો", [["report", "submit"]]),

    # === Punjabi (pa) ===
    ("pa", "ਮੀਟਿੰਗ ਕੈਂਸਲ ਹੋ ਗਈ ਹੈ", [["meeting", "cancel"]]),
    ("pa", "ਪਲੀਜ਼ ਡਾਕੂਮੈਂਟ ਸ਼ੇਅਰ ਕਰੋ", [["please", "document", "share"]]),
    ("pa", "ਆਫ਼ਿਸ ਵਿੱਚ ਇੰਟਰਨੈੱਟ ਸਲੋ ਹੈ", [["internet", "slow"]]),
    ("pa", "ਪ੍ਰੋਜੈਕਟ ਰੈਡੀ ਹੈ", [["project", "ready"]]),
    ("pa", "ਰਿਪੋਰਟ ਸਬਮਿਟ ਕਰੋ", [["report", "submit"]]),

    # === Marathi (mr) ===
    ("mr", "मीटिंग कॅन्सल झाली", [["meeting", "cancel"]]),
    ("mr", "प्लीज डॉक्युमेंट शेअर करा", [["please", "document", "share"]]),
    ("mr", "ऑफिसमध्ये इंटरनेट स्लो आहे", [["office", "internet", "slow"]]),
    ("mr", "प्रोजेक्ट रेडी आहे", [["project", "ready"]]),
    ("mr", "रिपोर्ट सबमिट करा", [["report", "submit"]]),
]

LANG_NAMES = {
    "hi": "Hindi", "bn": "Bengali", "ta": "Tamil", "te": "Telugu",
    "kn": "Kannada", "gu": "Gujarati", "pa": "Punjabi", "mr": "Marathi",
}

# Run all tests
results = []  # (lang, input, output, found_words, missing_words, passed)
lang_stats = {}  # lang -> [total, passed]

for lang, input_text, expected_groups in TEST_CASES:
    try:
        output = restorer.restore(input_text, lang=lang)
    except Exception as e:
        output = f"ERROR: {e}"

    output_lower = output.lower()

    all_found = []
    all_missing = []
    passed = True

    for group in expected_groups:
        for word in group:
            if word.lower() in output_lower:
                all_found.append(word)
            else:
                all_missing.append(word)
                passed = False

    results.append((lang, input_text, output, all_found, all_missing, passed))

    if lang not in lang_stats:
        lang_stats[lang] = [0, 0]
    lang_stats[lang][0] += 1
    if passed:
        lang_stats[lang][1] += 1

# Print results table
SEP = "=" * 160
THIN_SEP = "-" * 160

print(SEP)
print(f"{'#':<4} {'Lang':<10} {'Input':<45} {'Output':<45} {'Found Words':<25} {'Missing Words':<25} {'Result':<6}")
print(SEP)

current_lang = None
for idx, (lang, inp, out, found, missing, passed) in enumerate(results, 1):
    if lang != current_lang:
        if current_lang is not None:
            print(THIN_SEP)
        current_lang = lang
        print(f"  >>> {LANG_NAMES.get(lang, lang)} ({lang}) <<<")
        print(THIN_SEP)

    # Truncate long strings for display
    inp_disp = inp[:43] + ".." if len(inp) > 45 else inp
    out_disp = out[:43] + ".." if len(out) > 45 else out
    found_str = ", ".join(found) if found else "-"
    missing_str = ", ".join(missing) if missing else "-"
    status = "PASS" if passed else "FAIL"

    print(f"{idx:<4} {LANG_NAMES.get(lang, lang):<10} {inp_disp:<45} {out_disp:<45} {found_str:<25} {missing_str:<25} {status:<6}")

print(SEP)

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

total_tests = len(results)
total_passed = sum(1 for r in results if r[5])
total_failed = total_tests - total_passed

print(f"\n{'Language':<15} {'Total':<10} {'Passed':<10} {'Failed':<10} {'Accuracy':<10}")
print("-" * 55)

for lang in ["hi", "bn", "ta", "te", "kn", "gu", "pa", "mr"]:
    if lang in lang_stats:
        total, passed = lang_stats[lang]
        failed = total - passed
        acc = (passed / total * 100) if total > 0 else 0
        print(f"{LANG_NAMES.get(lang, lang):<15} {total:<10} {passed:<10} {failed:<10} {acc:.1f}%")

print("-" * 55)
overall_acc = (total_passed / total_tests * 100) if total_tests > 0 else 0
print(f"{'OVERALL':<15} {total_tests:<10} {total_passed:<10} {total_failed:<10} {overall_acc:.1f}%")
print()
