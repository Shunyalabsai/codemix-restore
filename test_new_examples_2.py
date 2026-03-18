"""
Comprehensive test examples (batch 2) for codemix_restore ScriptRestorer.

All-new sentences covering the same languages as batch 1.
Domains: healthcare, logistics, startups, agriculture, sports, insurance,
telecom, hospitality, journalism, legal, recruitment, retail, construction.
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

test("क्लाइंट ने अर्जेंट कॉलबैक रिक्वेस्ट किया है", "hi",
     description="Business: client urgent callback request")

test("वेंडर इनवॉइस अप्रूवल के लिए पेंडिंग है", "hi",
     description="Finance: vendor invoice pending approval")

test("ब्रांच मैनेजर ने रिजाइन कर दिया है", "hi",
     description="HR: branch manager resigned")

test("कैंटीन में लंच ब्रेक एक्सटेंड करो आज", "hi",
     description="Casual: extend lunch break today")

test("प्रिंटर जाम हो गया है, आईटी हेल्पडेस्क को कॉन्टैक्ट करो", "hi",
     description="Office: printer jammed, contact IT helpdesk")

test("ऑडिट रिपोर्ट में कई डिस्क्रिपेंसीज मिली हैं", "hi",
     description="Finance: audit report discrepancies found")

test("न्यू हायर्स के लिए ऑनबोर्डिंग सेशन अरेंज करो", "hi",
     description="HR: arrange onboarding session for new hires")

test("क्लाउड इंफ्रा पर कॉस्ट ऑप्टिमाइजेशन करना है", "hi",
     description="Tech: cloud infrastructure cost optimization")

test("इन्वेंटरी स्टॉक लेवल क्रिटिकली लो है", "hi",
     description="Retail: inventory stock critically low")

test("मोबाइल ऐप का क्रैश रेट बढ़ गया है लेटेस्ट रिलीज के बाद", "hi",
     description="Tech: mobile app crash rate increased after release")

test("डिजिटल मार्केटिंग स्ट्रेटेजी पर ब्रेनस्टॉर्मिंग सेशन रखो", "hi",
     description="Marketing: digital strategy brainstorming session")

test("फ्रीलांसर को पेमेंट रिलीज करो, इनवॉइस वेरिफाइड है", "hi",
     description="Finance: release freelancer payment")

test("बैकएंड में मेमोरी लीक डिटेक्ट हुआ है", "hi",
     description="Tech: backend memory leak detected")

test("स्टार्टअप फंडिंग राउंड क्लोज हो गया है", "hi",
     description="Startup: funding round closed")

test("कॉन्फ्रेंस रूम में प्रोजेक्टर काम नहीं कर रहा", "hi",
     description="Office: conference room projector not working")

test("कंपनी पॉलिसी अपडेट सभी एम्प्लॉइज को फॉरवर्ड करो", "hi",
     description="HR: forward company policy update to employees")

test("थर्ड पार्टी इंटीग्रेशन में लेटेंसी इश्यू आ रहा है", "hi",
     description="Tech: third party integration latency issue")

test("वर्कशॉप रजिस्ट्रेशन फॉर्म सर्कुलेट करो", "hi",
     description="Education: circulate workshop registration form")

test("प्रोक्योरमेंट टीम से क्वोटेशन कलेक्ट करो", "hi",
     description="Business: collect quotation from procurement team")

test("डेटा एनालिटिक्स डैशबोर्ड लाइव कर दो", "hi",
     description="Tech: make data analytics dashboard live")

# =============================================================================
# BENGALI (bn) - Bengali script
# =============================================================================
print("--- BENGALI (bn) ---")

test("ক্লায়েন্ট প্রেজেন্টেশন রেডি করো", "bn",
     description="Business: prepare client presentation")

test("ইমেইল ক্যাম্পেইন লঞ্চ করো আজ রাতে", "bn",
     description="Marketing: launch email campaign tonight")

test("সিস্টেম ক্র্যাশ হয়েছে, লগ ফাইল চেক করো", "bn",
     description="Tech: system crash, check log files")

test("ভেন্ডর কন্ট্র্যাক্ট রিনিউ করতে হবে", "bn",
     description="Business: vendor contract needs renewal")

test("ইনভেন্টরি ম্যানেজমেন্ট সিস্টেম আপগ্রেড করো", "bn",
     description="Retail: upgrade inventory management system")

test("নিউ প্রোডাক্ট লঞ্চ ইভেন্ট প্ল্যান করো", "bn",
     description="Marketing: plan new product launch event")

test("ড্রাইভার লোকেশন ট্র্যাক করো রিয়েল টাইমে", "bn",
     description="Logistics: track driver location real time")

test("হেল্থ ইন্স্যুরেন্স ক্লেম প্রসেস করো", "bn",
     description="Insurance: process health insurance claim")

test("ফ্রন্ট ডেস্ক রিসেপশনিস্ট ছুটিতে আছে", "bn",
     description="Office: front desk receptionist on leave")

test("ওয়্যারহাউস ক্যাপাসিটি ফুল হয়ে গেছে", "bn",
     description="Logistics: warehouse capacity full")

test("কোয়ালিটি চেক ফেল হয়েছে, প্রোডাকশন স্টপ করো", "bn",
     description="Manufacturing: quality check failed, stop production")

test("মার্কেট রিসার্চ রিপোর্ট রিভিউ করো", "bn",
     description="Business: review market research report")

# =============================================================================
# TAMIL (ta) - Tamil script
# =============================================================================
print("--- TAMIL (ta) ---")

test("க்ளையன்ட் ரிக்வயர்மென்ட் கலெக்ட் பண்ணுங்க", "ta",
     description="Business: collect client requirements")

test("டெஸ்ட் கேஸ் எக்ஸிக்யூட் பண்ணுங்க", "ta",
     description="Tech: execute test cases")

test("ப்ராடக்ட் டெமோ ஷெட்யூல் பண்ணுங்க", "ta",
     description="Business: schedule product demo")

test("மொபைல் ஆப் க்ராஷ் ஆகுது, ஹாட்ஃபிக்ஸ் ரிலீஸ் பண்ணுங்க", "ta",
     description="Tech: mobile app crashing, release hotfix")

test("வெண்டர் பேமெண்ட் ப்ராசஸ் பண்ணுங்க", "ta",
     description="Finance: process vendor payment")

test("கஸ்டமர் ரிட்டென்ஷன் ரேட் டிராப் ஆயிடுச்சு", "ta",
     description="Business: customer retention rate dropped")

test("ஸ்டாக் மார்கெட் ப்ரைஸ் அப்டேட் பண்ணுங்க", "ta",
     description="Finance: update stock market price")

test("ட்ரான்ஸ்போர்ட் லாஜிஸ்டிக்ஸ் கோஆர்டினேட் பண்ணுங்க", "ta",
     description="Logistics: coordinate transport logistics")

test("டாட்டா சென்டர் கூலிங் சிஸ்டம் ஃபெயில் ஆயிடுச்சு", "ta",
     description="Tech: data center cooling system failed")

test("ரிக்ரூட்மென்ட் டிரைவ் நெக்ஸ்ட் வீக் ஸ்டார்ட் ஆகும்", "ta",
     description="HR: recruitment drive starts next week")

test("பேஷண்ட் ரிகார்ட்ஸ் டிஜிடைஸ் பண்ணணும்", "ta",
     description="Healthcare: digitize patient records")

test("ஃப்ரீலான்ஸ் டிசைனர் ஹயர் பண்ணுங்க", "ta",
     description="HR: hire freelance designer")

# =============================================================================
# TELUGU (te) - Telugu script
# =============================================================================
print("--- TELUGU (te) ---")

test("క్లయింట్ ప్రపోజల్ డ్రాఫ్ట్ చేయండి", "te",
     description="Business: draft client proposal")

test("సిస్టమ్ లాగ్స్ అనాలైజ్ చేయండి", "te",
     description="Tech: analyze system logs")

test("ఇన్సూరెన్స్ క్లెయిమ్ వెరిఫై చేయండి", "te",
     description="Insurance: verify insurance claim")

test("మార్కెటింగ్ కాంపెయిన్ పర్ఫార్మెన్స్ రివ్యూ చేయండి", "te",
     description="Marketing: review campaign performance")

test("ఇన్వెంటరీ రీఆర్డర్ ట్రిగ్గర్ చేయండి", "te",
     description="Retail: trigger inventory reorder")

test("పేషెంట్ డిశ్చార్జ్ సమ్మరీ ప్రిపేర్ చేయండి", "te",
     description="Healthcare: prepare patient discharge summary")

test("లాజిస్టిక్స్ పార్ట్‌నర్ తో కాంట్రాక్ట్ నెగోషియేట్ చేయండి", "te",
     description="Business: negotiate contract with logistics partner")

test("మొబైల్ నెట్‌వర్క్ కవరేజ్ ఇష్యూ రిపోర్ట్ చేయండి", "te",
     description="Telecom: report mobile network coverage issue")

test("ఫ్రాంచైజీ అప్లికేషన్ ప్రాసెస్ చేయండి", "te",
     description="Business: process franchise application")

test("హోటల్ చెక్‌ఇన్ ప్రాసెస్ ఆటోమేట్ చేయండి", "te",
     description="Hospitality: automate hotel checkin process")

test("వెబ్‌సైట్ యూజర్ ఎక్స్‌పీరియన్స్ ఇంప్రూవ్ చేయండి", "te",
     description="Tech: improve website user experience")

test("టెండర్ డాక్యుమెంట్ సబ్మిట్ చేయండి డెడ్‌లైన్ లోపల", "te",
     description="Business: submit tender document before deadline")

# =============================================================================
# KANNADA (kn) - Kannada script
# =============================================================================
print("--- KANNADA (kn) ---")

test("ಕ್ಲೈಂಟ್ ಫೀಡ್‌ಬ್ಯಾಕ್ ಕಲೆಕ್ಟ್ ಮಾಡಿ", "kn",
     description="Business: collect client feedback")

test("ಬಿಲ್ಡ್ ಪೈಪ್‌ಲೈನ್ ಫಿಕ್ಸ್ ಮಾಡಿ", "kn",
     description="Tech: fix build pipeline")

test("ಇನ್ಶೂರೆನ್ಸ್ ಪ್ರೀಮಿಯಂ ಕ್ಯಾಲ್ಕುಲೇಟ್ ಮಾಡಿ", "kn",
     description="Insurance: calculate insurance premium")

test("ವೆಂಡರ್ ಪರ್ಫಾರ್ಮೆನ್ಸ್ ರಿವ್ಯೂ ಮಾಡಿ", "kn",
     description="Business: review vendor performance")

test("ಪೇಶೆಂಟ್ ಅಡ್ಮಿಷನ್ ಫಾರ್ಮ್ ಫಿಲ್ ಮಾಡಿ", "kn",
     description="Healthcare: fill patient admission form")

test("ಲೈಸೆನ್ಸ್ ರಿನ್ಯೂವಲ್ ಅಪ್ಲಿಕೇಶನ್ ಫೈಲ್ ಮಾಡಿ", "kn",
     description="Government: file license renewal application")

test("ಡಿಸ್ಟ್ರಿಬ್ಯೂಶನ್ ಚಾನೆಲ್ ಆಪ್ಟಿಮೈಜ್ ಮಾಡಿ", "kn",
     description="Business: optimize distribution channel")

test("ಸ್ಪೋರ್ಟ್ಸ್ ಟೂರ್ನಮೆಂಟ್ ರಿಜಿಸ್ಟ್ರೇಶನ್ ಓಪನ್ ಆಗಿದೆ", "kn",
     description="Sports: tournament registration open")

test("ಫ್ಲೋರ್ ಪ್ಲಾನ್ ಅಪ್ರೂವ್ ಆಗಿದೆ, ಕನ್ಸ್ಟ್ರಕ್ಷನ್ ಸ್ಟಾರ್ಟ್ ಮಾಡಿ", "kn",
     description="Construction: floor plan approved, start construction")

test("ಎಲೆಕ್ಟ್ರಿಸಿಟಿ ಬಿಲ್ ಪೇಮೆಂಟ್ ಡ್ಯೂ ಡೇಟ್ ಮಿಸ್ ಆಗಿದೆ", "kn",
     description="Utility: electricity bill payment due date missed")

# =============================================================================
# MALAYALAM (ml) - Malayalam script
# =============================================================================
print("--- MALAYALAM (ml) ---")

test("ക്ലൈന്റ് പ്രൊപോസൽ റെഡി ആക്കൂ", "ml",
     description="Business: prepare client proposal")

test("സിസ്റ്റം ക്രാഷ് ആയി, ലോഗ്സ് ചെക്ക് ചെയ്യൂ", "ml",
     description="Tech: system crashed, check logs")

test("ഇൻഷുറൻസ് പോളിസി റിന്യൂ ചെയ്യണം", "ml",
     description="Insurance: renew insurance policy")

test("ഫാർമസി സ്റ്റോക്ക് അപ്ഡേറ്റ് ചെയ്യൂ", "ml",
     description="Healthcare: update pharmacy stock")

test("ഹോട്ടൽ ബുക്കിംഗ് കൺഫേം ചെയ്യൂ", "ml",
     description="Hospitality: confirm hotel booking")

test("ടെലികോം പ്ലാൻ അപ്ഗ്രേഡ് ചെയ്യൂ", "ml",
     description="Telecom: upgrade telecom plan")

test("ടാക്സ് റിട്ടേൺ ഫൈൽ ചെയ്യണം ഡെഡ്ലൈൻ കഴിയുന്നതിന് മുമ്പ്", "ml",
     description="Finance: file tax return before deadline")

test("ലോജിസ്റ്റിക്സ് ട്രാക്കിംഗ് സിസ്റ്റം ഡൗൺ ആണ്", "ml",
     description="Logistics: tracking system down")

test("മീഡിയ കവറേജ് അറേഞ്ച് ചെയ്യൂ ഇവന്റിന്", "ml",
     description="Journalism: arrange media coverage for event")

test("കൺസ്ട്രക്ഷൻ സൈറ്റ് ഇൻസ്പെക്ഷൻ ഷെഡ്യൂൾ ചെയ്യൂ", "ml",
     description="Construction: schedule site inspection")

# =============================================================================
# MARATHI (mr) - Devanagari
# =============================================================================
print("--- MARATHI (mr) ---")

test("क्लायंट प्रपोजल ड्राफ्ट करा", "mr",
     description="Business: draft client proposal")

test("इन्शुरन्स क्लेम प्रोसेस करा", "mr",
     description="Insurance: process insurance claim")

test("मार्केट रिसर्च डेटा कलेक्ट करा", "mr",
     description="Business: collect market research data")

test("पेशंट रजिस्ट्रेशन सिस्टम अपग्रेड करा", "mr",
     description="Healthcare: upgrade patient registration system")

test("लॉजिस्टिक्स कॉस्ट रिड्यूस करा", "mr",
     description="Logistics: reduce logistics cost")

test("ट्रेनिंग मटेरियल प्रिपेअर करा", "mr",
     description="HR: prepare training material")

test("क्वालिटी कंट्रोल रिपोर्ट जनरेट करा", "mr",
     description="Manufacturing: generate quality control report")

test("इलेक्ट्रिसिटी कनेक्शन ट्रान्सफर करा", "mr",
     description="Utility: transfer electricity connection")

test("स्पोर्ट्स इक्विपमेंट ऑर्डर प्लेस करा", "mr",
     description="Sports: place sports equipment order")

test("फ्रँचायझी अग्रीमेंट साइन करा", "mr",
     description="Business: sign franchise agreement")

# =============================================================================
# GUJARATI (gu) - Gujarati script
# =============================================================================
print("--- GUJARATI (gu) ---")

test("ક્લાયન્ટ પ્રેઝન્ટેશન ડ્રાફ્ટ કરો", "gu",
     description="Business: draft client presentation")

test("ઇન્શ્યોરન્સ પોલિસી રિન્યુ કરો", "gu",
     description="Insurance: renew insurance policy")

test("ફાર્મસી ઇન્વેન્ટરી ચેક કરો", "gu",
     description="Healthcare: check pharmacy inventory")

test("ટ્રાન્સપોર્ટ ચાર્જીસ કેલ્ક્યુલેટ કરો", "gu",
     description="Logistics: calculate transport charges")

test("સેલ્સ ટાર્ગેટ અચીવ થયું નથી", "gu",
     description="Business: sales target not achieved")

test("ઇલેક્ટ્રિક બિલ ઓનલાઇન પે કરો", "gu",
     description="Utility: pay electric bill online")

test("સ્ટાફ પરફોર્મન્સ રિવ્યુ કમ્પ્લીટ કરો", "gu",
     description="HR: complete staff performance review")

test("કન્સ્ટ્રક્શન મટીરીયલ ઓર્ડર પ્લેસ કરો", "gu",
     description="Construction: place construction material order")

test("ટેક્સ ઓડિટ ડોક્યુમેન્ટ્સ રેડી કરો", "gu",
     description="Finance: prepare tax audit documents")

test("ફૂડ સેફ્ટી ઇન્સ્પેક્શન પાસ થયું", "gu",
     description="Hospitality: food safety inspection passed")

# =============================================================================
# PUNJABI (pa) - Gurmukhi script
# =============================================================================
print("--- PUNJABI (pa) ---")

test("ਕਲਾਇੰਟ ਰਿਕਵਾਇਰਮੈਂਟ ਡਾਕੂਮੈਂਟ ਤਿਆਰ ਕਰੋ", "pa",
     description="Business: prepare client requirement document")

test("ਇੰਸ਼ੋਰੈਂਸ ਪ੍ਰੀਮੀਅਮ ਕੈਲਕੁਲੇਟ ਕਰੋ", "pa",
     description="Insurance: calculate insurance premium")

test("ਡਿਲੀਵਰੀ ਸਟੇਟਸ ਚੈੱਕ ਕਰੋ", "pa",
     description="Logistics: check delivery status")

test("ਹੈਲਥ ਚੈੱਕਅੱਪ ਰਿਪੋਰਟ ਕਲੈਕਟ ਕਰੋ", "pa",
     description="Healthcare: collect health checkup report")

test("ਸੇਲਜ਼ ਟੀਮ ਪਰਫਾਰਮੈਂਸ ਰਿਵਿਊ ਕਰੋ", "pa",
     description="Business: review sales team performance")

test("ਟੈਕਸ ਰਿਟਰਨ ਫਾਈਲ ਕਰੋ ਡੈੱਡਲਾਈਨ ਤੋਂ ਪਹਿਲਾਂ", "pa",
     description="Finance: file tax return before deadline")

test("ਸਟਾਫ ਟ੍ਰੇਨਿੰਗ ਪ੍ਰੋਗਰਾਮ ਡਿਜ਼ਾਈਨ ਕਰੋ", "pa",
     description="HR: design staff training program")

test("ਇਲੈਕਟ੍ਰੀਸਿਟੀ ਮੀਟਰ ਰੀਡਿੰਗ ਸਬਮਿਟ ਕਰੋ", "pa",
     description="Utility: submit electricity meter reading")

# =============================================================================
# ODIA (or) - Oriya script
# =============================================================================
print("--- ODIA (or) ---")

test("କ୍ଲାଏଣ୍ଟ ମିଟିଂ ଶେଡ୍ୟୁଲ କରନ୍ତୁ", "or",
     description="Business: schedule client meeting")

test("ଇନସୁରେନ୍ସ ଡକ୍ୟୁମେଣ୍ଟ ଭେରିଫାଇ କରନ୍ତୁ", "or",
     description="Insurance: verify insurance document")

test("ଲଜିଷ୍ଟିକ୍ସ ଟ୍ରାକିଂ ସିଷ୍ଟମ ଡାଉନ ଅଛି", "or",
     description="Logistics: tracking system is down")

test("ହସ୍ପିଟାଲ ବେଡ ଆଭେଲେବିଲିଟି ଚେକ କରନ୍ତୁ", "or",
     description="Healthcare: check hospital bed availability")

test("ସ୍କୁଲ ଆଡମିଶନ ଫର୍ମ ସବମିଟ କରନ୍ତୁ", "or",
     description="Education: submit school admission form")

test("ଟ୍ରାନ୍ସପୋର୍ଟ ବସ ଟାଇମଟେବଲ ଅପଡେଟ କରନ୍ତୁ", "or",
     description="Transport: update bus timetable")

test("ଫାର୍ମର ସବସିଡି ଆପ୍ଲିକେଶନ ପ୍ରୋସେସ କରନ୍ତୁ", "or",
     description="Agriculture: process farmer subsidy application")

# =============================================================================
# ASSAMESE (as) - Bengali script variant
# =============================================================================
print("--- ASSAMESE (as) ---")

test("ক্লায়েন্ট ফিডবেক কলেক্ট কৰক", "as",
     description="Business: collect client feedback")

test("ইনচিউৰেন্স পলিচি ৰিনিউ কৰক", "as",
     description="Insurance: renew insurance policy")

test("হেল্থ কেয়াৰ ৰেকৰ্ড আপডেট কৰক", "as",
     description="Healthcare: update health care records")

test("ট্ৰেইনিং মেটেৰিয়েল প্ৰিপেয়াৰ কৰক", "as",
     description="HR: prepare training material")

test("ট্ৰান্সপৰ্ট ভাড়া কেলকুলেট কৰক", "as",
     description="Logistics: calculate transport fare")

test("চেলাৰি স্লিপ ডাউনলোড কৰক", "as",
     description="HR: download salary slip")

# =============================================================================
# NEPALI (ne) - Devanagari
# =============================================================================
print("--- NEPALI (ne) ---")

test("क्लाइन्ट प्रपोजल ड्राफ्ट गर्नुहोस्", "ne",
     description="Business: draft client proposal")

test("इन्स्युरेन्स क्लेम प्रोसेस गर्नुहोस्", "ne",
     description="Insurance: process insurance claim")

test("हेल्थ चेकअप रिपोर्ट कलेक्ट गर्नुहोस्", "ne",
     description="Healthcare: collect health checkup report")

test("लजिस्टिक्स ट्र्याकिङ अपडेट गर्नुहोस्", "ne",
     description="Logistics: update logistics tracking")

test("टुरिज्म प्याकेज बुकिङ कन्फर्म गर्नुहोस्", "ne",
     description="Tourism: confirm tourism package booking")

test("फार्मर्स मार्केट रजिस्ट्रेसन ओपन गर्नुहोस्", "ne",
     description="Agriculture: open farmers market registration")

test("स्कुल फी पेमेन्ट रिसिप्ट जनरेट गर्नुहोस्", "ne",
     description="Education: generate school fee payment receipt")

# =============================================================================
# URDU (ur) - Perso-Arabic script
# =============================================================================
print("--- URDU (ur) ---")

test("کلائنٹ پریزنٹیشن تیار کریں", "ur",
     description="Business: prepare client presentation")

test("انشورنس پالیسی ریویو کریں", "ur",
     description="Insurance: review insurance policy")

test("ہسپتال ایمرجنسی وارڈ میں ڈاکٹر کو کال کریں", "ur",
     description="Healthcare: call doctor to emergency ward")

test("ٹرانسپورٹ شیڈول اپ ڈیٹ کریں", "ur",
     description="Transport: update transport schedule")

test("ٹیکس فائلنگ ڈیڈ لائن آ رہی ہے", "ur",
     description="Finance: tax filing deadline approaching")

test("اسٹاف ٹریننگ ورکشاپ ارینج کریں", "ur",
     description="HR: arrange staff training workshop")

test("فوڈ ڈلیوری ایپ میں آرڈر ٹریکنگ ایشو ہے", "ur",
     description="Tech: food delivery app order tracking issue")

test("پراپرٹی ڈیلر سے کانٹریکٹ فائنلائز کریں", "ur",
     description="Real estate: finalize contract with property dealer")

# =============================================================================
# EDGE CASES & SPECIAL SCENARIOS (batch 2)
# =============================================================================
print("--- EDGE CASES (batch 2) ---")

# Startup / VC lingo
test("सीरीज ए फंडिंग क्लोज हुई, वैल्यूएशन डबल हो गया", "hi",
     description="Startup: series A funding closed, valuation doubled")

# Agriculture tech
test("ক্রপ মনিটরিং সিস্টেম ইনস্টল করো ফিল্ডে", "bn",
     description="AgriTech: install crop monitoring system in field")

# Sports commentary style
test("பேட்ஸ்மேன் சென்ச்சுரி ஸ்கோர் பண்ணிட்டார், கிரேட் பெர்ஃபார்மன்ஸ்", "ta",
     description="Sports: batsman scored century, great performance")

# Pharmaceutical
test("డ్రగ్ ట్రయల్ రిజల్ట్స్ పబ్లిష్ చేయండి", "te",
     description="Pharma: publish drug trial results")

# Journalism
test("ಪ್ರೆಸ್ ಕಾನ್ಫರೆನ್ಸ್ ಅಟೆಂಡ್ ಮಾಡಿ ಮತ್ತು ಆರ್ಟಿಕಲ್ ಡ್ರಾಫ್ಟ್ ಮಾಡಿ", "kn",
     description="Journalism: attend press conference, draft article")

# Telecom
test("ബ്രോഡ്ബാൻഡ് കണക്ഷൻ സ്പീഡ് ടെസ്റ്റ് ചെയ്യൂ", "ml",
     description="Telecom: test broadband connection speed")

# Election / government
test("वोटर रजिस्ट्रेशन कॅम्प ऑर्गनाइज करा", "mr",
     description="Government: organize voter registration camp")

# Retail / fashion
test("ન્યુ કલેક્શન લોન્ચ ડેટ ફાઇનલાઇઝ કરો", "gu",
     description="Retail: finalize new collection launch date")

# Farming
test("ਫਸਲ ਇੰਸ਼ੋਰੈਂਸ ਕਲੇਮ ਫਾਈਲ ਕਰੋ", "pa",
     description="Agriculture: file crop insurance claim")

# Disaster management
test("ଡିଜାଷ୍ଟର ମ୍ୟାନେଜମେଣ୍ଟ ଟିମ ଆଲର୍ଟ କରନ୍ତୁ", "or",
     description="Emergency: alert disaster management team")

# Pure native (no English expected)
test("मेरी बहन कल शाम को आ रही है", "hi",
     description="Pure native Hindi: sister coming tomorrow evening")

test("তোমার সাথে কথা বলতে চাই", "bn",
     description="Pure native Bengali: want to talk to you")

test("எங்க ஊர்ல மழை பெய்யுது", "ta",
     description="Pure native Tamil: raining in our town")

test("మా నాన్న రేపు వస్తారు", "te",
     description="Pure native Telugu: father coming tomorrow")

test("ನಮ್ಮ ಮನೆಯಲ್ಲಿ ಹಬ್ಬ ಇದೆ", "kn",
     description="Pure native Kannada: festival at our house")

test("ഞങ്ങളുടെ നാട്ടിൽ മഴ പെയ്യുന്നു", "ml",
     description="Pure native Malayalam: raining in our place")

# Sentence with only borrowed/loan words (tricky)
test("टेक्नोलॉजी इनोवेशन एक्सेलरेटर प्रोग्राम", "hi",
     description="All-English: technology innovation accelerator program")

# Very short
test("ओके", "hi",
     description="Single word: OK")

test("ডান", "bn",
     description="Single word: done")

test("ரெடி", "ta",
     description="Single word: ready")

# Repeated words
test("चेक चेक चेक, सब चेक करो", "hi",
     description="Repeated word: check check check")

# Mixed punctuation
test("हैलो! क्या मीटिंग कन्फर्म है? प्लीज रिप्लाई करो।", "hi",
     description="Mixed punctuation: hello, meeting confirmed?")

# Code-switching mid-word (agglutinative suffix)
test("ऑफिसमें मीटिंग होगी", "hi",
     description="Agglutinative: office+में fused")

test("কম্পিউটারে ইনস্টল করো", "bn",
     description="Agglutinative: computer+e fused")

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
