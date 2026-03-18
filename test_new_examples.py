"""
Comprehensive test examples for codemix_restore ScriptRestorer.

Covers: all major languages, diverse domains (tech, business, medical,
casual, academic), edge cases (abbreviations, numbers, punctuation,
long sentences, single words), and varying code-mix densities.
"""

from codemix_restore import ScriptRestorer

restorer = ScriptRestorer()
print("Neural available:", restorer._neural.is_available if restorer._neural else False)
print("=" * 80)

results = []
test_num = 0


def test(text, lang, expected=None, description=""):
    global test_num
    test_num += 1
    result = restorer.restore(text, lang=lang)
    status = ""
    if expected:
        status = " PASS" if result == expected else " FAIL"
        if status == " FAIL":
            status += f"\n   EXPECTED: {expected}"
    results.append((test_num, lang, status, description))
    print(f"T{test_num:03d} [{lang:>3}] {description}")
    print(f"   IN:  {text}")
    print(f"   OUT: {result}{status}")
    print()
    return result


# =============================================================================
# HINDI (hi) - Devanagari
# =============================================================================
print("--- HINDI (hi) ---")

test("मुझे ईमेल सेंड कर दो", "hi",
     description="Simple: send email")

test("प्लीज अपॉइंटमेंट रीशेड्यूल कर दो", "hi",
     description="Business: reschedule appointment")

test("सर्वर डाउन है, इमीजिएटली फिक्स करो", "hi",
     description="Tech: server down fix")

test("डेटाबेस बैकअप कंप्लीट हो गया है", "hi",
     description="Tech: database backup complete")

test("कस्टमर ने कंप्लेंट फाइल की है प्रोडक्ट क्वालिटी के बारे में", "hi",
     description="Business: customer complaint about product quality")

test("पेशेंट का ब्लड प्रेशर हाई है, इमीजिएटली डॉक्टर को कॉल करो", "hi",
     description="Medical: blood pressure high, call doctor")

test("ऑनलाइन पेमेंट फेल हो गया, ट्रांजैक्शन आईडी चेक करो", "hi",
     description="Finance: online payment failed")

test("एपीआई रिस्पॉन्स टाइम बहुत स्लो है", "hi",
     description="Tech: API response time slow")

test("मैं कल ऑफिस में लेट आऊंगा, प्लीज मीटिंग पोस्टपोन कर दो", "hi",
     description="Casual: late to office, postpone meeting")

test("प्रोजेक्ट डेडलाइन नेक्स्ट फ्राइडे है", "hi",
     description="Business: project deadline next friday")

test("यूनिट टेस्ट फेल हो रहे हैं, बिल्ड ब्रेक हो गया", "hi",
     description="Tech: unit tests failing, build broken")

test("रिज्यूम अपडेट कर के एचआर को सबमिट कर दो", "hi",
     description="HR: update resume and submit")

test("कस्टमर सपोर्ट टीम को ट्रेनिंग शेड्यूल करो", "hi",
     description="Business: schedule customer support training")

test("लैपटॉप की स्क्रीन क्रैक हो गई है, वारंटी क्लेम करो", "hi",
     description="Casual: laptop screen cracked, warranty claim")

test("पासवर्ड रीसेट करो और टू फैक्टर ऑथेंटिकेशन इनेबल करो", "hi",
     description="Tech: password reset + 2FA")

test("मार्केटिंग कैम्पेन का बजट अप्रूव हो गया है", "hi",
     description="Business: marketing campaign budget approved")

test("गिट पुल करो और लेटेस्ट ब्रांच पर मर्ज करो", "hi",
     description="Tech: git pull and merge")

test("इंटरव्यू कैंडिडेट का फीडबैक शेयर करो", "hi",
     description="HR: share interview candidate feedback")

test("वेबसाइट पर ट्रैफिक बहुत इंक्रीज हो गया है", "hi",
     description="Tech: website traffic increased")

test("ये बग क्रिटिकल है, प्रायोरिटी वन पर सेट करो", "hi",
     description="Tech: critical bug, set priority one")

# =============================================================================
# BENGALI (bn) - Bengali script
# =============================================================================
print("--- BENGALI (bn) ---")

test("প্লিজ ডকুমেন্ট আপডেট করো", "bn",
     description="Simple: update document")

test("সফটওয়্যার আপডেট ইনস্টল করো", "bn",
     description="Tech: install software update")

test("প্রোজেক্ট রিপোর্ট সাবমিট করতে হবে", "bn",
     description="Business: submit project report")

