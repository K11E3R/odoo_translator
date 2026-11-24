![Odoo PO Translator](docs/brand/logo.svg)

[Français](README.fr.md) · [English](README.md)

# Odoo PO Translator

A desktop workbench and command-line tool for reviewing and translating Odoo gettext \`.po\` files.

**Project:** [GitHub](https://github.com/K11E3R/odoo_translator) · **Website:** [Project site](https://k11e3r.github.io/odoo_translator/) · **License:** MIT · [Brand guide](docs/BRAND_GUIDE.md)

> **Current scope:** online AI translation through Google's supported \`google-genai\` SDK, plus a small deterministic offline glossary for common English/French and English/Spanish Odoo terminology. The offline glossary is not a general-purpose machine-translation engine.

## Features

- Import, merge and export gettext/Odoo PO files.
- Desktop UI built with CustomTkinter: search, filters, pagination, inline editing, undo/redo and export.
- Gemini translation using the current Google Gen AI Python SDK.
- Offline glossary assistance for common Odoo phrases and terms (EN↔FR and EN↔ES).
- Local language detection using compact heuristics; optional Lingua integration improves coverage when installed.
- Preserve placeholders and markup validation before accepting AI output.
- Translation cache with hashed keys, thread-safe access and atomic writes.
- Command-line translation with dry-run, in-place and output-directory modes.
- Preserve gettext contexts and plural-entry identity during merges.

## Requirements

- Python 3.11 or newer.
- Tk support for the desktop UI (on Debian/Ubuntu: \`sudo apt install python3-tk\`).
- A Gemini API key for online translation only.

## Install

\`\`\`bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\\Scripts\\Activate.ps1

python -m pip install --upgrade pip
pip install -e ".[dev]"
\`\`\`

You can also install runtime requirements using \`pip install -r requirements.txt\`.

### Optional language detection

For richer local detection, install Lingua separately:

```bash
pip install -e ".[language-detection]"
```

Without this extra, the application uses its built-in local heuristics and does not download a language model.

## Desktop application

\`\`\`bash
python app.py
\`\`\`

Enter a Gemini API key in the application for online translation. The GUI's API key field is session-only; the application does not write the key into the repository.

To use the local glossary without an API key, enable **Offline glossary mode** in the sidebar. This mode makes no network requests. It only translates phrases/terms present in the bundled glossary; unknown text remains unchanged and is counted as a failed/unmatched translation.

## Command line

The package installs the \`po-translator\` command:

\`\`\`bash
# Offline glossary EN -> FR; preserve the input and create module.translated.po
po-translator translate module.po --source en --target fr --offline

# French -> English; write over the input file atomically
po-translator translate module.fr.po --source fr --target en --offline --in-place

# Online Gemini translation
GEMINI_API_KEY="your-key" po-translator translate module.po --source en --target fr

# Choose an output directory
po-translator translate module.po --source en --target fr --output-dir build

# Validate/count without writing
po-translator translate module.po --source en --target fr --offline --dry-run
\`\`\`

Environment variables:

- \`GEMINI_API_KEY\` (or \`GOOGLE_API_KEY\`): Gemini Developer API key.
- \`PO_TRANSLATOR_GEMINI_MODEL\`: model name; default is \`gemini-3.5-flash-lite\`.
- \`PO_TRANSLATOR_OFFLINE_MODE=1\`: start the desktop app in offline glossary mode.
- \`PO_TRANSLATOR_RATE_LIMIT\`: minimum seconds between API requests; default \`0.2\`.

## Translation safeguards

Before accepting online output, the engine checks that the source and translation contain the same placeholder multiset (including repeated placeholders), HTML/XML tags, and newline count. Invalid output is retried and then rejected; the source string is left unchanged.

The cache is stored in \`~/.po_translator/translation_cache.json\`. Cache writes use a temporary file and atomic replacement. Cache keys are SHA-256 hashes, so source text is not embedded in cache-key filenames.

Offline glossary mode is deliberately conservative. It does not pretend to translate arbitrary prose. Use Gemini or a professional reviewer for full sentences and language pairs outside the glossary.

## PO file behavior

Gettext entries are identified using \`msgctxt\`, \`msgid\` and \`msgid_plural\`. Merging therefore keeps context-sensitive entries and singular/plural entries distinct. Export uses polib and preserves the PO file metadata carried through import.

Review translated files before deploying them to production Odoo databases. Always keep a copy of the original PO file.

## Development and tests

\`\`\`bash
python -m pytest
\`\`\`

Tests do not require a Gemini key; Gemini calls should be tested separately with a controlled API key and a small test PO file.

## Security

- Keep API keys in environment variables or a secrets manager.
- Do not commit \`.config\`, \`.env\`, API keys or customer PO files.
- Online translation sends submitted strings to Google's Gemini API. Requests use `store=False` so translation interactions are not retained as server-side conversation history; normal Google API processing and data policies still apply. Verify your organisation's data-processing requirements before using confidential text.
- Offline glossary mode makes no translation API calls. Language detection is local and does not download models at import time.

See [SECURITY.md](SECURITY.md) for the security policy.

## Limitations

- Offline mode is a fixed glossary/phrasebook, not a neural translation model.
- Language detection is advisory and can be uncertain for one-word strings and cognates.
- AI translation can still be semantically wrong. Review the results.
- The desktop application requires a graphical environment; use the CLI for headless workflows.

## Contributing

Bug reports and pull requests are welcome. Include a minimal PO fixture, expected result, actual result, and Python version. Do not attach customer data or credentials.

## Acknowledgements

Built with [polib](https://github.com/izimobil/polib), [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter), [Lingua](https://github.com/pemistahl/lingua-py), and the [Google Gen AI Python SDK](https://github.com/googleapis/python-genai).
