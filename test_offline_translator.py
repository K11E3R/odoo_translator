"""Offline glossary and translation validation regression tests."""
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from po_translator.translator import Translator, TranslationCache


class OfflineTranslatorTests(unittest.TestCase):
    def setUp(self):
        self.env_patcher = mock.patch.dict(
            os.environ,
            {"PO_TRANSLATOR_OFFLINE_MODE": "1", "GEMINI_API_KEY": ""},
        )
        self.env_patcher.start()
        self.tempdir = tempfile.TemporaryDirectory()
        self.translator = Translator(
            cache=TranslationCache(Path(self.tempdir.name) / "cache.json")
        )
        self.translator.configure_languages(source="en", target="fr", auto_detect=False)

    def tearDown(self):
        self.env_patcher.stop()
        self.tempdir.cleanup()

    def test_offline_translation_basic_phrase(self):
        self.assertEqual(
            self.translator.translate("Confirm the order", "en", "fr"),
            "Confirmer la commande",
        )
        stats = self.translator.get_stats()
        self.assertGreaterEqual(stats["offline_requests"], 1)
        self.assertEqual(stats["api_calls"], 0)

    def test_offline_placeholder_translation_preserves_exact_token(self):
        source = "Create %(count)s new invoice"
        result = self.translator.translate(source, "en", "fr")
        self.assertEqual(result, "Créer %(count)s nouvelle facture")
        self.assertTrue(self.translator._validate_translation(source, result))

    def test_duplicate_placeholders_are_counted(self):
        self.assertFalse(self.translator._validate_translation("Hello %s %s", "Bonjour %s"))
        self.assertTrue(self.translator._validate_translation("Hello %s %s", "Bonjour %s %s"))

    def test_markup_is_preserved(self):
        self.assertFalse(self.translator._validate_translation("<b>Hello</b>", "<b>Bonjour"))
        self.assertTrue(self.translator._validate_translation("<b>Hello</b>", "<b>Bonjour</b>"))

    def test_auto_translate_entry_uses_offline_glossary(self):
        entry = SimpleNamespace(msgid="Customer", msgstr="", msgstr_plural={})
        self.assertTrue(self.translator.auto_translate_entry(entry, module="sale"))
        self.assertEqual(entry.msgstr, "Client")

    def test_plural_entry_uses_singular_and_plural_source_strings(self):
        entry = SimpleNamespace(
            msgid="Invoice",
            msgid_plural="Invoices",
            msgstr="",
            msgstr_plural={0: "", 1: ""},
        )
        self.assertTrue(self.translator.auto_translate_entry(entry, module="account"))
        self.assertEqual(entry.msgstr_plural[0], "Facture")
        self.assertEqual(entry.msgstr_plural[1], "Factures")

    def test_translation_preserves_leading_and_trailing_whitespace(self):
        source = "  Customer\\n"
        self.assertEqual(
            self.translator.translate(source, "en", "fr"),
            "  Client\\n",
        )

    def test_unknown_phrase_preserves_original_whitespace(self):
        source = "  a phrase outside the glossary  "
        self.assertEqual(
            self.translator.translate(source, "en", "fr"),
            source,
        )

    def test_unknown_phrase_is_not_falsely_reported_as_translated(self):
        source = "This phrase is not in the bundled dictionary"
        self.assertEqual(self.translator.translate(source, "en", "fr"), source)
        self.assertEqual(self.translator.get_stats()["failed_requests"], 1)

    def test_cache_survives_new_instance_and_uses_hashed_keys(self):
        first = self.translator.translate("Customer", "en", "fr")
        second = Translator(
            cache=TranslationCache(Path(self.tempdir.name) / "cache.json")
        )
        self.assertEqual(second.translate("Customer", "en", "fr"), first)
        cache_text = (Path(self.tempdir.name) / "cache.json").read_text(encoding="utf-8")
        self.assertNotIn("Customer", cache_text)


if __name__ == "__main__":
    unittest.main()
