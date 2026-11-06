import numpy as np
import pandas as pd

from sentiment.finbert_analyzer import scores_from_probs
from sentiment.sentiment_aggregation import aggregate_daily, attach_trading_day, author_prior_activity

TZ = "America/New_York"


def test_sentiment_score_range_and_definition():
    rng = np.random.default_rng(0)
    p = rng.dirichlet([1, 1, 1], size=500)
    s = scores_from_probs(p[:, 0], p[:, 1], p[:, 2])
    assert (s["sentiment_score"] >= -1).all() and (s["sentiment_score"] <= 1).all()
    assert np.allclose(s["sentiment_score"], p[:, 0] - p[:, 2])
    assert np.allclose(p.sum(axis=1), 1)


def _posts():
    # Fri 2019-01-04 post-close (21:30Z, EST) -> rolls over weekend to Mon 2019-01-07
    ts = pd.to_datetime(["2019-01-03 15:00", "2019-01-04 21:30", "2019-01-06 12:00", "2019-01-07 13:00"], utc=True)
    return pd.DataFrame({"post_id": list("abcd"), "created_at": ts, "username": ["u1", "u1", "u2", "u1"],
                         "sentiment_score": [0.5, -0.5, 0.2, 0.9], "confidence": [0.9, 0.8, 0.7, 0.6],
                         "likes": 0, "reposts": 0, "replies": 0})


DAYS = pd.DatetimeIndex(pd.to_datetime(["2019-01-02", "2019-01-03", "2019-01-04", "2019-01-07", "2019-01-08"]))


def test_post_rolls_to_next_trading_day_no_lookahead():
    p = attach_trading_day(_posts(), DAYS, TZ)
    got = dict(zip(p["post_id"], p["trading_day"].dt.strftime("%Y-%m-%d")))
    assert got == {"a": "2019-01-03", "b": "2019-01-07", "c": "2019-01-07", "d": "2019-01-07"}


def test_empty_days_zero_count_but_nan_sentiment_not_forward_filled():
    p = attach_trading_day(_posts(), DAYS, TZ)
    p["author_prior_posts"] = author_prior_activity(p)
    agg = aggregate_daily(p, DAYS).set_index("trading_day")
    assert agg.loc["2019-01-04", "post_count"] == 0
    assert np.isnan(agg.loc["2019-01-04", "mean_sentiment"])   # not carried over from 01-03
    assert np.isnan(agg.loc["2019-01-08", "mean_sentiment"])
    assert agg.loc["2019-01-07", "post_count"] == 3
    assert abs(agg.loc["2019-01-07", "mean_sentiment"] - (-0.5 + 0.2 + 0.9) / 3) < 1e-12


def test_author_feature_is_point_in_time():
    p = _posts()
    prior = author_prior_activity(p)
    assert prior.tolist() == [0, 1, 0, 2]  # u1: 0,1,2 earlier posts; u2: 0


def test_label_resolution_handles_bullish_bearish_and_rejects_unknown():
    import pytest
    from sentiment.finbert_analyzer import resolve_label_indices
    assert resolve_label_indices({0: "positive", 1: "negative", 2: "neutral"}) == (0, 2, 1)
    assert resolve_label_indices({0: "NEUTRAL", 1: "BULLISH", 2: "BEARISH"}) == (1, 0, 2)
    with pytest.raises(ValueError):
        resolve_label_indices({0: "a", 1: "b", 2: "c"})
