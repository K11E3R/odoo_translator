"""
Translator v3 — Optimized for Odoo .po files
- Gemini 2.5 Flash-Lite
- Smart language detection (EN↔FR)
- Skips redundant French→French
- Odoo glossary-aware prompt
- Offline heuristic glossary translator
- Caching, validation, retry
- Compatible with test_translation_debug.py & app.py
"""

import os
import time
import json
import re
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    AVAILABLE = True
except ImportError:
    AVAILABLE = False
    genai = None  # type: ignore

from po_translator.utils.language import is_french_text, is_english_text, detect_language
from po_translator.utils.file_utils import sanitize_text
from po_translator.utils.logger import get_logger


# ==========================================================
# CACHE
# ==========================================================
class TranslationCache:
    """Simple JSON cache for translations"""
    def __init__(self, cache_file=None):
        cache_dir = Path.home() / ".po_translator"
        cache_dir.mkdir(exist_ok=True)
        self.cache_file = cache_dir / (cache_file or "translation_cache.json")
        self.cache = self._load_cache()

    def _load_cache(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get(self, text, context=None):
        return self.cache.get(f"{text}|{context or ''}")

    def set(self, text, translation, context=None):
        self.cache[f"{text}|{context or ''}"] = translation
        self._save()

    def clear(self):
        self.cache = {}
        self._save()


# ==========================================================
# OFFLINE TRANSLATOR
# ==========================================================
class OfflineTranslatorEngine:
    """Lightweight heuristic translator for offline scenarios."""

    PLACEHOLDER_PATTERN = re.compile(r"(%\([^)]+\)s|%s|\{[^}]+\}|\$\{[^}]+\}|{{[^}]+}})")

    OFFLINE_DICTIONARY: Dict[Tuple[str, str], Dict[str, Iterable[Tuple[str, str]]]] = {
        ("en", "fr"): {
            "phrases": (
                ("purchase order", "bon de commande"),
                ("sales order", "commande client"),
                ("delivery order", "bon de livraison"),
                ("quotation", "devis"),
                ("confirm the order", "confirmer la commande"),
                ("confirm order", "confirmer la commande"),
                ("create invoice", "créer la facture"),
                ("customer invoice", "facture client"),
                ("vendor bill", "facture fournisseur"),
                ("total amount", "montant total"),
                ("payment terms", "conditions de paiement"),
            ),
            "words": (
                ("confirm", "confirmer"),
                ("confirming", "confirmation"),
                ("confirmations", "confirmations"),
                ("order", "commande"),
                ("orders", "commandes"),
                ("customer", "client"),
                ("customers", "clients"),
                ("vendor", "fournisseur"),
                ("vendors", "fournisseurs"),
                ("invoice", "facture"),
                ("invoices", "factures"),
                ("quotation", "devis"),
                ("quotations", "devis"),
                ("delivery", "livraison"),
                ("product", "article"),
                ("products", "articles"),
                ("amount", "montant"),
                ("total", "total"),
                ("create", "créer"),
                ("new", "nouveau"),
                ("draft", "brouillon"),
                ("validate", "valider"),
                ("warehouse", "entrepôt"),
                ("stock", "stock"),
                ("partner", "partenaire"),
                ("payment", "paiement"),
                ("payments", "paiements"),
                ("due", "dû"),
                ("deadline", "échéance"),
                ("comment", "commentaire"),
                ("comments", "commentaires"),
                ("please", "veuillez"),
                ("save", "enregistrer"),
                ("cancel", "annuler"),
                ("apply", "appliquer"),
                ("amounts", "montants"),
                ("lines", "lignes"),
            ),
        },
        ("fr", "en"): {
            "phrases": (
                ("bon de commande", "purchase order"),
                ("bon de livraison", "delivery order"),
                ("facture client", "customer invoice"),
                ("facture fournisseur", "vendor bill"),
                ("confirmer la commande", "confirm the order"),
                ("montant total", "total amount"),
            ),
            "words": (
                ("commande", "order"),
                ("commandes", "orders"),
                ("client", "customer"),
                ("clients", "customers"),
                ("fournisseur", "vendor"),
                ("fournisseurs", "vendors"),
                ("facture", "invoice"),
                ("factures", "invoices"),
                ("devis", "quotation"),
                ("livraison", "delivery"),
                ("article", "product"),
                ("articles", "products"),
                ("montant", "amount"),
                ("montants", "amounts"),
                ("paiement", "payment"),
                ("paiements", "payments"),
                ("valider", "validate"),
                ("créer", "create"),
                ("annuler", "cancel"),
                ("enregistrer", "save"),
                ("commentaire", "comment"),
                ("commentaires", "comments"),
                ("entrepôt", "warehouse"),
            ),
        },
        ("en", "es"): {
            "phrases": (
                ("sales order", "orden de venta"),
                ("purchase order", "orden de compra"),
                ("confirm the order", "confirmar el pedido"),
            ),
            "words": (
                ("order", "pedido"),
                ("orders", "pedidos"),
                ("invoice", "factura"),
                ("invoices", "facturas"),
                ("customer", "cliente"),
                ("customers", "clientes"),
                ("total", "total"),
                ("amount", "importe"),
                ("confirm", "confirmar"),
                ("create", "crear"),
            ),
        },
        ("es", "en"): {
            "phrases": (
                ("orden de venta", "sales order"),
                ("orden de compra", "purchase order"),
            ),
            "words": (
                ("pedido", "order"),
                ("pedidos", "orders"),
                ("factura", "invoice"),
                ("facturas", "invoices"),
                ("cliente", "customer"),
                ("clientes", "customers"),
                ("confirmar", "confirm"),
                ("crear", "create"),
            ),
        },
    }

    WORD_PATTERN = re.compile(r"[A-Za-zÀ-ÿ']+")

    def __init__(self):
        self._phrase_cache: Dict[Tuple[str, str], Tuple[Tuple[Tuple[str, str], ...], Tuple[Tuple[str, str], ...]]] = {}

    @staticmethod
    def _apply_case(source: str, target: str) -> str:
        if not source or not target:
            return target

        if source.isupper():
            return target.upper()
        if source.islower():
            return target.lower()
        if source.istitle():
            return target.title()
        if source[0].isupper():
            return target[0].upper() + target[1:]
        return target

    def supports_pair(self, source: str, target: str) -> bool:
        return (source, target) in self.OFFLINE_DICTIONARY

    def _get_rules(self, source: str, target: str):
        pair = (source, target)
        if pair not in self._phrase_cache:
            data = self.OFFLINE_DICTIONARY.get(pair, {"phrases": (), "words": ()})
            phrases = tuple(sorted(data.get("phrases", ()), key=lambda item: len(item[0]), reverse=True))
            words = tuple(data.get("words", ()))
            self._phrase_cache[pair] = (phrases, words)
        return self._phrase_cache[pair]

    def translate(self, text: str, source: str, target: str) -> Optional[str]:
        if not text or not text.strip():
            return text

        if not self.supports_pair(source, target):
            return None

        working = text
        placeholders = {}

        def _stash_placeholder(match):
            token = f"__PH_{len(placeholders)}__"
            placeholders[token] = match.group(0)
            return token

        working = self.PLACEHOLDER_PATTERN.sub(_stash_placeholder, working)
        phrases, words = self._get_rules(source, target)

        for phrase, replacement in phrases:
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)

            def _phrase_repl(match):
                return self._apply_case(match.group(0), replacement)

            working = pattern.sub(_phrase_repl, working)

        word_map = {source_word: target_word for source_word, target_word in words}

        def _word_repl(match):
            token = match.group(0)
            lookup = token.lower()
            if lookup not in word_map:
                return token
            translated = word_map[lookup]
            return self._apply_case(token, translated)

        working = self.WORD_PATTERN.sub(_word_repl, working)

        for token, original in placeholders.items():
            working = working.replace(token, original)

        working = re.sub(r"\s+", lambda m: " " if "\n" not in m.group(0) else m.group(0), working)
        return working.strip()


