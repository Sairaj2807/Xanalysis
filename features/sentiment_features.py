"""Sentiment features from the per-day aggregate (rows already respect the close cutoff)."""
from __future__ import annotations

import numpy as np
import pandas as pd

LEAKY = {"sent_engagement_w", "engagement_total", "engagement_log"}  # lifetime counts, not point-in-time


def rolling_z(s: pd.Series, w: int = 60, min_periods: int = 20) -> pd.Series:
    """Causal z-score: mean/std from the trailing window only (current value included - it is observed)."""
    mu, sd = s.rolling(w, min_periods=min_periods).mean(), s.rolling(w, min_periods=min_periods).std()
    return (s - mu) / sd.replace(0, np.nan)


def sentiment_features(agg: pd.DataFrame, include_leaky: bool = False) -> pd.DataFrame:
    a = agg.set_index("trading_day") if "trading_day" in agg.columns else agg
    f = pd.DataFrame(index=a.index)
    m = a["mean_sentiment"]
    f["sent_mean"] = m
    f["sent_median"] = a["median_sentiment"]
    f["sent_author_w"] = a["sent_author_w"]
    f["sent_conf_w"] = a["sent_confidence_w"]
    f["sent_std"] = a["sentiment_std"]
    f["pos_ratio"] = a["positive_ratio"]
    f["neg_ratio"] = a["negative_ratio"]
    f["pos_neg_imbalance"] = a["positive_ratio"] - a["negative_ratio"]
    f["sent_confidence"] = a["sentiment_confidence"]
    f["post_count"] = a["post_count"]
    f["log_post_count"] = np.log1p(a["post_count"])
    f["unique_authors"] = a["unique_authors"]
    f["had_posts"] = a["had_posts"].astype(float)
    # lags / dynamics are computed over OBSERVED days only; gaps stay NaN (not filled)
    f["sent_lag1"] = m.shift(1)
    f["sent_lag2"] = m.shift(2)
    f["sent_mom_1"] = m - m.shift(1)
    f["sent_accel"] = f["sent_mom_1"] - f["sent_mom_1"].shift(1)
    for w in (3, 5, 10):
        f[f"sent_ma_{w}"] = m.rolling(w, min_periods=max(1, w // 2)).mean()
    f["sent_vol_10"] = m.rolling(10, min_periods=5).std()
    pc = a["post_count"]
    f["post_vol_change"] = pc.pct_change().replace([np.inf, -np.inf], np.nan)
    f["post_vol_accel"] = pc.diff().diff()
    f["sent_z"] = rolling_z(m)
    f["post_count_z"] = rolling_z(np.log1p(pc))
    if include_leaky:
        f["sent_engagement_w"] = a["sent_engagement_w"]
        f["engagement_log"] = np.log1p(a["engagement_total"])
    return f
