"""Focused language detection examples, not a synthetic accuracy claim."""
import unittest

from po_translator.utils.language import detect_language


class OdooLanguageExamples(unittest.TestCase):
    def test_common_sentences(self):
        self.assertEqual(detect_language("Veuillez confirmer la commande"), "fr")
        self.assertEqual(detect_language("Please confirm the order"), "en")
        self.assertEqual(detect_language("Por favor confirme el pedido"), "es")
