"""PO parser smoke tests without import-time work or network calls."""
from pathlib import Path
import unittest

import polib


class POLoadingTests(unittest.TestCase):
    def test_sample_po_file_loads(self):
        sample = Path(__file__).parent / "test_files" / "test_fr_en.po"
        parsed = polib.pofile(str(sample))
        self.assertGreater(len(parsed), 0)
        self.assertTrue(any(entry.msgid for entry in parsed))
