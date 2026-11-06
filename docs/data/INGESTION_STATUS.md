# Ingestion Status

| Pipeline | Status | Last run | Notes |
|---|---|---|---|
| Historical stock tweets → AAPL Parquet | Done (static) | 2026-11-05 | 1,424,481 rows |
| Historical prices (yfinance) | Done | 2026-11-05 | 1,343 bars |
| FinBERT scoring | Done | 2026-11-05 18:12-19:34 | 996,456 unique texts, 1,424,481 posts scored; log: `logs/score_sentiment.log` |
| Apify incremental collection | BLOCKED (live) | never | `XCollector` implements state/idempotence/failure isolation, tested with a fake client; needs APIFY_API_TOKEN + actor id |
| Tavily news | BLOCKED | never | no key |
| Live price updates | Implemented (`update_prices`), tested with a fake fetch; not run live | — | idempotent incremental merge |
Last-collected timestamp, latest post time, last post id, retrieved/new/duplicate counts and failures are stored in `ingestion_logs` by `XCollector` (tested).
