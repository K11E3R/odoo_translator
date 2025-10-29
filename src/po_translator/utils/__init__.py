"""Utility functions and helpers"""

from .language import (
    detect_language,
    is_french_text,
    is_english_text,
    is_untranslated
)
from .file_utils import extract_module_name, sanitize_text, validate_po_entry
from .logger import setup_logger, get_logger

__all__ = [
    'detect_language',
    'is_french_text',
    'is_english_text',
    'is_untranslated',
    'extract_module_name',
    'sanitize_text',
    'validate_po_entry',
    'setup_logger',
    'get_logger',
]

