# Security Policy

## Supported versions

Security fixes are developed against the latest code on the default branch. There is currently no promise of maintenance for historical binary releases.

## Reporting a vulnerability

Please report vulnerabilities privately to the repository owner rather than publishing exploit details in a public issue. Include a minimal reproduction, affected version, operating system and impact. Remove credentials and customer data from all reports.

## API keys

- Prefer \`GEMINI_API_KEY\` or \`GOOGLE_API_KEY\` environment variables, or a secrets manager.
- The desktop API-key field is held in application memory and is not written to the repository.
- Do not pass API keys in shell commands on shared systems because command history and process listings may expose them.
- Revoke and rotate any key accidentally committed or shared.

## Data handling

- Online mode sends source strings to Google's Gemini API. Do not submit customer or confidential content unless your organisation has approved that data flow.
- Offline glossary mode makes no translation API requests.
- Language detection is local and does not download an external model at import time.
- The translation cache is stored locally under \`~/.po_translator\`; remove it when disposing of a workstation or handling sensitive data.

## Supported behavior

The built-in offline glossary is not a full translation engine. Unknown phrases remain unchanged; check CLI summaries for failed/unmatched entries and review every generated PO file before deployment.
