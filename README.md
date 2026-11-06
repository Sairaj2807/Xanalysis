# Xanalysis - X (Twitter) sentiment vs. asset price prediction

A reproducible quantitative-research platform that asks one question: **does aggregated X sentiment add out-of-sample
predictive information about an asset's future price beyond historical prices?** It is built so that a negative
answer is a valid, honestly reported outcome.

**Result so far (AAPL, daily, 2017-2019 out-of-sample): no evidence that sentiment improves forecasts.** Sentiment
follows price (contemporaneous correlation) but does not lead it. See [docs/research/RESEARCH_FINDINGS.md](docs/research/RESEARCH_FINDINGS.md).

## Quick start (Windows, Python 3.12)

```
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu126
copy .env.example .env            # add APIFY_API_TOKEN / APIFY_ACTOR_ID / TAVILY_API_KEY only for live collection
.venv\Scripts\python.exe -m pytest -q          # tests need no network, GPU or paid API (FinBERT test skips if weights absent)
.venv\Scripts\python.exe scripts\run_pipeline.py --list
.venv\Scripts\python.exe scripts\run_pipeline.py          # all stages; completed stages are skipped (use --force to redo)
```

Data inputs: the CSVs in `data/` (stock tweets 2015-2019) are read-only inputs. Derived data lands in `data/raw|processed|aggregated|model_ready`
and experiment runs in `artifacts/runs/<UTC timestamp>_<kind>/` (never overwritten). Reports: `docs/reports/`, dashboard: `artifacts/reports/dashboard.html`.

## Layout

| Path | Purpose |
|---|---|
| `config/` | typed settings + `asset_config.yaml` (asset is configurable; nothing is hard-coded to AAPL) |
| `ingestion/` | historical CSV loader, yfinance prices, Apify X client + incremental collector, Tavily client, news processing, scheduler |
| `preprocessing/` | text cleaning/flags, timestamp normalisation and market-close cutoff logic |
| `sentiment/` | transformer scorer (FinBERT default), validation, daily aggregation (4 weightings) |
| `features/` | price / sentiment / interaction features, forward targets, nowcast table, leakage checks |
| `models/` | sklearn + boosting registry, multi-output and shared-head nets, GRU/LSTM/TCN/Transformer |
| `validation/` | purged walk-forward, metrics, Diebold-Mariano / bootstrap / Holm, importance, regimes, runner |
| `prediction/`, `reporting/`, `visualization/` | forecasts with empirical intervals, one-page outlook, Plotly dashboard |
| `monitoring/` | drift (PSI/KS), data quality, retrain triggers, promotion rule |
| `database/` | SQLAlchemy schema, Alembic migrations, append-only forecast store |
| `scripts/` | one entry point per pipeline stage + documentation tooling |
| `docs/` | the project knowledge base - **start at [docs/README.md](docs/README.md)** |

## Key rules (details in [docs/PROJECT_MASTER_CONTEXT.md](docs/PROJECT_MASTER_CONTEXT.md))

- Row `t` uses only information available at bar `t`'s close; automated leakage tests guard this.
- No random splits: chronological walk-forward with purging and embargo.
- News is excluded from the primary model; engagement counts (lifetime totals, not point-in-time) are excluded.
- Historical forecasts are immutable (DB triggers + write-new-run-folder convention).

## Status and limits

Live Apify / Tavily collection is implemented and tested on fixtures only (no credentials were available). PostgreSQL support is untested.
Only AAPL daily data from a 2015-2019 tweet archive has been studied. See [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md).
This is research code, not investment advice.
