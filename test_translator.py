#!/usr/bin/env python3
"""
Quick test script for the translator
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from po_translator.translator import Translator
from po_translator.utils.logger import setup_logger

# Setup logging
setup_logger('DEBUG')

print("="*60)
print("PO Translator - Quick Test")
print("="*60)

# Test 1: Initialize translator
print("\n1. Initializing translator...")
translator = Translator()

# Check if API key is available
api_key = os.environ.get('GEMINI_API_KEY')
if api_key:
    translator.set_api_key(api_key)
    print(f"   [OK] API key loaded from environment")
else:
    print(f"   [WARNING] No API key found. Set GEMINI_API_KEY environment variable.")
    print(f"   Translator will not work without API key.")
    sys.exit(1)

# Test 2: Set languages
print("\n2. Setting languages (English -> French)...")
translator.set_languages('en', 'fr', auto_detect=True)
print(f"   [OK] Languages set")

# Test 3: Test basic translation
print("\n3. Testing basic translations...")
test_cases = [
    ("Purchase Order", "en", "fr"),
    ("Invoice", "en", "fr"),
    ("Customer", "en", "fr"),
    ("Bon de commande", "fr", "en"),  # Should detect French and translate
]

for text, from_lang, to_lang in test_cases:
    result = translator.translate(text, from_lang, to_lang, context="Odoo ERP")
    print(f"   {text} ({from_lang}->{to_lang}) => {result}")

# Test 4: Test variable preservation
print("\n4. Testing variable preservation...")
test_vars = [
    "Welcome %(name)s!",
    "You have %s new messages",
    "Total: {amount} {currency}",
    "Order ${ref} confirmed"
]

for text in test_vars:
    result = translator.translate(text, 'en', 'fr', context="Odoo ERP")
    print(f"   {text}")
    print(f"   => {result}")

# Test 5: Show statistics
print("\n5. Translation statistics:")
stats = translator.get_stats()
for key, value in stats.items():
    print(f"   {key}: {value}")

print("\n" + "="*60)
print("Test completed!")
print("="*60)

