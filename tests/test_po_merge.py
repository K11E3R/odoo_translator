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
