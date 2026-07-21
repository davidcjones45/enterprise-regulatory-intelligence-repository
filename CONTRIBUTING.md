# Contributing

Contributions should preserve traceability, temporal correctness, and the separation between authoritative facts and human judgments.

## Development

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

## Pull requests

A pull request should state:

- what changed;
- why it changed;
- which schemas or records are affected;
- how it was tested;
- whether legal-status or source assertions changed.

Never submit copyrighted standards text, confidential client material, personal data, credentials, or unverified legal claims.
