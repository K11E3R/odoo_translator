# Automated tests

The supported test command is:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

The test suite is deterministic and does not require a Gemini API key. It exercises:
- PO parsing, context-aware identity and plural-entry merging
- Local language detection without model downloads or network calls
- Placeholder and markup preservation
- Offline phrasebook behavior and explicit unmatched-phrase reporting
- Cache persistence and concurrent writes
- CLI dry-run behavior and output safety

Online Gemini integration should be tested separately with a dedicated test API key and non-confidential sample data. Do not use customer PO files in automated tests.
