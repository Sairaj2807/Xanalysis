# Implementation Plan

## Open decisions (block Phase 2)
1. **Primary asset / dataset.** (a) A stock ticker (e.g. AAPL) from the stock-tweet set, 2015-2019, needs sentiment scoring. (b) BTC from the crypto set, 2019 and 2021-2022 blocks, VADER already present.
2. **Price source.** None exists. Needs a provider (yfinance for stocks, an exchange API for BTC). Free intraday history for 2015-2019 stocks is generally unavailable, so daily bars are likely for the stock set; BTC supports intraday.
3. **Bar size.** n+1..n+5 means five bars: daily or hourly.
4. **API credentials.** Apify token + actor ID and Tavily key are needed only for live ingestion; tests use cached/synthetic fixtures.
5. **Compute for FinBERT.** CPU-only scoring of millions of tweets is impractical; scope scoring to the chosen asset window.

## Phases (spec section 21)
- P1 audit: done (docs/). Unresolved: parse loss (F6) and profiling of tweets.csv and the derived files.
- P2 data engineering: skeleton, config, DB, CSV to Parquet, timestamp normalization, price ingestion, Apify/Tavily clients with mocked fixtures.
- P3 sentiment: FinBERT pipeline, validation set, aggregation methods.
- P4 features and leakage tests.
- P5 models and the A/B/C feature experiment.
- P6 walk-forward, metrics, DM tests, multiple-comparison correction.
- P7 dashboard and reports.
- P8 automation and monitoring.
- P9 end-to-end verification.

Each phase ends with the 7-item report required by the spec.

## Risks
- Python 3.14 package compatibility (torch, catboost, lightgbm); may need a 3.12 venv.
- Daily sentiment over 1-3 usable years gives few independent samples; significance tests will have low power. Results will be reported as found.
