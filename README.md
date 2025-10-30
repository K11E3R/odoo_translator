# Odoo PO Translator

Desktop helper for translating Odoo `.po` files. It ships with a focused GUI, language-aware validation, and an optional CLI so you can batch jobs locally or plug it into automation.

## Quick start
```bash
pip install -r requirements.txt
python app.py              # launch the desktop app
# or
po-translator translate module.po --target fr --offline
```

## Key features (v1.0.0)
- Gemini 2.5 Flash-Lite support with rate-limited requests and cache reuse when an API key is provided.
- Offline glossary engine (English↔French, English↔Spanish) that keeps placeholders intact for air-gapped use.
- Smart language detection combining heuristics, `langid`, and Google Translate (optional) to flag mismatches before translating.
- CustomTkinter UI with pagination, selection tools, theming, and language-mismatch prompts tuned for Odoo strings.
- Simple CLI (`po-translator`) that mirrors GUI rules for unattended runs, including dry-run validation.

## Working offline
- Set `PO_TRANSLATOR_OFFLINE_MODE=1` or toggle "Offline mode" in the sidebar to stay on local translations only.
- Disable network-backed detection by exporting `PO_TRANSLATOR_USE_GOOGLE_DETECTION=0`.
- Cached results live in `~/.po_translator` so repeated phrases stay instant even without the network.

## Important limitations
- Automated translations are drafts — review output for domain-specific vocabulary and legal terminology.
- Offline glossary coverage is intentionally narrow; uncommon language pairs fall back to the online model when available.
- Google Gemini or Translate APIs may change pricing or availability. Monitor usage and keep keys outside the repository.
- The GUI targets desktop workflows; server-side Odoo integration and headless automation are not bundled.
- No telemetry or analytics are collected, but logs and caches remain on disk. Clear them with `python clear_cache.py` if needed.

## Project status & support
- Current release: **v1.0.0** (MIT licensed).
- Tested on Python 3.11+ using `python -m unittest` with offline mode enabled.
- Security guidance and supported versions live in [SECURITY.md](SECURITY.md); lifecycle notes are kept in [CHANGELOG.md](CHANGELOG.md).
