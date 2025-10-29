#!/usr/bin/env python3
"""
Debug script to test translation with detailed logging
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from po_translator.translator import Translator
from po_translator.utils.logger import setup_logger
import logging

# Setup detailed logging
logger = setup_logger('po_translator', level=logging.DEBUG)

# Get API key
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    # Try to load from .config
    config_file = os.path.join(os.path.dirname(__file__), '.config')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            api_key = f.read().strip()

if not api_key:
    print("ERROR: No API key found!")
    print("Set GEMINI_API_KEY environment variable or create .config file")
    sys.exit(1)

print("="*60)
print("TRANSLATION DEBUG TEST")
print("="*60)

# Initialize translator
translator = Translator(api_key)
translator.set_languages(source_lang='en', target_lang='fr', auto_detect=True)

# Test cases
test_cases = [
    "Client",           # French word (should be detected)
    "Bon de commande",  # French phrase
    "Article",          # French word
    "Hello World",      # English phrase
]

print(f"\nTesting {len(test_cases)} translations...\n")

for i, text in enumerate(test_cases, 1):
    print(f"\n{'='*60}")
    print(f"Test {i}/{len(test_cases)}: '{text}'")
    print(f"{'='*60}")
    
    result = translator.translate(
        text,
        from_lang='fr',
        to_lang='en',
        context="Odoo ERP"
    )
    
    print(f"\n✅ Result: '{text}' → '{result}'")
    print(f"   Same as original: {text == result}")

print(f"\n{'='*60}")
print("STATISTICS")
print(f"{'='*60}")
stats = translator.get_stats()
for key, value in stats.items():
    print(f"  {key}: {value}")

print(f"\n{'='*60}")
print("TEST COMPLETE")
print(f"{'='*60}\n")