test("অনলাইন ক্লাস স্টার্ট হয়ে গেছে", "bn",
     description="Education: online class started")

test("সার্ভার মেইনটেনেন্স এর জন্য ডাউনটাইম হবে", "bn",
     description="Tech: server maintenance downtime")

test("কাস্টমার ফিডব্যাক অ্যানালাইসিস কমপ্লিট", "bn",
     description="Business: customer feedback analysis complete")

test("ব্যাংক অ্যাকাউন্ট ভেরিফাই করো", "bn",
     description="Finance: verify bank account")

test("ডেলিভারি ট্র্যাকিং নম্বর শেয়ার করো", "bn",
     description="Logistics: share delivery tracking number")

test("পাসওয়ার্ড চেঞ্জ করো, সিকিউরিটি ইস্যু আছে", "bn",
     description="Tech: change password, security issue")

test("টিম মিটিং রিশিডিউল করতে হবে", "bn",
     description="Business: reschedule team meeting")

# =============================================================================
# TAMIL (ta) - Tamil script
# =============================================================================
print("--- TAMIL (ta) ---")

test("சாப்ட்வேர் அப்டேட் இன்ஸ்டால் பண்ணுங்க", "ta",
     description="Tech: install software update")

test("ப்ராஜெக்ட் ரிப்போர்ட் சப்மிட் பண்ணணும்", "ta",
     description="Business: submit project report")

test("ஆன்லைன் பேமெண்ட் ஃபெயில் ஆயிடுச்சு", "ta",
     description="Finance: online payment failed")

test("டேட்டாபேஸ் பேக்கப் கம்ப்ளீட் ஆயிடுச்சு", "ta",
     description="Tech: database backup complete")

test("கஸ்டமர் சப்போர்ட் டிக்கெட் க்ளோஸ் பண்ணுங்க", "ta",
     description="Business: close customer support ticket")

test("லாப்டாப் ரிப்பேர் ஆகணும், சர்வீஸ் சென்டர் போகணும்", "ta",
     description="Casual: laptop repair, go to service center")

test("நெட்வொர்க் கனெக்ஷன் ஸ்லோ ஆ இருக்கு", "ta",
     description="Tech: network connection slow")

test("இன்டர்வியூ கால் மிஸ் ஆயிடுச்சு", "ta",
     description="HR: missed interview call")

test("பஜெட் அப்ரூவல் பெண்டிங் ல இருக்கு", "ta",
     description="Finance: budget approval pending")

test("ஸெக்யூரிட்டி ஆடிட் ரிசல்ட் ரெடி", "ta",
     description="Tech: security audit result ready")

# =============================================================================
# TELUGU (te) - Telugu script
# =============================================================================
print("--- TELUGU (te) ---")

test("సాఫ్ట్‌వేర్ అప్‌డేట్ ఇన్‌స్టాల్ చేయండి", "te",
     description="Tech: install software update")

test("ప్రాజెక్ట్ రిపోర్ట్ సబ్మిట్ చేయాలి", "te",
     description="Business: submit project report")

test("ఆన్‌లైన్ మీటింగ్ స్టార్ట్ అయింది", "te",
     description="Business: online meeting started")

test("నెట్‌వర్క్ ప్రాబ్లెమ్ వల్ల కనెక్ట్ అవ్వట్లేదు", "te",
     description="Tech: network problem, can't connect")

test("కస్టమర్ ఫీడ్‌బ్యాక్ అనాలిసిస్ చేయండి", "te",
     description="Business: analyze customer feedback")

test("డేటాబేస్ మైగ్రేషన్ కంప్లీట్ అయింది", "te",
     description="Tech: database migration complete")

test("బ్యాంక్ ట్రాన్సాక్షన్ ఫెయిల్ అయింది", "te",
     description="Finance: bank transaction failed")

test("రిజ్యూమ్ అప్‌డేట్ చేసి సెండ్ చేయండి", "te",
     description="HR: update and send resume")

test("సెక్యూరిటీ పాచ్ అప్లై చేయాలి", "te",
     description="Tech: apply security patch")

test("బగ్ ఫిక్స్ డిప్లాయ్ చేయండి", "te",
     description="Tech: deploy bug fix")

# =============================================================================
# KANNADA (kn) - Kannada script
# =============================================================================
print("--- KANNADA (kn) ---")

test("ಸಾಫ್ಟ್‌ವೇರ್ ಅಪ್‌ಡೇಟ್ ಮಾಡಿ", "kn",
     description="Tech: do software update")

