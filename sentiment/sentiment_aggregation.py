"""Aggregate post-level sentiment into per-trading-day features with an information cutoff.

A post belongs to the feature row of the first trading day whose close is >= the post time
(posts after the close, on weekends or holidays roll forward to the next trading day). A row dated D
therefore only contains information available at D's close; targets use closes after D.

Weighting methods: A simple, B engagement (LEAKY: lifetime counts, not point-in-time),
C author (prior post count only - point-in-time), D confidence.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from preprocessing.timestamp_alignment import assign_daily_bar


def author_prior_activity(posts: pd.DataFrame) -> pd.Series:
    """Point-in-time author feature: number of posts the author made strictly before this one."""
    p = posts.sort_values(["created_at", "post_id"], kind="stable")
    return p.groupby("username").cumcount().reindex(posts.index)


def attach_trading_day(posts: pd.DataFrame, trading_days: pd.DatetimeIndex, tz: str,
                        cutoff_hour: int = 16, cutoff_minute: int = 0) -> pd.DataFrame:
    created = posts["created_at"]
    if created.dt.tz is None:
        created = created.dt.tz_localize("UTC")
    bucket = assign_daily_bar(created, tz, cutoff_hour, cutoff_minute).rename("bucket").astype("datetime64[ns]")
    td = pd.DataFrame({"trading_day": pd.DatetimeIndex(trading_days).astype("datetime64[ns]")}).sort_values("trading_day")
    m = pd.merge_asof(bucket.sort_values().reset_index().rename(columns={"index": "_i"}), td,
                      left_on="bucket", right_on="trading_day", direction="forward")
    out = posts.copy()
    out["trading_day"] = m.set_index("_i")["trading_day"].reindex(posts.index)
    return out.dropna(subset=["trading_day"])


def _wmean(v: pd.Series, w: pd.Series) -> float:
    s = w.sum()
    return float((v * w).sum() / s) if s > 0 else np.nan


def aggregate_daily(posts: pd.DataFrame, trading_days: pd.DatetimeIndex, pos_thr: float = 0.05,
                    neg_thr: float = -0.05) -> pd.DataFrame:
    """posts needs: trading_day, sentiment_score, confidence, username, likes, reposts, replies,
    author_prior_posts. Days with no posts get post_count=0 and NaN sentiment (never forward-filled)."""
    d = posts.copy()
    d["w_eng"] = 1 + np.log1p(d[["likes", "reposts", "replies"]].sum(axis=1))
    d["w_author"] = 1 + np.log1p(d["author_prior_posts"])
    d["w_conf"] = d["confidence"]
    d["engagement"] = d[["likes", "reposts", "replies"]].sum(axis=1)
    rows = []
    for day, g in d.groupby("trading_day", sort=True):
        s = g["sentiment_score"]
        rows.append({
            "trading_day": day, "post_count": len(g),
            "positive_count": int((s > pos_thr).sum()), "negative_count": int((s < neg_thr).sum()),
            "neutral_count": int(s.between(neg_thr, pos_thr).sum()),
            "mean_sentiment": s.mean(), "median_sentiment": s.median(), "sentiment_std": s.std(ddof=0),
            "sent_engagement_w": _wmean(s, g["w_eng"]),     # LEAKY: lifetime engagement
            "sent_author_w": _wmean(s, g["w_author"]),
            "sent_confidence_w": _wmean(s, g["w_conf"]),
            "engagement_total": float(g["engagement"].sum()),  # LEAKY: lifetime engagement
            "unique_authors": g["username"].nunique(), "sentiment_confidence": g["confidence"].mean(),
        })
    agg = pd.DataFrame(rows).set_index("trading_day")
    agg = agg.reindex(pd.DatetimeIndex(trading_days, name="trading_day"))
    agg["had_posts"] = agg["post_count"].notna()
    for c in ["post_count", "positive_count", "negative_count", "neutral_count", "unique_authors", "engagement_total"]:
        agg[c] = agg[c].fillna(0)   # zero activity is a real observation ...
    # ... but sentiment statistics stay NaN on empty days (missing, not "unchanged").
    agg["positive_ratio"] = agg["positive_count"] / agg["post_count"].where(agg["post_count"] > 0)
    agg["negative_ratio"] = agg["negative_count"] / agg["post_count"].where(agg["post_count"] > 0)
    agg["sentiment_change"] = agg["mean_sentiment"].diff()
    return agg.reset_index()
