"""PO merge regression tests for gettext identity."""
from pathlib import Path
import tempfile

import polib

from po_translator.core.indexer import ModuleIndexer
from po_translator.core.merger import POMerger


def _write_po(path: Path, entries):
    po = polib.POFile()
    po.metadata = {"Content-Type": "text/plain; charset=UTF-8", "Language": "fr"}
    for entry in entries:
        po.append(entry)
    po.save(str(path))


def test_context_and_plural_identity_are_not_collapsed(tmp_path):
    path = tmp_path / "fr.po"
    _write_po(
        path,
        [
            polib.POEntry(msgctxt="field", msgid="Name", msgstr="Nom"),
            polib.POEntry(msgctxt="view", msgid="Name", msgstr="Nom affiché"),
            polib.POEntry(
                msgid="Invoice",
                msgid_plural="Invoices",
                msgstr_plural={0: "Facture", 1: "Factures"},
            ),
            polib.POEntry(msgid="Invoice", msgstr="Facture (label)"),
        ],
    )
    merger = POMerger()
    merged = merger.merge_files([path])
    assert len(merged) == 4
    assert merger.get_entry("Name", msgctxt="field").msgstr == "Nom"
    assert merger.get_entry("Name", msgctxt="view").msgstr == "Nom affiché"
    assert merger.get_entry("Invoice", msgid_plural="Invoices") is not None


def test_duplicate_identity_merges_occurrences_and_translation(tmp_path):
    first = tmp_path / "first.po"
    second = tmp_path / "second.po"
    _write_po(first, [polib.POEntry(msgid="Customer", msgstr="")])
    _write_po(second, [polib.POEntry(msgid="Customer", msgstr="Client")])
    merger = POMerger()
    merged = merger.merge_files([first, second])
    assert len(merged) == 1
    assert next(iter(merged.values())).msgstr == "Client"


def test_module_indexer_keys_same_msgid_by_context():
    indexer = ModuleIndexer()
    field_entry = polib.POEntry(msgctxt="field", msgid="Name")
    view_entry = polib.POEntry(msgctxt="view", msgid="Name")
    indexer.index_entry(field_entry, "/odoo/addons/sale/i18n/fr.po", field_entry)
    indexer.index_entry(view_entry, "/odoo/addons/stock/i18n/fr.po", view_entry)
    assert indexer.get_module(field_entry) == "sale"
    assert indexer.get_module(view_entry) == "stock"

def test_cleaner_preserves_whitespace_in_msgid_and_msgstr():
    entry = polib.POEntry(msgid=" Customer ", msgstr=" Client ")
    cleaned = POMerger().cleaner.clean_entries([entry])
    assert cleaned[0].msgid == " Customer "
    assert cleaned[0].msgstr == " Client "


def test_editing_entry_rekeys_identity_and_rebuilds_module_index(tmp_path):
    po_path = tmp_path / "addons" / "sale" / "i18n" / "fr.po"
    po_path.parent.mkdir(parents=True)
    _write_po(po_path, [polib.POEntry(msgctxt="field", msgid="Name", msgstr="Nom")])
    merger = POMerger()
    merger.merge_files([po_path])
    entry = merger.get_entry("Name", msgctxt="field")
    assert merger.update_entry(entry, new_msgid="Display Name", new_msgstr="Nom affiché")
    assert merger.get_entry("Name", msgctxt="field") is None
    assert merger.get_entry("Display Name", msgctxt="field") is entry
    assert merger.indexer.get_module(entry) == "sale"


def test_edit_rejects_identity_collision_without_mutating_entry():
    first = polib.POEntry(msgctxt="field", msgid="Name", msgstr="Nom")
    second = polib.POEntry(msgctxt="field", msgid="Other", msgstr="Autre")
    merger = POMerger()
    merger.merged_entries[merger.cleaner.entry_key(first)] = first
    merger.merged_entries[merger.cleaner.entry_key(second)] = second
    assert not merger.update_entry(second, new_msgid="Name", new_msgstr="Changed")
    assert second.msgctxt == "field"
    assert second.msgid == "Other"
    assert second.msgstr == "Autre"