test("ಮೀಟಿಂಗ್ ಕ್ಯಾನ್ಸಲ್ ಆಗಿದೆ", "kn",
     description="Business: meeting cancelled")

test("ಪ್ರಾಜೆಕ್ಟ್ ಡೆಡ್‌ಲೈನ್ ಮಿಸ್ ಆಗ್ತಿದೆ", "kn",
     description="Business: project deadline being missed")

test("ಆನ್‌ಲೈನ್ ಪೇಮೆಂಟ್ ಪ್ರಾಸೆಸ್ ಆಗ್ತಿಲ್ಲ", "kn",
     description="Finance: online payment not processing")

test("ಕಸ್ಟಮರ್ ಕಂಪ್ಲೇಂಟ್ ರೆಜಿಸ್ಟರ್ ಆಗಿದೆ", "kn",
     description="Business: customer complaint registered")

test("ಸರ್ವರ್ ರೀಸ್ಟಾರ್ಟ್ ಮಾಡಬೇಕು", "kn",
     description="Tech: server needs restart")

test("ಡಾಕ್ಯುಮೆಂಟ್ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ", "kn",
     description="Simple: upload document")

test("ನೆಟ್‌ವರ್ಕ್ ಸೆಕ್ಯುರಿಟಿ ಚೆಕ್ ಮಾಡಿ", "kn",
     description="Tech: check network security")

# =============================================================================
# MALAYALAM (ml) - Malayalam script
# =============================================================================
print("--- MALAYALAM (ml) ---")

test("സോഫ്റ്റ്‌വെയർ അപ്ഡേറ്റ് ഇൻസ്റ്റാൾ ചെയ്യൂ", "ml",
     description="Tech: install software update")

test("മീറ്റിംഗ് ക്യാൻസൽ ആയി", "ml",
     description="Business: meeting cancelled")

test("ഓൺലൈൻ പേയ്മെന്റ് ഫെയിൽ ആയി", "ml",
     description="Finance: online payment failed")

test("പ്രൊജക്ട് റിപ്പോർട്ട് സബ്മിറ്റ് ചെയ്യണം", "ml",
     description="Business: submit project report")

test("ഡാറ്റാബേസ് ബാക്കപ്പ് കംപ്ലീറ്റ് ആയി", "ml",
     description="Tech: database backup complete")

test("കസ്റ്റമർ സപ്പോർട്ട് ടിക്കറ്റ് ക്ലോസ് ചെയ്യൂ", "ml",
     description="Business: close customer support ticket")

test("പാസ്‌വേഡ് റീസെറ്റ് ചെയ്യൂ", "ml",
     description="Tech: reset password")

test("നെറ്റ്‌വർക്ക് കണക്ഷൻ പ്രോബ്ലം ഉണ്ട്", "ml",
     description="Tech: network connection problem")

# =============================================================================
# MARATHI (mr) - Devanagari
# =============================================================================
print("--- MARATHI (mr) ---")

test("सॉफ्टवेअर अपडेट इन्स्टॉल करा", "mr",
     description="Tech: install software update")

test("मीटिंग कॅन्सल झाली आहे", "mr",
     description="Business: meeting cancelled")

test("प्रोजेक्ट रिपोर्ट सबमिट करायची आहे", "mr",
     description="Business: submit project report")

test("ऑनलाइन पेमेंट फेल झाले", "mr",
     description="Finance: online payment failed")

test("कस्टमर फीडबॅक अॅनालिसिस पूर्ण झाले", "mr",
     description="Business: customer feedback analysis done")

test("सर्व्हर डाउन आहे, इमीजिएटली फिक्स करा", "mr",
     description="Tech: server down, fix immediately")

test("डेटाबेस मायग्रेशन कम्प्लीट झाले", "mr",
     description="Tech: database migration complete")

test("पासवर्ड चेंज करा, सिक्युरिटी इश्यू आहे", "mr",
     description="Tech: change password, security issue")

# =============================================================================
# GUJARATI (gu) - Gujarati script
# =============================================================================
print("--- GUJARATI (gu) ---")

test("સોફ્ટવેર અપડેટ ઇન્સ્ટોલ કરો", "gu",
     description="Tech: install software update")

test("મીટિંગ કેન્સલ થઈ ગઈ છે", "gu",
     description="Business: meeting cancelled")

test("ઓનલાઈન પેમેન્ટ ફેઈલ થયું", "gu",
     description="Finance: online payment failed")

test("પ્રોજેક્ટ રિપોર્ટ સબમિટ કરવાની છે", "gu",
     description="Business: submit project report")

