# Execution Guide

Run from the repo root with the venv interpreter (`.venv\Scripts\python.exe`). Stages are independent and idempotent unless noted.

| Order | Command | Output | Time observed |
|---|---|---|---|
| 1 | `scripts/initial_ingestion.py` | raw AAPL tweets + prices | ~1 min |
| 2 | `scripts/clean_posts.py` | data/processed/posts_AAPL.parquet | ~2 min |
| 3 | `scripts/score_sentiment.py --validate` | validation report | <1 min after model load |
| 4 | `scripts/score_sentiment.py` | data/processed/sentiment_AAPL.parquet; **resumable**, ~70 min | log: logs/score_sentiment.log |
| 5 | `scripts/build_features.py [primary|all_posts|no_bots]` | model table + leakage gate | never run |
| 6 | `scripts/run_validation.py [filter]` | artifacts/runs/<id>/ | never run; runtime unknown |
Docs: `scripts/update_project_context.py`, `generate_codebase_map.py`, `generate_project_status.py`, `validate_documentation.py`.
Tests: `-m pytest -q`.

## Full command list (2026-11-05)
| Purpose | Command |
|---|---|
| Everything, with checkpoints | `scripts/run_pipeline.py [--stages a,b] [--from stage] [--force] [--retries N] [--list]` |
| Sentiment with another model | `scripts/score_sentiment.py --model StephanAkkerman/FinTwitBERT-sentiment` (output `sentiment_AAPL_<tag>.parquet`) |
| Table / experiment for that model | `scripts/build_features.py primary <model>` then `scripts/run_validation.py primary <model>` |
| Robustness filters | `scripts/build_features.py all_posts` / `no_bots`, then `run_validation.py <filter>` |
| Economics + global correction | `scripts/evaluate_run.py <run_dir_name>` |
| Ablation / leaky engagement | `scripts/run_ablation.py primary`, `scripts/run_engagement_leaky.py` |
| Importance, SHAP, regimes, multi-horizon/deep | `scripts/run_analysis.py [importance regimes multihorizon]` |
| Nowcasts | `scripts/run_nowcast.py [model] [--intraday]`, `scripts/diagnose_nowcast.py [model]` |
| Run summary | `scripts/summarize_run.py <run_dir_name> ...` |
| Monitoring | `scripts/run_monitoring.py` |
| Reports + dashboard | `scripts/generate_report.py [YYYY-MM-DD]` → `artifacts/reports/dashboard.html`, `docs/reports/` |
| Data diagnostics | `scripts/diagnose_data_gaps.py`, `scripts/count_csv_rows.py <file>` |
| Migrations | `alembic upgrade head` |
Observed runtimes: full A/B/C experiment ~8 min; ablation ~10 min; multi-horizon/deep ~3 min; FinBERT-sized scoring of 996k texts ~70-85 min on a Quadro P2200.
