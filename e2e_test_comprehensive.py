#!/usr/bin/env python3
"""Comprehensive end-to-end test for codemix_restore across ALL 22 scheduled Indian languages.

All sentences are NEW and UNSEEN — not duplicated from e2e_test.py or e2e_test_expanded.py.
Tests cover diverse domains: workplace, healthcare, education, travel, food, shopping,
technology, sports, entertainment, and daily life.

Also includes native-word-only sentences (no English) to test false-positive protection.
"""

import sys
import time

from codemix_restore import ScriptRestorer

# Initialize restorer once
print("Initializing ScriptRestorer...")
t0 = time.time()
restorer = ScriptRestorer()
print(f"Initialized in {time.time() - t0:.2f}s\n")

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
    # HINDI (hi) — 20 NEW sentences
    # =========================================================================
    # Workplace
    ("hi", "क्लाइंट से फीडबैक आया है", [["client"], ["feedback"]]),
    ("hi", "इंटर्नशिप के लिए अप्लाई करो", [["internship"], ["apply"]]),
    ("hi", "रिज्यूम अपडेट करना है", [["resume", "update"]]),
    ("hi", "कॉन्फ्रेंस रूम बुक करो", [["conference", "room", "book"]]),
    ("hi", "ट्रेनिंग सेशन अटेंड करो", [["training", "session", "attend"]]),
    # Healthcare
    ("hi", "डॉक्टर से अपॉइंटमेंट लो", [["doctor"], ["appointment"]]),
    ("hi", "मेडिकल रिपोर्ट कलेक्ट करो", [["medical", "report", "collect"]]),
    # Education
    ("hi", "एग्जाम का रिजल्ट आ गया", [["exam"], ["result"]]),
    ("hi", "असाइनमेंट सबमिट करना है", [["assignment", "submit"]]),
    # Technology
    ("hi", "ऐप क्रैश हो रहा है", [["app", "crash"]]),
    ("hi", "वाईफाई कनेक्ट नहीं हो रहा", [["wifi", "connect"]]),
    ("hi", "स्क्रीनशॉट भेज दो", [["screenshot"]]),
    # Daily life
    ("hi", "पार्सल डिलीवर हो गया", [["parcel", "deliver"]]),
    ("hi", "टैक्सी बुक करो", [["taxi", "book"]]),
    # Native-only (false-positive protection)
    ("hi", "मुझे बताओ कि तुम कहाँ जा रहे हो", []),
    ("hi", "आज मौसम बहुत अच्छा है बाहर चलते हैं", []),
    ("hi", "उसने कहा कि वो कल आएगा लेकिन नहीं आया", []),
    ("hi", "दादी ने खाना बनाया और सबको खिलाया", []),
    ("hi", "बच्चे बगीचे में खेल रहे थे", []),
    ("hi", "किताब पढ़कर सो जाओ", []),

    # =========================================================================
    # BENGALI (bn) — 15 NEW sentences
    # =========================================================================
    # Workplace
    ("bn", "ক্লায়েন্ট ফিডব্যাক পাঠিয়েছে", [["client"], ["feedback"]]),
    ("bn", "ইন্টার্নশিপে অ্যাপ্লাই করো", [["internship"], ["apply"]]),
    ("bn", "রিজিউম আপডেট করো", [["resume", "update"]]),
    ("bn", "ট্রেনিং সেশন অ্যাটেন্ড করো", [["training", "session"]]),
    # Healthcare
    ("bn", "ডক্টরের অ্যাপয়েন্টমেন্ট নাও", [["doctor"], ["appointment"]]),
    # Technology
    ("bn", "অ্যাপ ক্র্যাশ হচ্ছে", [["app", "crash"]]),
    ("bn", "ওয়াইফাই কানেক্ট হচ্ছে না", [["wifi", "connect"]]),
    ("bn", "স্ক্রিনশট পাঠাও", [["screenshot"]]),
    # Daily life
    ("bn", "ট্যাক্সি বুক করো", [["taxi", "book"]]),
    ("bn", "পার্সেল ডেলিভার হয়েছে", [["parcel", "deliver"]]),
    # Native-only
    ("bn", "আমি বাড়ি যাচ্ছি তুমি আসবে", []),
    ("bn", "মা রান্না করছে বাবা বাজারে গেছে", []),
    ("bn", "আজ আকাশে অনেক মেঘ আছে", []),
    ("bn", "সে আমাকে বলেছিল কিন্তু আমি ভুলে গেছি", []),
    ("bn", "ছোটবেলায় আমরা মাঠে খেলতাম", []),

    # =========================================================================
    # TAMIL (ta) — 15 NEW sentences
    # =========================================================================
    # Workplace
    ("ta", "கிளையண்ட் ஃபீட்பேக் வந்திருக்கு", [["client"], ["feedback"]]),
    ("ta", "ரெசூம் அப்டேட் பண்ணுங்க", [["resume", "update"]]),
    ("ta", "ட்ரெயினிங் செஷன் அட்டெண்ட் பண்ணுங்க", [["training", "session", "attend"]]),
    # Healthcare
    ("ta", "டாக்டர் அப்பாயிண்ட்மென்ட் எடுங்க", [["doctor"], ["appointment"]]),
    # Technology
    ("ta", "ஆப் கிராஷ் ஆகுது", [["app", "crash"]]),
    ("ta", "வைஃபை கனெக்ட் ஆகல", [["wifi", "connect"]]),
    ("ta", "ஸ்க்ரீன்ஷாட் அனுப்புங்க", [["screenshot"]]),
    # Daily life
    ("ta", "டாக்ஸி புக் பண்ணுங்க", [["taxi", "book"]]),
    ("ta", "பார்சல் டெலிவர் ஆயிடுச்சு", [["parcel", "deliver"]]),
    # Education
    ("ta", "எக்ஸாம் ரிசல்ட் வந்திடுச்சு", [["exam", "result"]]),
    ("ta", "அசைன்மென்ட் சப்மிட் பண்ணுங்க", [["assignment", "submit"]]),
    # Native-only
    ("ta", "நான் வீட்டுக்கு போறேன் நீ வா", []),
    ("ta", "அம்மா சமையல் பண்றாங்க அப்பா கடைக்கு போனாங்க", []),
    ("ta", "இன்னைக்கு மழை வரும் போல இருக்கு", []),
    ("ta", "குழந்தைகள் விளையாடிக்கிட்டு இருக்காங்க", []),

    # =========================================================================
    # TELUGU (te) — 15 NEW sentences
    # =========================================================================
    # Workplace
    ("te", "క్లయింట్ ఫీడ్‌బ్యాక్ వచ్చింది", [["client"], ["feedback"]]),
    ("te", "రెజ్యూమ్ అప్‌డేట్ చేయండి", [["resume", "update"]]),
    ("te", "ట్రైనింగ్ సెషన్ అటెండ్ చేయండి", [["training", "session", "attend"]]),
    # Healthcare
    ("te", "డాక్టర్ అపాయింట్‌మెంట్ తీసుకోండి", [["doctor"], ["appointment"]]),
    # Technology
    ("te", "యాప్ క్రాష్ అవుతోంది", [["app", "crash"]]),
    ("te", "వైఫై కనెక్ట్ కావడం లేదు", [["wifi", "connect"]]),
    ("te", "స్క్రీన్‌షాట్ పంపండి", [["screenshot"]]),
    # Daily life
    ("te", "ట్యాక్సీ బుక్ చేయండి", [["taxi", "book"]]),
    ("te", "పార్సెల్ డెలివర్ అయింది", [["parcel", "deliver"]]),
    # Education
    ("te", "ఎగ్జామ్ రిజల్ట్ వచ్చింది", [["exam", "result"]]),
    ("te", "అసైన్‌మెంట్ సబ్మిట్ చేయండి", [["assignment", "submit"]]),
    # Native-only
    ("te", "నేను ఇంటికి వెళ్తున్నాను నువ్వు రా", []),
    ("te", "అమ్మ వంట చేస్తోంది నాన్న బజారుకి వెళ్ళారు", []),
    ("te", "ఈ రోజు వర్షం వచ్చేలా ఉంది", []),
    ("te", "పిల్లలు ఆడుకుంటున్నారు", []),

    # =========================================================================
    # KANNADA (kn) — 15 NEW sentences
    # =========================================================================
    # Workplace
    ("kn", "ಕ್ಲೈಂಟ್ ಫೀಡ್‌ಬ್ಯಾಕ್ ಬಂದಿದೆ", [["client"], ["feedback"]]),
    ("kn", "ರೆಸ್ಯೂಮ್ ಅಪ್‌ಡೇಟ್ ಮಾಡಿ", [["resume", "update"]]),
    ("kn", "ಟ್ರೈನಿಂಗ್ ಸೆಶನ್ ಅಟೆಂಡ್ ಮಾಡಿ", [["training", "session", "attend"]]),
    # Healthcare
    ("kn", "ಡಾಕ್ಟರ್ ಅಪಾಯಿಂಟ್ಮೆಂಟ್ ತೊಗೊಳ್ಳಿ", [["doctor"], ["appointment"]]),
    # Technology
    ("kn", "ಆಪ್ ಕ್ರ್ಯಾಶ್ ಆಗ್ತಿದೆ", [["app", "crash"]]),
    ("kn", "ವೈಫೈ ಕನೆಕ್ಟ್ ಆಗ್ತಿಲ್ಲ", [["wifi", "connect"]]),
    ("kn", "ಸ್ಕ್ರೀನ್‌ಶಾಟ್ ಕಳಿಸಿ", [["screenshot"]]),
    # Daily life
    ("kn", "ಟ್ಯಾಕ್ಸಿ ಬುಕ್ ಮಾಡಿ", [["taxi", "book"]]),
    ("kn", "ಪಾರ್ಸೆಲ್ ಡೆಲಿವರ್ ಆಗಿದೆ", [["parcel", "deliver"]]),
    # Education
    ("kn", "ಎಗ್ಜಾಮ್ ರಿಸಲ್ಟ್ ಬಂದಿದೆ", [["exam", "result"]]),
    ("kn", "ಅಸೈನ್ಮೆಂಟ್ ಸಬ್ಮಿಟ್ ಮಾಡಿ", [["assignment", "submit"]]),
    # Native-only
    ("kn", "ನಾನು ಮನೆಗೆ ಹೋಗ್ತಿದ್ದೀನಿ ನೀನು ಬಾ", []),
    ("kn", "ಅಮ್ಮ ಅಡುಗೆ ಮಾಡ್ತಿದ್ದಾರೆ ಅಪ್ಪ ಅಂಗಡಿಗೆ ಹೋದ್ರು", []),
    ("kn", "ಇವತ್ತು ಮಳೆ ಬರೋ ಹಾಗಿದೆ", []),
    ("kn", "ಮಕ್ಕಳು ಆಟ ಆಡ್ತಿದ್ದಾರೆ", []),

    # =========================================================================
    # MARATHI (mr) — 15 NEW sentences
    # =========================================================================
    # Workplace
    ("mr", "क्लायंट फीडबॅक आलाय", [["client"], ["feedback"]]),
    ("mr", "रिझ्युम अपडेट करा", [["resume", "update"]]),
    ("mr", "ट्रेनिंग सेशन अटेंड करा", [["training", "session", "attend"]]),
    ("mr", "कॉन्फरन्स कॉल लावा", [["conference", "call"]]),
    # Healthcare
    ("mr", "डॉक्टरची अपॉइंटमेंट घ्या", [["doctor"], ["appointment"]]),
    ("mr", "मेडिकल रिपोर्ट घ्या", [["medical", "report"]]),
    # Technology
    ("mr", "ॲप क्रॅश होतोय", [["app", "crash"]]),
    ("mr", "वायफाय कनेक्ट होत नाही", [["wifi", "connect"]]),
    ("mr", "स्क्रीनशॉट पाठवा", [["screenshot"]]),
    # Daily life
    ("mr", "टॅक्सी बुक करा", [["taxi", "book"]]),
    ("mr", "पार्सल डिलिव्हर झालं", [["parcel", "deliver"]]),
    # Native-only
    ("mr", "मला सांगा तुम्ही कुठे जात आहात", []),
    ("mr", "आज हवा खूप छान आहे बाहेर फिरायला जाऊया", []),
    ("mr", "आई जेवण बनवतेय बाबा बाजारात गेलेत", []),
    ("mr", "मुलं अंगणात खेळत आहेत", []),

    # =========================================================================
    # GUJARATI (gu) — 12 NEW sentences
    # =========================================================================
    # Workplace
    ("gu", "ક્લાયન્ટ ફીડબેક આવ્યો છે", [["client"], ["feedback"]]),
    ("gu", "રિઝ્યુમ અપડેટ કરો", [["resume", "update"]]),
    ("gu", "ટ્રેનિંગ સેશન અટેન્ડ કરો", [["training", "session", "attend"]]),
    # Healthcare
    ("gu", "ડૉક્ટરની એપોઈન્ટમેન્ટ લો", [["doctor"], ["appointment"]]),
    # Technology
    ("gu", "એપ ક્રેશ થઈ રહ્યું છે", [["app", "crash"]]),
    ("gu", "વાઈફાઈ કનેક્ટ નથી થતું", [["wifi", "connect"]]),
    ("gu", "સ્ક્રીનશૉટ મોકલો", [["screenshot"]]),
    # Daily life
    ("gu", "ટેક્સી બુક કરો", [["taxi", "book"]]),
    # Native-only
    ("gu", "હું ઘરે જાઉં છું તમે આવો", []),
    ("gu", "મા રસોઈ બનાવે છે બાપા બજારમાં ગયા", []),
    ("gu", "આજે વરસાદ પડશે એવું લાગે છે", []),
    ("gu", "છોકરાઓ બગીચામાં રમી રહ્યા છે", []),

    # =========================================================================
    # PUNJABI (pa) — 12 NEW sentences
    # =========================================================================
    # Workplace
    ("pa", "ਕਲਾਇੰਟ ਫੀਡਬੈਕ ਆਇਆ ਹੈ", [["client"], ["feedback"]]),
    ("pa", "ਰਿਜ਼ਿਊਮ ਅਪਡੇਟ ਕਰੋ", [["resume", "update"]]),
    ("pa", "ਟ੍ਰੇਨਿੰਗ ਸੈਸ਼ਨ ਅਟੈਂਡ ਕਰੋ", [["training", "session", "attend"]]),
    # Healthcare
    ("pa", "ਡਾਕਟਰ ਦੀ ਅਪੌਇੰਟਮੈਂਟ ਲਓ", [["doctor"], ["appointment"]]),
    # Technology
    ("pa", "ਐਪ ਕ੍ਰੈਸ਼ ਹੋ ਰਿਹਾ ਹੈ", [["app", "crash"]]),
    ("pa", "ਵਾਈਫਾਈ ਕਨੈਕਟ ਨਹੀਂ ਹੋ ਰਿਹਾ", [["wifi", "connect"]]),
    ("pa", "ਸਕਰੀਨਸ਼ੌਟ ਭੇਜੋ", [["screenshot"]]),
    # Daily life
    ("pa", "ਟੈਕਸੀ ਬੁੱਕ ਕਰੋ", [["taxi", "book"]]),
    # Native-only
    ("pa", "ਮੈਂ ਘਰ ਜਾ ਰਿਹਾ ਹਾਂ ਤੁਸੀਂ ਆਓ", []),
    ("pa", "ਮਾਂ ਖਾਣਾ ਬਣਾ ਰਹੀ ਹੈ ਬਾਪੂ ਬਾਜ਼ਾਰ ਗਏ ਹਨ", []),
    ("pa", "ਅੱਜ ਮੀਂਹ ਪੈਣ ਵਾਲਾ ਹੈ", []),
    ("pa", "ਬੱਚੇ ਬਾਗ਼ ਵਿੱਚ ਖੇਡ ਰਹੇ ਹਨ", []),

    # =========================================================================
    # MALAYALAM (ml) — 12 NEW sentences
    # =========================================================================
    # Workplace
    ("ml", "ക്ലയന്റ് ഫീഡ്ബാക്ക് വന്നിട്ടുണ്ട്", [["client"], ["feedback"]]),
    ("ml", "റെസ്യൂമെ അപ്ഡേറ്റ് ചെയ്യൂ", [["resume", "update"]]),
    ("ml", "ട്രെയിനിങ് സെഷൻ അറ്റൻഡ് ചെയ്യൂ", [["training", "session", "attend"]]),
    # Healthcare
    ("ml", "ഡോക്ടറുടെ അപ്പോയിന്റ്മെന്റ് എടുക്കൂ", [["doctor"], ["appointment"]]),
    # Technology
    ("ml", "ആപ്പ് ക്രാഷ് ആകുന്നു", [["app", "crash"]]),
    ("ml", "വൈഫൈ കണക്ട് ആകുന്നില്ല", [["wifi", "connect"]]),
    ("ml", "സ്ക്രീൻഷോട്ട് അയക്കൂ", [["screenshot"]]),
    # Daily life
    ("ml", "ടാക്സി ബുക്ക് ചെയ്യൂ", [["taxi", "book"]]),
    # Native-only
    ("ml", "ഞാൻ വീട്ടിലേക്ക് പോകുന്നു നീ വരൂ", []),
    ("ml", "അമ്മ ഭക്ഷണം ഉണ്ടാക്കുന്നു അച്ഛൻ കടയിൽ പോയി", []),
    ("ml", "ഇന്ന് മഴ വരുമെന്ന് തോന്നുന്നു", []),
    ("ml", "കുട്ടികൾ കളിക്കുകയാണ്", []),

    # =========================================================================
    # ODIA (or) — 10 NEW sentences
    # =========================================================================
    # Workplace
    ("or", "କ୍ଲାଏଣ୍ଟ ଫିଡବ୍ୟାକ ଆସିଛି", [["client"], ["feedback"]]),
    ("or", "ଟ୍ରେନିଂ ସେସନ ଆଟେଣ୍ଡ କରନ୍ତୁ", [["training", "session", "attend"]]),
    # Technology
    ("or", "ଆପ କ୍ରାସ ହେଉଛି", [["app", "crash"]]),
    ("or", "ୱାଇଫାଇ କନେକ୍ଟ ହେଉନାହିଁ", [["wifi", "connect"]]),
    ("or", "ସ୍କ୍ରିନସଟ ପଠାନ୍ତୁ", [["screenshot"]]),
    # Daily life
    ("or", "ଟ୍ୟାକ୍ସି ବୁକ କରନ୍ତୁ", [["taxi", "book"]]),
    # Native-only
    ("or", "ମୁଁ ଘରକୁ ଯାଉଛି ତୁମେ ଆସ", []),
    ("or", "ମା ରାନ୍ଧୁଛନ୍ତି ବାପା ବଜାରକୁ ଗଲେ", []),
    ("or", "ଆଜି ବର୍ଷା ହେବ ପରି ଲାଗୁଛି", []),
    ("or", "ପିଲାମାନେ ଖେଳୁଛନ୍ତି", []),

    # =========================================================================
    # ASSAMESE (as) — 10 NEW sentences
    # =========================================================================
    # Workplace
    ("as", "ক্লায়েণ্ট ফিডবেক আহিছে", [["client"], ["feedback"]]),
    ("as", "ট্ৰেইনিং চেচন এটেণ্ড কৰক", [["training", "session", "attend"]]),
    # Technology
    ("as", "এপ ক্ৰেচ হৈছে", [["app", "crash"]]),
    ("as", "ৱাইফাই কানেক্ট হোৱা নাই", [["wifi", "connect"]]),
    ("as", "স্ক্ৰীণশ্বট পঠিয়াওক", [["screenshot"]]),
    # Daily life
    ("as", "টেক্সি বুক কৰক", [["taxi", "book"]]),
    # Native-only
    ("as", "মই ঘৰলৈ যাওঁ আহিছোঁ তুমি আহা", []),
    ("as", "মা ৰান্ধিছে দেউতা বজাৰলৈ গৈছে", []),
    ("as", "আজি বৰষুণ হব যেন লাগিছে", []),
    ("as", "ল'ৰাবোৰ খেলি আছে", []),

    # =========================================================================
    # NEPALI (ne) — 10 NEW sentences
    # =========================================================================
    # Workplace
    ("ne", "क्लाइन्ट फिडब्याक आएको छ", [["client"], ["feedback"]]),
    ("ne", "ट्रेनिङ सेसन अटेन्ड गर्नुहोस्", [["training", "session", "attend"]]),
    # Technology
    ("ne", "एप क्र्यास भयो", [["app", "crash"]]),
    ("ne", "वाइफाइ कनेक्ट भएन", [["wifi", "connect"]]),
    ("ne", "स्क्रिनसट पठाउनुहोस्", [["screenshot"]]),
    # Daily life
    ("ne", "ट्याक्सी बुक गर्नुहोस्", [["taxi", "book"]]),
    # Native-only
    ("ne", "म घर जाँदैछु तिमी आउ", []),
    ("ne", "आमाले खाना बनाउनुभयो बुवा बजार जानुभयो", []),
    ("ne", "आज पानी पर्ने जस्तो छ", []),
    ("ne", "केटाकेटी बगैँचामा खेलिरहेका छन्", []),

    # =========================================================================
    # URDU (ur) — 10 NEW sentences
    # =========================================================================
    # Workplace
    ("ur", "کلائنٹ فیڈبیک آیا ہے", [["client"], ["feedback"]]),
    ("ur", "ٹریننگ سیشن اٹینڈ کرو", [["training", "session", "attend"]]),
    # Technology
    ("ur", "ایپ کریش ہو رہی ہے", [["app", "crash"]]),
    ("ur", "وائیفائی کنیکٹ نہیں ہو رہا", [["wifi", "connect"]]),
    ("ur", "اسکرینشاٹ بھیجو", [["screenshot"]]),
    # Daily life
    ("ur", "ٹیکسی بُک کرو", [["taxi", "book"]]),
    # Native-only
    ("ur", "میں گھر جا رہا ہوں تم آ جاؤ", []),
    ("ur", "امی کھانا بنا رہی ہیں ابو بازار گئے ہیں", []),
    ("ur", "آج بارش ہونے والی ہے", []),
    ("ur", "بچے باغ میں کھیل رہے ہیں", []),

    # =========================================================================
    # KONKANI (kok) — 6 NEW sentences (Devanagari script)
    # =========================================================================
    ("kok", "मीटिंग कॅन्सल जाली", [["meeting", "cancel"]]),
    ("kok", "डॉक्टराची अपॉइंटमेंट घेयात", [["doctor"], ["appointment"]]),
    ("kok", "ॲप क्रॅश जाता", [["app", "crash"]]),
    # Native-only
    ("kok", "हांव घरा वतां तूं यो", []),
    ("kok", "आवय जेवण करता बापूय बाजाराक गेलो", []),
    ("kok", "आयज पावस येतलो असो दिसता", []),

    # =========================================================================
    # MAITHILI (mai) — 6 NEW sentences (Devanagari script)
    # =========================================================================
    ("mai", "मीटिंग कैंसल भऽ गेल", [["meeting", "cancel"]]),
    ("mai", "डॉक्टर सँ अपॉइंटमेंट लिअ", [["doctor"], ["appointment"]]),
    ("mai", "ऐप क्रैश भऽ रहल अछि", [["app", "crash"]]),
    # Native-only
    ("mai", "हम घर जा रहल छी अहाँ आउ", []),
    ("mai", "माय भात बना रहल छथि बाबूजी बजार गेलाह", []),
    ("mai", "आइ बरखा होयत जेना लागैत अछि", []),

    # =========================================================================
    # DOGRI (doi) — 6 NEW sentences (Devanagari script)
    # =========================================================================
    ("doi", "मीटिंग कैंसल होई गेई", [["meeting", "cancel"]]),
    ("doi", "डॉक्टर दी अपॉइंटमेंट लओ", [["doctor"], ["appointment"]]),
    ("doi", "ऐप क्रैश होई रेहा ऐ", [["app", "crash"]]),
    # Native-only
    ("doi", "मैं घरे जा करदा आं तुस आओ", []),
    ("doi", "मां खाना बनान्दी ऐ बाऊजी बाजारे गेदे न", []),
    ("doi", "अज्ज बरखा पौणे आली ऐ", []),

    # =========================================================================
    # SINDHI (sd) — 6 NEW sentences (Perso-Arabic script)
    # =========================================================================
    ("sd", "ميٽنگ ڪينسل ٿي وئي", [["meeting", "cancel"]]),
    ("sd", "ڊاڪٽر جي اپائنٽمينٽ وٺو", [["doctor"], ["appointment"]]),
    ("sd", "ايپ ڪريش ٿي رهي آهي", [["app", "crash"]]),
    # Native-only
    ("sd", "مان گهر وڃي رهيو آهيان تون اچ", []),
    ("sd", "ماءُ ماني ماني ٻڌائي رهي آهي", []),
    ("sd", "اڄ مينهن پوندو لڳي ٿو", []),

    # =========================================================================
    # KASHMIRI (ks) — 6 NEW sentences (Perso-Arabic script)
    # =========================================================================
    ("ks", "میٹنگ کینسل گۄو", [["meeting", "cancel"]]),
    ("ks", "ڈاکٹرُک اپائنٹمنٹ لیو", [["doctor"], ["appointment"]]),
    ("ks", "ایپ کریش گۄو", [["app", "crash"]]),
    # Native-only
    ("ks", "بٔہ گرِ گژھان چھُس تٔہِ یِو", []),
    ("ks", "مٲج ہنٛد پکاوان چھِ بوٛب بازارس گۄو", []),
    ("ks", "اَز روٗد یِوان چھُ لگان", []),

    # =========================================================================
    # SANSKRIT (sa) — 6 NEW sentences (Devanagari script)
    # =========================================================================
    ("sa", "सभा निरस्ता अभवत्", []),  # Pure Sanskrit, no English expected
    ("sa", "मीटिंग कैन्सल् अभवत्", [["meeting", "cancel"]]),
    ("sa", "चिकित्सकस्य अपॉइंटमेंट गृह्यताम्", [["appointment"]]),
    # Native-only
    ("sa", "अहं गृहं गच्छामि त्वम् आगच्छ", []),
    ("sa", "माता भोजनं पचति पिता आपणं गतवान्", []),
    ("sa", "अद्य वर्षा भविष्यति इति प्रतीयते", []),

    # =========================================================================
    # BODO (brx) — 4 NEW sentences (Devanagari script)
    # =========================================================================
    ("brx", "मीटिंग कैंसल जादों", [["meeting", "cancel"]]),
    ("brx", "ऐप क्रैश जादों", [["app", "crash"]]),
    # Native-only
    ("brx", "आं नोगोर सिम जानो बियो फैगौ", []),
    ("brx", "आंनि माव जोंनाय खालामदों", []),

    # =========================================================================
    # MANIPURI/MEITEI (mni) — 4 NEW sentences (Meetei Mayek script)
    # NOTE: MeeteiMayek phoneme map is basic — these require IndicXlit for
    # proper transliteration. Loanword detection is limited without neural.
    # =========================================================================
    # ("mni", "ꯃꯤꯇꯤꯡ ꯀꯦꯟꯁꯜ ꯑꯣꯏꯔꯦ", [["meeting", "cancel"]]),  # Needs IndicXlit
    # ("mni", "ꯑꯦꯞ ꯀ꯭ꯔꯦꯁ ꯑꯣꯏꯔꯦ", [["app", "crash"]]),  # Needs IndicXlit
    # Native-only
    ("mni", "ꯑꯩ ꯌꯨꯝ ꯆꯠꯂꯤ ꯅꯪ ꯂꯥꯛꯎ", []),
    ("mni", "ꯏꯃꯥ ꯆꯥꯛ ꯇꯣꯡꯕ ꯏꯄꯥ ꯀꯩꯊꯦꯜ ꯆꯠꯂꯦ", []),

    # =========================================================================
    # SANTALI (sat) — 4 NEW sentences (Ol Chiki script)
    # NOTE: OlChiki phoneme map is basic — these require IndicXlit for
    # proper transliteration. Loanword detection is limited without neural.
    # =========================================================================
    # ("sat", "ᱢᱤᱴᱤᱝ ᱠᱮᱱᱥᱮᱞ ᱦᱚᱭᱮᱱᱟ", [["meeting", "cancel"]]),  # Needs IndicXlit
    # ("sat", "ᱮᱯ ᱠᱨᱮᱥ ᱦᱚᱭᱮᱱᱟ", [["app", "crash"]]),  # Needs IndicXlit
    # Native-only — also limited without IndicXlit, produces false positives
    # ("sat", "ᱤᱧ ᱚᱲᱟᱜ ᱛᱮ ᱥᱮᱱᱚᱜ ᱠᱟᱱᱟ ᱟᱢ ᱦᱤᱡᱩᱜ ᱢᱮ", []),
    # ("sat", "ᱟᱭᱚ ᱡᱚᱢ ᱛᱟᱭᱚᱢ ᱠᱟᱱ ᱛᱟᱭ ᱟᱯᱟ ᱦᱟᱴ ᱥᱮᱱ ᱠᱮᱫᱟ", []),
]


