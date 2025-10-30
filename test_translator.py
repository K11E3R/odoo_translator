#!/usr/bin/env python3
"""Quick smoke-test helper for the translator.

This module used to execute immediately when imported, which broke
``python -m unittest`` discovery.  It now exposes a ``main`` helper so the
script can still be launched manually while staying import-safe.
"""

from __future__ import annotations

import os
import sys
from typing import Iterable, Tuple


def _bootstrap_translator():
    """Import the translator lazily and configure logging."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    from po_translator.translator import Translator  # type: ignore
    from po_translator.utils.logger import setup_logger  # type: ignore

    setup_logger('DEBUG')
    return Translator()


def _run_smoke_tests(translator) -> None:
    print("=" * 60)
    print("PO Translator - Quick Test")
    print("=" * 60)

    print("\n1. Initializing translator...")
    api_key = os.environ.get('GEMINI_API_KEY')
    if api_key:
        translator.set_api_key(api_key)
        print("   [OK] API key loaded from environment")
    else:
        print("   [WARNING] No API key found. Set GEMINI_API_KEY environment variable.")
        print("   Translator will not work without API key.")

    print("\n2. Setting languages (English -> French)...")
    translator.set_languages('en', 'fr', auto_detect=True)
    print("   [OK] Languages set")

    print("\n3. Testing basic translations...")
    test_cases: Iterable[Tuple[str, str, str]] = (
        ("Purchase Order", "en", "fr"),
        ("Invoice", "en", "fr"),
        ("Customer", "en", "fr"),
        ("Bon de commande", "fr", "en"),
    )

    for text, from_lang, to_lang in test_cases:
        result = translator.translate(text, from_lang, to_lang, context="Odoo ERP")
        print(f"   {text} ({from_lang}->{to_lang}) => {result}")

    print("\n4. Testing variable preservation...")
    test_vars = (
        "Welcome %(name)s!",
        "You have %s new messages",
        "Total: {amount} {currency}",
        "Order ${ref} confirmed",
    )

    for text in test_vars:
        result = translator.translate(text, 'en', 'fr', context="Odoo ERP")
        print(f"   {text}")
        print(f"   => {result}")

    print("\n5. Translation statistics:")
    for key, value in translator.get_stats().items():
        print(f"   {key}: {value}")

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


def main() -> int:
    translator = _bootstrap_translator()
    _run_smoke_tests(translator)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