test("કસ્ટમર કમ્પ્લેઈન્ટ ફાઈલ થઈ છે", "gu",
     description="Business: customer complaint filed")

test("ડેટાબેઝ બેકઅપ કમ્પ્લીટ થયું", "gu",
     description="Tech: database backup complete")

test("નેટવર્ક કનેક્શન સ્લો છે", "gu",
     description="Tech: network connection slow")

test("પાસવર્ડ રીસેટ કરો", "gu",
     description="Tech: reset password")

# =============================================================================
# PUNJABI (pa) - Gurmukhi script
# =============================================================================
print("--- PUNJABI (pa) ---")

test("ਸਾਫਟਵੇਅਰ ਅੱਪਡੇਟ ਇੰਸਟਾਲ ਕਰੋ", "pa",
     description="Tech: install software update")

test("ਮੀਟਿੰਗ ਕੈਂਸਲ ਹੋ ਗਈ ਹੈ", "pa",
     description="Business: meeting cancelled")

test("ਔਨਲਾਈਨ ਪੇਮੈਂਟ ਫੇਲ ਹੋ ਗਿਆ", "pa",
     description="Finance: online payment failed")

test("ਪ੍ਰੋਜੈਕਟ ਡੈੱਡਲਾਈਨ ਮਿਸ ਹੋ ਰਹੀ ਹੈ", "pa",
     description="Business: project deadline being missed")

test("ਕਸਟਮਰ ਸਪੋਰਟ ਟਿਕਟ ਓਪਨ ਕਰੋ", "pa",
     description="Business: open customer support ticket")

test("ਸਰਵਰ ਰੀਸਟਾਰਟ ਕਰਨਾ ਪਵੇਗਾ", "pa",
     description="Tech: server needs restart")

# =============================================================================
# ODIA (or) - Oriya script
# =============================================================================
print("--- ODIA (or) ---")

test("ସଫ୍ଟୱେୟାର ଅପଡେଟ ଇନଷ୍ଟଲ କରନ୍ତୁ", "or",
     description="Tech: install software update")

test("ମିଟିଂ କ୍ୟାନ୍ସେଲ ହୋଇଗଲା", "or",
     description="Business: meeting cancelled")

test("ଅନଲାଇନ ପେମେଣ୍ଟ ଫେଲ ହୋଇଗଲା", "or",
     description="Finance: online payment failed")

test("ପ୍ରୋଜେକ୍ଟ ରିପୋର୍ଟ ସବମିଟ କରନ୍ତୁ", "or",
     description="Business: submit project report")

test("ସର୍ଭର ଡାଉନ ଅଛି", "or",
     description="Tech: server is down")

# =============================================================================
# ASSAMESE (as) - Bengali script variant
# =============================================================================
print("--- ASSAMESE (as) ---")

test("ছফটৱেৰ আপডেট ইনষ্টল কৰক", "as",
     description="Tech: install software update")

test("মিটিং কেনচেল হৈছে", "as",
     description="Business: meeting cancelled")

test("অনলাইন পেমেণ্ট ফেইল হৈছে", "as",
     description="Finance: online payment failed")

test("প্ৰজেক্ট ৰিপৰ্ট চাবমিট কৰক", "as",
     description="Business: submit project report")

# =============================================================================
# NEPALI (ne) - Devanagari
# =============================================================================
print("--- NEPALI (ne) ---")

test("सफ्टवेयर अपडेट इन्स्टल गर्नुहोस्", "ne",
     description="Tech: install software update")

test("मिटिङ क्यान्सल भयो", "ne",
     description="Business: meeting cancelled")

test("अनलाइन पेमेन्ट फेल भयो", "ne",
     description="Finance: online payment failed")

test("प्रोजेक्ट डेडलाइन मिस हुँदैछ", "ne",
     description="Business: project deadline being missed")

test("कस्टमर सपोर्ट टिकट ओपन गर्नुहोस्", "ne",
     description="Business: open support ticket")

# =============================================================================
# URDU (ur) - Perso-Arabic script
# =============================================================================
print("--- URDU (ur) ---")

test("سافٹ ویئر اپ ڈیٹ انسٹال کریں", "ur",
     description="Tech: install software update")

test("میٹنگ کینسل ہو گئی ہے", "ur",
     description="Business: meeting cancelled")

test("آن لائن پیمنٹ فیل ہو گئی", "ur",
     description="Finance: online payment failed")

