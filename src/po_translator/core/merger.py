"""PO file merger that preserves complete gettext entry identities."""
from __future__ import annotations

from pathlib import Path

import polib

from po_translator.core.cleaner import POCleaner
from po_translator.core.indexer import ModuleIndexer
from po_translator.utils.logger import get_logger


class POMerger:
    """Merge PO files without collapsing contexts or plural entries."""

    def __init__(self):
        self.cleaner = POCleaner()
        self.indexer = ModuleIndexer()
        self.merged_entries = {}
        self.original_metadata = None
        self.original_header = None
        self.logger = get_logger("po_translator.merger")
        self._entry_sources = {}

    def load_po_file(self, filepath):
        self.logger.info("Loading PO file: %s", filepath)
        try:
            po_file = polib.pofile(str(filepath))
            self.logger.debug("Loaded %s entries from %s", len(po_file), filepath)
            if self.original_metadata is None and po_file.metadata:
                self.original_metadata = dict(po_file.metadata)
            if self.original_header is None and po_file.header:
                self.original_header = po_file.header
            return po_file
        except (OSError, ValueError, UnicodeError) as exc:
            self.logger.exception("Unable to load PO file %s", filepath)
            return None

    def merge_files(self, filepaths):
        self.logger.info("Merging %s PO file(s)", len(filepaths))
        self.merged_entries.clear()
        self.indexer.clear()
        self._entry_sources.clear()
        self.original_metadata = None
        self.original_header = None
        all_entries = []

        for filepath in filepaths:
            po_file = self.load_po_file(filepath)
            if po_file is None:
                continue
            for entry in po_file:
                if entry.obsolete:
                    continue
                all_entries.append((entry, filepath))

        for raw_entry, filepath in all_entries:
            cleaned = self.cleaner.clean_entries([raw_entry])
            if not cleaned:
                continue
            entry = cleaned[0]
            key = self.cleaner.entry_key(entry)
            self.indexer.index_entry(entry, filepath, entry)
            self._entry_sources[key] = filepath
            if key in self.merged_entries:
                self.merged_entries[key] = self.cleaner.merge_entries(
                    self.merged_entries[key], entry
                )
            else:
                self.merged_entries[key] = entry

        self.logger.info("Merged %s distinct gettext entries", len(self.merged_entries))
        return self.merged_entries

    def get_entries_list(self):
        return list(self.merged_entries.values())

    def get_entry(self, msgid, msgctxt=None, msgid_plural=None):
        if isinstance(msgid, tuple):
            return self.merged_entries.get(msgid)
        if msgctxt is not None or msgid_plural is not None:
            return self.merged_entries.get((msgctxt or "", msgid, msgid_plural or ""))
        matches = [entry for entry in self.merged_entries.values() if entry.msgid == msgid]
        return matches[0] if len(matches) == 1 else None

    def update_entry(self, msgid, new_msgid=None, new_msgstr=None,
                     msgctxt=None, msgid_plural=None):
        entry = self.get_entry(msgid, msgctxt, msgid_plural)
        if entry is None:
            return False
        old_key = self.cleaner.entry_key(entry)
        old_module = self.indexer.get_module(entry)
        if new_msgstr is not None:
            entry.msgstr = new_msgstr
        if new_msgid is not None and new_msgid != entry.msgid:
            entry.msgid = new_msgid
        new_key = self.cleaner.entry_key(entry)
        if new_key != old_key:
            if new_key in self.merged_entries:
                self.cleaner.merge_entries(self.merged_entries[new_key], entry)
                del self.merged_entries[old_key]
            else:
                self.merged_entries[new_key] = entry
                del self.merged_entries[old_key]
        if old_module != "unknown":
            self.indexer.index_entry(entry, f"addons/{old_module}/i18n/translation.po", entry)
        return True

    def export_to_file(self, filepath, metadata=None):
        try:
            po_file = polib.POFile()
            if metadata:
                po_file.metadata = dict(metadata)
            elif self.original_metadata:
                po_file.metadata = dict(self.original_metadata)
            else:
                po_file.metadata = {
                    "Project-Id-Version": "Odoo Server",
                    "MIME-Version": "1.0",
                    "Content-Type": "text/plain; charset=UTF-8",
                    "Content-Transfer-Encoding": "8bit",
                }
            if self.original_header:
                po_file.header = self.original_header
            for entry in self.cleaner.sort_entries(self.get_entries_list()):
                po_file.append(entry)
            destination = Path(filepath)
            destination.parent.mkdir(parents=True, exist_ok=True)
            po_file.save(str(destination))
            self.logger.info("Exported %s entries to %s", len(po_file), destination)
            return True
        except (OSError, ValueError, TypeError):
            self.logger.exception("Unable to export PO file to %s", filepath)
            return False

    def compile_mo(self, po_filepath, mo_filepath=None):
        try:
            po_file = polib.pofile(str(po_filepath))
            destination = mo_filepath or str(Path(po_filepath).with_suffix(".mo"))
            po_file.save_as_mofile(str(destination))
            return True
        except (OSError, ValueError, TypeError):
            self.logger.exception("Unable to compile PO file %s", po_filepath)
            return False
