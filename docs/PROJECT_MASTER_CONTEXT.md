# Project Master Context

**Read this first.** Self-contained description of the project. Facts here were checked against code, tests or data on 2026-11-05; where something is an assumption or intention it is labelled. If this file and the code disagree, the code and test output win — then fix this file.

## Project identity
- **Name:** Xanalysis — X (Twitter) sentiment-based asset price prediction research platform.
- **Purpose:** test empirically whether aggregated X sentiment adds out-of-sample predictive information about future asset prices beyond historical prices. A null result is an acceptable, reportable outcome.
- **Stage (2026-11-05):** study complete for AAPL: **no evidence that sentiment improves out-of-sample forecasts**, replicated with a second sentiment model; low power (small effects cannot be excluded). See [PROJECT_STATUS](PROJECT_STATUS.md).
- **Configured asset / timeframe:** AAPL, daily bars, exchange timezone America/New_York ([config/asset_config.yaml](../config/asset_config.yaml)). Asset is configurable; nothing is hard-coded to AAPL.
- **Horizons:** n+1 … n+5 bars ahead as targets `y_h = ln(P_{t+h}/P_t)`. n+0 (nowcast) is *not yet defined* (ML-006).
- **Stack:** Python 3.12 venv (`.venv`), pandas, DuckDB, PyArrow/Parquet, scikit-learn, LightGBM/XGBoost/CatBoost, PyTorch (CUDA) + HuggingFace FinBERT, SQLAlchemy (SQLite), yfinance, apify-client, tavily-python, pytest. GPU: Quadro P2200.

## Research objective
Primary experiment, per horizon, out-of-sample, walk-forward:
- **A** price-only features, **B** sentiment-only, **C** price + sentiment (+ interactions).
- Central question: is `Performance(C) > Performance(A)`, and is it statistically and economically meaningful? Details: [RESEARCH_OBJECTIVE](research/RESEARCH_OBJECTIVE.md), [RESEARCH_HYPOTHESES](research/RESEARCH_HYPOTHESES.md).
- News (Tavily) is excluded from the primary model; only an explicitly labelled exploratory model D may use it.

## Data sources (actual)
| Source | Status |
|---|---|
| Historical stock tweets (`data/Tweet.csv`, `Company_Tweet.csv`, 2015–2019, pre-existing) | **Used.** 1,424,481 AAPL posts extracted |
| yfinance daily prices | **Used.** 1,343 AAPL bars |
| Apify live X collection | Code written, **never run** (no credentials) |
| Tavily news | Code written, **never run** (no key) |
| Crypto/BTC CSVs (`;`-delimited, up to 11 GB) | Pre-existing, **not used**, mostly unprofiled |
| Database | Schema defined; **not used by the pipeline** (pipeline uses Parquet) |
Full inventory: [DATA_INVENTORY](data/DATA_INVENTORY.md), lineage: [DATA_LINEAGE](data/DATA_LINEAGE.md).

## Architecture in one paragraph
Raw CSV → DuckDB join/filter → raw Parquet (`data/raw/x_posts`) → cleaning/flagging (`preprocessing/text_cleaner.py`) → FinBERT scoring of unique texts (`scripts/score_sentiment.py`) → assignment of each post to the first trading day whose 16:00 ET close is ≥ post time → daily aggregation (`sentiment/sentiment_aggregation.py`) → price + sentiment + interaction features and forward targets (`features/`) → leakage gate → purged walk-forward evaluation of baselines and ML models (`validation/model_comparison.py`) → comparison A vs C with Diebold-Mariano, block bootstrap, Holm correction. Diagrams: [DATA_FLOW](architecture/DATA_FLOW.md), [SYSTEM_ARCHITECTURE](architecture/SYSTEM_ARCHITECTURE.md), module detail: [CODEBASE_MAP](engineering/CODEBASE_MAP.md) (auto-generated).

