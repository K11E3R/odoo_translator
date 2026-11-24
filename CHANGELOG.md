# Changelog

All notable changes to this project are documented here.

## Unreleased — reliability and localization corrections

### Added
- Explicit deterministic offline phrasebook mode for selected EN↔FR and EN↔ES Odoo terms.
- Working `po-translator` CLI with dry-run, output-directory and atomic in-place modes.
- French README.
- Python 3.11–3.13 GitHub Actions test matrix and deterministic regression tests.
- SVG mark, wordmark and 1280×640 social-preview artwork.

### Changed
- Migrated from the legacy `google-generativeai` SDK to Google's supported `google-genai` SDK and Interactions API.
- Removed import-time FastText model downloads and network-backed language detection fallbacks.
- Made translation-cache updates thread-safe within an application process and atomic on disk.
- Preserved placeholder multiplicity, HTML/XML tags, newlines and intentional PO whitespace.
- Preserved gettext context and plural identity through merge, indexing and GUI editing.
- Aligned runtime and packaging dependencies; kept API keys session-only in the GUI.
- Reworked the landing page and README to state real capabilities and limitations.

### Security
- Documented that online translation sends PO source strings to Google's Gemini API.
- Removed project-local `.config` key loading and writing from the GUI and debug helper.

## [1.0.0] - 2025-10-30

### Added
- Initial desktop release of the Odoo PO Translator.
- Gemini-based translation, local glossary material, language detection and a translation cache.
- PO import, merge and export workflows.
- CustomTkinter desktop interface with search, filters, pagination and entry editing.

### Notes
- The v1.0 release predates the reliability corrections listed above.
- Claims in the original v1.0 announcement are historical; consult the current README for maintained behavior and limitations.
