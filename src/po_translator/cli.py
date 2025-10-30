"""Command-line interface for translating Odoo PO files.

The desktop GUI remains the primary experience for interactive use, but some
users prefer integrating translations inside automated build or CI pipelines.
This module offers a lightweight CLI that reuses the same Translator core with
optional offline execution.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable, List, Sequence

import polib

from .translator import Translator


def _derive_output_path(input_path: Path, *, output_dir: Path | None, suffix: str, in_place: bool) -> Path:
    if in_place:
        return input_path

    target_dir = output_dir or input_path.parent
    target_dir.mkdir(parents=True, exist_ok=True)

    if suffix:
        return target_dir / f"{input_path.stem}{suffix}{input_path.suffix}"
    return target_dir / input_path.name


def _init_translator(args: argparse.Namespace) -> Translator:
    translator = Translator()

    if args.offline:
        translator.set_offline_mode(True)

    if args.api_key:
        translator.set_api_key(args.api_key)
    elif not translator.offline_mode:
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            translator.set_api_key(api_key)
        else:
            translator.logger.warning(
                "No API key provided. Falling back to offline-only behaviour unless --offline is enabled."
            )
            translator.set_offline_mode(True)

    translator.set_languages(args.source, args.target, auto_detect=not args.no_auto_detect)
    return translator


def _iter_entries(po: polib.POFile, include_obsolete: bool) -> Iterable[polib.POEntry]:
    for entry in po:
        if entry.obsolete and not include_obsolete:
            continue
        yield entry


def _handle_translate(args: argparse.Namespace) -> int:
    translator = _init_translator(args)
    translator.reset_stats()

    translated_files: List[Path] = []
    total_results = {"total": 0, "translated": 0, "skipped": 0, "failed": 0}

    for raw_input in args.inputs:
        input_path = Path(raw_input)
        if not input_path.exists():
            print(f"⚠️  Skipping missing file: {input_path}")
            continue

        po = polib.pofile(str(input_path))
        entries = list(_iter_entries(po, include_obsolete=args.include_obsolete))
        module_name = args.module or po.metadata.get('Project-Id-Version') or None
        results = translator.batch_translate(entries, module=module_name, force=args.force)

        for key in total_results:
            total_results[key] += results.get(key, 0)

        if not args.dry_run:
            output_path = _derive_output_path(
                input_path,
                output_dir=Path(args.output_dir) if args.output_dir else None,
                suffix=args.suffix,
                in_place=args.in_place,
            )
            po.save(str(output_path))
            translated_files.append(output_path)

    stats = translator.get_stats()

    print("Translation summary:")
    print(f"  Files processed : {len(args.inputs)}")
    print(f"  Files written   : {len(translated_files)}")
    print(
        "  Entries         : total={total} translated={translated} skipped={skipped} failed={failed}".format(
            **total_results
        )
    )
    print(
        "  Stats           : cache_hits={cache_hits} offline_requests={offline_requests} api_calls={api_calls}".format(
            **stats
        )
    )

    if args.dry_run:
        print("  (dry run: no files were modified)")

    if not translated_files and not args.dry_run:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Translate Odoo PO files using the PO Translator core engine.")
    subparsers = parser.add_subparsers(dest='command')

    translate = subparsers.add_parser('translate', help='Translate one or more PO files')
    translate.add_argument('inputs', nargs='+', help='Input .po files to translate')
    translate.add_argument('--source', default='en', help='Source language code (default: en)')
    translate.add_argument('--target', default='fr', help='Target language code (default: fr)')
    translate.add_argument('--no-auto-detect', action='store_true', help='Disable automatic language detection')
    translate.add_argument('--module', help='Module name for context prompts')
    translate.add_argument('--api-key', help='Gemini API key (overrides environment variable)')
    translate.add_argument('--offline', action='store_true', help='Force offline glossary translator even if API key exists')
    translate.add_argument('--force', action='store_true', help='Force retranslation of existing msgstr values')
    translate.add_argument('--include-obsolete', action='store_true', help='Include obsolete entries in translation batch')
    translate.add_argument('--dry-run', action='store_true', help='Run validation without saving output files')
    translate.add_argument('--in-place', action='store_true', help='Overwrite original files instead of writing to a new path')
    translate.add_argument('--output-dir', help='Directory for translated files (ignored when --in-place is used)')
    translate.add_argument('--suffix', default='.translated', help='Filename suffix inserted before the extension (default: .translated)')

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == 'translate':
        return _handle_translate(args)

    parser.print_help()
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
