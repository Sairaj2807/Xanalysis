# Project Architecture (proposed)

Greenfield build following the layout in the master spec, adapted to the actual data.

## Principles
- Raw data is immutable. Derived artifacts go to Parquet under `data/processed|aggregated|model_ready`.
- Large CSVs are processed with DuckDB (out-of-core); pandas only on aggregated bars.
- All timestamps stored UTC; exchange timezone applied only for session logic (zoneinfo, DST-safe).
- Each pipeline stage is a standalone script plus importable module, with checkpoints.
- Database: SQLite for dev/tests via SQLAlchemy + Alembic; PostgreSQL/Timescale by URL switch. Bulk research data lives in Parquet; the DB holds ingestion state, predictions, model runs.

## Layers
1. ingestion/: Apify, Tavily, price clients (live). Legacy loaders adapt existing CSVs into the same raw schema.
2. preprocessing/: cleaning, dedup, timestamp normalization (handles the 3 formats in audit F5).
3. sentiment/: FinBERT analyzer (configurable), VADER adapter for existing scores, four aggregation methods.
4. features/: price, sentiment, interaction features; leakage checks.
5. models/ and validation/: baselines, classical ML, optional DL, purged walk-forward, metrics, Diebold-Mariano, multiple-comparison correction.
6. prediction/: append-only forecast store.
7. visualization/ and reporting/: Plotly dashboard, one-page outlook.
8. monitoring/: drift and data-quality checks.

Open decisions are listed in IMPLEMENTATION_PLAN.md.
