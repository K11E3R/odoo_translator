import os
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from po_translator.translator import Translator  # noqa: E402


class OfflineTranslatorTests(unittest.TestCase):
    def setUp(self):
        self.env_patcher = mock.patch.dict(os.environ, {"PO_TRANSLATOR_OFFLINE_MODE": "1"})
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    def test_offline_translation_basic_phrase(self):
        translator = Translator()
        translator.configure_languages(source="en", target="fr")
        translator.clear_cache()

        result = translator.translate("Confirm the order", from_lang="en", to_lang="fr")

        self.assertEqual(result, "Confirmer la commande")
        stats = translator.get_stats()
        self.assertGreaterEqual(stats["offline_requests"], 1)
        self.assertEqual(stats["api_calls"], 0)

    def test_offline_translation_preserves_placeholders(self):
        translator = Translator()
        translator.configure_languages(source="en", target="fr")
        translator.clear_cache()

        text = "Create %(count)s new invoice"
        result = translator.translate(text, from_lang="en", to_lang="fr")

        self.assertIn("%(count)s", result)
        self.assertTrue(result.startswith("Créer"))

    def test_auto_translate_entry_uses_offline_engine(self):
        translator = Translator()
        translator.configure_languages(source="en", target="fr")
        translator.clear_cache()

        entry = SimpleNamespace(msgid="Customer", msgstr="")
        translated = translator.auto_translate_entry(entry, module="sale")

        self.assertTrue(translated)
        self.assertEqual(entry.msgstr, "Client")

    def test_toggle_offline_mode_off_reenables_online_path(self):
        translator = Translator()
        translator.configure_languages(source="en", target="fr")

        translator.set_offline_mode(False)
        self.assertFalse(translator.offline_mode)

    def test_unsupported_pair_returns_original_text(self):
        translator = Translator()
        translator.configure_languages(source="en", target="de")
        translator.clear_cache()

        result = translator.translate("Confirm the order", from_lang="en", to_lang="de")

        self.assertEqual(result, "Confirm the order")
        stats = translator.get_stats()
        self.assertGreaterEqual(stats["offline_requests"], 1)


if __name__ == "__main__":
    unittest.main()
