# Development Roadmap

Phases follow the master specification. Status reflects the task register, not intent. Original Phase 1 notes: [IMPLEMENTATION_PLAN](IMPLEMENTATION_PLAN.md) (historical).

| Phase | Scope | Status | Key tasks |
|---|---|---|---|
| 1 Audit | Inventory, profiling | Done, partial profiling | ARCH-001, DATA-001 |
| 2 Data engineering | Ingestion, cleaning, DB | Mostly done for historical AAPL; live ingestion, migrations, DB use outstanding | DATA-002/005/006, ING-001..007, DB-001..004 |
| 3 Sentiment | FinBERT, aggregation | Scoring in progress | NLP-001..006 |
| 4 Features | Price/sentiment/interaction, leakage | Code tested on synthetic; real table pending | FEAT-001..005 |
| 5 Modelling | Baselines, ML, deep learning, architectures | Baselines + classical implemented; DL/multi-output not started | ML-001..006 |
| 6 Validation | Walk-forward, tests, significance | Machinery tested; real run pending | VAL-001..006, STAT-001..003 |
| 7 Visualization | Dashboards, forecast matrix, heatmap | Not started | VIS-001..003, REP-001/002 |
| 8 Automation / monitoring | Scheduler, drift | Not started | ING-007, MON-001, OPS-003 |
| 9 Final verification | End-to-end run, reports | Not started | TEST-002, STAT-001 |

## Near-term sequence
Finish scoring → build real table → run A/B/C → cover untested models → ablation/importance → human-reviewed sentiment validation → nowcast → persistence in DB → visualisation and reports.

## Dependencies on the user
Apify token + actor ID, Tavily key (live ingestion only); review of the 48 validation labels; decision on whether to pursue BTC as a second study.
