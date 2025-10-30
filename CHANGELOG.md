# Changelog

All notable changes to this project will be documented in this file. The format
roughly follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-10-30
### Added
- Command-line interface for translating `.po` files with offline support.
- Release changelog, security guidelines, and updated README coverage for CLI
  usage and deployment considerations.
- Regression coverage for the CLI offline workflow and import-safe helper
  scripts.

### Fixed
- Prevented debug helper scripts from aborting `python -m unittest` by running
  their logic only when executed directly.

## [1.0.0] - 2024-12-01
### Added
- Initial public release with Gemini 2.5 integration, CustomTkinter GUI, and
  offline glossary translation fallback.
