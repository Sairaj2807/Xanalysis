# Technical Debt

| ID | Item | Impact | Status |
|---|---|---|---|
| TD-001 | Pipeline data lives in Parquet; the database holds runs/forecasts/ingestion state only when explicitly called (`store_run_predictions`); no automated sync | Two stores to keep consistent | Open |
| TD-002 | No dataset/feature version tags; model-table names encode only filter and sentiment-model tag | Traceability relies on run folders + EXPERIMENT_LOG | Open |
| TD-003 | Spec file names partly not followed (`models/baselines.py`, `linear_models.py`, `tree_models.py`); baselines live in `model_registry.py` | Cosmetic | Accepted |
| TD-004 | Multi-horizon runners use folds purged with max horizon; independent models purge per horizon (same test blocks) | Slightly different training sets; comparable test windows | Accepted |
| TD-005 | `author_dup_share`/`author_post_count` use full-history information | Fine for flags; must never be features | Accepted (documented) |
| TD-006 | RESOLVED: global Holm now applied via `add_global_correction` (STAT-004) | — | Closed |
| TD-007 | Hyperparameter grids are tiny and tuning is serial | Runtime ok (~8 min/full run); results sensitive to config | Accepted |
| TD-008 | `requirements.txt` pins `torch==2.14.1+cu126` needing an extra index | Install friction | Documented |
| TD-009 | Orchestrator stage list hard-codes script names and AAPL file names | Another asset needs config-driven stage definitions | Open |
| TD-010 | Walk-forward parameters (train_min 500, test_len 60, ...) are constants in scripts, not in YAML | Harder to vary | Open |
| TD-011 | Dashboard rendering was never visually inspected; figures are only construction-tested | Possible layout issues | Open |
| TD-012 | Live APIs (Apify/Tavily) and PostgreSQL untested | Cannot claim production readiness | Open (blocked) |
| TD-013 | `scripts/*` stage entry points are not unit-tested (logic is in tested packages) | Wiring errors surface only on real runs (see BUG-008/009) | Open |
| TD-014 | Several analysis scripts print and write ad-hoc CSVs; no schema for analysis artifacts | Report generator couples to file names | Open |
