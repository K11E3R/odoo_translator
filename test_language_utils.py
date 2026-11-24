"""Regression tests for local, network-free language detection."""
import os
import unittest
from unittest import mock

os.environ["PO_TRANSLATOR_USE_GOOGLE_DETECTION"] = "0"

from po_translator.utils import language


class LanguageDetectionTests(unittest.TestCase):
    def test_empty_input_is_unknown(self):
        self.assertEqual(language.detect_language_details(""), (None, 0.0))

    def test_arabic_is_detected_from_script(self):
        self.assertEqual(language.detect_language("فاتورة العميل"), "ar")

    def test_french_odoo_sentence(self):
        detected, confidence = language.detect_language_details(
            "Veuillez confirmer la commande et vérifier le montant de la facture."
        )
        self.assertEqual(detected, "fr")
        self.assertGreater(confidence, 0.3)

    def test_english_odoo_sentence(self):
        detected, confidence = language.detect_language_details(
            "Please confirm the order and review the total invoice amount."
        )
        self.assertEqual(detected, "en")
        self.assertGreater(confidence, 0.3)

    def test_plural_entries_are_pending_until_all_forms_exist(self):
        self.assertTrue(language.is_untranslated("Invoice", "", {0: "", 1: ""}))
        self.assertTrue(language.is_untranslated("Invoice", "", {0: "Invoice", 1: ""}))
        self.assertFalse(language.is_untranslated("Invoice", "", {0: "Facture", 1: "Factures"}))

    def test_detection_has_no_network_download_fallback(self):
        import inspect
        source = inspect.getsource(language)
        self.assertNotIn("urlretrieve", source)
        self.assertNotIn("fasttext.load_model", source)

    def test_builtin_heuristics_work_without_optional_lingua(self):
        with mock.patch.object(language, "_LINGUA", None):
            self.assertEqual(language.detect_language("Please confirm the order"), "en")
            self.assertEqual(language.detect_language("Veuillez confirmer la commande"), "fr")

    def test_detection_is_cached(self):
        language.detect_language_details.cache_clear()
        language.detect_language_details("Please confirm the order")
        self.assertGreaterEqual(language.detect_language_details.cache_info().currsize, 1)


if __name__ == "__main__":
    unittest.main()
