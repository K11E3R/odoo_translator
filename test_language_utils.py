import unittest
from unittest import mock

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Provide a lightweight langid stub when the dependency is unavailable.
if 'langid.langid' not in sys.modules:
    import types

    langid_pkg = types.ModuleType('langid')
    langid_mod = types.ModuleType('langid.langid')

    class _StubLanguageIdentifier:
        def __init__(self, *_, **__):
            self.languages = []

        @classmethod
        def from_modelstring(cls, *_args, **_kwargs):
            return cls()

        def classify(self, text):
            lowered = (text or '').lower()
            if not lowered.strip():
                return 'und', 0.0
            french_keywords = ('commande', 'facture', 'veuillez', 'montant', 'client')
            english_keywords = ('order', 'invoice', 'confirm', 'customer', 'amount', 'please')
            if any(word in lowered for word in french_keywords):
                return 'fr', 0.88
            if any(word in lowered for word in english_keywords):
                return 'en', 0.88
            return 'en', 0.55

        def set_languages(self, languages):
            self.languages = list(languages)

    langid_mod.LanguageIdentifier = _StubLanguageIdentifier
    langid_mod.model = 'stub-model'
    langid_pkg.langid = langid_mod
    sys.modules['langid'] = langid_pkg
    sys.modules['langid.langid'] = langid_mod

from po_translator.utils import language


class LanguageDetectionTestCase(unittest.TestCase):
    """Test suite covering language detection heuristics and helpers."""

    def setUp(self):
        # Disable external network calls from googletrans.
        self.google_patcher = mock.patch.object(language, "_GOOGLE_TRANSLATOR", None)
        self.google_patcher.start()

        # Clear caches between tests to ensure deterministic behaviour.
        language._detect_with_langid.cache_clear()
        language._detect_with_google.cache_clear()

    def tearDown(self):
        self.google_patcher.stop()

    def test_detect_language_details_identifies_french_phrase(self):
        text = "Confirmer la commande, veuillez vérifier le montant total de la facture."
        lang, confidence = language.detect_language_details(text)

        self.assertEqual(lang, "fr")
        self.assertGreaterEqual(confidence, 0.7)

    def test_detect_language_details_identifies_english_phrase(self):
        text = "Confirm the order and please review the total amount before invoicing."
        lang, confidence = language.detect_language_details(text)

        self.assertEqual(lang, "en")
        self.assertGreaterEqual(confidence, 0.7)

    def test_detect_language_details_overrides_romance_false_positive(self):
        text = (
            "Veuillez confirmer la commande et vérifier le montant total de cette facture client."
        )

        # Ensure heuristic detection does not short-circuit the langid path.
        with mock.patch.object(language, "_heuristic_detect", return_value=(None, 0.0)):
            with mock.patch.object(
                language._LANGID_IDENTIFIER, "classify", return_value=("ca", 0.83)
            ):
                language._detect_with_langid.cache_clear()
                lang, confidence = language.detect_language_details(text)

        self.assertEqual(lang, "fr")
        self.assertGreaterEqual(confidence, 0.82)

    def test_detect_language_handles_placeholders(self):
        text = "Confirm the order for %(customer)s before {deadline}."
        lang = language.detect_language(text)

        self.assertEqual(lang, "en")

    def test_detect_language_returns_none_for_empty_text(self):
        lang = language.detect_language("")
        self.assertIsNone(lang)

    def test_is_untranslated_flags_empty_or_matching_strings(self):
        self.assertTrue(language.is_untranslated("Order", ""))
        self.assertTrue(language.is_untranslated("Order", "Order"))
        self.assertFalse(language.is_untranslated("Order", "Commande"))


if __name__ == "__main__":
    unittest.main()