# ==========================================================
# TRANSLATOR
# ==========================================================
class Translator:
    """Gemini-based translator for Odoo PO files"""

    LANGUAGES = {
        "en": {"name": "English"},
        "fr": {"name": "French"},
        "es": {"name": "Spanish"},
        "de": {"name": "German"},
        "it": {"name": "Italian"},
        "pt": {"name": "Portuguese"},
        "nl": {"name": "Dutch"},
        "ar": {"name": "Arabic"},
        "ca": {"name": "Catalan"},
        "ro": {"name": "Romanian"},
        "da": {"name": "Danish"},
        "sv": {"name": "Swedish"},
        "no": {"name": "Norwegian"},
        "fi": {"name": "Finnish"},
        "gl": {"name": "Galician"},
    }

    ODOO_TERMS = {
        "fr": {
            "Invoice": "Facture",
            "Quotation": "Devis",
            "Sales": "Ventes",
            "Purchase Order": "Bon de commande",
            "Delivery Order": "Livraison",
            "Partner": "Partenaire",
            "Customer": "Client",
            "Vendor": "Fournisseur",
            "Stock": "Stock",
            "Warehouse": "Entrepôt",
            "Payment": "Paiement",
            "Accounting": "Comptabilité",
        }
    }

    def __init__(self, api_key=None):
        self.logger = get_logger("po_translator.translator")
        self.cache = TranslationCache()
        self.api_key = api_key
        self.model = None

        self.source_lang = "en"
        self.target_lang = "fr"
        self.auto_detect = True

        offline_toggle = os.environ.get("PO_TRANSLATOR_OFFLINE_MODE", "0").strip().lower()
        self.offline_mode = offline_toggle in {"1", "true", "yes", "on"}
        self._offline_warning_pairs = set()
        self.offline_engine = OfflineTranslatorEngine()

        self.last_request = 0
        self.rate_limit = 0.1  # ~10 requests/sec

        # Stats
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "api_calls": 0,
            "errors": 0,
            "retries": 0,
            "auto_corrections": 0,
            "offline_requests": 0,
        }

        if api_key:
            self.set_api_key(api_key)

        if self.offline_mode:
            self.logger.info("🛜 Offline mode enabled — using heuristic glossary translator.")

    # ------------------------------------------------------
    # API setup
    # ------------------------------------------------------
    def set_api_key(self, api_key):
        self.api_key = api_key
        if self.offline_mode:
            self.logger.info("Stored API key for later use. Offline mode is active, skipping Gemini initialisation.")
            return

        if not AVAILABLE:
            self.logger.warning("google-generativeai is not available. Install the dependency to enable online translation.")
            return

        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(
                "gemini-2.5-flash-lite",
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 256,
                    "top_p": 0.9,
                    "top_k": 20,
                },
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                },
            )
            self.logger.info("✅ Translator initialized with Gemini 2.5 Flash-Lite")
        except Exception as e:
            self.logger.error(f"❌ Gemini initialization failed: {e}")
            self.model = None

    def set_offline_mode(self, offline: bool):
        offline = bool(offline)
        if offline == self.offline_mode:
            return

        self.offline_mode = offline

        if offline:
            self.logger.info("🛜 Offline mode enabled — remote API calls disabled.")
            self.model = None
        else:
            self.logger.info("🌐 Offline mode disabled — remote API calls permitted.")
            if self.api_key and AVAILABLE:
                self.set_api_key(self.api_key)

    # ------------------------------------------------------
    # Prompt generation
    # ------------------------------------------------------
    def _get_prompt(self, from_lang, to_lang, context=None):
        """Context-aware Odoo prompt"""
        from_name = self.LANGUAGES[from_lang]["name"]
        to_name = self.LANGUAGES[to_lang]["name"]
        ctx = f"Odoo module: {context}" if context else "Odoo ERP"

        glossary = json.dumps(self.ODOO_TERMS.get(to_lang, {}), ensure_ascii=False, indent=2)

        prompt = f"""
You are an expert translator for Odoo ERP software.

Task:
Translate the given text from {from_name} to {to_name}.
Context: {ctx}

Rules:
1. Keep placeholders exactly (%(name)s, %s, {{x}}, etc.).
2. Preserve HTML and newlines (\\n).
3. Use professional, natural {to_name}.
4. Only return the translation — no quotes, no explanation.
5. Do NOT return the same text unless it's a real cognate like "Client" or "Stock".

Glossary for consistent terminology:
{glossary}
"""
        return prompt.strip()

    # ------------------------------------------------------
    # Helpers
    # ------------------------------------------------------
    def _rate_limit(self):
        elapsed = time.time() - self.last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request = time.time()

    def _validate_translation(self, src, trans):
        if not trans or not trans.strip():
            return False
        src_vars = set(re.findall(r"%\([^)]+\)s|%s|\{[^}]+\}|\$\{[^}]+\}", src))
        trans_vars = set(re.findall(r"%\([^)]+\)s|%s|\{[^}]+\}|\$\{[^}]+\}", trans))
        if src_vars != trans_vars:
            self.logger.warning(f"Variable mismatch: {src_vars} vs {trans_vars}")
            return False
        return True

    def configure_languages(self, source=None, target=None, auto_detect=None):
        """Configure source/target languages and auto-detection"""
        changed = False

        if source:
            if source not in self.LANGUAGES:
                self.logger.warning(f"Unsupported source language: {source}")
            elif source != self.source_lang:
                self.source_lang = source
                changed = True

        if target:
            if target not in self.LANGUAGES:
                self.logger.warning(f"Unsupported target language: {target}")
            elif target != self.target_lang:
                self.target_lang = target
                changed = True

        if auto_detect is not None and auto_detect != self.auto_detect:
            self.auto_detect = auto_detect
            changed = True

        if changed:
            self.logger.info(
                f"Language configuration updated: {self.source_lang} → {self.target_lang} (auto-detect={'on' if self.auto_detect else 'off'})"
            )

        return changed

    def set_languages(self, source, target, auto_detect=True):
        """Compatibility helper for legacy callers"""
        self.configure_languages(source=source, target=target, auto_detect=auto_detect)

    # ------------------------------------------------------
    # Main translation
    # ------------------------------------------------------
    def translate(self, text, from_lang=None, to_lang=None, context=None, max_retries=1):
        if not text:
            return text

        text = sanitize_text(text)
        from_lang = from_lang or self.source_lang
        to_lang = to_lang or self.target_lang
        self.stats["total_requests"] += 1

        cache_key = f"{from_lang}→{to_lang}|{context or ''}"
        cached = self.cache.get(text, cache_key)
        if cached:
            self.stats["cache_hits"] += 1
            return cached

        if self.offline_mode:
            translation = self.offline_engine.translate(text, from_lang, to_lang)
            if translation is None:
                pair = (from_lang, to_lang)
                if pair not in self._offline_warning_pairs:
                    self.logger.warning(
                        "Offline translator does not support %s → %s yet. Returning original text.",
                        from_lang,
                        to_lang,
                    )
                    self._offline_warning_pairs.add(pair)
                translation = text
            else:
                translation = translation or text

            self.cache.set(text, translation, cache_key)
            self.stats["offline_requests"] += 1
            return translation

        if not self.model:
            self.logger.debug("No online model configured; returning original text.")
            return text

        for attempt in range(max_retries + 1):
            try:
                self._rate_limit()
                self.stats["api_calls"] += 1

                prompt = self._get_prompt(from_lang, to_lang, context)
                prompt += f"\n\nText: {text}\nTranslation:"
                response = self.model.generate_content(prompt)
                translation = response.text.strip().strip('"\'')
                if "\n" in translation:
                    translation = translation.split("\n")[0]

                if self._validate_translation(text, translation):
                    self.cache.set(text, translation, cache_key)
                    self.logger.info(f"[OK] {text[:40]}... → {translation[:40]}...")
                    return translation
                else:
                    if attempt < max_retries:
                        self.logger.warning(f"Retrying invalid translation: {text[:40]}...")
                        self.stats["retries"] += 1
                        time.sleep(0.5)
                        continue
                    else:
                        return text

            except Exception as e:
                self.stats["errors"] += 1
                self.logger.error(f"Translation error: {e}")
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                else:
                    return text

        return text

    # ------------------------------------------------------
    # Auto translation for PO entry
    # ------------------------------------------------------
    def auto_translate_entry(self, entry, module=None, force=False):
        """Auto-translate PO entry intelligently"""
        if not entry.msgid:
            return False

        msgid = entry.msgid.strip()
        if not msgid:
            return False

        # Skip if already translated
        if entry.msgstr and entry.msgid != entry.msgstr and not force:
            return False

        # Skip if text already French and target is French
        if not force and is_french_text(msgid) and self.target_lang == "fr":
            self.logger.debug(f"Already French, skipping: {msgid[:40]}...")
            return False

        detected_lang = detect_language(msgid)
        from_lang = self.source_lang

        # Auto-detection logic
        if self.auto_detect and detected_lang:
            if detected_lang == self.target_lang:
                if force:
                    self.logger.warning(
                        "Detected %s which matches target %s; proceeding due to override for: %s",
                        detected_lang,
                        self.target_lang,
                        msgid[:40],
                    )
                else:
                    self.logger.info(f"Detected {detected_lang} same as target, skipping: {msgid[:40]}")
                    return False
            elif detected_lang != self.source_lang:
                self.logger.warning(
                    f"Detected {detected_lang}, translating → {self.target_lang}: {msgid[:40]}..."
                )
                from_lang = detected_lang

        context = f"Odoo module: {module}" if module else "Odoo ERP"
        translation = self.translate(msgid, from_lang=from_lang, to_lang=self.target_lang, context=context)
        if translation and translation != msgid:
            entry.msgstr = translation
            return True

        return False

    # ------------------------------------------------------
    # Batch processing
    # ------------------------------------------------------
    def batch_translate(self, entries, module=None, progress_callback=None, force=False):
        """Translate multiple entries with stats"""
        results = {"total": len(entries), "translated": 0, "skipped": 0, "failed": 0}
        for i, entry in enumerate(entries):
            try:
                if self.auto_translate_entry(entry, module, force=force):
                    results["translated"] += 1
                else:
                    results["skipped"] += 1
            except Exception as e:
                results["failed"] += 1
                self.logger.error(f"Entry failed: {e}")
            if progress_callback:
                progress_callback(i + 1, len(entries))
        return results

    # ------------------------------------------------------
    # Utilities
    # ------------------------------------------------------
    def get_stats(self):
        total = max(1, self.stats["total_requests"])
        return {
            **self.stats,
            "cache_hit_rate": f"{self.stats['cache_hits']/total*100:.1f}%",
            "api_efficiency": f"{self.stats['api_calls']/total*100:.1f}%",
            "cache_entries": len(self.cache.cache),
        }

    def clear_cache(self):
        self.cache.clear()
        self.logger.info("✅ Cache cleared.")

    def reset_stats(self):
        for k in self.stats:
            self.stats[k] = 0
        self.logger.info("🔁 Stats reset.")
