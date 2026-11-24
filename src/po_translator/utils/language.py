"""Offline-first language detection for short Odoo UI strings.

Lingua is used when installed. A compact deterministic heuristic is used otherwise.
This module never downloads language models or calls external detection services at import time.
"""
from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Optional

LOGGER = logging.getLogger(__name__)

PRIMARY_LANGUAGES = {"en", "fr", "es", "de", "it", "pt", "nl", "ar"}
_WORDS = {
    "en": {"the", "and", "with", "please", "order", "invoice", "customer", "confirm", "create", "delete", "settings"},
    "fr": {"le", "la", "les", "une", "un", "des", "et", "veuillez", "commande", "facture", "client", "créer", "confirmer", "livraison"},
    "es": {"el", "la", "los", "las", "una", "un", "y", "por", "favor", "pedido", "factura", "cliente", "confirmar", "crear"},
    "de": {"der", "die", "das", "und", "bitte", "bestellung", "rechnung", "kunde", "erstellen"},
    "it": {"il", "lo", "la", "gli", "una", "e", "per", "favore", "ordine", "fattura", "cliente", "confermare"},
    "pt": {"o", "a", "os", "as", "uma", "e", "por", "favor", "pedido", "fatura", "cliente", "confirmar"},
    "nl": {"de", "het", "een", "en", "bestelling", "factuur", "klant", "bevestigen"},
}
_LINGUA = None
try:
    from lingua import Language, LanguageDetectorBuilder
    _LANGUAGE_MAP = {
        "en": Language.ENGLISH, "fr": Language.FRENCH, "es": Language.SPANISH,
        "de": Language.GERMAN, "it": Language.ITALIAN, "pt": Language.PORTUGUESE,
        "nl": Language.DUTCH,
    }
    _LINGUA = LanguageDetectorBuilder.from_languages(*_LANGUAGE_MAP.values()).build()
except (ImportError, RuntimeError, ValueError):
    LOGGER.info("Lingua unavailable; using local language heuristics")

@lru_cache(maxsize=8192)
def detect_language_details(text: str, min_confidence: float = 0.3,
                            expected_language: Optional[str] = None) -> tuple[Optional[str], float]:
    if not text or not text.strip():
        return None, 0.0
    value = re.sub(r"\s+", " ", text).strip()
    if re.search(r"[\u0600-\u06ff]", value):
        return "ar", 0.99

    if _LINGUA is not None:
        try:
            rows = _LINGUA.compute_language_confidence_values(value)
            if rows:
                top = rows[0]
                code = next((c for c, language in _LANGUAGE_MAP.items() if language == top.language), None)
                confidence = float(top.value)
                if expected_language in _LANGUAGE_MAP:
                    expected = next((r for r in rows if r.language == _LANGUAGE_MAP[expected_language]), None)
                    if expected and expected.value >= confidence * 0.92:
                        return expected_language, float(expected.value)
                if code and confidence >= min_confidence:
                    return code, confidence
        except Exception:
            LOGGER.debug("Lingua detection failed; using heuristics", exc_info=True)

    tokens = re.findall(r"[^\W\d_]+", value.casefold(), flags=re.UNICODE)
    if not tokens:
        return None, 0.0
    scores = {code: sum(token in vocabulary for token in tokens) for code, vocabulary in _WORDS.items()}
    if expected_language in scores and scores[expected_language] > 0:
        scores[expected_language] += 0.15
    best = max(scores, key=scores.get)
    total_hits = scores[best]
    if total_hits == 0:
        # Diacritics offer weak evidence, never a fabricated high-confidence result.
        if any(char in value for char in "àâçéèêëîïôùûüÿœ"):
            return "fr", 0.55
        if any(char in value for char in "áíóúñ¿¡"):
            return "es", 0.55
        return None, 0.0
    confidence = min(0.95, 0.5 + total_hits / max(1, len(tokens)) * 0.45)
    return (best, confidence) if confidence >= min_confidence else (None, confidence)

def detect_language(text: str, min_confidence: float = 0.3) -> Optional[str]:
    code, _ = detect_language_details(text, min_confidence)
    return code

def detect_language_with_context(text: str, context_texts=None, min_confidence: float = 0.3,
                                 expected_language: Optional[str] = None):
    lang, confidence = detect_language_details(text, min_confidence, expected_language)
    if confidence >= 0.85 or not context_texts:
        return lang, confidence
    votes = {}
    for item in context_texts:
        detected, score = detect_language_details(item, min_confidence)
        if detected and score >= 0.4:
            votes[detected] = votes.get(detected, 0) + 1
    if votes:
        context_lang = max(votes, key=votes.get)
        if votes[context_lang] >= max(2, len(votes)):
            return context_lang, max(confidence, 0.65)
    return lang, confidence

def is_french_text(text: str) -> bool:
    return detect_language(text) == "fr"

def is_english_text(text: str) -> bool:
    return detect_language(text) == "en"

def is_untranslated(msgid: str, msgstr: str) -> bool:
    return not msgstr or not msgstr.strip() or msgid.strip() == msgstr.strip()

def extract_module_name(filepath: str) -> str:
    if not filepath:
        return "unknown"
    match = re.search(r"(?:addons|modules)[/\\]([^/\\]+)[/\\]i18n", filepath)
    return match.group(1) if match else "unknown"

def sanitize_text(text: str | None) -> str:
    return text.strip() if text else ""

def validate_po_entry(entry) -> bool:
    return bool(getattr(entry, "msgid", ""))
