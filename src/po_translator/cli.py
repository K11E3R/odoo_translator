"""Command-line interface for translating gettext/Odoo PO files."""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

import polib

from po_translator.translator import Translator
from po_translator.utils.language import is_untranslated


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="po-translator", description="Translate Odoo gettext PO files.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("gui", help="Launch the desktop application.")
    translate = sub.add_parser("translate", help="Translate a .po file.")
    translate.add_argument("file", type=Path)
    translate.add_argument("--source", default="en", choices=sorted(Translator.LANGUAGES))
    translate.add_argument("--target", default="fr", choices=sorted(Translator.LANGUAGES))
    translate.add_argument("--offline", action="store_true", help="Use the built-in deterministic glossary; no network/API calls.")
    translate.add_argument("--api-key", help="Gemini API key (prefer GEMINI_API_KEY environment variable).")
    translate.add_argument("--model", help="Gemini model name (or PO_TRANSLATOR_GEMINI_MODEL).")
    output = translate.add_mutually_exclusive_group()
    output.add_argument("--in-place", action="store_true", help="Replace the input file atomically.")
    output.add_argument("--output-dir", type=Path, help="Write output into this directory.")
    translate.add_argument("--suffix", default=".translated", help="Filename suffix when --output-dir is used.")
    translate.add_argument("--dry-run", action="store_true", help="Validate and count work without writing output.")
    translate.add_argument("--include-obsolete", action="store_true", help="Include obsolete entries.")
    translate.add_argument("--force", action="store_true", help="Retranslate existing msgstr values.")
    return parser


def _output_path(source: Path, args) -> Path:
    if args.in_place:
        return source
    directory = args.output_dir or source.parent
    stem = source.stem if args.output_dir else source.stem + args.suffix
    return directory / f"{stem}{source.suffix}"


def _atomic_save(po_file: polib.POFile, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent)
    os.close(fd)
    try:
        po_file.save(temp_path)
        os.replace(temp_path, destination)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def translate_file(args) -> int:
    source = args.file.expanduser().resolve()
    if not source.is_file():
        print(f"Error: input file does not exist: {source}", file=sys.stderr)
        return 2
    try:
        po_file = polib.pofile(str(source), check_for_duplicates=True)
    except Exception as exc:
        print(f"Error: unable to parse {source}: {exc}", file=sys.stderr)
        return 2

    translator = Translator(api_key=args.api_key)
    if args.model:
        translator.model_name = args.model
    if args.offline:
        translator.set_offline_mode(True)
    translator.configure_languages(args.source, args.target, auto_detect=False)

    entries = [entry for entry in po_file if args.include_obsolete or not entry.obsolete]
    if args.dry_run:
        pending = [
            entry for entry in entries
            if args.force or is_untranslated(
                entry.msgid, entry.msgstr, entry.msgstr_plural, entry.msgid_plural
            )
        ]
        print(f"Entries: {len(entries)} | need translation: {len(pending)}")
        print("Dry run: no translations requested, no API calls and no files written.")
        return 0

    translated = skipped = failed = 0
    for entry in entries:
        if not args.force and entry.msgstr and entry.msgstr != entry.msgid:
            skipped += 1
            continue
        before_failed = translator.get_stats()["failed_requests"]
        if translator.auto_translate_entry(entry, force=args.force):
            translated += 1
        elif translator.get_stats()["failed_requests"] > before_failed:
            # In glossary mode, an unknown phrase is intentionally left unchanged.
            # Report it as skipped/unmatched rather than a broken file operation.
            if translator.offline_mode:
                skipped += 1
            else:
                failed += 1
        else:
            skipped += 1

    destination = _output_path(source, args)
    if not args.dry_run:
        try:
            _atomic_save(po_file, destination)
        except Exception as exc:
            print(f"Error: could not write {destination}: {exc}", file=sys.stderr)
            return 1

    mode = "offline glossary" if translator.offline_mode else f"Gemini ({translator.model_name})"
    print(f"Mode: {mode}")
    print(f"Entries: {len(entries)} | translated: {translated} | skipped: {skipped} | failed: {failed}")
    print(f"Output: {destination}")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "gui":
        from po_translator.gui import POTranslatorApp

        POTranslatorApp().run()
        return 0
    if args.command == "translate":
        return translate_file(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
