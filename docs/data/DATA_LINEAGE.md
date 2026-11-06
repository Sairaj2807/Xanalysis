# Data Lineage

Diagram: [DATA_FLOW](../architecture/DATA_FLOW.md).

| Dataset | Source / method | Frequency | Original timestamp | Transformations | Destination | Key | Quality rules | Limitations |
|---|---|---|---|---|---|---|---|---|
| Raw AAPL posts | Tweet.csv ⋈ Company_Tweet.csv (static historical files) | one-off | `post_date` epoch s (presumed UTC) | filter ticker/date, cast | data/raw/x_posts | post_id | unique ids, non-empty text | 532 linked ids missing; no ingestion timestamp (static data) |
| Processed posts | text_cleaner | one-off | created_at | clean, dedup, flags | data/processed | post_id | no rows dropped | heuristics |
| Post sentiment | FinBERT on unique dedup_key | one-off | n/a | score, merge back | data/processed (pending) | post_id | score ∈ [-1,1] asserted | model accuracy modest |
| Prices | yfinance | one-off (2014-10→2020-01) | bar date | UTC, dedupe, sort | data/raw/prices | (symbol, bar_start_utc) | unique, sorted, no NaN | split- not dividend-adjusted |
| Daily sentiment | aggregate_daily | derived | trading_day | 16:00 ET cutoff, weights | data/aggregated (pending) | trading_day | no forward fill | engagement leaky |
| Model table | build_model_table | derived | trading_day | features + targets | data/model_ready (pending) | trading_day | leakage gate | — |
| Predictions | run_walk_forward | per run | prediction ts | OOS only | artifacts/runs/<id> | (run, ts, horizon, model, set) | immutable | not in DB |

Versioning: dataset and feature versions are not formally tracked yet (TECHNICAL_DEBT). Until they are, every experiment must record the code state and the filter name in [EXPERIMENT_LOG](../history/EXPERIMENT_LOG.md).
