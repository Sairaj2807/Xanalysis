# Next Actions (ordered queue)

The planned research programme is finished (see [PROJECT_STATUS](../PROJECT_STATUS.md)). Remaining items mostly need inputs only the owner can give. Items marked **[needs user]** cannot be done by an agent alone.

| # | Task ID | Action | Done when |
|---|---|---|---|
| 1 | ING-003 | **[needs user]** Provide `APIFY_API_TOKEN` and `APIFY_ACTOR_ID` in `.env`; run `XCollector.collect_incremental` against the real actor; correct the assumed `run_input` keys (BUG-005); record field availability | A live run stores >0 valid posts and re-running adds 0 duplicates |
| 2 | ING-005 / ING-006 | **[needs user]** Provide `TAVILY_API_KEY`; collect news; run `process_articles`; run the labelled exploratory model D (news features) separately from the primary model | News table + comparison with social sentiment; model D result logged as exploratory |
| 3 | NLP-002 | **[needs user]** Human review of `data/validation/sentiment_validation.csv` (48 AI-written labels); extend the set; rerun `score_sentiment.py --validate --model <m>` for each model | Reviewed labels; accuracy per model on reviewed data |
| 4 | STAT-007 / DEC-018 | Once live collection runs repeatedly, store engagement snapshots so a point-in-time engagement feature can be built (the only way to answer research question 5 cleanly) | Snapshot table; point-in-time feature; rerun ablation |
| 5 | DB-004 / BUG-006 | Test the PostgreSQL branch against a real PostgreSQL/Timescale server and write the equivalent immutability trigger | Migration + tests green on PostgreSQL |
| 6 | OPS-003 / TD-009 / TD-010 | Cold full run of `scripts/run_pipeline.py --force` (hours); move walk-forward constants and stage definitions into config | One command reproduces everything from raw CSVs |
| 7 | BUG-004 follow-up | Optionally merge `stock_tweets_AAPL_recovered.parquet` into the extract and rerun cleaning/scoring/experiments (532 posts = 0.037%) | Updated runs logged as new experiments |
| 8 | TD-011 | Open `artifacts/reports/dashboard.html` and visually inspect every chart; fix layout issues | Visual check done |
| 9 | DEC-013 | **[needs user decision]** Replicate on the BTC corpus (VADER already scored; intraday prices needed) | Second-asset experiment logged |
| 10 | Power | If a positive claim is ever wanted: pre-register one model/horizon/feature set, collect more data (intraday or more assets), test once | Confirmatory result |
| - | DEC-011 | Commit/push only if the owner explicitly asks | - |
