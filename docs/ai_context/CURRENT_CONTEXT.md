# Current Context

Last updated: 2026-11-05

1. **Stage:** research programme complete for AAPL daily (2015-2019); the central question is answered and replicated with a second sentiment model.
2. **Active workstream:** none running. Remaining work needs owner inputs (credentials, label review) - see [NEXT_ACTIONS](NEXT_ACTIONS.md).
3. **Recently completed:** EXP-001..013 (A/B/C, filters, ablation, importance, regimes, deep/multi-output, vs-persistence, nowcasts, leaky engagement, FinTwitBERT replication, power analysis); DB layer + migrations; incremental collector; news processing; monitoring; dashboard + reports; documentation system.
4. **Currently active tasks:** none (all research tasks VERIFIED).
5. **Blockers:** no Apify/Tavily credentials (ING-003, ING-005); human review of validation labels (NLP-002).
6. **Key decisions:** [DECISION_LOG](../decisions/DECISION_LOG.md) DEC-001..019 - AAPL daily (001), FinBERT then FinTwitBERT replication (003/016), 16:00 ET cutoff (006), engagement excluded (007/018), no agent commits (011), global Holm for claims (014), two nowcast definitions (015).
7. **Architecture:** CSV → Parquet → clean → transformer sentiment → daily aggregate → features → leakage gate → purged walk-forward → comparison/tests → reports; DB layer for runs/forecasts; see [DATA_FLOW](../architecture/DATA_FLOW.md).
8. **Latest verified results:** no significant sentiment benefit anywhere (0/40, 0/105, 0/35, 0/60, 0/40 after global Holm); nothing beats persistence significantly (4/230 significantly worse); sentiment is contemporaneous only (session sentiment vs same-day return 0.56; lagged ≈ 0); nowcast edge = overnight-gap echo; buy-and-hold net PnL 0.854 vs sentiment strategies negative; power: 1% R² → 5% detection, 4% → 80%. Details: [RESEARCH_FINDINGS](../research/RESEARCH_FINDINGS.md).
9. **Data coverage:** AAPL tweets 2015-01-01..2019-12-31 (1,424,481; primary filter 663,144); prices 2014-10-01..2020-01-31; news none; DB schema + migrations, pipeline data in Parquet.
10. **Next five priorities:** (1) live Apify run [needs user] (2) Tavily news + model D [needs user] (3) human label review [needs user] (4) PostgreSQL test (5) cold full pipeline run + config-driven constants.

## Immediate blockers
Credentials and human label review (both owner-supplied). Nothing blocks reading, testing or re-running the existing pipeline.

<!-- AUTO:FACTS:START -->
_Measured 2026-11-05 21:41 by `scripts/update_project_context.py`._

- Collected tests: 101
- Sentiment scoring chunks on disk: 40 (50,000 unique texts each; 996,456 total expected)
- Experiment runs on disk: 11 (latest `20261105T160721Z_nowcast_fintwitbert-sentiment`)
- Derived data files present:
- `data/raw/x_posts/stock_tweets_AAPL.parquet` (68.2 MB)
- `data/raw/x_posts/stock_tweets_AAPL_recovered.parquet` (77.7 KB)
- `data/raw/prices/AAPL_1d.parquet` (70.0 KB)
- `data/processed/posts_AAPL.parquet` (269.0 MB)
- `data/processed/sentiment_AAPL.parquet` (46.9 MB)
- `data/processed/sentiment_AAPL_fintwitbert-sentiment.parquet` (47.2 MB)
- `data/aggregated/sentiment_daily_AAPL_all_posts.parquet` (133.8 KB)
- `data/aggregated/sentiment_daily_AAPL_no_bots.parquet` (129.0 KB)
- `data/aggregated/sentiment_daily_AAPL_primary.parquet` (129.9 KB)
- `data/aggregated/sentiment_daily_AAPL_primary_fintwitbert-sentiment.parquet` (129.8 KB)
- `data/model_ready/feature_sets.json` (1.6 KB)
- `data/model_ready/model_table_AAPL_all_posts.parquet` (595.1 KB)
- `data/model_ready/model_table_AAPL_no_bots.parquet` (590.6 KB)
- `data/model_ready/model_table_AAPL_primary.parquet` (591.9 KB)
- `data/model_ready/model_table_AAPL_primary_fintwitbert-sentiment.parquet` (592.3 KB)
<!-- AUTO:FACTS:END -->
