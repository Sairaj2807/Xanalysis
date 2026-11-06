# Changelog

Chronological; newest last. Repository has no commits, so entries cite sessions, not commits.

## 2026-11-05 (session 1)
- Added: repository skeleton, config + asset YAML, historical AAPL tweet extraction, yfinance price ingestion, Apify and Tavily clients (untested live), cleaning/flagging, timestamp/cutoff utilities, FinBERT analyzer + validation set, sentiment aggregation, price/sentiment/interaction features, leakage checks, purged walk-forward, metrics, statistical tests, model registry, A/B/C runner, SQLAlchemy schema, 39 tests, documentation system and doc tooling.
- Fixed: BUG-001 mixed-offset timestamp parsing; BUG-002 Holm family size; BUG-003 requirements missing torch; BUG-007 codebase-map generator.
- Changed: none to pre-existing data.

## 2026-11-05 (later)
- Fixed: BUG-008 (leakage-gate slicing false alarm).
- Added: tests for every registry model (ML-002) and `build_table` (TEST-004); suite 51 passing.
- Ran: FinBERT scoring (complete), model table build, EXP-001.

## 2026-11-05 (completion session)
- Added: model registry tests for all models; `build_table` refactor + tests; nowcast module (two definitions); multi-output, shared-head, GRU/LSTM/TCN/Transformer; permutation importance, SHAP, correlations; regime analysis; global correction + versus-persistence tests; strategy table; ablation/robustness/engagement/power scripts; incremental collector, news processing, scheduler; repositories, Alembic migrations, immutable forecast triggers; monitoring; Plotly dashboard + auto reports + one-page outlook; orchestrator; incremental price update; intraday bar assignment and price aggregation; second sentiment model plumbing; README; memory notes.
- Fixed: BUG-004 (root cause + recovery), BUG-009 (run lookup), BUG-010 (predictions unique key), BUG-008 (earlier).
- Resolved: DATA-004 (no parse loss in the crypto vader file), DATA-003.
- Ran: EXP-002..013 (see EXPERIMENT_LOG).
- Tests: 101 passing.
