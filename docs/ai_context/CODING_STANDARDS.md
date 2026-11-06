# Coding Standards

- Python 3.12, type hints on public functions, module docstring stating purpose and leakage assumptions.
- Logic in importable packages; scripts only orchestrate. Pure functions where possible (aid testing).
- Timestamps: UTC; naive requires explicit tz; no hard-coded EST offsets.
- Randomness: seed everything.
- No silent fallbacks: raise on invalid config; unavailable fields stay null.
- Tests: pytest, synthetic deterministic fixtures, no network/paid APIs. Every new feature/model gets a test, features a leakage check.
- Vectorised pandas/DuckDB for large data; never load the multi-GB CSVs whole.
- Never overwrite raw data or prior run artifacts.
- Keep comments to non-obvious intent.
