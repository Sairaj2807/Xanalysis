# Data Audit (Phase 1)

Audit date: 2026-11-05. Scope: everything under `C:\Xanalysis`. Profiling used DuckDB (read-only; no raw file modified).

## 1. Repository state
The repository contains **only `data/`**. There is no Python code, config, notebook, database, `requirements.txt`, `.env`, API integration, price dataset, news dataset, or git history. Nothing exists to reuse; everything is built from scratch.

Environment: Python 3.14.6; pandas 3.0.5, duckdb 2.0.0, pyarrow 25.0.1, numpy 2.5.1 installed (user site). No sklearn / torch / transformers / xgboost / lightgbm / plotly / sqlalchemy yet. Python 3.14 wheel availability for torch/catboost/etc. must be checked before pinning.

## 2. Inventory

| File | Size | Delim | Rows | Date range | Content |
|---|---|---|---|---|---|
| Company.csv | 1 KB | `,` | 6 | n/a | ticker -> name (AAPL, GOOG, GOOGL, AMZN, TSLA, MSFT) |
| Tweet.csv | 632 MB | `,` | 3,717,964 (all tweet_id unique; 140,131 writers) | 2015-01-01 00:00:57 to 2019-12-31 23:55:53 (epoch seconds; presumed UTC) | stock tweets: tweet_id, writer, post_date, body, comment/retweet/like_num |
| Company_Tweet.csv | 106 MB | `,` | 4,336,445 | n/a | tweet_id -> ticker. AAPL 1,425,013; TSLA 1,096,868; AMZN 718,715; GOOG 392,569; MSFT 375,711; GOOGL 327,569 |
| tweets.csv | 4.0 GB | `;` | ~47.5M lines (NOT profiled: DuckDB parser rejected it) | unknown | crypto raw: id,user,fullname,url,timestamp,replies,likes,retweets,text |
| Spambots.csv | 1.4 GB | `;` | ~15.5M lines (header only) | not profiled | spam-account tweets, full schema |
| dataset_combinado_completo.csv | 11 GB | `;` | ~126.7M lines (header only) | not profiled | merged crypto set, `origen` column |
| dataset_sin_spam.csv | 9.2 GB | `;` | ~111.2M lines (header only) | not profiled | merged minus spam |
| englishtweets.csv / otherlanguages.csv | 8.5 GB / 0.8 GB | `;` | ~100.7M / ~10.5M lines (header only) | not profiled | language split, adds `tweet_language` |
| engtweetsbtc_clean.csv | 5.9 GB | `;` | ~67.2M lines (header only) | not profiled | English BTC-related, cleaned |
| engtweetsbtc_vader_sentiment.csv | 5.6 GB | `;` | **26,344,493 parseable rows** (65.0M physical lines) | 2013-01-01 to 2023-05-28 | adds `vader_compound`, `vader_sentiment` |

"Header only" means line counts come from `wc -l` and the first row; contents were not profiled. Physical line counts overstate row counts where tweet text contains newlines.

## 3. Findings

### F1. There is NO price data anywhere (blocking)
No OHLCV file exists for any asset (neither the 6 stocks nor BTC). The central experiment (price-only vs price+sentiment) cannot run until prices are ingested from a source the user approves.

### F2. Two unrelated datasets
- **Stock set (Tweet.csv + Company_Tweet.csv + Company.csv)**: 6 tickers, 2015-2019, ~4.3M ticker-tweet links. No sentiment scores. Engagement counts are lifetime totals only; no follower counts, language, or verified flag.
- **Crypto set (`;` files)**: Bitcoin-related English tweets, 2013-2023, VADER sentiment already computed. Richer metadata (followers, following, verified, location, hashtags, language).

### F3. The "last 180 days via Apify" design conflicts with existing data
Existing data is 2015-2019 (stocks) and 2013-2023 (crypto). A 180-day Apify pull today (Nov 2026) is a different, much smaller sample with different fields. Existing historical data can drive the research; Apify/Tavily serve live/incremental use.

### F4. Crypto vader file: uneven coverage
Parseable rows per year: 2013: 124k, 2014: 250k, 2015: 151k, 2016: 186k, 2017: 430k, 2018: 631k, 2019: 6.55M, **2020: 0**, 2021: 11.34M, 2022: 6.53M, 2023: 140k. There is a full-year gap in 2020 and thin coverage before 2019. Walk-forward work should use the 2019 and 2021-2022 blocks, not treat the file as continuous.

### F5. Mixed timestamp formats in crypto set
`date` length 25 (`2019-05-27 11:49:14+00:00`, 24.1M rows), length 19 (no timezone, 2.19M rows, `origen=df4`), length 10 (date only, 7,926 rows, `origen=df3`). The timezone of the 19- and 10-char rows is **unknown** and must not be assumed UTC without confirmation. Row counts by origen: df1 8.33M, df2 2.5k, df3 7.9k, df4 2.19M, df5 15.82M.

### F6. Duplicates and parse loss
> **Update 2026-11-05:** the suspected parse loss did not exist - stdlib `csv` and DuckDB both read exactly 26,344,493 rows (22 columns); the 65.0M physical lines are newlines inside tweet text (DATA-004). This file is otherwise kept as the original Phase 1 record.
- 16,262 duplicate (username, date, text) rows in the vader file (0.06%).
- 65.0M physical lines vs 26.3M parsed rows. The cause (embedded newlines vs rows dropped by `ignore_errors`) is **not yet established**; resolve before trusting row counts.
- `vader_compound` was read as strings, so the reported min/max are lexical, not numeric. Numeric range not yet verified. Label split: NEUTRAL 10.55M / POSITIVE 10.35M / NEGATIVE 5.45M.

### F7. Existing sentiment is VADER, not financial-domain
The spec requires FinBERT-style scoring with full probability distributions. VADER can serve as a lexicon baseline but does not replace it. Transformer inference over millions of tweets is costly; score only the chosen asset and window.

### F8. Leakage risks identified
- Engagement counts (both sets) are lifetime totals at scrape time, not at post time. Using them as point-in-time features leaks the future (spec 4.4).
- Crypto follower counts are scrape-time values: same issue.
- Stock tweets can match several tickers (Company_Tweet); GOOG/GOOGL are the same company.

### F9. Price adjustment / news
Not applicable yet (no price data, no news data).

## 4. Reuse decision
- Raw CSVs stay untouched; derived Parquet mirrors are new files.
- Crypto vader file: reusable as a baseline sentiment input after timestamp normalization and dedup.
- Stock tweets: reusable after the ticker join; need sentiment scoring.
