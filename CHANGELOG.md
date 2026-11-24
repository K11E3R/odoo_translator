# Changelog

## Unreleased — reliability and localization corrections

### Added
- Functional deterministic offline glossary mode for EN↔FR and EN↔ES.
- A working \`po-translator\` CLI with dry-run, output directory and atomic in-place output.
- French README translation.
- GitHub Actions test workflow and a consistent pytest test suite.
- SVG project identity assets.

### Changed
- Migrated from the legacy \`google-generativeai\` SDK to Google's supported \`google-genai\` SDK.
- Made language detection local/offline at import time; removed automatic FastText model downloads and Google Translate detection.
- Made cache access thread-safe and writes atomic.
- Preserved placeholder multiplicity, markup and newline counts in AI-output validation.
- Preserved gettext context and plural identity during PO merges.
- Aligned runtime and packaging dependencies.

### Security
- Documented the actual online data flow and session-only GUI key handling.
