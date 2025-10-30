import unittest
from types import SimpleNamespace
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
        self.env_patcher = mock.patch.dict(
            os.environ, {"PO_TRANSLATOR_USE_GOOGLE_DETECTION": "0"}
        )
        self.env_patcher.start()

        language._GOOGLE_TRANSLATOR_SINGLETON = None
        language._GOOGLE_TRANSLATOR_DISABLED = False
        language._disable_google_detection()

        # Clear caches between tests to ensure deterministic behavior.
        language._detect_with_langid.cache_clear()
        language._detect_with_google.cache_clear()

    def tearDown(self):
        self.env_patcher.stop()

    def test_detect_language_details_identifies_italian_phrase(self):
        text = "Confermare l'ordine e verificare l'importo totale della fattura."

        with mock.patch.object(language, "_detect_with_langid", return_value=("it", 0.91)) as mocked:
            with mock.patch.object(language, "_heuristic_detect", return_value=(None, 0.0)):
                lang, confidence = language.detect_language_details(text)

        mocked.assert_called_once_with(text)
        self.assertEqual(lang, "it")
        self.assertGreaterEqual(confidence, 0.91)

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

    def test_detect_language_details_uses_google_when_available(self):
        stub_detection = SimpleNamespace(lang="de", confidence=0.88)
        stub_translator = mock.Mock()
        stub_translator.detect.return_value = stub_detection

        with mock.patch.dict(os.environ, {"PO_TRANSLATOR_USE_GOOGLE_DETECTION": "1"}):
            language._GOOGLE_TRANSLATOR_SINGLETON = None
            language._GOOGLE_TRANSLATOR_DISABLED = False

            with mock.patch.object(
                language, "_get_google_translator", return_value=stub_translator
            ) as patched_get:
                language._detect_with_google.cache_clear()
                with mock.patch.object(language, "_heuristic_detect", return_value=(None, 0.0)):
                    with mock.patch.object(
                        language._LANGID_IDENTIFIER, "classify", return_value=("und", 0.0)
                    ):
                        with mock.patch.object(language, "detect_langs", return_value=[]):
                            language._detect_with_langid.cache_clear()
                            lang, confidence = language.detect_language_details(
                                "Guten Tag zusammen."
                            )

        self.assertEqual(lang, "de")
        self.assertGreaterEqual(confidence, 0.88)
        stub_translator.detect.assert_called_once()
        patched_get.assert_called()

    def test_detect_with_google_disabled_returns_none(self):
        language._detect_with_google.cache_clear()
        lang, confidence = language._detect_with_google("Hello")

        self.assertIsNone(lang)
        self.assertEqual(confidence, 0.0)

    def test_detect_language_details_falls_back_to_heuristics_for_invoice(self):
        with mock.patch.object(
            language._LANGID_IDENTIFIER, "classify", return_value=("und", 0.0)
        ):
            with mock.patch.object(language, "detect_langs", return_value=[]):
                language._detect_with_langid.cache_clear()
                lang, confidence = language.detect_language_details("Invoice")

        self.assertEqual(lang, "en")
        self.assertGreaterEqual(confidence, 0.9)

    def test_detect_language_details_uses_langdetect_fallback(self):
        text = "Esto es una prueba importante para la localización del sistema."
        spanish_guess = SimpleNamespace(lang="es", prob=0.93)

        with mock.patch.object(language, "_heuristic_detect", return_value=(None, 0.0)):
            with mock.patch.object(
                language._LANGID_IDENTIFIER, "classify", return_value=("und", 0.0)
            ):
                with mock.patch.object(language, "detect_langs", return_value=[spanish_guess]):
                    language._detect_with_langid.cache_clear()
                    lang, confidence = language.detect_language_details(text)

        self.assertEqual(lang, "es")
        self.assertGreaterEqual(confidence, 0.93)

    def test_is_untranslated_flags_empty_or_matching_strings(self):
        self.assertTrue(language.is_untranslated("Order", ""))
        self.assertTrue(language.is_untranslated("Order", "Order"))
        self.assertFalse(language.is_untranslated("Order", "Commande"))

    def test_language_helper_wrappers(self):
        self.assertTrue(language.is_french_text("Veuillez confirmer la commande."))
        self.assertTrue(language.is_english_text("Please confirm the order."))

    def test_extract_module_name_handles_common_paths(self):
        cases = {
            "/opt/odoo/addons/sale/i18n/fr.po": "sale",
            r"C:\odoo\modules\stock\i18n\en.po": "stock",
            "./random/path.po": "unknown",
        }

        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertEqual(language.extract_module_name(path), expected)

    def test_sanitize_text_trims_whitespace(self):
        self.assertEqual(language.sanitize_text("  hello world  \n"), "hello world")
        self.assertEqual(language.sanitize_text(None), "")


if __name__ == "__main__":
    unittest.main()
