"""Diagnose WHY pre-open sentiment correlates with the same-day return (EXP-009 follow-up).

Splits the sentiment of each trading day into a PRE-OPEN block (day D-1 16:00 .. D 09:30) and a SESSION block
(D 09:30 .. 16:00), and splits the day's return into the overnight GAP (close D-1 -> open D, already realised at
09:30) and INTRADAY (open D -> close D, genuinely unknown at 09:30). Correlations (Spearman) answer:
 * does pre-open sentiment merely echo the gap that has already happened?
 * does it predict the intraday part (the only part still unknown at 09:30)?
 * does session sentiment (which is contemporaneous with intraday moves) correlate far more strongly?
 * does lagged sentiment predict anything (the n+1 question again)?
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from config.settings import ROOT, load_settings  # noqa: E402
from scripts.build_features import FILTERS  # noqa: E402
from sentiment.finbert_analyzer import model_tag  # noqa: E402
from sentiment.sentiment_aggregation import attach_trading_day  # noqa: E402


def block_sentiment(px: pd.DataFrame, posts: pd.DataFrame, tz: str) -> pd.DataFrame:
    d = attach_trading_day(posts, px.index, tz, 16, 0)
    open_local = (d["trading_day"] + pd.Timedelta(hours=9, minutes=30)).dt.tz_localize(tz, ambiguous="NaT", nonexistent="NaT")
    created = d["created_at"].dt.tz_localize("UTC") if d["created_at"].dt.tz is None else d["created_at"].dt.tz_convert("UTC")
    d["block"] = np.where(created < open_local.dt.tz_convert("UTC"), "pre_open", "session")
    g = d.groupby(["trading_day", "block"])["sentiment_score"].agg(["mean", "size"]).unstack("block")
    out = pd.DataFrame({"s_pre": g[("mean", "pre_open")], "s_session": g[("mean", "session")],
                        "n_pre": g[("size", "pre_open")], "n_session": g[("size", "session")]})
    return out.reindex(px.index)


def main(sent_model: str | None = None) -> pd.DataFrame:
    a = load_settings().asset
    tag = model_tag(sent_model) if sent_model else ""
    px = pd.read_parquet(ROOT / "data" / "raw" / "prices" / f"{a.symbol}_{a.bar_interval}.parquet")
    px["trading_day"] = px["bar_start_utc"].dt.tz_localize(None).dt.normalize()
    px = px.set_index("trading_day").sort_index()
    posts = pd.read_parquet(ROOT / "data" / "processed" / f"posts_{a.symbol}.parquet")
    sent = pd.read_parquet(ROOT / "data" / "processed" / f"sentiment_{a.symbol}{tag}.parquet")
    d = posts.merge(sent[["post_id", "sentiment_score"]], on="post_id")
    d = d[FILTERS["primary"](d)]
    b = block_sentiment(px, d, a.exchange_timezone)
    r = pd.DataFrame({
        "gap": np.log(px["open"] / px["close"].shift(1)),
        "intraday": np.log(px["close"] / px["open"]),
        "total": np.log(px["close"] / px["close"].shift(1)),
    })
    df = pd.concat([b, r], axis=1).loc["2015-02-02":"2019-12-31"].dropna(subset=["s_pre", "s_session", "gap", "intraday"])
    df["s_session_lag"] = df["s_session"].shift(1)
    df["s_pre_lag"] = df["s_pre"].shift(1)
    rows = []
    for s in ("s_pre", "s_session", "s_session_lag", "s_pre_lag"):
        for tgt in ("gap", "intraday", "total"):
            x = df[[s, tgt]].dropna()
            rho = x.corr(method="spearman").iloc[0, 1]
            # permutation-free standard error approximation for Spearman
            se = 1 / np.sqrt(len(x) - 1)
            rows.append({"sentiment_block": s, "return_part": tgt, "spearman": rho, "approx_z": rho / se, "n": len(x)})
    res = pd.DataFrame(rows)
    print(res.round(4).to_string(index=False))
    print("\nshare of daily total-return variance from gap vs intraday:",
          (df["gap"].var() / df["total"].var()).round(3), (df["intraday"].var() / df["total"].var()).round(3))
    return res


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