test("پروجیکٹ رپورٹ سبمٹ کریں", "ur",
     description="Business: submit project report")

test("سرور ڈاؤن ہے، فوری فکس کریں", "ur",
     description="Tech: server down, fix immediately")

test("ڈیٹا بیس بیک اپ کمپلیٹ ہو گیا", "ur",
     description="Tech: database backup complete")

# =============================================================================
# EDGE CASES & SPECIAL SCENARIOS
# =============================================================================
print("--- EDGE CASES ---")

# Heavy code-mix (mostly English in Indic script)
test("फ्रंटएंड डेवलपर ने रिएक्ट कंपोनेंट में स्टेट मैनेजमेंट का बग फिक्स किया", "hi",
     description="Heavy code-mix: frontend React component state management bug fix")

# Minimal code-mix (mostly native with one English word)
test("मुझे कल तक ये काम करना है प्लीज", "hi",
     description="Minimal code-mix: one English word")

# Technical jargon dense
test("माइक्रोसर्विसेज आर्किटेक्चर में डॉकर कंटेनर डिप्लॉय करो कुबरनेट्स क्लस्टर पर", "hi",
     description="Dense tech: microservices docker kubernetes")

# Business/corporate speak
test("क्वार्टरली रेवेन्यू टार्गेट अचीव हो गया है, स्टेकहोल्डर्स को नोटिफाई करो", "hi",
     description="Corporate: quarterly revenue target, notify stakeholders")

# Medical domain
test("पेशेंट का एमआरआई रिपोर्ट नॉर्मल है लेकिन ईसीजी में एब्नॉर्मलिटी है", "hi",
     description="Medical: MRI normal, ECG abnormality")

# Education domain
test("অ্যাসাইনমেন্ট সাবমিশন ডেডলাইন এক্সটেন্ড করা হয়েছে", "bn",
     description="Education: assignment submission deadline extended")

# E-commerce
test("ஆர்டர் ட்ராக்கிங் ஸ்டேட்டஸ் அவுட் ஃபார் டெலிவரி ஆ இருக்கு", "ta",
     description="E-commerce: order tracking status out for delivery")

# Social media / casual
test("ये पोस्ट वायरल हो गई है, ट्रेंडिंग पर आ गई", "hi",
     description="Social media: post went viral, trending")

# Legal domain
test("కాంట్రాక్ట్ రివ్యూ కంప్లీట్ అయింది, లీగల్ టీమ్ అప్రూవ్ చేసింది", "te",
     description="Legal: contract review complete, legal team approved")

# Single English word in native context
test("আমি অফিসে যাচ্ছি", "bn",
     description="Single English: office")

test("நான் ஆஃபீஸ் போறேன்", "ta",
     description="Single English: office")

test("ಕಂಪ್ಯೂಟರ್ ಆನ್ ಮಾಡಿ", "kn",
     description="Single English: computer on")

# Multiple sentences
test("सर्वर क्रैश हो गया। लॉग्स चेक करो। डेवलपर टीम को अलर्ट भेजो।", "hi",
     description="Multiple sentences: server crash, check logs, alert team")

# Sentence with numbers mixed
test("टीम में पाँच डेवलपर्स हैं और तीन टेस्टर्स", "hi",
     description="Numbers mixed: five developers, three testers")

# Very long sentence
test("इंफ्रास्ट्रक्चर टीम ने प्रोडक्शन एनवायरनमेंट में न्यू माइक्रोसर्विस डिप्लॉय की है जो कस्टमर ऑर्डर प्रोसेसिंग को हैंडल करेगी और ऑटोमैटिकली स्केल होगी बेस्ड ऑन ट्रैफिक लोड", "hi",
     description="Long: infrastructure deployed new microservice for order processing")

# Gaming / casual
test("ગેમ અપડેટ ડાઉનલોડ કરો, ન્યૂ ફીચર્સ આવ્યા છે", "gu",
     description="Gaming: download game update, new features")

# Travel
test("ਫਲਾਈਟ ਡਿਲੇ ਹੋ ਗਈ ਹੈ, ਏਅਰਪੋਰਟ ਤੇ ਵੇਟ ਕਰੋ", "pa",
     description="Travel: flight delayed, wait at airport")

# Real estate
test("प्रॉपर्टी का लीगल वेरिफिकेशन कंप्लीट हो गया, रजिस्ट्रेशन प्रोसेस स्टार्ट करो", "hi",
     description="Real estate: property legal verification, start registration")

# Food delivery
test("ফুড ডেলিভারি অর্ডার কনফার্ম হয়েছে", "bn",
     description="Food: delivery order confirmed")

