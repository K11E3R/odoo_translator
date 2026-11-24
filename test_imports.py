"""Core imports must work without optional GUI or network model downloads."""
import unittest

import polib
from google import genai
from po_translator.core.cleaner import POCleaner
from po_translator.core.indexer import ModuleIndexer
from po_translator.core.merger import POMerger
from po_translator.translator import Translator
from po_translator.gui.app import POTranslatorApp
from po_translator.utils import language


class ImportTests(unittest.TestCase):
    def test_core_components_import(self):
        self.assertTrue(polib)
        self.assertTrue(genai)
        self.assertTrue(POCleaner)
        self.assertTrue(ModuleIndexer)
        self.assertTrue(POMerger)
        self.assertTrue(Translator)
        self.assertTrue(POTranslatorApp)
        self.assertTrue(language.detect_language)