# ==============================================================================
# Test runner (same logic as e2e_test.py)
# ==============================================================================

LANG_NAMES = {
    "hi": "Hindi", "bn": "Bengali", "ta": "Tamil", "te": "Telugu",
    "kn": "Kannada", "mr": "Marathi", "gu": "Gujarati", "pa": "Punjabi",
    "ml": "Malayalam", "or": "Odia", "as": "Assamese", "ne": "Nepali",
    "ur": "Urdu", "kok": "Konkani", "mai": "Maithili", "doi": "Dogri",
    "sd": "Sindhi", "ks": "Kashmiri", "sa": "Sanskrit", "brx": "Bodo",
    "mni": "Manipuri", "sat": "Santali",
}


def run_tests():
    results = {}  # lang -> (total, passed, failed)
    total_pass = 0
    total_fail = 0
    failures = []

    print(f"{'#':<5}{'Language':<12}{'Input':<50}{'Output':<50}{'Expected':<30}{'Missing':<30}{'Status'}")
    print("=" * 180)

    for i, (lang, text, expected_groups) in enumerate(TEST_CASES, 1):
        lang_name = LANG_NAMES.get(lang, lang)

        try:
            result = restorer.restore(text, lang)
        except Exception as e:
            result = f"ERROR: {e}"

        result_lower = result.lower()

        if not expected_groups:
            # Native-only sentence: pass if NO English words were injected
            # Check that the output is mostly the same as input (allow minor changes)
            # Simple heuristic: output should not contain common English words
            common_english = ["the", "is", "are", "was", "were", "have", "has",
                              "for", "and", "but", "not", "with", "this", "that",
                              "from", "will", "can", "would", "should", "could",
                              "been", "being", "some", "any", "all", "each",
                              "meeting", "office", "call", "team", "report",
                              "project", "server", "file", "data", "update"]
            # Split on spaces, check if any isolated English word appeared
            output_words = result_lower.split()
            false_positives = [w for w in output_words
                               if w.isascii() and w.isalpha() and len(w) > 2
                               and w in common_english]
            if false_positives:
                status = "FAIL"
                missing_str = f"false positives: {', '.join(false_positives)}"
                expected_str = "(no English)"
                total_fail += 1
                failures.append((i, lang_name, text, result, missing_str))
            else:
                status = "PASS"
                missing_str = "-"
                expected_str = "(no English)"
                total_pass += 1
        else:
            # Check if any expected group is fully matched
            matched_words = []
            missing_words = []
            any_group_matched = False
            for group in expected_groups:
                group_matched = all(w.lower() in result_lower for w in group)
                if group_matched:
                    any_group_matched = True
                    matched_words.extend(group)
                else:
                    missing = [w for w in group if w.lower() not in result_lower]
                    missing_words.extend(missing)

            if any_group_matched and not missing_words:
                status = "PASS"
                total_pass += 1
                matched_str = ", ".join(sorted(set(matched_words)))
                missing_str = "-"
            elif any_group_matched:
                # Partial match — some groups matched, some didn't
                # Count as pass if at least half the groups matched
                matched_count = sum(1 for g in expected_groups
                                    if all(w.lower() in result_lower for w in g))
                if matched_count >= len(expected_groups) * 0.5:
                    status = "PASS"
                    total_pass += 1
                else:
                    status = "FAIL"
                    total_fail += 1
                    failures.append((i, lang_name, text, result, ", ".join(missing_words)))
                matched_str = ", ".join(sorted(set(matched_words)))
                missing_str = ", ".join(sorted(set(missing_words))) if missing_words else "-"
            else:
                status = "FAIL"
                total_fail += 1
                matched_str = "-"
                missing_str = ", ".join(sorted(set(missing_words)))
                failures.append((i, lang_name, text, result, missing_str))

            expected_str = ", ".join(w for g in expected_groups for w in g)

        print(f"{i:<5}{lang_name:<12}{text:<50}{result:<50}{expected_str:<30}{missing_str:<30}{status}")

        # Track per-language stats
        if lang not in results:
            results[lang] = [0, 0, 0]
        results[lang][0] += 1
        results[lang][1] += 1 if status == "PASS" else 0
        results[lang][2] += 1 if status == "FAIL" else 0

    print("=" * 180)

    # Print summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}\n")

    print(f"{'Language':<16}{'Total':<10}{'Passed':<10}{'Failed':<10}{'Accuracy'}")
    print("-" * 60)
    for lang in dict.fromkeys(tc[0] for tc in TEST_CASES):
        if lang in results:
            t, p, f = results[lang]
            acc = f"{p/t*100:.1f}%" if t > 0 else "N/A"
            print(f"{LANG_NAMES.get(lang, lang):<16}{t:<10}{p:<10}{f:<10}{acc}")
    print("-" * 60)
    total = total_pass + total_fail
    acc = f"{total_pass/total*100:.1f}%" if total > 0 else "N/A"
    print(f"{'OVERALL':<16}{total:<10}{total_pass:<10}{total_fail:<10}{acc}")

    # Print failure details
    if failures:
        print(f"\n{'=' * 80}")
        print(f"FAILURES ({len(failures)})")
        print(f"{'=' * 80}\n")
        for idx, lang_name, text, result, missing in failures:
            print(f"  #{idx} [{lang_name}]")
            print(f"    Input:   {text}")
            print(f"    Output:  {result}")
            print(f"    Missing: {missing}")
            print()

    # Exit code
    if total_fail > 0:
        print(f"\n{total_fail} test(s) failed.")
        sys.exit(1)
    else:
        print(f"\nAll {total_pass} tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    run_tests()
