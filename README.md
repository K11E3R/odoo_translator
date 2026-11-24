![Odoo PO Translator](docs/brand/logo.svg)

[Français](README.fr.md) · [English](README.md)

# Odoo PO Translator

**For Odoo developers and implementation partners:** localize Odoo module `.po` files with Gemini-assisted translation, context-aware PO merging, and a reviewable desktop or command-line workflow.

Use the tool to reduce repetitive localization work while keeping translated strings reviewable before they reach a production Odoo database. Online translation uses Google Gemini; the built-in offline glossary covers only selected English/French and English/Spanish Odoo terms.

**Project:** [GitHub](https://github.com/K11E3R/odoo_translator) · **Website:** [Project site](https://k11e3r.github.io/odoo_translator/) · **License:** MIT · [Brand guide](docs/BRAND_GUIDE.md)

## See the application

![Odoo PO Translator desktop interface showing the translation table and controls](docs/screenshots/main-interface.png)

*The desktop workbench for importing, reviewing, editing and exporting Odoo gettext files.*

## Features

- Import, merge and export gettext/Odoo PO files.
- Desktop UI built with CustomTkinter: search, filters, pagination, inline editing, undo/redo and export.
- Gemini translation using Google's current Gen AI Python SDK.
- Limited offline glossary assistance for selected Odoo phrases and terms (EN↔FR and EN↔ES); unmatched text stays unchanged.
- Local language detection using compact heuristics; optional Lingua integration improves coverage when installed.
- Placeholder and markup validation before accepting AI output.
- Translation cache with hashed keys, thread-safe access within one process and atomic writes.
- Command-line translation with dry-run, in-place and output-directory modes.
- Context-aware gettext merging that keeps plural entries distinct.

## Requirements

- Python 3.11 or newer.
- Git, to install directly from this GitHub repository.
- Tk support for the desktop UI (on Debian/Ubuntu: `sudo apt install python3-tk`).
- A Gemini API key for online translation only; offline glossary mode does not need one.

## Install

Install the application directly from GitHub in one command:

```bash
python -m pip install "git+https://github.com/K11E3R/odoo_translator.git"
```

Then launch the desktop application:

```bash
po-translator gui
```

The same installation provides the `po-translator` CLI. For an isolated install, use `pipx install "git+https://github.com/K11E3R/odoo_translator.git"` instead. On Debian/Ubuntu, install `python3-tk` first if Tk is missing.

### Optional language detection

For richer local detection, install the optional extra from a source checkout:

```bash
python -m pip install -e ".[language-detection]"
```

Without this extra, the application uses its built-in local heuristics and does not download a language model.

## Desktop application

Start the installed desktop app with `po-translator gui`. Enter a Gemini API key in the application for online translation. The GUI key field is session-only; the application does not write the key into the repository.

To use the local glossary without an API key, enable **Offline glossary mode** in the sidebar. This mode makes no network requests. It only translates phrases and terms present in the bundled glossary; unknown text remains unchanged and is reported as unmatched.

## Command line

Translate a PO file offline from English into French:

```bash
po-translator translate module.po --source en --target fr --offline
```

Translate French into English and replace the input file atomically:

```bash
po-translator translate module.fr.po --source fr --target en --offline --in-place
```

Use Gemini for online translation:

```bash
GEMINI_API_KEY="your-key" po-translator translate module.po --source en --target fr
```

Choose an output directory or validate without writing:

```bash
po-translator translate module.po --source en --target fr --output-dir build
po-translator translate module.po --source en --target fr --offline --dry-run
```

Environment variables:

- `GEMINI_API_KEY` (or `GOOGLE_API_KEY`): Gemini Developer API key.
- `PO_TRANSLATOR_GEMINI_MODEL`: model name; default is `gemini-3.5-flash-lite`.
- `PO_TRANSLATOR_OFFLINE_MODE=1`: start the desktop app in offline glossary mode.
- `PO_TRANSLATOR_RATE_LIMIT`: minimum seconds between API requests; default `0.2`.

## Translation safeguards

Before accepting online output, the engine checks that the source and translation contain the same placeholder multiset (including repeated placeholders), HTML/XML tags and newline count. Invalid output is retried and then rejected; the source string is left unchanged.

The cache is stored in `~/.po_translator/translation_cache.json`. Cache writes use a temporary file and atomic replacement. Cache keys are SHA-256 hashes, so source text is not embedded in cache-key filenames.

Offline glossary mode is deliberately conservative. It does not pretend to translate arbitrary prose. Use Gemini or a professional reviewer for full sentences and language pairs outside the glossary.

## PO file behavior

Gettext entries are identified using `msgctxt`, `msgid` and `msgid_plural`. Merging therefore keeps context-sensitive entries and singular/plural entries distinct. Export uses polib and preserves the PO file metadata carried through import.

Review translated files before deploying them to production Odoo databases. Always keep a copy of the original PO file.

## Development and tests

For contributors working from a checkout:

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

Tests do not require a Gemini key. Gemini calls should be tested separately with a controlled API key and a small test PO file.

## Security

- Keep API keys in environment variables or a secrets manager.
- Do not commit `.config`, `.env`, API keys or customer PO files.
- Online translation sends submitted strings to Google's Gemini API. Requests use `store=False` so translation interactions are not retained as server-side conversation history; normal Google API processing and data policies still apply. Verify your organisation's data-processing requirements before using confidential text.
- Offline glossary mode makes no translation API calls. Language detection is local and does not download models at import time.

See [SECURITY.md](SECURITY.md) for the security policy.

## Limitations

- Offline mode is a fixed glossary/phrasebook, not a neural translation model.
- Language detection is advisory and can be uncertain for one-word strings and cognates.
- AI translation can still be semantically wrong. Review the results.
- The desktop application requires a graphical environment; use the CLI for headless workflows.

## Contributing

Bug reports and pull requests are welcome. Include a minimal PO fixture, expected result, actual result and Python version. Do not attach customer data or credentials.

## Acknowledgements

Built with [polib](https://github.com/izimobil/polib), [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter), [Lingua](https://github.com/pemistahl/lingua-py) and the [Google Gen AI Python SDK](https://github.com/googleapis/python-genai).
