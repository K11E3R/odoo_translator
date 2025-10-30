"""Utility functions for language detection and validation"""
from __future__ import annotations

import logging
import os
import re
from functools import lru_cache
from typing import Optional, Tuple

from langdetect import LangDetectException, detect_langs
from langid.langid import LanguageIdentifier, model

try:
    from googletrans import Translator as GoogleTranslator  # type: ignore
except Exception:  # pragma: no cover - optional dependency/network issues
    GoogleTranslator = None  # type: ignore

_GOOGLE_TRANSLATOR_SINGLETON: Optional[GoogleTranslator] = None
_GOOGLE_TRANSLATOR_DISABLED = False

LOGGER = logging.getLogger(__name__)


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


def _normalize_lang_code(code: Optional[str]) -> Optional[str]:
    if not code:
        return None
    primary = code.split("-")[0].lower()
    if primary == "zh":  # Normalise Chinese variants to zh
        return "zh"
    return primary


@lru_cache(maxsize=2048)
def _detect_with_langid(text: str) -> Tuple[Optional[str], float]:
    """Detect language using langid with caching and normalization."""
    if not text or not text.strip():
        return None, 0.0

    lang, confidence = _LANGID_IDENTIFIER.classify(text)
    normalized = _normalize_lang_code(lang)

    # langid occasionally reports related romance languages with slightly better scores.
    # Boost French probability when romance variants share the vocabulary.
    if normalized in {"ca", "ro", "it", "es", "pt"}:
        french_bias = sum(1 for word in FRENCH_INDICATORS if word in text.lower())
        if french_bias >= 3:
            normalized = "fr"
            confidence = max(confidence, 0.82)

    if normalized in {"da", "no", "sv"}:
        english_bias = sum(1 for word in ENGLISH_INDICATORS if word in text.lower())
        if english_bias:
            normalized = "en"
            confidence = max(confidence, 0.8)

    if normalized in {"gl", "ca"} and "commande" in text.lower():
        normalized = "fr"
        confidence = max(confidence, 0.8)

    if normalized not in RELATED_LANGUAGES:
        return normalized, float(confidence)

    return normalized, float(confidence)


def _is_google_detection_enabled() -> bool:
    """Return True when Google-backed detection is allowed."""

    global _GOOGLE_TRANSLATOR_DISABLED

    if _GOOGLE_TRANSLATOR_DISABLED:
        return False

    toggle = os.environ.get("PO_TRANSLATOR_USE_GOOGLE_DETECTION", "1").strip().lower()
    if toggle in {"0", "false", "off"}:
        _GOOGLE_TRANSLATOR_DISABLED = True
        return False

    if GoogleTranslator is None:
        _GOOGLE_TRANSLATOR_DISABLED = True
        return False

    return True


def _get_google_translator() -> Optional[GoogleTranslator]:  # pragma: no cover - thin wrapper
    """Lazy-load Google Translate client when enabled."""

    global _GOOGLE_TRANSLATOR_SINGLETON

    if not _is_google_detection_enabled():
        return None

    if _GOOGLE_TRANSLATOR_SINGLETON is None:
        try:
            _GOOGLE_TRANSLATOR_SINGLETON = GoogleTranslator()
        except Exception as exc:  # pragma: no cover - network/initialisation
            LOGGER.debug("Failed to initialise googletrans: %s", exc)
            _GOOGLE_TRANSLATOR_SINGLETON = None
            _disable_google_detection()
            return None

    return _GOOGLE_TRANSLATOR_SINGLETON


def _disable_google_detection():
    """Disable Google detection for the remainder of the process."""

    global _GOOGLE_TRANSLATOR_DISABLED, _GOOGLE_TRANSLATOR_SINGLETON
    _GOOGLE_TRANSLATOR_DISABLED = True
    _GOOGLE_TRANSLATOR_SINGLETON = None


@lru_cache(maxsize=2048)
def _detect_with_google(text: str) -> Tuple[Optional[str], float]:
    """Detect language using Google Translate with caching."""
    translator = _get_google_translator()

    if not text or not text.strip() or not translator:
        return None, 0.0

    try:
        detection = translator.detect(text)
    except Exception as exc:  # pragma: no cover - network variability
        LOGGER.debug("Google detection failed: %s", exc)
        _disable_google_detection()
        return None, 0.0

    if not detection:
        return None, 0.0

    lang = _normalize_lang_code(getattr(detection, "lang", None))
    confidence = getattr(detection, "confidence", 0.0) or 0.0
    return lang, float(confidence)


def _heuristic_detect(text: str) -> Tuple[Optional[str], float]:
    text_lower = text.lower()
    french_count = sum(1 for word in FRENCH_INDICATORS if word in text_lower)
    english_count = sum(1 for word in ENGLISH_INDICATORS if word in text_lower)

    if french_count > 0 and french_count > english_count:
        return "fr", 0.95
    if english_count > 0 and english_count > french_count:
        return "en", 0.95
    return None, 0.0


def detect_language_details(text: str, min_confidence: float = 0.7) -> Tuple[Optional[str], float]:
    """Detect language and provide confidence.

    Returns the detected language code and a confidence score between 0 and 1.
    """

    if not text or not text.strip():
        return None, 0.0

    # First attempt heuristics for very short strings
    heuristic_lang, heuristic_conf = _heuristic_detect(text)
    if heuristic_lang and heuristic_conf >= min_confidence:
        return heuristic_lang, heuristic_conf

    # Leverage statistical detection for broader coverage
    langid_lang, langid_conf = _detect_with_langid(text)
    if langid_lang and langid_conf >= min_confidence:
        return langid_lang, langid_conf

    # Use Google Translate detection when available
    google_lang, google_conf = _detect_with_google(text)
    if google_lang and google_conf >= min_confidence:
        return google_lang, google_conf

    # Fall back to heuristics even if confidence was low
    if heuristic_lang:
        return heuristic_lang, heuristic_conf

    # Langdetect as a last resort for longer texts
    if len(text.split()) >= 3:
        try:
            langs = detect_langs(text)
        except LangDetectException:
            langs = []
        if langs:
            detected = _normalize_lang_code(langs[0].lang)
            prob = float(langs[0].prob)
            if detected in ['af', 'nl', 'no', 'da', 'sv']:
                return 'fr', prob
            if detected in ['ca', 'ro', 'it', 'es', 'pt'] and heuristic_lang == 'fr':
                return 'fr', max(prob, heuristic_conf)
            if prob >= min_confidence:
                return detected, prob
            return detected, prob

    if langid_lang:
        return langid_lang, langid_conf

    return google_lang or heuristic_lang, max(google_conf, heuristic_conf, langid_conf)


def detect_language(text: str, min_confidence: float = 0.7) -> Optional[str]:
    """Return only the detected language code for convenience."""

    lang, conf = detect_language_details(text, min_confidence=min_confidence)
    if lang and conf >= min_confidence:
        return lang
    return lang


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

# Core language set we care about for Odoo translations
PRIMARY_LANGUAGES = ["en", "fr", "es", "de", "it", "pt", "nl", "ar"]

# Broader family to help disambiguate romance/germanic texts that frequently appear
RELATED_LANGUAGES = PRIMARY_LANGUAGES + [
    "ca",  # Catalan
    "ro",  # Romanian
    "da",  # Danish
    "sv",  # Swedish
    "no",  # Norwegian
    "fi",  # Finnish
    "gl",  # Galician
]

_LANGID_IDENTIFIER = LanguageIdentifier.from_modelstring(model, norm_probs=True)
_LANGID_IDENTIFIER.set_languages(RELATED_LANGUAGES)