# Weather / casual conversation
test("இன்னைக்கு வெதர் கண்டிஷன் பேட் ஆ இருக்கு", "ta",
     description="Weather: bad weather condition today")

# Automotive
test("కార్ సర్వీసింగ్ బుకింగ్ కన్ఫర్మ్ అయింది", "te",
     description="Automotive: car servicing booking confirmed")

# Fitness / health
test("जिम मेंबरशिप रिन्यू करो, एक्सपायर हो गई है", "hi",
     description="Fitness: renew gym membership, expired")

# Banking
test("ক্রেডিট কার্ড বিল পেমেন্ট ডিউ ডেট মিস হয়ে গেছে", "bn",
     description="Banking: credit card bill payment due date missed")

# Government / bureaucratic
test("ಪಾಸ್‌ಪೋರ್ಟ್ ರಿನ್ಯೂವಲ್ ಅಪ್ಲಿಕೇಶನ್ ಸಬ್ಮಿಟ್ ಮಾಡಿ", "kn",
     description="Government: submit passport renewal application")

# Entertainment
test("మూవీ టికెట్ బుక్ చేయండి, ఈవెనింగ్ షో కోసం", "te",
     description="Entertainment: book movie ticket for evening show")

# Pure native (should keep everything as-is)
test("मुझे कल बाजार जाना है", "hi",
     description="Pure native Hindi: no English words expected")

test("আমি বাড়ি যাচ্ছি", "bn",
     description="Pure native Bengali: no English words expected")

test("நான் வீட்டுக்கு போறேன்", "ta",
     description="Pure native Tamil: no English words expected")

# =============================================================================
# DOMAIN-SPECIFIC BATCHES
# =============================================================================
print("--- IT / DEVOPS ---")

test("डिप्लॉयमेंट पाइपलाइन में फेलियर आ रही है, सीआई सीडी चेक करो", "hi",
     description="DevOps: deployment pipeline failure, check CI/CD")

test("লোড ব্যালান্সার কনফিগারেশন আপডেট করো", "bn",
     description="DevOps: update load balancer configuration")

test("ஃபயர்வால் ரூல்ஸ் அப்டேட் பண்ணுங்க", "ta",
     description="DevOps: update firewall rules")

test("ఎస్‌ఎస్‌ఎల్ సర్టిఫికేట్ ఎక్స్‌పైర్ అయింది, రీన్యూ చేయండి", "te",
     description="DevOps: SSL certificate expired, renew")

test("ಕ್ಲೌಡ್ ಸ್ಟೋರೇಜ್ ಲಿಮಿಟ್ ಎಕ್ಸೀಡ್ ಆಗಿದೆ", "kn",
     description="DevOps: cloud storage limit exceeded")

print("--- CUSTOMER SERVICE ---")

test("कस्टमर ने रिफंड रिक्वेस्ट रेज किया है, प्रोसेस करो", "hi",
     description="CS: customer raised refund request")

test("কমপ্লেইন্ট নম্বর জেনারেট করো এবং কাস্টমারকে নোটিফাই করো", "bn",
     description="CS: generate complaint number, notify customer")

test("எஸ்கலேஷன் மேட்ரிக்ஸ் ஃபாலோ பண்ணுங்க", "ta",
     description="CS: follow escalation matrix")

print("--- EDUCATION ---")

test("ऑनलाइन एग्जाम का रिजल्ट डिक्लेयर हो गया है", "hi",
     description="Education: online exam result declared")

test("অ্যাডমিশন ফর্ম সাবমিট করো ডেডলাইনের আগে", "bn",
     description="Education: submit admission form before deadline")

test("ஸ்கூல் போர்டல் ல ஃபீஸ் பேமெண்ட் பண்ணுங்க", "ta",
     description="Education: pay fees on school portal")

test("స్కాలర్‌షిప్ అప్లికేషన్ రిజెక్ట్ అయింది", "te",
     description="Education: scholarship application rejected")

# =============================================================================
# SUMMARY
# =============================================================================
print("=" * 80)
print(f"Total tests: {test_num}")
pass_count = sum(1 for _, _, s, _ in results if "PASS" in s)
fail_count = sum(1 for _, _, s, _ in results if "FAIL" in s)
no_expected = sum(1 for _, _, s, _ in results if s == "")
print(f"With expected values: PASS={pass_count}, FAIL={fail_count}")
print(f"Without expected values (manual review): {no_expected}")
print("=" * 80)
