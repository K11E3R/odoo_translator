from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

import polib

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from po_translator import cli


class CLITestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp(prefix="po_translator_cli_")
        self.sample = Path(self.tmpdir) / "sample.po"
        shutil.copy(Path(__file__).parent / "test_files" / "test_fr_en.po", self.sample)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_offline_translation_in_place(self) -> None:
        exit_code = cli.main(
            [
                'translate',
                str(self.sample),
                '--source', 'fr',
                '--target', 'en',
                '--offline',
                '--in-place',
            ]
        )
        self.assertEqual(exit_code, 0)

        po = polib.pofile(str(self.sample))
        translated = [entry for entry in po if entry.msgstr]
        self.assertGreater(len(translated), 0, "at least one entry should be translated offline")

    def test_dry_run_does_not_modify_files(self) -> None:
        exit_code = cli.main(
            [
                'translate',
                str(self.sample),
                '--source', 'fr',
                '--target', 'en',
                '--offline',
                '--dry-run',
            ]
        )
        self.assertEqual(exit_code, 0, "dry run should complete successfully")

        po = polib.pofile(str(self.sample))
        self.assertTrue(all(not entry.msgstr for entry in po))


class HelperScriptsTestCase(unittest.TestCase):
    def test_test_translator_import_safe(self) -> None:
        module = __import__('test_translator')
        self.assertTrue(callable(getattr(module, 'main', None)))

    def test_test_translation_debug_import_safe(self) -> None:
        module = __import__('test_translation_debug')
        self.assertTrue(callable(getattr(module, 'main', None)))


if __name__ == '__main__':
    unittest.main()
