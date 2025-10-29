"""File utility functions"""
import re


def extract_module_name(filepath):
    """
    Extract module name from .po file path
    
    Args:
        filepath: Path to .po file (e.g., /path/addons/module_name/i18n/fr.po)
        
    Returns:
        str: Module name or 'unknown' if not found
    """
    if not filepath:
        return 'unknown'
    
    pattern = r'(?:addons|modules)[/\\]([^/\\]+)[/\\]i18n'
    match = re.search(pattern, filepath)
    
    if match:
        return match.group(1)
    
    return 'unknown'


def sanitize_text(text):
    """
    Sanitize text for translation (remove extra whitespace, etc.)
    
    Args:
        text: Text to sanitize
        
    Returns:
        str: Sanitized text
    """
    if not text:
        return ""
    
    return text.strip()


def validate_po_entry(entry):
    """
    Validate PO entry has required fields
    
    Args:
        entry: polib.POEntry object
        
    Returns:
        bool: True if valid
    """
    return bool(entry.msgid)