## Quantitative methodology (summary)
- **Sentiment:** FinBERT (`ProsusAI/finbert`) → P(pos), P(neu), P(neg); `S = P(pos) − P(neg)`; confidence = max class probability (not calibrated). Measured accuracy on 48 AI-labelled validation items: 0.604 — weak on slang and mixed statements. [SENTIMENT_METHODOLOGY](research/SENTIMENT_METHODOLOGY.md)
- **Aggregation:** simple, engagement-weighted (**leaky** — lifetime counts), author-weighted (prior post count only), confidence-weighted. Empty days: post_count = 0, sentiment NaN, never forward-filled.
- **Features:** causal price features, sentiment features, interactions, causal rolling z-scores. [FEATURE_ENGINEERING](research/FEATURE_ENGINEERING.md)
- **Targets / validation / tests:** [FORECASTING_METHODOLOGY](research/FORECASTING_METHODOLOGY.md), [VALIDATION_METHODOLOGY](research/VALIDATION_METHODOLOGY.md), [STATISTICAL_TESTING](research/STATISTICAL_TESTING.md).

## Current implementation status (verified 2026-11-05)
- **Verified on real data:** ingestion (historical tweets, prices, incremental price update), cleaning, two full FinBERT-family sentiment scorings, aggregation, features + leakage gates, purged walk-forward, 10 classical models, multi-output/shared-head/GRU/LSTM/TCN/Transformer, ablation, filter robustness, regimes, importance/SHAP/correlations, nowcasts, power analysis, economics, monitoring, reports/dashboard, orchestrator.
- **Tested on fixtures only:** Apify collector, Tavily + news processing, scheduler, database layer and migrations (SQLite).
- **Blocked:** live Apify and Tavily (no credentials); consequently no news layer and no point-in-time engagement.
- **Open:** human-reviewed sentiment labels, PostgreSQL verification, BTC study (out of scope, DEC-013).
- **Result:** no evidence that X sentiment improves out-of-sample forecasts ([RESEARCH_FINDINGS](research/RESEARCH_FINDINGS.md)).
Task-level truth: [MASTER_TASK_REGISTER](MASTER_TASK_REGISTER.md).

## Critical constraints
1. No future information in features. Row `t` = information available at bar `t`'s close; targets use later closes. Enforced by [features/leakage_checks.py](../features/leakage_checks.py).
2. All timestamps UTC; exchange timezone (zoneinfo, DST-aware) only for session logic. Naive timestamps require an explicit timezone.
3. Point-in-time availability: engagement counts and follower counts in the datasets are **lifetime/scrape-time** values — not point-in-time. They are excluded from the primary feature sets.
4. No random train/test split. Chronological walk-forward with purging of overlapping targets plus embargo.
5. Never tune on the final holdout; hyperparameters are tuned on a chronological validation block inside each training window.
6. News excluded from the primary price + X sentiment model.
7. Historical predictions are immutable: each run writes a new `artifacts/runs/<run_id>/`; never overwrite.
8. Reproducible: fixed seeds, pinned [requirements.txt](../requirements.txt), config in YAML.
9. Raw data (`data/*.csv`, `data/raw/`) is never modified.
10. **No git commits or pushes by AI agents** unless the user explicitly asks (user instruction 2026-11-05). See [AGENTS](ai_context/AGENTS.md).

## Instructions for AI agents
1. Read [docs/README.md](README.md), this file, [PROJECT_STATUS](PROJECT_STATUS.md), [CURRENT_CONTEXT](ai_context/CURRENT_CONTEXT.md), [SESSION_HANDOFF](ai_context/SESSION_HANDOFF.md), [NEXT_ACTIONS](ai_context/NEXT_ACTIONS.md).
2. Check [MASTER_TASK_REGISTER](MASTER_TASK_REGISTER.md) before implementing anything.
3. Inspect the actual source and compare to the docs; do not trust a previous agent's description.
4. Do not duplicate existing functionality; reuse modules in [CODEBASE_MAP](engineering/CODEBASE_MAP.md).
5. Read the relevant methodology file before changing research logic; record changes in [DECISION_LOG](decisions/DECISION_LOG.md).
6. Update documentation after every meaningful change (table in [AGENTS](ai_context/AGENTS.md)); run `python scripts/validate_documentation.py`.
7. Report results honestly, including null results. Never mark untested work as VERIFIED.
