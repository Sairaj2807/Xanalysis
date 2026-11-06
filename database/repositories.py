"""Persistence helpers. Bulk research data stays in Parquet; these store state, runs and forecasts."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import select, text

from database.connection import insert_ignore_duplicates, session_scope
from database.models import HistoricalPrice, IngestionLog, ModelPrediction, ModelRun, RawXPost


def _naive_utc(s: pd.Series) -> pd.Series:
    s = pd.to_datetime(s, utc=True)
    return s.dt.tz_convert("UTC").dt.tz_localize(None)


def _records(df: pd.DataFrame) -> list[dict]:
    return df.astype(object).where(df.notna(), None).to_dict("records")


def save_prices(engine, df: pd.DataFrame) -> int:
    d = df.copy()
    d["bar_start_utc"] = _naive_utc(d["bar_start_utc"])
    cols = [c for c in ["symbol", "interval", "bar_start_utc", "open", "high", "low", "close", "adj_close", "volume"] if c in d]
    rows = _records(d[cols])
    for r in rows:
        r["bar_start_utc"] = pd.Timestamp(r["bar_start_utc"]).to_pydatetime()
    with session_scope(engine) as s:
        return insert_ignore_duplicates(s, HistoricalPrice, rows)


def save_raw_posts(engine, df: pd.DataFrame) -> int:
    d = df.copy()
    d["created_at"] = _naive_utc(d["created_at"])
    cols = [c for c in ["post_id", "asset_symbol", "created_at", "text", "username", "author_id", "followers_count",
                        "likes", "reposts", "replies", "views", "language", "query_source", "collected_at"] if c in d]
    rows = _records(d[cols])
    for r in rows:
        r["created_at"] = pd.Timestamp(r["created_at"]).to_pydatetime()
    with session_scope(engine) as s:
        return insert_ignore_duplicates(s, RawXPost, rows)


def register_run(engine, run_id: str, model_name: str, feature_set: str, config: dict, metrics: dict | None = None,
                 artifact_path: str | None = None) -> None:
    with session_scope(engine) as s:
        insert_ignore_duplicates(s, ModelRun, [{
            "run_id": run_id, "created_at": datetime.now(timezone.utc).replace(tzinfo=None), "model_name": model_name,
            "feature_set": feature_set, "config": json.loads(json.dumps(config, default=str)),
            "metrics": json.loads(json.dumps(metrics, default=str)) if metrics else None, "artifact_path": artifact_path}])


def save_predictions(engine, run_id: str, asset: str, preds: pd.DataFrame) -> int:
    """Append-only: existing rows are never modified (ON CONFLICT DO NOTHING + DB triggers on SQLite).
    `preds` uses the long format produced by validation.model_comparison.run_walk_forward."""
    ts = pd.to_datetime(preds["ts"])
    ts = ts.dt.tz_localize(None) if ts.dt.tz is None else ts.dt.tz_convert("UTC").dt.tz_localize(None)
    rows = []
    for r, t in zip(preds.itertuples(index=False), ts):
        rows.append({"run_id": run_id, "asset": asset, "model_name": r.model, "feature_set": r.feature_set,
                     "fold": int(r.fold), "prediction_ts": t.to_pydatetime(), "horizon": int(r.horizon),
                     "pred_return": float(r.y_pred), "pred_price": float(r.pred_price),
                     "actual_return": None if pd.isna(r.y_true) else float(r.y_true),
                     "actual_price": None if pd.isna(r.actual_price) else float(r.actual_price)})
    with session_scope(engine) as s:
        return insert_ignore_duplicates(s, ModelPrediction, rows)


def load_predictions(engine, run_id: str) -> pd.DataFrame:
    with engine.connect() as c:
        return pd.read_sql(text("SELECT * FROM model_predictions WHERE run_id = :r"), c, params={"r": run_id})


def log_ingestion(engine, source: str, started: datetime, status: str, n_retrieved: int = 0, n_new: int = 0,
                  n_duplicate: int = 0, latest_post_ts: datetime | None = None, last_post_id: str | None = None,
                  error: str | None = None) -> None:
    with session_scope(engine) as s:
        s.add(IngestionLog(source=source, started_at=started,
                           finished_at=datetime.now(timezone.utc).replace(tzinfo=None), status=status,
                           n_retrieved=n_retrieved, n_new=n_new, n_duplicate=n_duplicate,
                           latest_post_ts=latest_post_ts, last_post_id=last_post_id, error=error))


def last_successful_collection(engine, source: str) -> IngestionLog | None:
    with session_scope(engine) as s:
        row = s.execute(select(IngestionLog).where(IngestionLog.source == source,
                                                   IngestionLog.status.in_(["ok", "partial"]))
                        .order_by(IngestionLog.id.desc()).limit(1)).scalars().first()
        if row:
            s.expunge(row)
        return row
