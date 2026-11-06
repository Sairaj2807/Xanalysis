# Database Architecture

Defined in [database/models.py](../../database/models.py); engine/session/upsert in [database/connection.py](../../database/connection.py). `create_all` is used; no migrations (DB-002).

**Update 2026-11-05:** repositories, Alembic migrations (up/down tested) and SQLite immutability triggers are implemented and tested; `model_predictions` now has model_name/feature_set/fold (BUG-010). The original status text follows.

**Status (original):** schema TESTED for one path (idempotent insert into `raw_x_posts`, in-memory SQLite). **The pipeline does not read or write the database**; it uses Parquet (DEC-004). The default file `artifacts/xanalysis.db` has not been created.

| Table | Purpose | Key / constraints | Used by pipeline |
|---|---|---|---|
| raw_x_posts | Raw posts | PK post_id | No |
| sentiment_predictions | Post-level sentiment | UNIQUE(post_id, model_name), FK → raw_x_posts | No |
| historical_prices | OHLCV | UNIQUE(symbol, interval, bar_start_utc) | No |
| news_articles | News metadata/content | PK article_id, UNIQUE(url) | No |
| model_runs | Run config/metrics | PK run_id | No |
| model_predictions | Append-only forecasts | UNIQUE(run_id, asset, prediction_ts, horizon), FK → model_runs | No |
| ingestion_logs | Collection history/state | PK id | No |

**Not implemented vs specification:** `processed_x_posts`, `sentiment_aggregates`, `news_sentiment`, `model_features` tables; migrations; Timescale; PostgreSQL upsert (BUG-006); repositories layer. Conventions: UTC naive datetimes, FK enforcement on SQLite, transactional `session_scope`.

## Current state (2026-11-05)
- Tables: raw_x_posts, sentiment_predictions, historical_prices, news_articles, model_runs, model_predictions, ingestion_logs (+ alembic_version). Not implemented as separate tables: processed_x_posts, sentiment_aggregates, news_sentiment, model_features (kept as Parquet).
- Migrations: `database/migrations/versions/*_initial_schema.py` (extended by hand with the SQLite triggers). Apply with `alembic upgrade head` (URL from `DATABASE_URL`).
- Persistence helpers: [database/repositories.py](../../database/repositories.py); forecast storage: [prediction/prediction_storage.py](../../prediction/prediction_storage.py).
- Untested: PostgreSQL/Timescale; PostgreSQL immutability trigger not written.
