# Data Quality Report

As of 2026-11-05.

| Dataset | Observation | Source |
|---|---|---|
| AAPL raw posts | 1,424,481 rows, ids unique, 0 empty texts, 89,101 distinct authors, 491,610 (34.5%) with non-zero engagement; per-year counts 2015: 360,055; 2016: 405,517; 2017: 218,976; 2018: 223,038; 2019: 216,895 | DuckDB checks |
| ID reconciliation | 1,425,013 linked vs 1,424,481 extracted: 532 (0.04%) unexplained | BUG-004 |
| Cleaning flags | duplicate 30.05%, promo 1.45%, many-cashtags 23.5%, url-only ≈0.002% (24 posts), spam (any) 24.0%, bot-like 27.5%, english_score ≥ 0.5: 85.5% | scripts/clean_posts.py |
| Prices | 1,343 daily bars, 0 NaN, unique; close range 22.58–81.08 (split-adjusted) | initial_ingestion |
| Volume drop | Post volume falls ~45% after 2016 | per-year counts |
| Crypto vader file | 26.3M parseable of 65.0M lines (cause unknown); mixed date formats (25/19/10 chars); no 2020; 16,262 duplicate (user,date,text) | [DATA_AUDIT](../DATA_AUDIT.md) |

Model table (primary filter): 663,144 of 1,424,481 posts kept (46.6%); 1,238 trading days 2015-02-02..2019-12-31; posts/day median 400, 10th percentile 153; no empty days inside the table; daily mean FinBERT score mean 0.008, std 0.063, range -0.246..0.220 (compressed: day-averaging shrinks extremes).

**Resolved 2026-11-05:** (1) the 532 'missing' AAPL ids exist in the raw file and were dropped by the bulk parser after malformed records; recovered 532/532 into `stock_tweets_AAPL_recovered.parquet`, downstream not re-run (0.037% of posts) - BUG-004. (2) the crypto vader file has no parse loss: stdlib csv and DuckDB both read 26,344,493 rows × 22 columns; the 65.0M physical lines are embedded newlines (DATA-004). (3) language heuristic vs py3langid: 81.8% agreement on 20,000 posts. (4) monitoring: no missing/thin trading days; 46 volume anomalies; strong sentiment/volume drift between 2015-17 and 2019 ([monitoring report](../reports/data_quality/2026-11-05_monitoring_report.md)).

Not yet checked: missing trading days vs posts, timezone of `post_date` (presumed UTC), spam-flag precision, tweets mentioning several tickers (Company_Tweet is many-to-one), GOOG/GOOGL duplicate company.
