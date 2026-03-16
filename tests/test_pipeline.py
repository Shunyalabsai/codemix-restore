"""End-to-end tests for the script restoration pipeline."""

import pytest

from codemix_restore.pipeline import RestoreResult, ScriptRestorer

# Shared restorer instance (dictionary-only mode, no GPU needed for tests)
_restorer = ScriptRestorer(use_neural=False)


def _restore(text: str, lang: str) -> str:
    return _restorer.restore(text, lang=lang)


def _word_accuracy(expected: str, actual: str) -> float:
    exp_words = expected.split()
    act_words = actual.split()
    total = max(len(exp_words), len(act_words))
    if total == 0:
        return 1.0
    correct = sum(
        1 for e, a in zip(exp_words, act_words)
        if e.lower().strip(".,!?।") == a.lower().strip(".,!?।")
    )
    return correct / total


class TestEndToEnd:
    """Tests that each language achieves reasonable accuracy on representative examples."""

    # Telugu — 100% accuracy in previous evaluation
    def test_telugu_meeting(self):
        result = _restore("రేపు మీటింగ్ అట్ ఫైవ్ ఉంది", "te")
        assert _word_accuracy("రేపు meeting at five ఉంది", result) >= 0.8

    def test_telugu_report(self):
        result = _restore("ఈ రిపోర్ట్ సెండ్ చేయండి ప్లీజ్", "te")
        assert _word_accuracy("ఈ report send చేయండి please", result) >= 0.8

    # Kannada — 100% accuracy
    def test_kannada_meeting(self):
        result = _restore("ನಾಳೆ ಮೀಟಿಂಗ್ ಅಟ್ ಫೈವ್ ಇದೆ", "kn")
        assert _word_accuracy("ನಾಳೆ meeting at five ಇದೆ", result) >= 0.8

    def test_kannada_document(self):
        result = _restore("ಈ ಡಾಕ್ಯುಮೆಂಟ್ ಚೆಕ್ ಮಾಡಿ", "kn")
        assert _word_accuracy("ಈ document check ಮಾಡಿ", result) >= 0.8

    # Marathi — 100% accuracy
    def test_marathi_meeting(self):
        result = _restore("उद्या मीटिंग अॅट फाइव्ह आहे", "mr")
        assert _word_accuracy("उद्या meeting at five आहे", result) >= 0.8

    def test_marathi_report(self):
        result = _restore("हा रिपोर्ट सेंड करा प्लीज", "mr")
        assert _word_accuracy("हा report send करा please", result) >= 0.8

    # Gujarati — 94.7%
    def test_gujarati_meeting(self):
        result = _restore("કાલે મીટિંગ એટ ફાઇવ છે", "gu")
        assert _word_accuracy("કાલે meeting at five છે", result) >= 0.8

    # Punjabi — 94.7%
    def test_punjabi_meeting(self):
        result = _restore("ਕੱਲ ਮੀਟਿੰਗ ਐਟ ਫਾਈਵ ਹੈ", "pa")
        assert _word_accuracy("ਕੱਲ meeting at five ਹੈ", result) >= 0.8

    # Hindi
    def test_hindi_mixed(self):
        result = _restore("धन्यवाद फॉर योर हेल्प", "hi")
        assert "for" in result.lower()
        assert "your" in result.lower()
        assert "help" in result.lower()
        assert "धन्यवाद" in result

    # Bengali
    def test_bengali_later_call(self):
        result = _restore("আমি তোমাকে লেটার কল করবো", "bn")
        assert _word_accuracy("আমি তোমাকে later call করবো", result) >= 0.8

    # Tamil
    def test_tamil_document(self):
        result = _restore("இந்த டாக்குமெண்ட் செக் பண்ணுங்க", "ta")
        assert "document" in result.lower()
        assert "check" in result.lower()


class TestReturnDetails:
    def test_returns_restore_result(self):
        result = _restorer.restore("मीटिंग अट", lang="hi", return_details=True)
        assert isinstance(result, RestoreResult)
        assert result.tokens_total > 0
        assert result.lang_code == "hi"
        assert len(result.details) > 0

    def test_empty_input(self):
        result = _restorer.restore("", lang="hi", return_details=True)
        assert isinstance(result, RestoreResult)
        assert result.tokens_total == 0


class TestAutoDetect:
    def test_auto_detect_hindi(self):
        result = _restorer.restore("मीटिंग फॉर")
        assert "meeting" in result.lower()

    def test_auto_detect_telugu(self):
        result = _restorer.restore("మీటింగ్ అట్ ఫైవ్")
        assert "meeting" in result.lower()

    def test_pure_latin_passthrough(self):
        result = _restorer.restore("hello world")
        assert result == "hello world"
