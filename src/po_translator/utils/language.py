"""Utility functions for language detection and validation"""
import re
from langdetect import detect, LangDetectException, detect_langs


# Common French words for better detection
FRENCH_INDICATORS = {
    'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'à', 'au', 'aux',
    'est', 'sont', 'être', 'avoir', 'faire', 'pour', 'dans', 'sur', 'avec',
    'commande', 'facture', 'livraison', 'client', 'fournisseur', 'article',
    'paiement', 'devis', 'partenaire', 'bon', 'créer', 'confirmer', 'annuler',
    'veuillez', 'montant', 'total', 'calculé', 'automatiquement', 'saisir',
    'commentaires', 'nouvelle', 'ici'
}

# Common English words
ENGLISH_INDICATORS = {
    'the', 'a', 'an', 'is', 'are', 'be', 'have', 'do', 'for', 'in', 'on', 'with',
    'order', 'invoice', 'delivery', 'customer', 'supplier', 'product', 'payment',
    'quotation', 'partner', 'create', 'confirm', 'cancel', 'please', 'amount',
    'total', 'calculated', 'automatically', 'enter', 'comments', 'new', 'here'
}


def detect_language(text, min_confidence=0.7):
    """
    Detect language with improved accuracy for short texts
    
    Args:
        text: String to detect language from
        min_confidence: Minimum confidence threshold (0.0-1.0)
        
    Returns:
        str: Language code (e.g., 'fr', 'en') or None if detection fails
    """
    if not text or not text.strip():
        return None
    
    text_lower = text.lower()
    
    # Check for French indicators first (more reliable for short texts)
    french_count = sum(1 for word in FRENCH_INDICATORS if word in text_lower)
    english_count = sum(1 for word in ENGLISH_INDICATORS if word in text_lower)
    
    if french_count > 0 and french_count > english_count:
        return 'fr'
    elif english_count > 0 and english_count > french_count:
        return 'en'
    
    # Fall back to langdetect for longer texts
    if len(text.split()) >= 3:  # Only use langdetect for 3+ words
        try:
            # Get probabilities for better accuracy
            langs = detect_langs(text)
            if langs and langs[0].prob >= min_confidence:
                detected = langs[0].lang
                # Map common misdetections
                if detected in ['af', 'nl', 'no', 'da', 'sv']:  # Often confused with French
                    return 'fr'
                elif detected in ['ca', 'ro', 'it', 'es', 'pt']:  # Romance languages
                    # Check if it's actually French
                    if french_count > 0:
                        return 'fr'
                return detected
        except LangDetectException:
            pass
    
    return None


def is_french_text(text):
    """
    Check if text is in French
    
    Args:
        text: String to check
        
    Returns:
        bool: True if text is detected as French
    """
    if not text or not text.strip():
        return False
    
    lang = detect_language(text)
    return lang == 'fr'


def is_english_text(text):
    """
    Check if text is in English
    
    Args:
        text: String to check
        
    Returns:
        bool: True if text is detected as English
    """
    if not text or not text.strip():
        return False
    
    lang = detect_language(text)
    return lang == 'en'


def is_untranslated(msgid, msgstr):
    """
    Check if entry is untranslated (msgid == msgstr or empty msgstr)
    
    Args:
        msgid: Source string
        msgstr: Translation string
        
    Returns:
        bool: True if untranslated
    """
    if not msgstr or not msgstr.strip():
        return True
    
    return msgid.strip() == msgstr.strip()


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

