# Initial Project Audit — 2026-11-05

Written for: the project owner and the next AI agent.

## What the repository contains
About 2,000 lines of Python in 10 packages, 39 passing tests, a 66-file Markdown knowledge base under docs/ (63 new + the 3 Phase 1 audit files), a 3.12 venv, and derived data for AAPL (1,424,481 posts; 1,343 daily prices). A FinBERT scoring job (996,456 texts) was running. Git: initialised, remote set, **no commits** (by instruction).

## Actually completed (tested/verified)
Price ingestion (verified on real data); timestamp/cutoff logic; cleaning/flags; aggregation; features; leakage checks; walk-forward; metrics; DM/bootstrap/Holm; A-vs-C runner on synthetic data; unit tests. See [IMPLEMENTATION_TRACKER](../../engineering/IMPLEMENTATION_TRACKER.md).

## Partially completed
FinBERT scoring (running); Apify/Tavily clients (no live run, no pagination/incremental); database (schema only); model registry (6 of 10 families never executed).

## Not started
n+0 nowcast; deep learning; multi-output models; importance/SHAP/ablation; regime analysis; dashboards; reports; monitoring; scheduler; migrations; news processing.

## Broken or doubtful
No known failing test. Open: BUG-004 (532 IDs), BUG-005 (assumed Apify input), BUG-006 (SQLite-only upsert). Doubtful: sentiment quality (0.604, n=48, self-labelled); spam/bot/language heuristics.

## Untested
Live APIs; FinBERT wrapper; lasso, elasticnet, extra_trees, lightgbm, xgboost, catboost; `build_features.py`; `run_validation.py`; end-to-end run; sentiment-cutoff scrambling.

## What must be done next
[NEXT_ACTIONS](../../ai_context/NEXT_ACTIONS.md): finish scoring → build table → run EXP-001 → cover untested models.

## Where things are documented
Entry point [docs/README.md](../../README.md). Facts verified vs. assumptions: assumptions are labelled in [DATA_LIMITATIONS](../../data/DATA_LIMITATIONS.md) and [MODEL_LIMITATIONS](../../models/MODEL_LIMITATIONS.md).
