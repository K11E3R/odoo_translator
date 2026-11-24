"""Reliable Odoo PO translation engine with Gemini and an explicit offline glossary mode."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import threading
import time
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from google import genai
except ImportError:  # Gemini is optional for offline-only installations.
    genai = None

from po_translator.utils.language import detect_language, is_french_text
from po_translator.utils.logger import get_logger


PLACEHOLDER_RE = re.compile(
    r"%\([^)]+\)[#0\- +]?[0-9]*(?:\.[0-9]+)?[diouxXeEfFgGcrsa]"
    r"|%(?:[#0\- +]?[0-9]*(?:\.[0-9]+)?[diouxXeEfFgGcrsa])"
    r"|\$\{[^{}]+\}|\{\{[^{}]+\}\}|\{[^{}]+\}"
)
HTML_TAG_RE = re.compile(r"</?[A-Za-z][^>]*?>")

LANGUAGES = {
    "en": "English", "fr": "French", "es": "Spanish", "de": "German",
    "it": "Italian", "pt": "Portuguese", "nl": "Dutch", "ar": "Arabic",
    "ca": "Catalan", "ro": "Romanian", "da": "Danish", "sv": "Swedish",
    "no": "Norwegian", "fi": "Finnish", "gl": "Galician",
}

# Deterministic phrase/term lookup, not a claim of general-purpose machine translation.
OFFLINE_PHRASES = {
    ("en", "fr"): {
        "confirm the order": "Confirmer la commande",
        "please confirm the order": "Veuillez confirmer la commande",
        "create a new order": "Créer une nouvelle commande",
        "please enter your comments here": "Veuillez saisir vos commentaires ici",
        "the total amount is calculated automatically": "Le montant total est calculé automatiquement",
        "total amount is calculated automatically": "Le montant total est calculé automatiquement",
        "are you sure you want to delete this record?": "Êtes-vous sûr de vouloir supprimer cet enregistrement ?",
        "purchase order": "Bon de commande", "purchase orders": "Bons de commande",
        "invoice": "Facture", "invoices": "Factures", "delivery order": "Bon de livraison",
        "delivery": "Livraison", "customer": "Client", "vendor": "Fournisseur",
        "quotation": "Devis", "product": "Article", "partner": "Partenaire",
        "payment": "Paiement", "warehouse": "Entrepôt", "sales": "Ventes",
        "cancel": "Annuler", "stock": "Stock", "article": "Article",
    },
    ("fr", "en"): {
        "bon de commande": "Purchase Order", "bons de commande": "Purchase Orders",
        "facture": "Invoice", "livraison": "Delivery", "bon de livraison": "Delivery Order",
        "client": "Customer", "fournisseur": "Vendor", "devis": "Quotation",
        "article": "Product", "partenaire": "Partner", "paiement": "Payment",
        "entrepôt": "Warehouse", "ventes": "Sales", "annuler": "Cancel",
        "veuillez saisir vos commentaires ici": "Please enter your comments here",
        "le montant total est calculé automatiquement": "The total amount is calculated automatically",
        "créer une nouvelle commande": "Create a new order",
        "confirmer la commande": "Confirm the order",
        "veuillez confirmer la commande": "Please confirm the order",
    },
    ("en", "es"): {
        "confirm the order": "Confirmar el pedido",
        "create a new order": "Crear un nuevo pedido",
        "purchase order": "Orden de compra", "invoice": "Factura",
        "delivery": "Entrega", "customer": "Cliente", "vendor": "Proveedor",
        "quotation": "Presupuesto", "product": "Producto", "partner": "Contacto",
        "payment": "Pago", "warehouse": "Almacén", "sales": "Ventas", "cancel": "Cancelar",
    },
    ("es", "en"): {
        "orden de compra": "Purchase Order", "factura": "Invoice",
        "entrega": "Delivery", "cliente": "Customer", "proveedor": "Vendor",
        "presupuesto": "Quotation", "producto": "Product", "contacto": "Partner",
        "pago": "Payment", "almacén": "Warehouse", "ventas": "Sales",
        "cancelar": "Cancel", "confirmar el pedido": "Confirm the order",
        "crear un nuevo pedido": "Create a new order",
    },
}


OFFLINE_PATTERNS = {
    ("en", "fr"): [
        (re.compile(r"^Create\s+(?P<value>%\([^)]+\)s|%s)\s+new invoice$", re.I),
         r"Créer \g<value> nouvelle facture"),
        (re.compile(r"^You have\s+(?P<value>%\([^)]+\)s|%s)\s+new messages$", re.I),
         r"Vous avez \g<value> nouveaux messages"),
        (re.compile(r"^Welcome\s+(?P<value>%\([^)]+\)s|%s)!$", re.I),
         r"Bienvenue \g<value> !"),
    ],
    ("fr", "en"): [
        (re.compile(r"^Bienvenue\s+(?P<value>%\([^)]+\)s|%s)\s*!$", re.I),
         r"Welcome \g<value>!"),
    ],
    ("en", "es"): [
        (re.compile(r"^Welcome\s+(?P<value>%\([^)]+\)s|%s)!$", re.I),
         r"¡Bienvenido \g<value>!"),
    ],
}

OFFLINE_WORDS = {
    ("en", "fr"): {
        "create": "Créer", "new": "nouveau", "invoice": "facture",
        "order": "commande", "customer": "client", "vendor": "fournisseur",
        "confirm": "confirmer", "cancel": "annuler", "delivery": "livraison",
        "purchase": "achat", "payment": "paiement", "product": "article",
        "please": "veuillez", "total": "total", "amount": "montant",
    },
    ("fr", "en"): {
        "créer": "Create", "confirmer": "Confirm", "commande": "order",
        "facture": "invoice", "client": "customer", "fournisseur": "vendor",
        "livraison": "delivery", "annuler": "Cancel", "paiement": "payment",
        "montant": "amount", "total": "total", "automatiquement": "automatically",
        "veuillez": "Please", "saisir": "enter", "commentaires": "comments",
    },
    ("en", "es"): {
        "create": "Crear", "new": "nuevo", "order": "pedido", "invoice": "factura",
        "customer": "cliente", "vendor": "proveedor", "confirm": "confirmar",
        "cancel": "cancelar", "delivery": "entrega", "payment": "pago",
        "please": "por favor",
    },
    ("es", "en"): {
        "crear": "Create", "pedido": "order", "factura": "invoice",
        "cliente": "customer", "proveedor": "vendor", "confirmar": "confirm",
        "cancelar": "Cancel", "entrega": "delivery", "pago": "payment",
        "por": "please", "favor": "please",
    },
}


def _normalise(value: str) -> str:
    return " ".join(value.casefold().strip().split())


class TranslationCache:
    """Thread-safe JSON cache written atomically to avoid partial/corrupt files."""

    def __init__(self, cache_file: str | Path | None = None):
        cache_dir = Path.home() / ".po_translator"
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = Path(cache_file) if cache_file else cache_dir / "translation_cache.json"
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.cache: dict[str, str] = self._load_cache()

    def _load_cache(self) -> dict[str, str]:
        try:
            payload = json.loads(self.cache_file.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except FileNotFoundError:
            return {}
        except (OSError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _key(text: str, context: str | None = None) -> str:
        raw = json.dumps([text, context or ""], ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _save(self) -> None:
        temp_name = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=self.cache_file.parent,
                prefix=f".{self.cache_file.name}.", suffix=".tmp", delete=False
            ) as handle:
                temp_name = handle.name
                json.dump(self.cache, handle, ensure_ascii=False, separators=(",", ":"))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.cache_file)
        except OSError:
            if temp_name:
                try:
                    os.unlink(temp_name)
                except OSError:
                    pass
            # Cache failures must not break translation.

    def get(self, text: str, context: str | None = None) -> str | None:
        with self._lock:
            return self.cache.get(self._key(text, context))

    def set(self, text: str, translation: str, context: str | None = None) -> None:
        with self._lock:
            self.cache[self._key(text, context)] = translation
            self._save()

    def clear(self) -> None:
        with self._lock:
            self.cache.clear()
            self._save()


class Translator:
    """Odoo-aware translator. Offline mode is phrase/glossary assistance, not free-form MT."""

    LANGUAGES = {code: {"name": name} for code, name in LANGUAGES.items()}
    ODOO_TERMS = {
        "fr": {"Invoice": "Facture", "Quotation": "Devis", "Sales": "Ventes",
               "Purchase Order": "Bon de commande", "Delivery Order": "Bon de livraison",
               "Partner": "Partenaire", "Customer": "Client", "Vendor": "Fournisseur"},
        "en": {"Facture": "Invoice", "Devis": "Quotation", "Ventes": "Sales",
               "Bon de commande": "Purchase Order", "Client": "Customer"},
    }

    def __init__(self, api_key: str | None = None, cache: TranslationCache | None = None):
        self.logger = get_logger("po_translator.translator")
        self.cache = cache or TranslationCache()
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model_name = os.getenv("PO_TRANSLATOR_GEMINI_MODEL", "gemini-3.5-flash-lite")
        self.client: Any = None
        self.model: Any = None  # Kept for compatibility with the GUI's availability check.
        self.source_lang = "en"
        self.target_lang = "fr"
        self.auto_detect = True
        self.offline_mode = os.getenv("PO_TRANSLATOR_OFFLINE_MODE", "0").strip().lower() in {"1", "true", "yes", "on"}
        self._rate_lock = threading.Lock()
        self._stats_lock = threading.RLock()
        self.last_request = 0.0
        self.rate_limit = max(0.0, float(os.getenv("PO_TRANSLATOR_RATE_LIMIT", "0.2")))
        self.stats = {
            "total_requests": 0, "cache_hits": 0, "api_calls": 0,
            "offline_requests": 0, "translated": 0, "failed_requests": 0,
            "errors": 0, "retries": 0, "auto_corrections": 0,
        }
        if self.api_key:
            self.set_api_key(self.api_key)

    def set_offline_mode(self, enabled: bool | None = None) -> bool:
        """Enable deterministic local glossary translation without any API calls."""
        new_value = (
            os.getenv("PO_TRANSLATOR_OFFLINE_MODE", "0").strip().lower() in {"1", "true", "yes", "on"}
            if enabled is None else bool(enabled)
        )
        changed = new_value != self.offline_mode
        self.offline_mode = new_value
        return changed

    def set_api_key(self, api_key: str) -> bool:
        self.api_key = (api_key or "").strip()
        if not self.api_key:
            self.client = self.model = None
            return False
        if genai is None:
            self.logger.error("Gemini SDK missing. Install the google-genai package.")
            self.client = self.model = None
            return False
        try:
            self.client = genai.Client(api_key=self.api_key)
            self.model = self.client
            self.logger.info("Gemini client initialized with model %s", self.model_name)
            return True
        except Exception:
            self.logger.exception("Gemini client initialization failed")
            self.client = self.model = None
            return False

    def configure_languages(self, source: str | None = None, target: str | None = None,
                            auto_detect: bool | None = None) -> bool:
        changed = False
        if source is not None:
            if source not in self.LANGUAGES:
                raise ValueError(f"Unsupported source language: {source}")
            if source != self.source_lang:
                self.source_lang = source
                changed = True
        if target is not None:
            if target not in self.LANGUAGES:
                raise ValueError(f"Unsupported target language: {target}")
            if target != self.target_lang:
                self.target_lang = target
                changed = True
        if auto_detect is not None and bool(auto_detect) != self.auto_detect:
            self.auto_detect = bool(auto_detect)
            changed = True
        return changed

    def set_languages(self, source: str, target: str, auto_detect: bool = True) -> None:
        self.configure_languages(source, target, auto_detect)

    def _get_prompt(self, from_lang: str, to_lang: str, context: str | None = None) -> str:
        if from_lang not in self.LANGUAGES or to_lang not in self.LANGUAGES:
            raise ValueError("Unsupported language code")
        glossary = json.dumps(self.ODOO_TERMS.get(to_lang, {}), ensure_ascii=False)
        return (
            f"You are a professional Odoo ERP software translator. Translate from "
            f"{self.LANGUAGES[from_lang]['name']} to {self.LANGUAGES[to_lang]['name']}.\n"
            f"Context: {context or 'Odoo ERP'}.\n"
            "Return only the translated text. Preserve every placeholder, HTML/XML tag, "
            "newline and formatting token exactly. Do not add explanations or quotation marks.\n"
            f"Use these preferred Odoo terms where relevant: {glossary}\n\n"
            "The next line contains the source text as a JSON-escaped string:\n"
        )

    def _rate_limit(self) -> None:
        # Serialize the check and update so concurrent GUI workers cannot burst together.
        with self._rate_lock:
            elapsed = time.monotonic() - self.last_request
            if elapsed < self.rate_limit:
                time.sleep(self.rate_limit - elapsed)
            self.last_request = time.monotonic()

    @staticmethod
    def _validate_translation(src: str, trans: str) -> bool:
        if not trans or not trans.strip():
            return False
        if Counter(PLACEHOLDER_RE.findall(src)) != Counter(PLACEHOLDER_RE.findall(trans)):
            return False
        if Counter(HTML_TAG_RE.findall(src)) != Counter(HTML_TAG_RE.findall(trans)):
            return False
        if src.count("\n") != trans.count("\n"):
            return False
        return True

    @staticmethod
    def _offline_translate(text: str, from_lang: str, to_lang: str) -> str | None:
        pair = (from_lang, to_lang)
        phrases = OFFLINE_PHRASES.get(pair)
        if not phrases:
            return None

        # Protect placeholders and markup before applying local terminology substitutions.
        protected: list[str] = []
        token_re = re.compile(
            PLACEHOLDER_RE.pattern + r"|</?[A-Za-z][^>]*?>",
        )
        def protect(match: re.Match[str]) -> str:
            protected.append(match.group(0))
            return f"POKEEP{len(protected) - 1}TOKEN"

        safe_text = token_re.sub(protect, text)
        exact_pattern = next(
            (pattern.sub(replacement, text) for pattern, replacement in OFFLINE_PATTERNS.get(pair, [])
             if pattern.fullmatch(text)),
            None,
        )
        exact = phrases.get(_normalise(safe_text))
        if exact_pattern is not None:
            result = exact_pattern
        elif exact is not None:
            result = exact
        else:
            result = safe_text
            for term in sorted(phrases, key=len, reverse=True):
                if len(term) < 3:
                    continue
                result = re.sub(
                    rf"(?<!\w){re.escape(term)}(?!\w)",
                    phrases[term], result, flags=re.IGNORECASE
                )
            for term, replacement in sorted(OFFLINE_WORDS.get(pair, {}).items(), key=lambda item: len(item[0]), reverse=True):
                result = re.sub(
                    rf"(?<!\w){re.escape(term)}(?!\w)",
                    replacement, result, flags=re.IGNORECASE
                )
        for index, original in enumerate(protected):
            result = result.replace(f"POKEEP{index}TOKEN", original)
        return result if result != text else None

    def translate(self, text: str, from_lang: str | None = None, to_lang: str | None = None,
                  context: str | None = None, max_retries: int = 1) -> str:
        if not text:
            return text
        original_text = text
        # Preserve intentional whitespace in gettext strings. Translate only
        # the core text and reattach the exact original prefix/suffix.
        leading = text[:len(text) - len(text.lstrip())]
        trailing = text[len(text.rstrip()):]
        end = len(text) - len(trailing) if trailing else len(text)
        core_text = text[len(leading):end]
        if not core_text:
            return text
        text = core_text
        from_lang = from_lang or self.source_lang
        to_lang = to_lang or self.target_lang
        if from_lang not in self.LANGUAGES or to_lang not in self.LANGUAGES:
            raise ValueError(f"Unsupported language pair: {from_lang} -> {to_lang}")

        with self._stats_lock:
            self.stats["total_requests"] += 1
        cache_context = f"{from_lang}>{to_lang}|{context or ''}|{self.model_name}"
        cached = self.cache.get(text, cache_context)
        if cached is not None:
            with self._stats_lock:
                self.stats["cache_hits"] += 1
            return leading + cached + trailing

        if self.offline_mode:
            with self._stats_lock:
                self.stats["offline_requests"] += 1
            translated = self._offline_translate(text, from_lang, to_lang)
            if translated and self._validate_translation(text, translated):
                self.cache.set(text, translated, cache_context)
                with self._stats_lock:
                    self.stats["translated"] += 1
                return leading + translated + trailing
            with self._stats_lock:
                self.stats["failed_requests"] += 1
            return original_text

        if self.client is None:
            with self._stats_lock:
                self.stats["failed_requests"] += 1
            self.logger.warning("Translation skipped: no Gemini API key/client configured")
            return original_text

        prompt = self._get_prompt(from_lang, to_lang, context) + "\n" + json.dumps(text, ensure_ascii=False)
        for attempt in range(max_retries + 1):
            try:
                self._rate_limit()
                with self._stats_lock:
                    self.stats["api_calls"] += 1
                interaction = self.client.interactions.create(
                    model=self.model_name,
                    input=prompt,
                )
                translated = (getattr(interaction, "output_text", None) or "").strip()
                if self._validate_translation(text, translated):
                    self.cache.set(text, translated, cache_context)
                    with self._stats_lock:
                        self.stats["translated"] += 1
                    return leading + translated + trailing
                self.logger.warning("Rejected invalid translation (placeholder/markup mismatch)")
            except Exception:
                with self._stats_lock:
                    self.stats["errors"] += 1
                self.logger.exception("Gemini translation request failed")
            if attempt < max_retries:
                with self._stats_lock:
                    self.stats["retries"] += 1
                time.sleep(min(2 ** attempt, 4))
        with self._stats_lock:
            self.stats["failed_requests"] += 1
        return original_text

    def auto_translate_entry(self, entry: Any, module: str | None = None, force: bool = False) -> bool:
        msgid = getattr(entry, "msgid", "") or ""
        if not msgid.strip():
            return False
        if not force:
            if getattr(entry, "msgstr", "") and entry.msgstr != msgid:
                return False
            existing_plural = getattr(entry, "msgstr_plural", None) or {}
            if existing_plural and all(value.strip() for value in existing_plural.values()):
                return False

        if self.auto_detect:
            detected = detect_language(msgid.strip())
            if detected == self.target_lang and not force:
                return False
            from_lang = detected if detected in self.LANGUAGES else self.source_lang
        else:
            from_lang = self.source_lang

        context = f"Odoo module: {module}" if module else "Odoo ERP"
        changed = False

        plural_forms = getattr(entry, "msgstr_plural", None)
        if plural_forms:
            plural_source = getattr(entry, "msgid_plural", None) or msgid
            for index in list(plural_forms):
                source_text = msgid if str(index) == "0" else plural_source
                current_translation = plural_forms.get(index, "")
                if (
                    not force
                    and current_translation
                    and current_translation.strip()
                    and current_translation.strip() != source_text.strip()
                ):
                    continue
                result = self.translate(source_text, from_lang, self.target_lang, context)
                if result != source_text:
                    plural_forms[index] = result
                    changed = True
        else:
            result = self.translate(msgid, from_lang, self.target_lang, context)
            if result != msgid:
                entry.msgstr = result
                changed = True

        return changed

    def batch_translate(self, entries, module: str | None = None, progress_callback=None, force=False):
        results = {"total": len(entries), "translated": 0, "skipped": 0, "failed": 0}
        for index, entry in enumerate(entries, start=1):
            before_failures = self.stats["failed_requests"]
            try:
                if self.auto_translate_entry(entry, module, force=force):
                    results["translated"] += 1
                elif self.stats["failed_requests"] > before_failures:
                    results["failed"] += 1
                else:
                    results["skipped"] += 1
            except Exception:
                results["failed"] += 1
                self.logger.exception("PO entry translation failed")
            if progress_callback:
                progress_callback(index, len(entries))
        return results

    def get_stats(self) -> dict[str, Any]:
        with self._stats_lock:
            snapshot = dict(self.stats)
        total = max(1, snapshot["total_requests"])
        snapshot["cache_hit_rate"] = f"{snapshot['cache_hits'] / total * 100:.1f}%"
        snapshot["api_efficiency"] = f"{snapshot['api_calls'] / total * 100:.1f}%"
        snapshot["cache_entries"] = len(self.cache.cache)
        snapshot["model"] = self.model_name
        snapshot["offline_mode"] = self.offline_mode
        return snapshot

    def clear_cache(self) -> None:
        self.cache.clear()

    def reset_stats(self) -> None:
        with self._stats_lock:
            for key in self.stats:
                self.stats[key] = 0
