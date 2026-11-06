# Implementation Tracker

Capability-level status (hand-maintained). File inventory is auto-generated in [CODEBASE_MAP](CODEBASE_MAP.md). Task IDs refer to [MASTER_TASK_REGISTER](../MASTER_TASK_REGISTER.md). Evidence = tests in [TESTING_STATUS](TESTING_STATUS.md) and run artifacts. Last verified 2026-11-05.

| Module | File | Capability | Status | Evidence / notes |
|---|---|---|---|---|
| config | config/settings.py | YAML asset config + validation | TESTED | env secrets loaded, never used live |
| ingestion | legacy_loaders.py | Stock CSV → AAPL Parquet; record-level recovery | TESTED | real run; 532 recovered (BUG-004) |
| ingestion | price_ingestion.py | yfinance download, UTC, dedupe, save, **incremental update** | VERIFIED | real download; update tested with fake fetch (ING-002) |
| ingestion | apify_client.py | Mapping, validation, retries, credentials check | TESTED (fixtures) | live BLOCKED; actor input assumed (BUG-005) |
| ingestion | x_scraper.py | Incremental idempotent collection, state in `ingestion_logs`, failure isolation | TESTED (fake client) | live BLOCKED |
| ingestion | tavily_client.py | Parse, dedupe | TESTED (fixtures) | `search()` never called live |
| ingestion | news_processing.py | Relevance, time validity, clustering, events, sentiment hook, social-vs-news flags | TESTED (fixtures) | no real news data |
| ingestion | ingestion_scheduler.py | Interval jobs, status, failure isolation | TESTED | not deployed |
| preprocessing | text_cleaner.py, timestamp_alignment.py | Cleaning/flags; UTC + cutoff logic (16:00 close and 09:30 pre-open) | TESTED | flags heuristic (language heuristic: 81.8% agreement with langid) |
| sentiment | finbert_analyzer.py | GPU batched scoring; label aliasing (positive/bullish…) | TESTED | FinBERT + FinTwitBERT scored the full corpus |
| sentiment | sentiment_validation.py | accuracy/report/confusion/calibration | IMPLEMENTED | 4 models compared on 48 AI-labelled items |
| sentiment | sentiment_aggregation.py | Trading-day assignment (configurable cutoff), 4 weightings, empty-day handling | TESTED | real run |
| features | price/sentiment/interaction/feature_pipeline/leakage_checks | Features, targets, A/B/C sets, leakage gates | VERIFIED | real table 1,238×57 |
| features | nowcast.py | n+0 tables: close-to-close and intraday | VERIFIED | EXP-009/010 |
| database | models.py, connection.py, repositories.py, migrations/ | 8 tables, SQLite immutability triggers, dialect-aware upsert, Alembic | TESTED | PostgreSQL untested |
| models | model_registry.py | 10 classical models in train-only pipelines | VERIFIED | EXP-001 |
| models | multi_horizon.py, deep_learning.py | Multi-output, shared-head, GRU/LSTM/TCN/Transformer | VERIFIED | EXP-007 |
| validation | walk_forward, metrics, statistical_tests | Purged splits, metrics, DM/bootstrap/Holm | VERIFIED | all runs |
| validation | model_comparison.py | Runner, incremental value, global correction, strategy table, versus persistence | VERIFIED | EXP-001..011 |
| validation | importance.py, regime_analysis.py | Permutation importance, SHAP, regimes | VERIFIED | EXP-005/006 |
| prediction | forecasting.py, uncertainty.py, prediction_storage.py | Latest forecast, empirical intervals + coverage check, append-only store | TESTED | interval coverage measured 70.5% for nominal 80% |
| visualization | price_sentiment, sentiment_heatmap, forecast_matrix, performance_dashboard | Plotly charts + HTML dashboard | TESTED | built from real artifacts; not visually inspected |
| reporting | sentiment_report, research_report, run_index | One-page outlook, auto reports, exact run lookup | VERIFIED (outlook) / TESTED | docs/reports/ |
| monitoring | data_monitor, drift_monitor, model_monitor | Gaps, anomalies, PSI/KS, degradation, retrain + promotion rule | VERIFIED | applied to the study |
| scripts | initial_ingestion, clean_posts, score_sentiment, build_features, run_validation, evaluate_run, run_ablation, run_analysis, run_nowcast, diagnose_nowcast, diagnose_data_gaps, run_engagement_leaky, run_monitoring, generate_report, summarize_run, count_csv_rows | Stage and analysis entry points | VERIFIED by execution | wiring bugs found by real runs (BUG-008/009) |
| scripts | run_pipeline.py | Orchestrator with state/skip/retry | TESTED (fakes) | not yet driven end-to-end on real data |
| scripts | doc tooling (4 scripts) | Map, validate, status, context | IMPLEMENTED | self-run, validator has no tests |

Not implemented: live Apify/Tavily runs, PostgreSQL verification, news-inclusive model D (no news data), point-in-time engagement features (data not available), intraday bars, multi-asset support in the orchestrator.
