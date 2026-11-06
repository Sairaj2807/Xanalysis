# Data Inventory

Full Phase 1 audit (unchanged): [DATA_AUDIT](../DATA_AUDIT.md). Verified 2026-11-05.

## Pre-existing raw files (`data/`, never modified)
| File | Size | Rows | Dates | Profiled |
|---|---|---|---|---|
| Company.csv | 1 KB | 6 | — | Yes |
| Tweet.csv | 632 MB | 3,717,964 (unique ids) | 2015-01-01 → 2019-12-31 | Yes |
| Company_Tweet.csv | 106 MB | 4,336,445 | — | Yes (AAPL 1,425,013) |
| tweets.csv | 4.0 GB | ~47.5M lines | unknown | No (parser rejected) |
| Spambots.csv | 1.4 GB | ~15.5M lines | — | Header only |
| dataset_combinado_completo / dataset_sin_spam / englishtweets / otherlanguages / engtweetsbtc_clean | 0.8–11 GB | 10–127M lines | — | Header only |
| engtweetsbtc_vader_sentiment.csv | 5.6 GB | 26,344,493 parseable rows (65.0M lines) | 2013-01 → 2023-05 (no 2020) | Yes (partial) |
The crypto/BTC files are unused by the current study.

## Derived files (git-ignored)
| File | Rows | Producer |
|---|---|---|
| data/raw/x_posts/stock_tweets_AAPL.parquet | 1,424,481 | ingestion/legacy_loaders.py |
| data/raw/prices/AAPL_1d.parquet | 1,343 | ingestion/price_ingestion.py |
| data/processed/posts_AAPL.parquet | 1,424,481 | scripts/clean_posts.py |
| artifacts/sentiment_chunks/ProsusAI_finbert/chunk_*.parquet | 50,000 each (in progress) | scripts/score_sentiment.py |
| data/validation/sentiment_validation.csv | 48 | hand-written (AI) |
Live counts: AUTO block in [CURRENT_CONTEXT](../ai_context/CURRENT_CONTEXT.md).
