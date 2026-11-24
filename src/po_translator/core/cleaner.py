"""PO entry validation and merge helpers that respect gettext entry identity."""
from __future__ import annotations

from po_translator.utils.file_utils import sanitize_text, validate_po_entry


class POCleaner:
    """Clean entries without collapsing context-sensitive or plural translations."""

    @staticmethod
    def entry_key(entry):
        # Gettext treats msgctxt + msgid as distinct keys; plural msgids are distinct too.
        return (getattr(entry, "msgctxt", None) or "", entry.msgid, getattr(entry, "msgid_plural", None) or "")

    def clean_entries(self, entries):
        cleaned = []
        for entry in entries:
            if not validate_po_entry(entry):
                continue
            entry.msgid = sanitize_text(entry.msgid)
            if not entry.msgid:
                continue
            entry.msgstr = sanitize_text(getattr(entry, "msgstr", ""))
            cleaned.append(entry)
        return cleaned

    def merge_entries(self, entry1, entry2):
        if getattr(entry2, "msgstr", "") and not getattr(entry1, "msgstr", ""):
            entry1.msgstr = entry2.msgstr
        first_plural = getattr(entry1, "msgstr_plural", {}) or {}
        second_plural = getattr(entry2, "msgstr_plural", {}) or {}
        for index, value in second_plural.items():
            if value and not first_plural.get(index):
                first_plural[index] = value
        if first_plural:
            entry1.msgstr_plural = first_plural
        if getattr(entry2, "comment", "") and not getattr(entry1, "comment", ""):
            entry1.comment = entry2.comment
        if getattr(entry2, "tcomment", "") and not getattr(entry1, "tcomment", ""):
            entry1.tcomment = entry2.tcomment
        if getattr(entry2, "flags", None):
            entry1.flags = sorted(set(getattr(entry1, "flags", [])) | set(entry2.flags))
        existing = set(getattr(entry1, "occurrences", []) or [])
        entry1.occurrences = list(getattr(entry1, "occurrences", []) or [])
        for occurrence in getattr(entry2, "occurrences", []) or []:
            if occurrence not in existing:
                entry1.occurrences.append(occurrence)
                existing.add(occurrence)
        return entry1

    @staticmethod
    def remove_obsolete(entries):
        return [entry for entry in entries if not entry.obsolete]

    @staticmethod
    def sort_entries(entries):
        return sorted(entries, key=lambda entry: (
            (getattr(entry, "msgctxt", None) or "").casefold(),
            entry.msgid.casefold(),
            (getattr(entry, "msgid_plural", None) or "").casefold(),
        ))
