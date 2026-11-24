"""Index PO entries by their complete gettext identity."""
from __future__ import annotations

import re

from po_translator.utils.file_utils import extract_module_name


def entry_identity(entry):
    """Return gettext identity: context, singular id and plural id."""
    return (
        getattr(entry, "msgctxt", None) or "",
        getattr(entry, "msgid", "") or "",
        getattr(entry, "msgid_plural", None) or "",
    )


class ModuleIndexer:
    """Track module/model metadata without conflating equal msgids."""

    def __init__(self):
        self.entry_to_module = {}
        self.entry_to_model = {}
        self.entry_to_field = {}
        self.entry_to_occurrence = {}
        self.module_to_entries = {}

    @staticmethod
    def _key(identifier, entry=None):
        candidate = entry if entry is not None else identifier
        if hasattr(candidate, "msgid"):
            return entry_identity(candidate)
        return candidate

    def index_entry(self, entry_id, filepath, entry=None):
        key = self._key(entry_id, entry)
        module_name = "unknown"
        model_info = None

        comment = getattr(entry, "comment", "") if entry is not None else ""
        if comment:
            match = re.search(r"module:\s*([\w.]+)", comment)
            if match:
                module_name = match.group(1)

        if module_name == "unknown":
            module_name = extract_module_name(filepath)

        for occ_file, _occ_line in (getattr(entry, "occurrences", []) or []):
            if "model:" not in occ_file:
                continue
            self.entry_to_occurrence[key] = occ_file
            parts = occ_file.split(":")
            if len(parts) >= 2:
                model_parts = parts[1].split(",")
                if model_parts:
                    model_info = model_parts[0]
            if len(parts) >= 3:
                self.entry_to_field[key] = parts[2]
            break

        self.entry_to_module[key] = module_name
        if model_info:
            self.entry_to_model[key] = model_info
        self.module_to_entries.setdefault(module_name, [])
        if key not in self.module_to_entries[module_name]:
            self.module_to_entries[module_name].append(key)

    def _lookup(self, mapping, identifier, default=None):
        key = self._key(identifier)
        if key in mapping:
            return mapping[key]
        # Backward compatibility for callers that only have a msgid.
        if isinstance(identifier, str):
            matches = [value for candidate, value in mapping.items()
                       if isinstance(candidate, tuple) and len(candidate) == 3
                       and candidate[1] == identifier]
            if matches and len(set(matches)) == 1:
                return matches[0]
        return default

    def get_module(self, entry_id):
        return self._lookup(self.entry_to_module, entry_id, "unknown")

    def get_model(self, entry_id):
        return self._lookup(self.entry_to_model, entry_id)

    def get_field(self, entry_id):
        return self._lookup(self.entry_to_field, entry_id)

    def get_occurrence(self, entry_id):
        return self._lookup(self.entry_to_occurrence, entry_id)

    def get_module_and_model(self, entry_id):
        return self.get_module(entry_id), self.get_model(entry_id)

    def get_full_info(self, entry_id):
        return {
            "module": self.get_module(entry_id),
            "model": self.get_model(entry_id),
            "field": self.get_field(entry_id),
            "occurrence": self.get_occurrence(entry_id),
        }

    def get_entries_by_module(self, module_name):
        return self.module_to_entries.get(module_name, [])

    def get_all_modules(self):
        return sorted(self.module_to_entries)

    def clear(self):
        self.entry_to_module.clear()
        self.entry_to_model.clear()
        self.entry_to_field.clear()
        self.entry_to_occurrence.clear()
        self.module_to_entries.clear()
