# Project Status

As of 2026-11-05 (end of session 1). Evidence for every line is in [MASTER_TASK_REGISTER](MASTER_TASK_REGISTER.md). No overall completion percentage is given: tasks are not equal in size. Use the counts below.

<!-- AUTO:STATUS_COUNTS:START -->

Task counts by workstream (auto-generated from the task register; unweighted, not a completion %):

| Workstream | VERIFIED | TESTED | IMPLEMENTED | IN_PROGRESS | BLOCKED | NOT_STARTED | DEPRECATED | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ARCH | 1 | 3 | 0 | 0 | 0 | 0 | 0 | 4 |
| DATA | 2 | 3 | 1 | 1 | 0 | 0 | 0 | 7 |
| DB | 0 | 3 | 1 | 0 | 0 | 0 | 0 | 4 |
| FEAT | 1 | 4 | 0 | 0 | 0 | 0 | 0 | 5 |
| ING | 1 | 4 | 0 | 0 | 2 | 0 | 0 | 7 |
| ML | 4 | 2 | 0 | 0 | 0 | 0 | 0 | 6 |
| MON | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| NLP | 3 | 3 | 1 | 0 | 0 | 0 | 0 | 7 |
| OPS | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 3 |
| REP | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 2 |
| SEC | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 2 |
| STAT | 7 | 1 | 0 | 0 | 0 | 0 | 0 | 8 |
| TEST | 3 | 1 | 0 | 0 | 0 | 0 | 0 | 4 |
| VAL | 3 | 4 | 0 | 0 | 0 | 0 | 0 | 7 |
| VIS | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 3 |
| **All** | 29 | 34 | 4 | 1 | 2 | 0 | 0 | 70 |

<!-- AUTO:STATUS_COUNTS:END -->

## Summary
The research platform is complete for the AAPL / daily / 2015-2019 study and the central question has been answered: **no evidence that X sentiment improves out-of-sample price forecasts**, replicated with a second sentiment model. What remains is work that needs inputs only the owner can provide (API credentials, human label review) or that is outside the study's scope (other assets, live deployment).

## Workstreams
- **Complete and verified on real data:** historical ingestion, price ingestion (+ incremental update), cleaning, sentiment scoring with two models, aggregation, features and leakage gates, purged walk-forward validation, 10 classical models, multi-output/shared-head/deep models, ablation, robustness, regimes, importance/SHAP/correlations, nowcasts, power analysis, economics, monitoring, reports/dashboard, documentation system.
- **Complete, tested on fixtures only:** Apify collector (incremental, idempotent), news processing, scheduler, database layer with migrations and immutable forecast store, orchestrator logic.
- **Blocked on credentials:** live Apify (ING-003) and Tavily (ING-005) calls; hence no news-layer data and no point-in-time engagement snapshots.
- **Open / partial:** human-reviewed sentiment labels (NLP-002), PostgreSQL verification (DB-004), crypto/BTC study (deliberately out of scope, DEC-013), DATA-001 (profiling limited to AAPL-relevant files).

## Data status
- X: 1,424,481 AAPL posts (2015-01-01 → 2019-12-31) + 532 recovered in a supplementary file (not merged downstream). Primary filter keeps 663,144. Two full sentiment scorings exist (FinBERT, FinTwitBERT).
- Prices: 1,343 AAPL daily bars (2014-10-01 → 2020-01-31); `close` split-adjusted, not dividend-adjusted.
- News: none (Tavily not run). Database: schema + migrations exist; the pipeline's bulk data is Parquet.
- Quality: [DATA_QUALITY_REPORT](data/DATA_QUALITY_REPORT.md), [monitoring report](reports/data_quality/2026-11-05_monitoring_report.md) (no missing days; strong sentiment/volume drift 2015-17 → 2019).

## Research status
Answers to all 12 questions: [RESEARCH_FINDINGS](research/RESEARCH_FINDINGS.md). Key numbers: 0 of 40 (EXP-001), 0 of 105 (ablation), 0 of 35 (deep), 0 of 60 (leaky engagement), 0 of 40 (FinTwitBERT repeat) sentiment effects significant after global correction; 0 models significantly better than persistence (4 significantly worse with FinBERT features); intraday nowcast: no sentiment value; the close-to-close nowcast edge (+3-4%) is the overnight-gap echo; power analysis: 1% R² effects were detected only 5% of the time.

## Engineering status
- Tests: **101 passing** ([TESTING_STATUS](engineering/TESTING_STATUS.md)). Untested: live APIs, PostgreSQL, dashboard visuals, the documentation validator.
- Pipeline: orchestrator run on real state (skips completed stages); a cold full run was not performed.
- Automation/monitoring: scheduler and monitors exist and are tested; no deployed service.
- Version control: the owner committed and pushed to `origin` (https://github.com/Sairaj2807/Xanalysis.git, branch `main`) on 2026-11-06; local and remote were identical afterwards. Agents still do not commit or push unless asked (DEC-011).
- **Not on GitHub (excluded by `.gitignore`):** the large data under `data/raw|processed|aggregated|model_ready`, `artifacts/`, `logs/`, `.venv` and `.env`. Anyone cloning the repo must regenerate these by running the pipeline (`scripts/run_pipeline.py`). Credentials are never stored in the repo.

## Risks and limitations
1. Low statistical power at daily frequency (EXP-013): small effects cannot be excluded.
2. Sentiment labels are AI-written and unreviewed (n=48).
3. One asset, one period; no live data, news or point-in-time engagement.
4. Intervals under-cover (70.5% for nominal 80%).
5. Nothing is committed or backed up off this machine.

## Immediate priorities
See [NEXT_ACTIONS](ai_context/NEXT_ACTIONS.md).
