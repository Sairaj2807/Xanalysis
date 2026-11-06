import numpy as np
import pandas as pd

from features.nowcast import build_nowcast_table
from sentiment.sentiment_aggregation import aggregate_daily, attach_trading_day
from tests.test_features import synth
from validation.model_comparison import incremental_value, run_walk_forward

TZ = "America/New_York"


def test_preopen_cutoff_assignment():
    days = pd.DatetimeIndex(pd.to_datetime(["2019-01-02", "2019-01-03", "2019-01-04"]))
    ts = pd.to_datetime(["2019-01-02 14:29:59", "2019-01-02 14:30:00", "2019-01-02 14:30:01", "2019-01-02 21:30:00"], utc=True)
    posts = pd.DataFrame({"post_id": list("abcd"), "created_at": ts})
    out = attach_trading_day(posts, days, TZ, 9, 30)               # 14:30 UTC == 09:30 EST
    got = dict(zip(out.post_id, out.trading_day.dt.strftime("%Y-%m-%d")))
    assert got == {"a": "2019-01-02", "b": "2019-01-02", "c": "2019-01-03", "d": "2019-01-03"}


def test_nowcast_features_never_see_the_target_day_price():
    px, agg = synth(300)
    t0, sets = build_nowcast_table(px, agg)
    k = 200
    px2 = px.copy()
    px2.iloc[k] = px2.iloc[k] * 1.5                                 # change day k's whole bar (incl. close)
    t1, _ = build_nowcast_table(px2, agg)
    feats = sets["A_price"]
    assert np.allclose(t0.iloc[k][feats].to_numpy(float), t1.iloc[k][feats].to_numpy(float), equal_nan=True)
    assert not np.isclose(t0.iloc[k]["y_0"], t1.iloc[k]["y_0"])    # but the target does change
    # target identity and reconstruction
    assert np.isclose(t0.iloc[k]["price"] * np.exp(t0.iloc[k]["y_0"]), px.close.iloc[k])


def test_nowcast_detects_planted_same_day_sentiment_signal():
    rng = np.random.default_rng(2)
    n = 700
    idx = pd.bdate_range("2016-01-01", periods=n, name="trading_day")
    s = rng.normal(0, 1, n)
    r = 0.01 * s + rng.normal(0, 0.005, n)                           # today's return depends on today's pre-open sentiment
    close = 100 * np.exp(np.cumsum(r))
    px = pd.DataFrame({"open": close, "high": close * 1.002, "low": close * 0.998, "close": close}, index=idx)
    agg = pd.DataFrame({"trading_day": idx, "post_count": 20.0, "positive_count": 7, "negative_count": 7,
                        "neutral_count": 6, "mean_sentiment": s, "median_sentiment": s, "sentiment_std": 0.2,
                        "sent_engagement_w": s, "sent_author_w": s, "sent_confidence_w": s, "engagement_total": 5.0,
                        "unique_authors": 10, "sentiment_confidence": 0.8, "had_posts": True,
                        "positive_ratio": 0.35, "negative_ratio": 0.35, "sentiment_change": 0.0})
    table, sets = build_nowcast_table(px, agg)
    p = run_walk_forward(table.dropna(subset=["y_0"]), sets, ["ridge"], [0], 300, 60, val_len=60)
    inc = incremental_value(p, "ridge")
    assert inc.loc[0, "improvement_rmse_pct"] > 20 and inc.loc[0, "dm_p"] < 0.001


def test_intraday_variant_uses_open_gap_but_never_same_day_high_low_close():
    px, agg = synth(300)
    t0, sets = build_nowcast_table(px, agg, target="intraday")
    assert "px_gap" in sets["A_price"] and "px_gap" in sets["C_combined"]
    k = 200
    px2 = px.copy()
    for col in ("high", "low", "close"):
        px2.iloc[k, px2.columns.get_loc(col)] *= 1.3                # change everything about day k EXCEPT its open
    t1, _ = build_nowcast_table(px2, agg, target="intraday")
    f = sets["C_combined"]
    assert np.allclose(t0.iloc[k][f].to_numpy(float), t1.iloc[k][f].to_numpy(float), equal_nan=True)
    assert not np.isclose(t0.iloc[k]["y_0"], t1.iloc[k]["y_0"])
    assert np.isclose(t0.iloc[k]["price"] * np.exp(t0.iloc[k]["y_0"]), px.close.iloc[k])   # open * exp(y) = close
    assert np.isclose(t0.iloc[k]["px_gap"], np.log(px.open.iloc[k] / px.close.iloc[k - 1]))
