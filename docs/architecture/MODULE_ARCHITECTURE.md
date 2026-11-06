# Module Architecture

Per-file inventory (auto-generated): [CODEBASE_MAP](../engineering/CODEBASE_MAP.md). Capability status: [IMPLEMENTATION_TRACKER](../engineering/IMPLEMENTATION_TRACKER.md).

| Package | Responsibility | Depends on |
|---|---|---|
| config | Typed settings + asset YAML | pydantic, yaml |
| ingestion | Source adapters (legacy CSV, yfinance, Apify, Tavily) | config |
| preprocessing | Cleaning, flags, timestamp/cutoff logic | pandas |
| sentiment | FinBERT scoring, validation, daily aggregation | preprocessing, torch, transformers |
| features | Price/sentiment/interaction features, targets, leakage checks | sentiment output |
| models | Model registry (sklearn/boosters) | sklearn, lightgbm, xgboost, catboost |
| validation | Walk-forward splits, metrics, statistical tests, runner | models, features |
| database | SQLAlchemy schema/session | sqlalchemy |
| scripts | One entry point per pipeline stage + doc tooling | all |
| prediction, visualization, reporting, monitoring | Planned; empty packages | — |

Rule: logic in packages, orchestration in `scripts/`; scripts never contain research logic that is not importable and testable.
