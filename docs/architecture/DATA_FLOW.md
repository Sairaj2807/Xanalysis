# Data Flow and Lineage Diagram

```mermaid
flowchart TD
  A[data/Tweet.csv 632MB\ndata/Company_Tweet.csv] -->|DuckDB join ticker=AAPL, 2015-2019| B[data/raw/x_posts/stock_tweets_AAPL.parquet\n1,424,481 rows]
  B -->|text_cleaner: normalise, dedup_key, flags| C[data/processed/posts_AAPL.parquet]
  C -->|unique dedup_key: 996,456 texts| D[artifacts/sentiment_chunks/ProsusAI_finbert/chunk_*.parquet]
  D -->|merge back on dedup_key| E[data/processed/sentiment_AAPL.parquet\npending]
  P[yfinance AAPL 1d] --> Q[data/raw/prices/AAPL_1d.parquet\n1,343 rows]
  C --> F
  E --> F[assign trading day by 16:00 ET close\naggregate_daily]
  F --> G[data/aggregated/sentiment_daily_AAPL_primary.parquet\npending]
  Q --> H
  G --> H[build_model_table + leakage gate]
  H --> I[data/model_ready/model_table_AAPL_primary.parquet\npending]
  I --> J[run_walk_forward]
  J --> K[artifacts/runs/run_id/oos_predictions.parquet\n+ metrics CSVs - pending]
```
"pending" = not yet produced (as of 2026-11-05). Per-dataset detail: [DATA_LINEAGE](../data/DATA_LINEAGE.md). Independent pipelines: prices (above) and news (Tavily → `data/raw/news`, not implemented).
