#!/usr/bin/env python3
"""Interactive debugging helper for translation issues.

Historically this script exited during module import which caused the test
runner to fail.  It now provides a ``main`` helper so manual debugging is
unchanged while imports remain side-effect free.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Iterable


def _bootstrap_translator():
    """Import translator utilities lazily for debug sessions."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    from po_translator.translator import Translator  # type: ignore
    from po_translator.utils.logger import setup_logger  # type: ignore

    setup_logger('po_translator', level=logging.DEBUG)
    return Translator()


def _iter_cases() -> Iterable[str]:
    return (
        "Client",
        "Bon de commande",
        "Article",
        "Hello World",
    )


def _require_api_key() -> str:
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        return api_key

    config_file = os.path.join(os.path.dirname(__file__), '.config')
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as handle:
            return handle.read().strip()
    raise SystemExit(
        "ERROR: No API key found!\n"
        "Set GEMINI_API_KEY environment variable or create .config file"
    )


def _run_debug(translator) -> None:
    print("=" * 60)
    print("TRANSLATION DEBUG TEST")
    print("=" * 60)

    api_key = _require_api_key()
    translator.set_api_key(api_key)
    translator.set_languages(source_lang='en', target_lang='fr', auto_detect=True)

    test_cases = list(_iter_cases())
    print(f"\nTesting {len(test_cases)} translations...\n")

    for index, text in enumerate(test_cases, 1):
        print(f"\n{'=' * 60}")
        print(f"Test {index}/{len(test_cases)}: '{text}'")
        print(f"{'=' * 60}")

        result = translator.translate(
            text,
            from_lang='fr',
            to_lang='en',
            context="Odoo ERP",
        )

        print(f"\n✅ Result: '{text}' → '{result}'")
        print(f"   Same as original: {text == result}")

    print(f"\n{'=' * 60}")
    print("STATISTICS")
    print(f"{'=' * 60}")
    stats = translator.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print(f"\n{'=' * 60}")
    print("TEST COMPLETE")
    print(f"{'=' * 60}\n")


def main() -> int:
    translator = _bootstrap_translator()
    _run_debug(translator)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
