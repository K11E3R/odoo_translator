# Security Policy

## Supported Versions

The PO Translator currently targets **Python 3.11+**. Security fixes are
applied to the latest published minor release only.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | ✅ Full support    |
| < 1.0   | ❌ Unsupported     |

## Reporting a Vulnerability

Please open a private issue or email the maintainer listed in `pyproject.toml`
(or the repository owner) with detailed reproduction steps. Include the
following where possible:

- A minimal `.po` file that reproduces the issue
- Operating system information
- Whether offline mode or Gemini was used

## API Key Handling

- Prefer setting the `GEMINI_API_KEY` environment variable in your shell or CI
  secrets manager rather than committing keys to disk.
- When using the GUI, the key is stored in memory only. If a `.config` file is
  used for debugging, set permissions to `0600` to prevent accidental exposure.
- The CLI accepts `--api-key` but still honours the environment variable to
  simplify secure CI integration.

## Data Residency & Privacy

- Offline mode keeps all translations on the workstation and is recommended for
  sensitive `.po` files.
- When using Gemini, ensure your usage complies with Google's terms and your
  organisation's data processing policies. The translator does not cache Gemini
  responses beyond the local JSON cache in `~/.po_translator`.
- Disable network-backed detection by setting
  `PO_TRANSLATOR_USE_GOOGLE_DETECTION=0` when compliance requires fully offline
  behaviour.

## Rate Limiting & Abuse Protection

- The translator enforces a ~10 req/s limit to stay within Gemini free tier
  quotas. Adjust `Translator.rate_limit` carefully if you extend the project.
- Monitor `translator.get_stats()` or the GUI statistics dialog to detect
  unusual API usage patterns.
