"""Data-quality monitoring: missing trading days, post-volume anomalies, ingestion failures."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sqlalchemy import text


def missing_periods(daily: pd.DataFrame, trading_days: pd.DatetimeIndex, min_posts: int = 1) -> pd.DataFrame:
    """Trading days with no data row at all (missing) vs rows present but below `min_posts` (thin)."""
    d = daily.set_index("trading_day") if "trading_day" in daily.columns else daily
    out = pd.DataFrame(index=pd.DatetimeIndex(trading_days, name="trading_day"))
    out["post_count"] = d["post_count"].reindex(out.index)
    out["status"] = np.where(out["post_count"].isna(), "missing", np.where(out["post_count"] < min_posts, "thin", "ok"))
    return out[out["status"] != "ok"]


def volume_anomalies(post_count: pd.Series, window: int = 60, z: float = 3.0) -> pd.DataFrame:
    """Days whose log post count deviates > z robust sigmas from the trailing median (past data only)."""
    lp = np.log1p(post_count)
    med = lp.rolling(window, min_periods=20).median().shift(1)
    mad = (lp - med).abs().rolling(window, min_periods=20).median().shift(1) * 1.4826
    score = (lp - med) / mad.replace(0, np.nan)
    res = pd.DataFrame({"post_count": post_count, "robust_z": score})
    return res[res["robust_z"].abs() > z]


def ingestion_failures(engine, since: str | None = None) -> pd.DataFrame:
    q = "SELECT source, started_at, status, n_retrieved, n_new, error FROM ingestion_logs WHERE status != 'ok'"
    if since:
        q += " AND started_at >= :since"
    with engine.connect() as c:
        return pd.read_sql(text(q), c, params={"since": since} if since else {})
