#!/usr/bin/env python3
"""Clear translation cache"""
import os
from pathlib import Path

cache_dir = Path.home() / '.po_translator'
cache_file = cache_dir / 'translation_cache.json'

if cache_file.exists():
    os.remove(cache_file)
    print(f"✅ Cleared cache: {cache_file}")
else:
    print(f"ℹ️  No cache found at: {cache_file}")

print("\n🔄 Cache cleared! Translations will be fresh.")

